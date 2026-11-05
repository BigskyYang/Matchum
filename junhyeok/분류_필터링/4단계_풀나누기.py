# -*- coding: utf-8 -*-
"""
4단계: 풀 나누기
기준: 「영양제_분류_필터링_기준(1104).pdf」 3절, 3-1절, 3-3절, 8절

남은 제품을 대상(일반·남성·여성·시니어)별로 아래 풀에 나눈다.
  · 단일      : 성분 1개, 또는 주성분 1개 + 보조 성분 1개
  · 목적형    : 성분 2~6개, '무엇을 위한 제품인지'(뼈·면역·피로 등)로 분류
  · 종합비타민 : 성분 7개 이상, 또는 이름에 멀티·종합·올인원 + 성분 3개 이상 → 균형형 / 피로회복형
  · 제외      : 목적이 3개 이상 섞였거나, 불분명하거나, 우리 항목과 무관한 목적

단일 제품의 주성분 판단 순서 (3-1절)
  ⓪ 제품명에 우리 영양소가 2개 이상이면 단일이 아님 → 목적형 (예: 비타민C&D, 철분&엽산)
  ① 제품명에 나온 성분  ② 기능성 원료(유산균·오메가3 등) 쪽  ③ 기준치 대비 함량이 2배 이상인 쪽
  + 가이드 밖 영양소(셀렌·크롬 등)는 1개까지만 보조로 인정
  * (11-05) 유산균과 식이섬유 두 가지만 든 제품은 단일이 아니라 목적형(장)으로 분류
    (유산균은 보조 성분이 아니라 그 자체가 주 목적인 원료라서. 생활기능 영양제 유산균 쪽으로 보관됨)

목적형의 목적 판단 (3-3절): 단서마다 가중치 → 제품명 3 · 기능성 원료 문구 2 · 비타민·미네랄 문구 1
  ① 제품명이 한 목적을 가리키면 그 목적  ② 제품명에 영양소가 하나면 그 영양소의 목적
  ③ 목적 3개 이상이 비슷하면 제외  ④ 1·2등 점수 차 2점 이상이면 1등  ⑤ 두 목적 모두 우리 항목이면 복수 목적
  ⑥ 성분 구성이 한 목적 그룹에 다 들어가면 그 목적  ⑦ 그래도 안 되면 '불분명'으로 제외

입력  3단계_결과.pkl, 최종본 엑셀의 성분 시트(함량 비교용)
출력  4단계_풀나누기.xlsx, 4단계_결과.pkl (다음 단계 입력)
"""
import re
from collections import Counter
import pandas as pd
from 공통 import out, nf, find, FINAL_XLSX, new_book, add_sheet, add_criteria_sheet

T13 = ["비타민 B군", "비타민 C", "비타민 D", "칼슘", "마그네슘", "아연", "철", "엽산",
       "오메가3", "유산균", "식이섬유", "루테인", "밀크씨슬"]
RAWS = {"오메가3", "유산균", "식이섬유", "루테인", "밀크씨슬"}          # 기능성 원료
TARGETS = ["일반", "남성", "여성", "시니어"]
NAME = {
    "비타민 B군": r"비타민\s*B|B\s*컴플렉스|(?i:b-?complex)|비타민비|B군|비오틴|나이아신|판토텐|(?i:biotin)",
    "비타민 C": r"비타민\s*C|(?i:vitamin\s*c)",
    "비타민 D": r"비타민\s*D|(?i:vitamin\s*d)|\bD3\b",
    "칼슘": r"칼슘|칼마|진주|어골|(?i:calcium)|(?<![A-Za-z])Ca(?![a-z])",
    "마그네슘": r"마그네슘|(?i:magnesium)|(?<![A-Za-z])Mg(?![a-z])",
    "아연": r"아연|(?i:zinc)|(?<![A-Za-z])Zn(?![a-z])",
    "철": r"철분|헴철|(?i:iron)",
    "엽산": r"엽산|(?i:folic|folate)",
    "오메가3": r"오메가|(?i:omega|rTG)",
    "유산균": r"유산균|프로바이오|바이오틱|(?i:probiotic)",
    "식이섬유": r"식이섬유|차전자|화이바|(?i:fiber)",
    "루테인": r"루테인|(?i:lutein)",
    "밀크씨슬": r"밀크\s*[씨시]슬|(?i:milk\s*thistle)|실리마린",
    "비타민 A": r"비타민\s*A", "비타민 E": r"비타민\s*E", "비타민 K": r"비타민\s*K", "칼륨": r"칼륨|포타슘",
}
# 1일 영양성분 기준치 (함량 2배 비교용, 초안)
DV = {"비타민 C": (100, "mg"), "비타민 D": (10, "μg"), "칼슘": (700, "mg"), "마그네슘": (315, "mg"),
      "철": (12, "mg"), "아연": (8.5, "mg"), "엽산": (400, "μg DFE"), "비타민 A": (700, "μg RAE"),
      "비타민 E": (11, "mg α-TE"), "비타민 K": (70, "μg")}
