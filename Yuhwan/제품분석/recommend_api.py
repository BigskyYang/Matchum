"""개인별 영양제 추천 함수 (개인화 트랙용, 준혁님 전달)

04_제품추천.py(유형 기반)의 추천 로직을 그대로 쓰되, 입력을 '군집'에서 '개인'으로 바꾼 것.
  - 입력: 개인별 부족 위험(재준님 모델 결과) + 본인 정보(성별·나이·흡연·안전 문항)
  - 필터: 군집 평균(성비·평균나이·흡연율) 대신 본인 성별·나이·흡연
  - 안전 문항: 해당 성분이 든 제품은 '조용히' 후보에서 뺌. 화면에는 "피하세요" 같은 안내를 하지 않고
    공통 문구 "질환이 있거나 약을 드시고 계시면 전문가와 상담하세요"만 보여줌 (11/3 회의 의료법 원칙)
  - 표현: 처방 뉘앙스 금지 → "이런 제품은 어떨까요?" 수준

사용 예
    from recommend_api import Recommender
    rec = Recommender()                                   # 제품 데이터 1번만 읽음
    out = rec.recommend(
        needs={'iron': 'High', 'protein': 'High', 'vitamin_c': 'Mid'},   # 재준님 targets.json 키 또는 한글 이름
        profile={'sex': '남자', 'age': 45, 'smoker': True,
                 'pregnant_or_breastfeeding': False, 'kidney_disease_or_stones': False,
                 'anticoagulant_or_aspirin': False, 'current_supplements': ['비타민D']},
        type_nutrients=['비타민D'],                        # (선택) 내 유형의 유형특이 영양소 = 보조 판단 지표
    )

필요 파일 (01·02·03 실행 결과): output/product_types.csv, output/product_features.csv, 원본 식약처 CSV
"""
from pathlib import Path
import re
import warnings
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '제품분석' / 'output'

# ── 설정 (결과 보기 전에 정한 값) ──
LEVEL_WEIGHT = {'High': 1.0, 'Mid': 0.5, 'Low': 0.0}   # 재준님 위험 구간 → 가중치 (04의 유형특이 1.0 / 공통주의 0.5와 같은 척도)
CORE_LEVEL = 1.0                                       # 이 가중치 이상 = 핵심 영양소 (04의 '유형특이' 자리)
TYPE_BONUS = 0.1                                       # 보조 지표: 내 유형의 유형특이 영양소가 개인 결과에도 있으면 가중치 +0.1
TYPE_ONLY_WEIGHT = 0.3                                 # 보조 지표: 개인 모델에 없는 영양소(비타민D·E)만 유형 결과로 0.3 추가
K_TYPES, FALLBACK, TOP_N = 3, 0.90, 3
CONSULT_MSG = '질환이 있거나 약을 드시고 계시면 전문가와 상담하세요.'
HEADER_MSG = '부족하기 쉬운 영양소를 채우는 데 이런 제품은 어떨까요?'

# 재준님 targets.json 키 → 우리 영양소 이름
JAEJUN_KEY = {'protein': '단백질', 'calcium': '칼슘', 'magnesium': '마그네슘', 'iron': '철', 'zinc': '아연',
              'phosphorus': '인', 'vitamin_a': '비타민A', 'vitamin_b1': '티아민', 'vitamin_b2': '리보플라빈',
              'folate': '엽산', 'vitamin_c': '비타민C', 'fiber': '식이섬유', 'potassium': '칼륨', 'sodium_excess': '나트륨과다',
              'vitamin_d': '비타민D', 'vitamin_e': '비타민E'}
COLMAP = {'단백질': '단백질', '비타민A': '비타민 A', '비타민D': '비타민 D', '비타민E': '비타민 E', '비타민C': '비타민 C',
          '티아민': '티아민', '리보플라빈': '리보플라빈', '엽산': '엽산', '칼슘': '칼슘', '마그네슘': '마그네슘',
          '철': '철', '아연': '아연', '식이섬유': '식이섬유'}
FOOD_ONLY = {'인': '인은 식품으로 충분히 섭취돼 영양제 대상이 아니에요', '칼륨': '칼륨은 채소·과일 등 식품으로 채우는 영양소예요',
             '나트륨과다': '나트륨은 줄이는 것이 목표라 영양제 대상이 아니에요'}
