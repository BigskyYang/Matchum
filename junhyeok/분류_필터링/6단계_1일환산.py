# -*- coding: utf-8 -*-
"""
6단계: 1일 섭취량·1일 함량 계산
기준: 「영양제_분류_필터링_기준(1104).pdf」 2절, 6-①절

7단계(상한섭취량 거르기)와 8단계(점수)를 하려면 '하루에 실제로 먹는 양'이 필요하다.

하는 일
  ① 1일 섭취량: 섭취방법에서 '1일 몇 회 × 1회 몇 정(포·캡슐…)'을 읽는다.  예) 1일 2회, 1회 1정 → 하루 2정
  ② 1일 함량: 기준규격의 표시량을 성분별로 읽는다.
     - 식약처 기준규격의 표시량은 '1일 섭취량당 함량'이다.
       (확인: 섭취방법에 1정 무게가 적힌 제품 중 약 92%가 '표시량의 기준 무게 = 하루 먹는 총 무게'로 일치)
     - 단, 기준 무게가 '1회 먹는 양'인 것이 확실한 경우(하루 총 무게의 1/2·1/3 등)는 그만큼 곱한다.
     - 단위 통일: ㎍·ug → μg, 비타민 D IU → μg (40 IU = 1 μg)
  ③ 상한이 있는 성분은 모두 계산 (주성분이 아니어도): 비타민 C·D·A·E, 칼슘, 마그네슘, 철, 아연, 엽산, 비타민 B6, 니아신
     - 니아신은 원재료로 형태를 구분 (니코틴산 / 니코틴산아미드) → 상한이 다름
  ④ 계산할 수 없는 성분은 '확인 불가'로 남긴다 (빼는 건 7단계에서 결정)

입력  5단계_결과.pkl
출력  6단계_1일환산.xlsx, 6단계_결과.pkl (영양소별 줄 + 1일 함량), 6단계_제품별함량.pkl
"""
import re
import pandas as pd
from 공통 import out, nf, new_book, add_sheet, add_criteria_sheet

# 상한 확인에 필요한 성분: (기준규격에서 찾는 이름, 표준 단위)
NUTRIENTS = {
    "비타민 C": (r"비타민\s*C", "mg"),
    "비타민 D": (r"비타민\s*D3?", "μg"),
    "칼슘": (r"칼슘", "mg"),
    "마그네슘": (r"마그네슘", "mg"),
    "철": (r"(?<![가-힣])철(?!분말)", "mg"),
    "아연": (r"아연", "mg"),
    "엽산": (r"엽산", "μg"),
    "비타민 B6": (r"비타민\s*B6", "mg"),
    "니아신": (r"나이아신|니아신", "mg"),
    "비타민 A": (r"비타민\s*A", "μg"),
    "비타민 E": (r"비타민\s*E", "mg"),
}
# 읽은 값이 이보다 크면 잘못 읽은 것으로 보고 '확인 불가' 처리 (단위 착오 방지)
TOO_BIG = {"비타민 C": 10000, "비타민 D": 500, "칼슘": 3000, "마그네슘": 1000, "철": 100, "아연": 100,
           "엽산": 5000, "비타민 B6": 300, "니아신": 2000, "비타민 A": 10000, "비타민 E": 2000}
# 웹 영양소의 1일 영양성분 기준치 (기준치 대비 %에 사용, 초안)
DV = {"비타민 C": 100, "비타민 D": 10, "칼슘": 700, "마그네슘": 315, "철": 12, "아연": 8.5, "엽산": 400}
UNIT_FORM = {"정": "정", "캡슐": "캡슐", "포": "포", "병": "병", "매": "매", "스틱": "포", "알": "알", "환": "환",
             "개": "개", "팩": "팩", "봉": "포"}


def to_float(x):
    try:
        return float(str(x).replace(",", ""))
    except ValueError:
        return None


def weight_mg(x, unit):
    v = to_float(x)
    if v is None:
        return None
    return v * 1000 if unit.lower() == "g" else v