MULTI = r"멀티|종합|올인원|(?i:multi|all[\s-]?in[\s-]?one)"
OTHER_MINERAL = r"셀레늄|셀렌|망간|구리|크롬|몰리브덴|요오드"
CORE8 = ["비타민 B군", "비타민 C", "비타민 D", "칼슘", "마그네슘", "아연", "철", "엽산"]

# 목적: (제품명 단서, 기능성 원료 문구, 비타민·미네랄 문구)
P = {
    "간": (r"간\s*건강|간건강|간보|간케어|간에|리버|(?i:liver)|밀크\s*씨슬|헛개|실리마린", r"간 건강|간을 보호|간건강", None),
    "눈": (r"눈|아이케어|아이즈|(?i:\beye)|루테인|오큐|비전|(?i:vision)|마리골드", r"황반|눈 건강|눈의 피로|건조한 눈", r"시각 적응"),
    "뼈": (r"뼈|칼슘|칼마|본케어|본스|(?i:bone)", r"뼈 건강|칼슘흡수", r"뼈와 치아|뼈의 형성|뼈의 구성|골다공증"),
    "관절": (r"관절|(?i:joint)|콘드로이친|글루코사민|MSM|엠에스엠|보스웰리아|뮤코다당|초록입홍합", r"관절|연골", None),
    "남녀 건강": (r"쏘팔메토|전립선|갱년기|석류|(?i:prostate)", r"전립선|갱년기|배뇨|요로", None),
    "위": (r"위건강|위 건강|매스틱|위케어", r"위 건강|위 점막|위 불편", None),
    "혈압·콜레스테롤": (r"콜레스테롤|혈압|홍국|폴리코사놀", r"콜레스테롤|혈압", None),
    "장": (r"장\s*건강|장건강|장케어|유산균|프로바이오|바이오틱|락토|비피더스|쾌변|(?i:probiotic)|식이섬유|차전자", r"배변|유익균|장 건강|장건강", None),
    "면역": (r"면역|이뮨|(?i:immun)|방어", r"면역", r"정상적인 면역기능"),
    "혈행·혈액": (r"혈행|헤모|철분|헴철|오메가|(?i:omega|rTG)|엽산", r"혈행|중성지질|혈소판", r"혈액생성|산소운반"),
    "피로·활력": (r"피로|활력|에너지|(?i:energy)|부스트", r"피로|지구력|운동수행", r"에너지 대사|에너지 생성|에너지 이용"),
    "체지방·혈당": (r"다이어트|슬림|체지방|혈당|당케어|부기|컷팅|(?i:slim|diet)", r"체지방|혈당|탄수화물 흡수", None),
    "피부·모발": (r"피부|콜라겐|뷰티|모발|헤어|스킨|히알루론|글루타치온|(?i:skin|collagen)", r"피부|모발|보습", r"피부와 점막"),
    "수면·스트레스": (r"수면|숙면|릴렉스|스트레스|굿나잇|아쉬아간다|테아닌|락티움|가바|홍경천|(?i:sleep|relax)", r"수면|긴장|스트레스로 인한", None),
    "기억·인지": (r"기억|두뇌|브레인|인지|(?i:brain|memory)", r"기억력|인지", None),
}
# 우리 항목과 연결된 목적
LINK = {"간": ["밀크씨슬"], "눈": ["루테인", "오메가3"], "뼈": ["칼슘", "비타민 D", "마그네슘"],
        "장": ["유산균", "식이섬유"], "면역": ["아연", "비타민 C", "비타민 D"],
        "혈행·혈액": ["오메가3", "철", "엽산"], "피로·활력": ["비타민 B군", "마그네슘"]}