NOT_IN_MODEL = {'비타민D', '비타민E'}                   # 재준님 개인 모델 예측 대상에 없음
QUANT = {'단백질', '식이섬유', '칼슘', '철', '비타민 A', '비타민 D', '비타민 C', '티아민', '리보플라빈', '니아신'}
REFERENCE = ['오메가3', '유산균', '루테인', '밀크씨슬', '비타민 K']
FORMS = ['D3', 'rTG', '리포좀', '활성엽산', '활성비타민B', '장용성']
# 안전 문항 → 조용히 뺄 성분 (Jaejun/config/supplement_safety_rules.json과 같은 매핑)
SAFETY_EXCLUDE = {'kidney_disease_or_stones': ['calcium', 'potassium', 'phosphorus'],
                  'anticoagulant_or_aspirin': ['omega3', 'vitamin_k']}


RANK = {'Low': 0, 'Mid': 1, 'High': 2}


def needs_from_model(lifestyle, habitual=None):
    """재준님 모델 결과(영양소별 Lifestyle / Habitual Low·Mid·High, 두 신호는 평균하지 않음) → recommend()의 needs

    합치는 규칙(제안, 팀 확인 필요): 확률은 평균하지 않고 '두 구간 중 높은 쪽'을 씀
      예) Lifestyle Mid + Habitual High → High / mini-FFQ가 없는 영양소(65세 이상 등)는 Lifestyle만
    반환: (needs, 근거)  근거 = 화면 설명용 {'calcium': 'Lifestyle Mid · Habitual High'}
    """
    habitual = habitual or {}
    needs, basis = {}, {}
    for k in set(lifestyle) | set(habitual):
        a, b = lifestyle.get(k), habitual.get(k)
        levels = [x for x in (a, b) if x in RANK]
        if not levels:
            continue
        needs[k] = max(levels, key=RANK.get)
        basis[k] = ' · '.join(f'{s} {x}' for s, x in (('Lifestyle', a), ('Habitual', b)) if x in RANK)
    return needs, basis


def _norm_name(s):
    return re.sub(r'[\(\[].*?[\)\]]|\d+\s*(정|캡슐|포|ml|mg|g|개|병)|\s', '', str(s))[:12]


def _pick(df, score, n=TOP_N):
    df = df.assign(score=score).sort_values('score', ascending=False)
    out, seen_m, seen_n = [], set(), set()
    for _, r in df.iterrows():
        if r['score'] <= 0 or r['제조사명'] in seen_m or _norm_name(r['식품명']) in seen_n:
            continue
        out.append(r); seen_m.add(r['제조사명']); seen_n.add(_norm_name(r['식품명']))
        if len(out) == n:
            break
    return pd.DataFrame(out)


