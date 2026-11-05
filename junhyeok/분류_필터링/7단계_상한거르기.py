# -*- coding: utf-8 -*-
"""
7단계: 상한섭취량 거르기
기준: 「영양제_분류_필터링_기준(1104).pdf」 6-①절 + 2025 한국인 영양소 섭취기준(KDRI) + 11-04 결정

하는 일 (제품 단위로 판단해서, 걸리면 그 제품의 모든 영양소 줄을 뺌)
  ① 확인 불가 제외 (11-04 결정): 하루 섭취량을 읽지 못했거나, 상한이 있는 성분의 하루 함량을 확인할 수 없는 제품
  ② 상한 초과 제외: 상한이 있는 성분 중 하나라도 하루 함량이 2025 KDRI 성인 상한을 넘으면 제외
     - 주성분만이 아니라 제품에 든 모든 성분을 확인 (종합비타민의 비타민 A·B6 등)
     - 칼슘 상한은 성별·나이에 따라 달라서, 제품 대상별로 가장 낮은 값을 씀
       (일반·여성·시니어 2,000mg / 남성 2,500mg — 일반 제품은 누구에게나 보일 수 있으므로 가장 낮은 값)
     - 마그네슘 350mg은 식품 외(영양제) 섭취분 기준이라 제품 함량에 그대로 적용
     - 니아신: 니코틴산 35mg / 니코틴산아미드 850mg. 형태를 모르면 더 낮은 35mg 적용
     - 엽산: 1,000μg (영양제·강화식품의 엽산 기준). DFE로 적힌 값도 그대로 비교 (더 엄격한 쪽)
     - 요오드: 2,400μg (11-05 추가. 우리 가이드 성분은 아니지만 종합비타민·아연 제품 등에 섞여 있어서 확인)
  * '상한 미설정 ≠ 무제한 안전': 상한이 없는 성분은 여기서 거르지 않지만, 고함량이라고 가점을 주지도 않음 (8단계)

입력  6단계_결과.pkl, 6단계_제품별함량.pkl
출력  7단계_상한거르기.xlsx, 7단계_결과.pkl (다음 단계 입력)
"""
import re
import pandas as pd
from 공통 import out, new_book, add_sheet, add_criteria_sheet

TARGETS = ["일반", "남성", "여성", "시니어"]
# 2025 KDRI 성인 상한섭취량 (하루)
UL = {"비타민 C": 2000, "비타민 D": 100, "마그네슘": 350, "철": 45, "아연": 35, "엽산": 1000,
      "비타민 B6": 50, "비타민 A": 3000, "비타민 E": 540, "요오드": 2400}
UL_UNIT = {"비타민 C": "mg", "비타민 D": "μg", "칼슘": "mg", "마그네슘": "mg", "철": "mg", "아연": "mg",
           "엽산": "μg", "비타민 B6": "mg", "니아신": "mg", "비타민 A": "μg RAE", "비타민 E": "mg α-TE", "요오드": "μg"}
CALCIUM_UL = {"일반": 2000, "여성": 2000, "시니어": 2000, "남성": 2500}
NIACIN_UL = {"니코틴산": 35, "니코틴산아미드": 850, "형태 모름": 35}


def check_product(amt_row, target):
    """(결과, 이유) — 결과: '통과' / '확인 불가' / '상한 초과'"""
    if not amt_row["1일 섭취량"]:
        return "확인 불가", "1일 섭취량을 읽지 못함"
    if "확인 불가" in str(amt_row["계산 메모"]):
        miss = re.findall(r"([가-힣]+(?: [A-Z]\d?)?) (?:확인 불가|값 이상|IU 단위)", str(amt_row["계산 메모"]))
        return "확인 불가", "하루 함량 확인 불가 (" + ", ".join(miss) + ")"
    over = []
    for k, limit in list(UL.items()) + [("칼슘", CALCIUM_UL[target]), ("니아신", None)]:
        if k not in amt_row.index or pd.isna(amt_row[k]):
            continue
        if k == "니아신":
            limit = NIACIN_UL.get(amt_row.get("니아신 형태", "형태 모름"), 35)
        if amt_row[k] > limit:
            over.append(f"{k} {amt_row[k]:g}{UL_UNIT[k]} > 상한 {limit:g}")
    if over:
        return "상한 초과", "; ".join(over)
    return "통과", ""