LINKED = list(LINK)
PURPOSE_OF = {}
for g, items in LINK.items():
    for it in items:
        PURPOSE_OF.setdefault(it, []).append(g)
# 목적별로 같이 들어 있어도 자연스러운 성분 묶음
ING_GROUP = {"간": {"밀크씨슬", "비타민 B군"}, "눈": {"루테인", "오메가3", "비타민 A", "비타민 E"},
             "뼈": {"칼슘", "비타민 D", "마그네슘", "비타민 K"}, "장": {"유산균", "식이섬유"},
             "면역": {"아연", "비타민 C", "비타민 D"}, "혈행·혈액": {"철", "엽산", "비타민 B군", "비타민 C", "오메가3", "비타민 E"},
             "피로·활력": {"비타민 B군", "마그네슘", "비타민 C"}}


def load_percent():
    """최종본 성분 시트의 함량으로 기준치 대비 %를 구함 {신고번호: {성분: %}}"""
    book = pd.ExcelFile(find(FINAL_XLSX))
    pct = {}
    for k, (dv, unit) in DV.items():
        d = pd.read_excel(book, sheet_name=k, dtype=str, usecols=["품목제조신고번호", "함량", "함량 단위"])
        for no, a, u in zip(d["품목제조신고번호"], d["함량"], d["함량 단위"]):
            try:
                if str(u).replace("a-TE", "α-TE") == unit:
                    pct.setdefault(no, {})[k] = float(a) / dv * 100
            except (TypeError, ValueError):
                pass
    return pct


def names_in(name, ings):
    found = [k for k in ings if re.search(NAME.get(k, r"$^"), name)]
    if re.search(r"(?i)C\s*(&|\+|and|앤)\s*D", name) and "비타민 D" in ings and "비타민 D" not in found:
        found.append("비타민 D")
    return found


def main_ingredient(no, name, ings, pct):
    """성분 2개 제품의 주성분. (주성분, 근거) 또는 (None, 이유)"""
    nm = names_in(name, ings)
    if len(nm) >= 2:
        return None, "제품명에 영양소 2개"
    if len(nm) == 1:
        return nm[0], "제품명"
    raw = [k for k in ings if k in RAWS]
    if len(raw) == 1:
        return raw[0], "기능성 원료"
    p = pct.get(no, {})
    if len(p) == 2:
        (a, x), (b, y) = sorted(p.items(), key=lambda t: -t[1])
        if x >= 2 * y:
            return a, "함량 2배"
    return None, "주성분 판단 불가"


def purpose_scores(name, f):
    sc = Counter()
    for g, (nk, fk, nuk) in P.items():
        if re.search(nk, name):
            sc[g] += 3
        if fk:
            sc[g] += 2 * len(re.findall(fk, f))
        if nuk:
            sc[g] += len(re.findall(nuk, f))
    return sc