def daily_intake(text):
    """섭취방법 → (하루 횟수, 1회 개수, 단위, 1일 섭취량 문구, 하루 총 무게 mg 또는 None)"""
    s = nf(text)
    t = re.search(r"1일\s*(\d+)\s*회", s)
    n = re.search(r"1회\s*(\d+(?:\.\d+)?)\s*(정|캡슐|포|병|매|스틱|알|환|개|팩|봉)", s)
    if not n:                                   # 예: '1일 1매', '1일 2정'
        m = re.search(r"1일\s*(\d+(?:\.\d+)?)\s*(정|캡슐|포|병|매|스틱|알|환|개|팩|봉)", s)
        if m:
            cnt, unit = float(m.group(1)), UNIT_FORM[m.group(2)]
            label = f"하루 {cnt:g}{unit}"
            return 1, cnt, unit, label, None
        return None, None, None, "", None
    times = int(t.group(1)) if t else 1
    cnt, unit = float(n.group(1)), UNIT_FORM[n.group(2)]
    label = f"1일 {times}회, 1회 {cnt:g}{unit} (하루 {times * cnt:g}{unit})"
    per_unit = re.search(r"(?:1?(?:정|캡슐|포)당)\s*([\d,\.]+)\s*(mg|g)\b", s)
    paren = re.search(r"\(\s*([\d,\.]+)\s*(mg|g)\s*\)", s)
    total = None
    if per_unit:
        w = weight_mg(*per_unit.groups())
        total = w * cnt * times if w else None
    elif paren:
        w = weight_mg(*paren.groups())
        total = w * times if w else None
    return times, cnt, unit, label, total


NOT_IN_SPEC = "없음"
NEXT_ITEM = re.compile(r"\s(?:\d{1,2}[\.\)]|[①-⑳]|\(\d{1,2}\))\s*[가-힣A-Za-z]")


def find_amount(spec, name_pat):
    """기준규격에서 성분 표시량 → (값, 단위, 기준 무게 mg 또는 None) / 이름이 없으면 NOT_IN_SPEC / 못 읽으면 None
    예) '비타민D : 표시량(25 ㎍/1,200 mg)의 80~180%', '아연 : 표시량의 80~150% (표시량 : 8.5mg / 800mg)'"""
    s = nf(spec).replace("ug", "μg").replace("µg", "μg")
    m = re.search(name_pat, s)
    if not m:
        return NOT_IN_SPEC
    seg = s[m.end():m.end() + 140]
    cut = NEXT_ITEM.search(seg)
    if cut:
        seg = seg[:cut.start()]
    num = r"([\d,]+(?:\.\d+)?)\s*(mg|μg|IU)"
    pair = re.search(num + r"(?:\s*(?:mg\s*)?(?:α-TE|RAE|DFE|NE))?\s*(?:\([^)]*\))?\s*/\s*([\d,]+(?:\.\d+)?)\s*(mg|g)\b", seg)
    if pair:
        return to_float(pair.group(1)), pair.group(2), weight_mg(pair.group(3), pair.group(4))
    one = re.search(num + r"\b(?!\s*%)", seg)
    if one:
        return to_float(one.group(1)), one.group(2), None
    return None


def niacin_form(raw):
    r = nf(raw)
    if re.search(r"니코틴산\s*아미드|니코틴아미드|나이아신아미드", r):
        return "니코틴산아미드"
    if re.search(r"니코틴산", r):
        return "니코틴산"
    return "형태 모름"