def main():
    print("[1/3] 6단계 결과 읽는 중...")
    web = pd.read_pickle(out("6단계_결과.pkl"))
    amt = pd.read_pickle(out("6단계_제품별함량.pkl"))
    target_of = web.drop_duplicates("품목제조신고번호").set_index("품목제조신고번호")["대상"].astype(str)

    print("[2/3] 상한섭취량 확인 중...")
    res = {no: check_product(amt.loc[no], target_of[no]) for no in amt.index}
    amt["결과"] = [res[no][0] for no in amt.index]
    amt["이유"] = [res[no][1] for no in amt.index]
    web["결과"] = web["품목제조신고번호"].map(amt["결과"])
    web["이유"] = web["품목제조신고번호"].map(amt["이유"])

    keep = web[web["결과"] == "통과"].drop(columns=["결과", "이유"]).reset_index(drop=True)
    keep.to_pickle(out("7단계_결과.pkl"))
    n_unknown = int((amt["결과"] == "확인 불가").sum())
    n_over = int((amt["결과"] == "상한 초과").sum())
    over_by = amt.loc[amt["결과"] == "상한 초과", "이유"].str.split("; ").explode().str.extract(r"^(\S+(?: [A-Z]\d?)?)")[0].value_counts()
    unk_by = amt.loc[amt["결과"] == "확인 불가", "이유"].str.replace(r" \(.*", "", regex=True).value_counts()

    order = list(web["영양소"].cat.categories) if hasattr(web["영양소"], "cat") else sorted(web["영양소"].unique())
    before = pd.crosstab(web["영양소"], web["대상"]).reindex(index=order, columns=TARGETS).fillna(0).astype(int)
    after = pd.crosstab(keep["영양소"], keep["대상"]).reindex(index=order, columns=TARGETS).fillna(0).astype(int)
    table = after.copy()
    table.columns = [f"{c}" for c in TARGETS]
    table.insert(0, "7단계 전 (일반)", before["일반"])

    print("[3/3] 결과 엑셀 저장 중... (1~2분, 아무 키도 누르지 마세요)")
    n_prod = len(amt)
    lines = [
        ("7단계: 상한섭취량 거르기 (2025 KDRI)", True), ("", False),
        ("결과", True),
        (f"· 제품 {n_prod:,}개 → 확인 불가 {n_unknown:,} · 상한 초과 {n_over:,} 제외 → 남은 제품 {n_prod - n_unknown - n_over:,}개 (영양소별 {len(keep):,}줄)", False),
        ("", False), ("상한 초과 (성분별, 한 제품이 여러 성분에서 넘을 수 있음)", True),
    ] + [(f"· {k}: {v:,}개", False) for k, v in over_by.items()] + [
        ("", False), ("확인 불가 (11-04 결정: 모두 제외)", True),
    ] + [(f"· {k}: {v:,}개", False) for k, v in unk_by.items()] + [
        ("", False), ("사용한 상한 (2025 KDRI, 성인, 하루)", True),
        ("· 비타민 C 2,000mg · 비타민 D 100μg · 칼슘 2,000mg(남성 대상 2,500mg) · 마그네슘 350mg(식품 외) · 철 45mg · 아연 35mg", False),
        ("· 엽산 1,000μg · 비타민 B6 50mg · 니아신 니코틴산 35mg / 니코틴산아미드 850mg (형태 모르면 35mg) · 비타민 A 3,000μg RAE · 비타민 E 540mg α-TE · 요오드 2,400μg (11-05 추가)", False),
        ("· 출처: 2025 한국인 영양소 섭취기준 요약 자료 (보건복지부·한국영양학회)", False),
        ("· 같은 결과를 다시 만들려면: python 7단계_상한거르기.py", False),
    ]
    wb = new_book(lines)
    done = {k: "적용 완료 (이전 단계)" for k in [
        "식품영양성분DB", "기능성 문구만 있는 제품도", "원재료·섭취방법·기준규격은", "2022년 이후 신고", "제품명에 '수출'",
        "대상 판별", "임산부·수유부", "제품명이 질환을", "일반·전문 의약품", "성분은 기능성 칸으로", "나이아신·판토텐산·비오틴",
        "식이섬유는 기능성 칸에", "제품명에 나온 영양소가", "원료 껍데기형", "다른 목적 원료·문구", "제품명의 피부·미백",
        "수면·긴장 원료", "오메가3 자체의 기억력", "단일: 성분 1개", "주성분 판단 순서", "제품명에 우리 영양소가 2개",
        "목적형: 성분 2~6개", "종합비타민: 성분 7개", "칼슘+철 제품도", "13개 항목", "목적형은 이름이 아니라",
        "단백질·인·칼륨·비타민 A·나트륨", "제품 식별자는", "압축된 후보만 표시량"]}
    done["비타민 D는 일반 정보로"] = "비타민 D 포함 / 오메가3·유산균·루테인·밀크씨슬은 웹에서 아직 안 씀 (11-04)"
    done["상한섭취량 초과 제품 제외"] = f"적용 완료 (2025 KDRI, 상한 초과 {n_over:,} · 확인 불가 {n_unknown:,} 제외)"
    done["기능성 원료는 상한이 아니라"] = "해당 없음 (웹에서 오메가3·루테인 등을 쓰지 않음)"
    add_criteria_sheet(wb, done)
    add_sheet(wb, "영양소×대상 (7단계 후)", table.reset_index().rename(columns={"index": "영양소"}), [22, 16, 10, 10, 10, 10], freeze="A2")
    cols = ["영양소", "대상", "구분", "품목제조신고번호", "제품명", "업체명", "1일 섭취량", "1일 함량", "1일 함량 단위", "기준치 대비(%)"]
    add_sheet(wb, f"남은 제품 ({len(keep):,}줄)", keep[cols], [20, 8, 18, 18, 32, 20, 26, 10, 8, 10])
    p = web.drop_duplicates("품목제조신고번호")
    rcols = ["결과", "이유", "품목제조신고번호", "제품명", "업체명", "대상", "1일 섭취량", "함께 든 가이드 성분", "기준규격"]
    add_sheet(wb, f"빠짐-상한 초과 ({n_over:,})", p[p["결과"] == "상한 초과"][rcols].sort_values("이유"), [10, 44, 18, 32, 20, 8, 26, 30, 60])
    add_sheet(wb, f"빠짐-확인 불가 ({n_unknown:,})", p[p["결과"] == "확인 불가"][rcols].sort_values("이유"), [10, 44, 18, 32, 20, 8, 26, 30, 60])
    wb.save(out("7단계_상한거르기.xlsx"))
    print(f"7단계 완료: 제품 {n_prod:,} → 확인 불가 {n_unknown:,} · 상한 초과 {n_over:,} → 남은 제품 {n_prod - n_unknown - n_over:,} ({len(keep):,}줄)")
    print(after.to_string())


if __name__ == "__main__":
    main()