def classify(no, name, f, ings, pct):
    """(풀, 키, 근거)"""
    n = len(ings)
    multi_name = bool(re.search(MULTI, name))
    # 종합비타민 후보
    if n >= 7 and not multi_name:
        nm_p = [g for g, (nk, _, _) in P.items() if re.search(nk, name)]
        if len(nm_p) == 1 and nm_p[0] in LINKED:
            return "목적형", nm_p[0], "제품명 목적 (성분 7개 이상)"
    if n >= 7 or (n >= 3 and multi_name):
        fatigue = ("비타민 B군" in ings and "비타민 C" in ings) and bool(
            re.search(r"피로|활력|에너지|(?i:energy|active)|액티브|부스트|비타민\s*B|B\s*컴플렉스|(?i:b-?complex)", name)
            or re.search(r"피로 개선|지구력", f))
        cov = len([k for k in CORE8 if k in ings])
        return "종합비타민", "피로회복형" if fatigue else "균형형", f"핵심 8종 중 {cov}종"
    # 단일
    other = len(set(re.findall(OTHER_MINERAL, f)))
    if n == 1 and other <= 1:
        return "단일", ings[0], "성분 1개" if other == 0 else "주성분 + 보조(기타 영양소)"
    if n == 2 and set(ings) == {"유산균", "식이섬유"}:     # 11-05: 유산균 + 식이섬유는 단일이 아니라 장 목적형
        return "목적형", "장", "유산균 + 식이섬유 (장)"
    if n == 2 and other == 0:
        m, why = main_ingredient(no, name, ings, pct)
        if m:
            return "단일", m, f"주성분 + 보조({why})"
    # 목적형
    sc = purpose_scores(name, f)
    top, top3 = sc.most_common(2), sc.most_common(3)
    nm_p = [g for g, (nk, _, _) in P.items() if re.search(nk, name) and g in LINKED]
    nm_n = [k for k in T13 if k in ings and re.search(NAME[k], name)]
    if len(nm_p) == 1:
        return "목적형", nm_p[0], "제품명 목적"
    if len(nm_n) == 1 and nm_n[0] in PURPOSE_OF:
        cand = [g for g in PURPOSE_OF[nm_n[0]] if g in LINKED]
        if cand:
            return "목적형", max(cand, key=lambda g: sc.get(g, 0)), "제품명 성분"
    if len(top3) == 3 and top3[2][1] >= 2 and top3[2][1] >= 0.7 * top3[0][1]:
        return "제외", "목적 여러 개", "목적 3개 이상"
    g, why = None, ""
    if top and (len(top) == 1 or top[0][1] - top[1][1] >= 2):
        g, why = top[0][0], "단서 점수"
    elif len(top) == 2 and top[0][0] in LINKED and top[1][0] in LINKED:
        g, why = top[0][0] + "+" + top[1][0], "복수 목적"
    else:
        hit = [gg for gg, members in ING_GROUP.items() if set(ings) <= members]
        if len(hit) == 1:
            g, why = hit[0], "성분 구성"
    if g is None:
        return "제외", "불분명", "목적을 알 수 없음"
    if g == "수면·스트레스":
        return "스트레스 참고", g, why
    if all(x in LINKED for x in g.split("+")):
        return "목적형", g, why
    return "제외", g, "우리 항목과 무관한 목적"