def main():
    print("[1/3] 5단계 결과 읽는 중...")
    web = pd.read_pickle(out("5단계_결과.pkl"))
    prod = web.drop_duplicates("품목제조신고번호").set_index("품목제조신고번호")

    print("[2/3] 하루 먹는 양 계산 중...")
    rows = []
    for no, r in prod.iterrows():
        times, cnt, unit, label, total = daily_intake(r["섭취방법"])
        ings = set(str(r["함께 든 가이드 성분"]).split(", "))
        rec = {"품목제조신고번호": no, "1일 섭취량": label}
        method = []
        for k, (pat, std) in NUTRIENTS.items():
            if k in ("비타민 B6", "니아신"):
                if "비타민 B군" not in ings:
                    continue
            elif k not in ings:
                continue
            found = find_amount(r["기준규격"], pat)
            if found == NOT_IN_SPEC and k in ("비타민 B6", "니아신"):
                continue                            # B군 제품이어도 B6·니아신이 안 든 경우
            if found == NOT_IN_SPEC or not found or found[0] is None:
                rec[k] = None
                method.append(f"{k} 확인 불가")
                continue
            val, u, ref = found
            if k == "비타민 D" and u == "IU":
                val, u = val / 40, "μg"
            factor = 1.0
            if ref and total:
                ratio = ref / total
                if 0.2 <= ratio <= 0.6:            # 기준 무게가 1회분인 경우 → 하루 양으로 늘림
                    factor = round(1 / ratio)
                    method.append(f"{k} ×{factor:g} (표시 기준이 1회분)")
            if u != std and not (std == "mg" and u == "mg"):
                if u == "μg" and std == "mg":
                    val = val / 1000
                elif u == "mg" and std == "μg":
                    val = val * 1000
                elif u == "IU":
                    rec[k] = None
                    method.append(f"{k} IU 단위 (확인 불가)")
                    continue
            if val * factor > TOO_BIG[k]:
                rec[k] = None
                method.append(f"{k} 값 이상 (확인 불가)")
                continue
            rec[k] = round(val * factor, 3)
        if rec.get("니아신") is not None or "니아신 확인 불가" in "; ".join(method):
            rec["니아신 형태"] = niacin_form(r["원재료"])
        rec["계산 메모"] = "; ".join(method) if method else "표시량 = 1일 섭취량당"
        rows.append(rec)
    amt = pd.DataFrame(rows).set_index("품목제조신고번호")
    amt.to_pickle(out("6단계_제품별함량.pkl"))

    # 영양소별 줄에 1일 섭취량·1일 함량·기준치 % 붙이기
    web["1일 섭취량"] = web["품목제조신고번호"].map(amt["1일 섭취량"])
    def own_amount(row):
        k = row["영양소"]
        if k in NUTRIENTS and k in amt.columns:
            v = amt.at[row["품목제조신고번호"], k]
            return v if pd.notna(v) else None
        return None
    web["1일 함량"] = web.apply(own_amount, axis=1)
    web["1일 함량 단위"] = web["영양소"].map(lambda k: NUTRIENTS.get(k, (None, ""))[1])
    web["기준치 대비(%)"] = web.apply(lambda r: round(r["1일 함량"] / DV[r["영양소"]] * 100)
                                    if r["영양소"] in DV and pd.notna(r["1일 함량"]) else None, axis=1)
    web.to_pickle(out("6단계_결과.pkl"))

    # 집계
    n_prod = len(amt)
    no_intake = int((amt["1일 섭취량"] == "").sum())
    rescaled = int(amt["계산 메모"].str.contains("×").sum())
    check_cols = [c for c in NUTRIENTS if c in amt.columns]
    per_nutrient = []
    for k in check_cols:
        has = amt[k].notna().sum()
        tried = amt["계산 메모"].str.contains(f"{k} ").sum() + has
        per_nutrient.append({"성분": k, "제품 수(이 성분이 든)": int(tried), "1일 함량 계산됨": int(has), "확인 불가": int(tried - has)})
    per_nutrient = pd.DataFrame(per_nutrient)

    print("[3/3] 결과 엑셀 저장 중... (1~2분, 아무 키도 누르지 마세요)")
    lines = [
        ("6단계: 1일 섭취량·1일 함량 계산", True), ("", False),
        ("결과", True),
        (f"· 제품 {n_prod:,}개 (영양소별 {len(web):,}줄)", False),
        (f"· 1일 섭취량을 읽은 제품: {n_prod - no_intake:,}개 / 읽지 못함: {no_intake:,}개", False),
        (f"· 표시 기준이 1회분이라 하루 양으로 늘린 경우: {rescaled:,}개", False),
        ("· 성분별 계산 결과는 '성분별 계산' 시트", False),
        ("", False), ("계산 방법", True),
        ("· 식약처 기준규격의 표시량은 '1일 섭취량당 함량'. 섭취방법에 1정 무게가 적힌 582개 중 약 92%에서 표시 기준 무게 = 하루 먹는 총 무게로 확인", False),
        ("· 비타민 D IU는 μg로 바꿈 (40 IU = 1 μg). 니아신은 원재료로 니코틴산 / 니코틴산아미드를 구분", False),
        ("· 계산할 수 없거나 단위를 잘못 읽은 것으로 보이는 값(예: 비타민 D 500μg 초과)은 '확인 불가'로 남김 → 7단계에서 어떻게 할지 결정", False),
        ("· 기준치 대비(%) = 1일 함량 ÷ 1일 영양성분 기준치 (기준치는 초안, 원문 확인 필요)", False),
        ("· 같은 결과를 다시 만들려면: python 6단계_1일환산.py", False),
    ]
    wb = new_book(lines)
    done = {k: "적용 완료 (이전 단계)" for k in [
        "식품영양성분DB", "기능성 문구만 있는 제품도", "원재료·섭취방법·기준규격은", "2022년 이후 신고", "제품명에 '수출'",
        "대상 판별", "임산부·수유부", "제품명이 질환을", "일반·전문 의약품", "성분은 기능성 칸으로", "나이아신·판토텐산·비오틴",
        "식이섬유는 기능성 칸에", "제품명에 나온 영양소가", "원료 껍데기형", "다른 목적 원료·문구", "제품명의 피부·미백",
        "수면·긴장 원료", "오메가3 자체의 기억력", "단일: 성분 1개", "주성분 판단 순서", "제품명에 우리 영양소가 2개",
        "목적형: 성분 2~6개", "종합비타민: 성분 7개", "칼슘+철 제품도", "13개 항목", "목적형은 이름이 아니라",
        "단백질·인·칼륨·비타민 A·나트륨", "제품 식별자는"]}
    done["비타민 D는 일반 정보로"] = "비타민 D 포함 / 오메가3·유산균·루테인·밀크씨슬은 웹에서 아직 안 씀 (11-04)"
    done["압축된 후보만 표시량"] = f"적용 완료 (제품 {n_prod:,}개, 1일 섭취량 읽음 {n_prod - no_intake:,})"
    add_criteria_sheet(wb, done)
    add_sheet(wb, "성분별 계산", per_nutrient, [14, 20, 18, 12], freeze="A2")
    cols = ["영양소", "대상", "구분", "품목제조신고번호", "제품명", "업체명", "1일 섭취량", "1일 함량", "1일 함량 단위",
            "기준치 대비(%)", "섭취방법", "기준규격"]
    add_sheet(wb, f"영양소별 ({len(web):,})", web[cols], [20, 8, 18, 18, 32, 20, 26, 10, 8, 10, 40, 60])
    a2 = amt.reset_index().merge(prod[["제품명", "섭취방법", "원재료"]].reset_index(), on="품목제조신고번호")
    lead = ["품목제조신고번호", "제품명", "1일 섭취량"] + check_cols + [c for c in ["니아신 형태"] if c in a2.columns] + ["계산 메모", "섭취방법"]
    add_sheet(wb, f"제품별 1일 함량 ({n_prod:,})", a2[lead], [18, 32, 26] + [10] * len(check_cols) + [14, 40, 40])
    wb.save(out("6단계_1일환산.xlsx"))
    print(f"6단계 완료: 제품 {n_prod:,}개 · 1일 섭취량 읽음 {n_prod - no_intake:,} / 못 읽음 {no_intake:,} · 1회분 보정 {rescaled:,}")
    print(per_nutrient.to_string(index=False))


if __name__ == "__main__":
    main()