class Recommender:
    def __init__(self, out_dir=OUT, raw_csv=ROOT / '전국건강기능식품영양성분정보표준데이터.csv', price_file=None):
        warnings.simplefilter('ignore', pd.errors.PerformanceWarning)   # 열을 하나씩 붙여서 생기는 성능 경고 (결과와 무관)
        p = pd.read_csv(out_dir / 'product_types.csv', encoding='utf-8-sig', low_memory=False)
        f = pd.read_csv(out_dir / 'product_features.csv', encoding='utf-8-sig', low_memory=False)
        new = [c for c in f.columns if c not in p.columns]
        p = p.merge(f[['식품코드'] + new].drop_duplicates('식품코드'), on='식품코드', how='left')
        p['주목적_기능성'] = p['주목적_기능성'].fillna('')
        raw = pd.read_csv(raw_csv, encoding='cp949', low_memory=False)
        p = p.merge(raw[['식품코드', '에너지(kcal)']].drop_duplicates('식품코드'), on='식품코드', how='left')
        p['식사대용'] = p['에너지(kcal)'].fillna(0) * p['n_day'] >= 200
        nm = p['식품명'].fillna('')
        p['대상_제외'] = nm.str.contains(r'키즈|어린이|유아|주니어|청소년|베이비|키디|kids|junior|children|임산부|임신|맘스|프리나탈|prenatal|수유', case=False, regex=True)
        p['대상_여성'] = nm.str.contains(r'우먼|여성|레이디|woman|women|for\s?her', case=False, regex=True)
        p['대상_남성'] = nm.str.contains(r'남성|맨즈|포\s?맨|실버맨|for\s?men|\bmen\b|\bman\b', case=False, regex=True)
        p['대상_실버'] = nm.str.contains(r'실버|시니어|50\+|50플러스|silver|senior', case=False, regex=True)
        safety = {'calcium': (p['일_칼슘'].fillna(0) > 0) | nm.str.contains('칼슘|calcium', case=False),
                  'potassium': (p['일_칼륨'].fillna(0) > 0) | nm.str.contains('칼륨|potassium', case=False),
                  'phosphorus': p['일_인'].fillna(0) > 0,
                  'omega3': p['has_오메가3'] == 1, 'vitamin_k': p['has_비타민 K'] == 1}
        for k, s in safety.items():
            p[f'safety_{k}'] = s.astype(bool)
        self.V = [c for c in p.columns if c.startswith('v_')]
        Xv = p[self.V].astype(float).copy()
        qcols = [f'v_{q}' for q in QUANT]
        kind = p['군집변환'].iat[0]
        Xv[qcols] = np.log1p(Xv[qcols] / 100) if kind == 'log' else np.minimum(Xv[qcols], 300 if kind == 'cap300' else 100) / 100
        p['주성분'] = Xv.apply(lambda r: '·'.join(c[2:] for c in r.sort_values(ascending=False).index[:3] if r[c] > 0), axis=1)
        self.cent = Xv.groupby(p['제품유형명']).mean()
        # 가격: 가격조사_대상.xlsx에 가격이 30개 이상 있으면 가성비형 활성화
        price_file = price_file or out_dir / '가격조사_대상.xlsx'
        if Path(price_file).exists():
            from price_file import read_price_file
            pr = read_price_file(price_file)
            pr = pr[pd.to_numeric(pr['판매가격(원)'], errors='coerce').gt(0) & pd.to_numeric(pr['총개수'], errors='coerce').gt(0)]
            pr['price_per_day'] = pr['판매가격(원)'].astype(float) / (pr['총개수'].astype(float) / pr['1일개수'].astype(float))
            p = p.merge(pr[['식품코드', 'price_per_day']], on='식품코드', how='left')
        self.has_price = 'price_per_day' in p.columns and p['price_per_day'].notna().sum() >= 30
        self.p = p.copy()

    def _coverage(self, col):
        v = self.p[f'v_{col}'].astype(float)
        return np.minimum(v / 100, 1) if col in QUANT else v * 0.3     # 함량 미상 = 고시형 최소 30% 가정

    @staticmethod
    def _weights(needs, type_nutrients):
        """needs: {영양소: 'High'/'Mid'/'Low' 또는 0~1 숫자} → (제품 매칭용 가중치, 식품으로만 안내할 영양소)"""
        w, food = {}, []
        for k, v in needs.items():
            n = JAEJUN_KEY.get(k, k)
            x = LEVEL_WEIGHT.get(v, v) if isinstance(v, str) else float(v)
            if x <= 0:
                continue
            if n in FOOD_ONLY:
                food.append(n)
            elif n in COLMAP:
                w[n] = max(w.get(n, 0), x)
        for n in type_nutrients or []:             # 보조 판단 지표 (유형 결과)
            n = JAEJUN_KEY.get(n, n)
            if n in w:
                w[n] = min(1.0, w[n] + TYPE_BONUS)
            elif n in NOT_IN_MODEL and n in COLMAP:
                w[n] = TYPE_ONLY_WEIGHT
        return w, food

    def recommend(self, needs, profile=None, type_nutrients=None):
        profile = profile or {}
        base = {'안내': HEADER_MSG, '상담안내': CONSULT_MSG, '참고정보(순위없음)': REFERENCE}
        # 임신·수유: 일반 성인 기준 자동 추천 중단 (supplement_safety_rules.json) → 상담 안내만
        if profile.get('pregnant_or_breastfeeding'):
            return {**base, '상태': '상담안내', '안내': '임신·수유 중에는 필요한 영양소 기준이 달라요. 전문가와 상담해 보세요.', '장르': {}}
        wd, food = self._weights(needs, type_nutrients)
        out = {**base, '상태': 'ok', '식품으로만': [{'영양소': n, '설명': FOOD_ONLY[n]} for n in food], '장르': {}}
        if not wd:
            out['상태'] = '추천영양소없음'
            return out
        p = self.p
        order = sorted(wd, key=lambda n: -wd[n])                       # 가중치 큰 순 (같으면 입력 순서)
        w = {COLMAP[n]: wd[n] for n in order}
        cols = list(w)
        spec_cols = [COLMAP[n] for n in order if wd[n] >= CORE_LEVEL]
        common_cols = [k for k in cols if k not in spec_cols]
        cov = pd.DataFrame({k: self._coverage(k) for k in cols})
        wcov = sum(cov[k] * w[k] for k in cols) / sum(w.values())

        # 필터: 안전(UL 초과·식사대용·키즈/임산부용) + 본인 성별·나이·흡연
        ok = (p['UL초과'] == 0) & ~p['식사대용'] & ~p['대상_제외']
        sex, age = profile.get('sex'), profile.get('age')
        if sex == '남자':
            ok &= ~p['대상_여성']
        elif sex == '여자':
            ok &= ~p['대상_남성']
        if age is not None and age < 50:
            ok &= ~p['대상_실버']
        if profile.get('smoker'):
            ok &= p['베타카로틴함유'] == 0
        # 안전 문항: 해당 성분이 든 제품은 조용히 제외 (화면에 '피하세요' 안내 없음)
        for q, comps in SAFETY_EXCLUDE.items():
            if profile.get(q):
                for comp in comps:
                    ok &= ~p[f'safety_{comp}']
        ok &= (cov[spec_cols] > 0).any(axis=1) if spec_cols else (cov > 0).any(axis=1)

        # 제품 유형 매칭 (코사인) + 안전장치
        vec = np.array([w.get(col[2:], 0) for col in self.V])
        sim = pd.Series(self.cent.values @ vec / (np.linalg.norm(self.cent.values, axis=1) * np.linalg.norm(vec) + 1e-9),
                        index=self.cent.index)
        torder = sim.sort_values(ascending=False).index.tolist()
        k = K_TYPES
        best_all = wcov[ok].max()
        while k < len(torder) and wcov[ok & p['제품유형명'].isin(torder[:k])].max() < FALLBACK * best_all:
            k += 1
        types = torder[:k]
        in_type = ok & p['제품유형명'].isin(types)

        # 장르 (04와 동일)
        core = (spec_cols or cols)[:2]
        core_cov = cov[core].sum(axis=1)
        extra = (p[self.V] > 0).sum(axis=1) - (cov > 0).sum(axis=1)
        purpose = pd.Series(False, index=p.index)
        for c in core:
            if f'목적일치_{c}' in p.columns:
                purpose |= (cov[c] > 0) & (p[f'목적일치_{c}'] == 1)
        single = in_type & purpose & (p['종합형'] == 0) & (core_cov > 0)
        full = pd.Series(False, index=p.index)
        low = pd.Series(False, index=p.index)
        for c in [c for c in core if c in QUANT]:
            full |= p[f'v_{c}'] >= 100
            low |= (p[f'v_{c}'] > 0) & (p[f'v_{c}'] < 30)
        suff = single & full & ~low
        named = pd.Series(0.0, index=p.index)
        for c in core:
            if f'name_{c}' in p.columns:
                named = np.maximum(named, p[f'name_{c}'].fillna(0))
        conv = single & p['1일개수'].eq(1) & p['n_day'].eq(1)
        n_spec = (cov[spec_cols] >= 0.3).sum(axis=1) if spec_cols else 0
        n_comm = (cov[common_cols] >= 0.3).sum(axis=1)
        multi = ok & (p['종합형'] == 1)
        score = core_cov + 0.3 * wcov - 0.05 * extra + 0.5 * named
        genres = {'충분함량형': _pick(p[suff], score[suff]), '편의형(1일 1회 1개)': _pick(p[conv], score[conv])}
        if self.has_price:
            pv = single & p['price_per_day'].notna()
            genres['가성비형'] = _pick(p[pv], ((core_cov + 0.3 * wcov) / p['price_per_day'])[pv])
        genres['종합형'] = _pick(p[multi], (100 * n_spec + 10 * n_comm + wcov)[multi])

        current = {COLMAP.get(JAEJUN_KEY.get(n, n), n) for n in profile.get('current_supplements', [])}
        out.update({'추천영양소': [{'영양소': n, '가중치': round(wd[n], 2)} for n in order],
                    '매칭제품유형': types, '가성비형': '' if self.has_price else '가격 조사 중'})
        for g, df in genres.items():
            items = []
            for _, r in df.iterrows():
                covers = [x for x in cols if cov.loc[r.name, x] >= 0.3]
                if not covers:
                    continue
                items.append(dict(식품명=r['식품명'], 제조사=r['제조사명'], 식품코드=r['식품코드'], 제품유형=r['제품유형명'],
                                  주성분=r['주성분'], 채우는영양소=covers, 함량미상=[x for x in covers if x not in QUANT],
                                  가중커버율=round(float(wcov[r.name]), 3), 하루개수=r['1일개수'],
                                  표시형태=[f for f in FORMS if r.get(f'form_{f}', 0) == 1],
                                  주목적=r.get('주목적_기능성', '') or '비타민·미네랄',
                                  지금드시는영양제와겹침=[x for x in covers if x in current]))
            out['장르'][g] = items
        return out


if __name__ == '__main__':
    import json
    rec = Recommender()
    demo = rec.recommend({'iron': 'High', 'protein': 'High', 'vitamin_c': 'Mid', 'potassium': 'High'},
                         {'sex': '남자', 'age': 45, 'smoker': True, 'current_supplements': ['비타민C']},
                         type_nutrients=['철', '비타민D'])
    print(json.dumps(demo, ensure_ascii=False, indent=1, default=str)[:3000])