def main():
    print("[1/3] 3단계 결과와 함량 읽는 중... (1분 정도)")
    p = pd.read_pickle(out("3단계_결과.pkl"))
    pct = load_percent()
    n0 = len(p)

    print("[2/3] 풀 나누는 중...")
    res = [classify(no, nm, nf(f), i.split(", "), pct)
           for no, nm, f, i in zip(p["품목제조신고번호"], p["제품명"], p["기능성"], p["함께 든 가이드 성분"])]
    p["풀"] = [r[0] for r in res]
    p["주성분·목적"] = [r[1] for r in res]
    p["분류 근거"] = [r[2] for r in res]
    p["추천 대상 성분"] = ~((p["풀"] == "단일") & p["주성분·목적"].isin(["비타민 A", "비타민 E", "비타민 K", "칼륨"]))
    p["추천 대상 성분"] = p["추천 대상 성분"].map({True: "예", False: "아님 (A·E·K·칼륨)"})
    keep = p[p["풀"].isin(["단일", "목적형", "종합비타민"])].reset_index(drop=True)
    extra = p[~p["풀"].isin(["단일", "목적형", "종합비타민"])]
    keep.to_pickle(out("4단계_결과.pkl"))

    # 대상 × 풀 표
    table = pd.crosstab(keep["대상"], keep["풀"]).reindex(index=TARGETS, columns=["단일", "목적형", "종합비타민"]).fillna(0).astype(int)
    table["합계"] = table.sum(axis=1)
    table.loc["합계"] = table.sum()
    single = keep[keep["풀"] == "단일"]
    single_tbl = pd.crosstab(single["주성분·목적"], single["대상"]).reindex(columns=TARGETS).fillna(0).astype(int)
    single_tbl = single_tbl.reindex([k for k in T13 + ["비타민 A", "비타민 E", "비타민 K", "칼륨"] if k in single_tbl.index])
    purpose = keep[keep["풀"] == "목적형"].copy()
    purpose["목적"] = purpose["주성분·목적"].where(~purpose["주성분·목적"].str.contains(r"\+"), "복수 목적")
    purpose_tbl = pd.crosstab(purpose["목적"], purpose["대상"]).reindex(columns=TARGETS).fillna(0).astype(int)
    multi_tbl = pd.crosstab(keep.loc[keep["풀"] == "종합비타민", "주성분·목적"], keep.loc[keep["풀"] == "종합비타민", "대상"]).reindex(columns=TARGETS).fillna(0).astype(int)
    extra_cnt = extra["주성분·목적"].value_counts()

    print("[3/3] 결과 엑셀 저장 중... (1~2분, 아무 키도 누르지 마세요)")
    gen = table.loc["일반"]
    lines = [
        ("4단계: 풀 나누기", True), ("", False),
        ("결과", True),
        (f"· 시작 {n0:,}개 → 단일 {table.loc['합계','단일']:,} · 목적형 {table.loc['합계','목적형']:,} · 종합비타민 {table.loc['합계','종합비타민']:,} (합계 {len(keep):,}) / 빠짐 {len(extra):,}", False),
        (f"· 일반 대상: 단일 {gen['단일']:,} · 목적형 {gen['목적형']:,} · 종합비타민 {gen['종합비타민']:,}", False),
        ("· 대상별 개수는 '대상별 개수' 시트", False),
        ("", False), ("빠진 제품", True),
    ] + [(f"· {k}: {v:,}개", False) for k, v in extra_cnt.items()] + [
        ("", False), ("참고", True),
        ("· 비타민 A·E·K·칼륨이 주성분인 단일 제품은 '추천 대상 성분 = 아님'으로 표시 (5단계에서 뺌)", False),
        ("· 같은 결과를 다시 만들려면: python 4단계_풀나누기.py", False),
    ]
    wb = new_book(lines)
    done = {k: "적용 완료 (이전 단계)" for k in [
        "식품영양성분DB", "기능성 문구만 있는 제품도", "원재료·섭취방법·기준규격은", "2022년 이후 신고", "제품명에 '수출'",
        "대상 판별", "임산부·수유부", "제품명이 질환을", "일반·전문 의약품", "성분은 기능성 칸으로", "나이아신·판토텐산·비오틴",
        "식이섬유는 기능성 칸에", "제품명에 나온 영양소가", "원료 껍데기형", "다른 목적 원료·문구", "제품명의 피부·미백",
        "수면·긴장 원료", "오메가3 자체의 기억력"]}
    done.update({
        "단일: 성분 1개": f"적용 완료 (단일 {table.loc['합계','단일']:,})",
        "주성분 판단 순서": "적용 완료",
        "제품명에 우리 영양소가 2개": "적용 완료",
        "목적형: 성분 2~6개": f"적용 완료 (목적형 {table.loc['합계','목적형']:,})",
        "종합비타민: 성분 7개": f"적용 완료 (종합비타민 {table.loc['합계','종합비타민']:,})",
        "칼슘+철 제품도": "적용 완료 (제외 규칙 없음)",
    })
    add_criteria_sheet(wb, done)
    add_sheet(wb, "대상별 개수", table.reset_index().rename(columns={"index": "대상"}), [10, 10, 10, 12, 10], freeze="A2")
    add_sheet(wb, "단일 - 성분별", single_tbl.reset_index().rename(columns={"주성분·목적": "성분"}), [14, 10, 10, 10, 10], freeze="A2")
    add_sheet(wb, "목적형 - 목적별", purpose_tbl.reset_index(), [14, 10, 10, 10, 10], freeze="A2")
    add_sheet(wb, "종합비타민 - 종류별", multi_tbl.reset_index().rename(columns={"주성분·목적": "종류"}), [14, 10, 10, 10, 10], freeze="A2")
    cols = ["풀", "주성분·목적", "분류 근거", "대상", "추천 대상 성분", "품목제조신고번호", "제품명", "업체명",
            "가이드 성분 수", "함께 든 가이드 성분", "기능성", "섭취방법", "기준규격", "섭취 시 주의사항"]
    w = [10, 14, 22, 8, 12, 18, 32, 20, 8, 30, 60, 30, 40, 40]
    for pool in ["단일", "목적형", "종합비타민"]:
        d = keep[keep["풀"] == pool].sort_values(["주성분·목적", "대상"])
        add_sheet(wb, f"{pool} ({len(d):,})", d[cols], w)
    add_sheet(wb, f"빠짐 ({len(extra):,})", extra[cols].sort_values("주성분·목적"), w)
    wb.save(out("4단계_풀나누기.xlsx"))
    print(f"4단계 완료: {n0:,} → 단일 {table.loc['합계','단일']:,} · 목적형 {table.loc['합계','목적형']:,} · 종합비타민 {table.loc['합계','종합비타민']:,} / 빠짐 {len(extra):,}")
    print(table.to_string())


if __name__ == "__main__":
    main()
