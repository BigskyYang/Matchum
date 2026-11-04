# -*- coding: utf-8 -*-
"""
8단계: 점수로 차등 (점수는 화면에 공개하지 않음)
기준: 「영양제_분류_필터링_기준(1104).pdf」 6절, 8절 + 11-04 결정

점수 (100점)
  ① 함량 기준 충족 50 — 하루 함량이 1일 영양성분 기준치의 몇 %인지 (고함량 가점 없음)
       100% 이상 50 / 30~100% 40 / 30% 미만 20
       · 비타민 B군: 들어 있는 B 비타민(B1·B2·니아신·B6·B12·판토텐산·비오틴) 각각의 기준치 % 중 가장 낮은 값 (11-04)
       · 식이섬유: 식품으로 먼저 안내하는 항목이라 함량 차등 없이 모두 50 (11-04)
       · 종합비타민: 핵심 8종 중 기준치 30% 이상 든 성분 수 / 8 × 50 (11-04)
       · 감점: 상한이 있는 성분 중 하나라도 하루 함량이 상한의 80% 이상이면 −10
  ② 섭취 편의 25 — 하루 1개 25 / 2개 15 / 3개 이상 6 (1정·1포·1병을 같은 1개로 보는 것은 팀의 설계 가정)
  ③ 주의 원료 15 — 없음 15 / 있음 0
       주의 원료 (11-04): 카페인(주의사항의 '카페인' 또는 원재료의 카페인·과라나·커피·녹차추출물),
                         간 관련(주의사항의 '간 질환' 등). 식약처 공통 안내 문구(알레르기·신장·항응고제 등)는 쓰지 않음
  ④ 성분 구성 관련성 10 — 식약처 문구에 '흡수'가 직접 나오는 짝만: 철 + 비타민 C, 칼슘 + 비타민 D

순서 (점수는 공개하지 않고 순서·등급에만 씀)
  · 단일·목적형: 점수 높은 순 → 같으면 성분이 적은 단순한 제품 → 품목제조신고번호 순
  · 종합비타민 균형형: 핵심 8종 중 기준치 30% 이상 든 성분 수 → 점수 → …
  · 종합비타민 피로회복형: B군·C의 기준치 충족도(100%까지만 셈) → 핵심 8종 충족 수 → 점수 → …
등급: 상 / 중 / 하 (경계 점수는 분포를 보고 정함, 아래 GRADE)

입력  7단계_결과.pkl, 6단계_제품별함량.pkl, 최종본 엑셀(기준규격의 B 비타민 표시량)
출력  8단계_점수.xlsx, 8단계_결과.pkl (다음 단계 입력)
"""
import re
import importlib
import pandas as pd
from 공통 import out, nf, new_book, add_sheet, add_criteria_sheet

step6 = importlib.import_module("6단계_1일환산")      # 표시량 읽는 함수를 같이 씀

TARGETS = ["일반", "남성", "여성", "시니어"]
DV = {"비타민 C": 100, "비타민 D": 10, "칼슘": 700, "마그네슘": 315, "철": 12, "아연": 8.5, "엽산": 400}
# B 비타민별 (기준규격 이름, 기준치, 단위)
B_VITAMINS = {"비타민 B1": (r"비타민\s*B1(?!\d)|티아민", 1.2, "mg"), "비타민 B2": (r"비타민\s*B2|리보플라빈", 1.4, "mg"),
              "니아신": (r"나이아신|니아신", 15, "mg"), "비타민 B6": (r"비타민\s*B6", 1.5, "mg"),
              "비타민 B12": (r"비타민\s*B12", 2.4, "μg"), "판토텐산": (r"판토텐산", 5, "mg"),
              "비오틴": (r"비오틴", 30, "μg")}
CORE8 = ["비타민 B군", "비타민 C", "비타민 D", "칼슘", "마그네슘", "아연", "철", "엽산"]
UL = {"비타민 C": 2000, "비타민 D": 100, "칼슘": 2000, "마그네슘": 350, "철": 45, "아연": 35, "엽산": 1000,
      "비타민 B6": 50, "비타민 A": 3000, "비타민 E": 540}
CAUTION_TEXT = r"카페인|간\s*질환|간\s*손상|간\s*기능\s*이상|간에\s*이상"
CAUTION_RAW = r"카페인|과라나|커피|녹차\s*추출"
GRADE = [("상", 80), ("중", 60), ("하", 0)]          # 경계 점수 (분포를 보고 정함)


def b_percent(spec):
    """기준규격에서 B 비타민별 기준치 % → {이름: %}"""
    res = {}
    for name, (pat, dv, unit) in B_VITAMINS.items():
        found = step6.find_amount(spec, pat)
        if found in (None, step6.NOT_IN_SPEC) or found[0] is None:
            continue
        val, u, _ = found
        if u == "μg" and unit == "mg":
            val /= 1000
        elif u == "mg" and unit == "μg":
            val *= 1000
        elif u == "IU":
            continue
        res[name] = val / dv * 100
    return res


def amount_score(pct):
    if pct is None:
        return None
    return 50 if pct >= 100 else 40 if pct >= 30 else 20


def daily_count(label):
    m = re.search(r"하루\s*([\d\.]+)", str(label))
    return float(m.group(1)) if m else None


def grade_of(score):
    for g, cut in GRADE:
        if score >= cut:
            return g
    return "하"


def main():
    print("[1/3] 7단계 결과 읽는 중...")
    web = pd.read_pickle(out("7단계_결과.pkl"))
    amt = pd.read_pickle(out("6단계_제품별함량.pkl"))
    prod = web.drop_duplicates("품목제조신고번호").set_index("품목제조신고번호")

    print("[2/3] 점수 매기는 중...")
    # 제품 단위 값
    info = {}
    for no, r in prod.iterrows():
        a = amt.loc[no]
        ings = set(str(r["함께 든 가이드 성분"]).split(", "))
        bp = b_percent(r["기준규격"]) if "비타민 B군" in ings else {}
        b_min = min(bp.values()) if bp else None
        pct = {k: (a[k] / dv * 100 if k in a.index and pd.notna(a[k]) else None) for k, dv in DV.items()}
        pct["비타민 B군"] = b_min
        core_ok = sum(1 for k in CORE8 if k in ings and pct.get(k) is not None and pct[k] >= 30)
        near_ul = [k for k, lim in UL.items() if k in a.index and pd.notna(a[k]) and a[k] >= 0.8 * lim]
        caution = bool(re.search(CAUTION_TEXT, nf(r["섭취 시 주의사항"])) or re.search(CAUTION_RAW, nf(r["원재료"])))
        cnt = daily_count(r["1일 섭취량"])
        info[no] = dict(pct=pct, b=bp, core_ok=core_ok, near_ul=near_ul, caution=caution, cnt=cnt, ings=ings)

    rows = []
    for _, r in web.iterrows():
        no, k = r["품목제조신고번호"], str(r["영양소"])
        d = info[no]
        if k.startswith("종합비타민"):
            s_amt, why_amt = round(d["core_ok"] / 8 * 50), f"핵심 8종 중 기준치 30% 이상 {d['core_ok']}종"
        elif k == "식이섬유":
            s_amt, why_amt = 50, "식이섬유: 함량 차등 없음"
        else:
            p = d["pct"].get(k)
            s_amt = amount_score(p)
            why_amt = (f"기준치 {p:.0f}%" if p is not None else "함량 확인 불가") + (" (B 비타민 중 가장 낮은 값)" if k == "비타민 B군" else "")
            if s_amt is None:
                s_amt = 20
        penalty = -10 if d["near_ul"] else 0
        c = d["cnt"]
        s_conv = 25 if c is not None and c <= 1 else 15 if c is not None and c <= 2 else 6
        s_caut = 0 if d["caution"] else 15
        s_pair = 10 if (k == "철" and "비타민 C" in d["ings"]) or (k == "칼슘" and "비타민 D" in d["ings"]) else 0
        total = s_amt + penalty + s_conv + s_caut + s_pair
        # 종합비타민 정렬 키
        bc = sum(min(100, d["pct"].get(x) or 0) for x in ["비타민 B군", "비타민 C"])
        rows.append({**r.to_dict(),
                     "함량 점수": s_amt, "상한 근접 감점": penalty, "편의 점수": s_conv, "주의 원료 점수": s_caut,
                     "성분 구성 점수": s_pair, "점수": total, "등급": grade_of(total),
                     "함량 근거": why_amt, "상한 80% 이상 성분": ", ".join(d["near_ul"]),
                     "주의 원료": "있음" if d["caution"] else "", "핵심 8종 충족": d["core_ok"], "B·C 충족도": round(bc),
                     "성분 수": len(d["ings"])})
    sc = pd.DataFrame(rows)

    # 순서 (영양소 × 대상 안에서)
    sc["_k1"] = 0.0
    sc["_k2"] = 0.0
    bal = sc["영양소"].astype(str) == "종합비타민 (균형형)"
    fat = sc["영양소"].astype(str) == "종합비타민 (피로회복형)"
    sc.loc[bal, "_k1"] = sc.loc[bal, "핵심 8종 충족"]
    sc.loc[fat, "_k1"] = sc.loc[fat, "B·C 충족도"]
    sc.loc[fat, "_k2"] = sc.loc[fat, "핵심 8종 충족"]
    sc = sc.sort_values(["영양소", "대상", "_k1", "_k2", "점수", "성분 수", "품목제조신고번호"],
                        ascending=[True, True, False, False, False, True, True]).drop(columns=["_k1", "_k2"])
    sc["순서"] = sc.groupby(["영양소", "대상"], observed=True).cumcount() + 1
    sc = sc.reset_index(drop=True)
    sc.to_pickle(out("8단계_결과.pkl"))

    # 분포
    order = list(web["영양소"].cat.categories) if hasattr(web["영양소"], "cat") else sorted(web["영양소"].unique())
    bins = [0, 40, 50, 60, 70, 80, 90, 101]
    labels = ["40 미만", "40~49", "50~59", "60~69", "70~79", "80~89", "90~100"]
    sc["점수대"] = pd.cut(sc["점수"], bins=bins, labels=labels, right=False)
    dist_all = sc["점수대"].value_counts().reindex(labels).fillna(0).astype(int)
    dist = pd.crosstab(sc["영양소"], sc["점수대"]).reindex(index=order, columns=labels).fillna(0).astype(int)
    grade_tbl = pd.crosstab([sc["영양소"], sc["대상"]], sc["등급"]).reindex(columns=["상", "중", "하"]).fillna(0).astype(int)
    grade_tbl = grade_tbl[grade_tbl.sum(axis=1) > 0].reset_index()
    sc = sc.drop(columns="점수대")

    print("[3/3] 결과 엑셀 저장 중... (1~2분, 아무 키도 누르지 마세요)")
    lines = [
        ("8단계: 점수로 차등 (점수는 화면에 공개하지 않음)", True), ("", False),
        ("결과", True),
        (f"· 영양소별 {len(sc):,}줄에 점수와 등급을 매김 (제품 {sc['품목제조신고번호'].nunique():,}개). 빼는 제품은 없음 — 등급 경계를 정한 뒤 9단계에서 '하' 등급을 뺌", False),
        ("· 전체 점수 분포: " + " / ".join(f"{k} {v:,}" for k, v in dist_all.items()), False),
        (f"· 지금 등급 경계(초안): 상 {GRADE[0][1]}점 이상 / 중 {GRADE[1][1]}점 이상 / 하 그 미만", False),
        (f"· 주의 원료(카페인·간 관련)가 있는 줄: {int((sc['주의 원료'] == '있음').sum()):,}개 / 상한 80% 이상 감점: {int((sc['상한 근접 감점'] < 0).sum()):,}개", False),
        ("", False), ("점수 (100점)", True),
        ("· 함량 기준 충족 50: 기준치 100% 이상 50 / 30~100% 40 / 30% 미만 20, 상한 80% 이상이면 −10", False),
        ("   - 비타민 B군은 든 B 비타민 중 가장 낮은 기준치 %, 식이섬유는 모두 50, 종합비타민은 핵심 8종 중 기준치 30% 이상 성분 수 / 8 × 50", False),
        ("· 섭취 편의 25: 하루 1개 25 / 2개 15 / 3개 이상 6", False),
        ("· 주의 원료 15: 카페인·간 관련 원료가 없으면 15", False),
        ("· 성분 구성 관련성 10: 철 + 비타민 C, 칼슘 + 비타민 D", False),
        ("", False), ("순서", True),
        ("· 단일·목적형: 점수 → 성분이 적은 제품 → 품목제조신고번호", False),
        ("· 종합비타민 균형형: 핵심 8종 중 기준치 30% 이상 성분 수 → 점수 / 피로회복형: B군·C 충족도 → 핵심 8종 → 점수", False),
        ("· 같은 결과를 다시 만들려면: python 8단계_점수.py", False),
    ]
    wb = new_book(lines)
    done = {k: "적용 완료 (이전 단계)" for k in [
        "식품영양성분DB", "기능성 문구만 있는 제품도", "원재료·섭취방법·기준규격은", "2022년 이후 신고", "제품명에 '수출'",
        "대상 판별", "임산부·수유부", "제품명이 질환을", "일반·전문 의약품", "성분은 기능성 칸으로", "나이아신·판토텐산·비오틴",
        "식이섬유는 기능성 칸에", "제품명에 나온 영양소가", "원료 껍데기형", "다른 목적 원료·문구", "제품명의 피부·미백",
        "수면·긴장 원료", "오메가3 자체의 기억력", "단일: 성분 1개", "주성분 판단 순서", "제품명에 우리 영양소가 2개",
        "목적형: 성분 2~6개", "종합비타민: 성분 7개", "칼슘+철 제품도", "13개 항목", "목적형은 이름이 아니라",
        "단백질·인·칼륨·비타민 A·나트륨", "제품 식별자는", "압축된 후보만 표시량", "상한섭취량 초과 제품 제외"]}
    done["비타민 D는 일반 정보로"] = "비타민 D 포함 / 오메가3·유산균·루테인·밀크씨슬은 웹에서 아직 안 씀 (11-04)"
    done["기능성 원료는 상한이 아니라"] = "해당 없음 (웹에서 오메가3·루테인 등을 쓰지 않음)"
    done["함량 기준 충족 50"] = "적용 완료 (B군은 가장 낮은 B 비타민 %, 식이섬유 차등 없음, 종합비타민은 30% 이상 성분 수)"
    done["섭취 편의 25"] = "적용 완료"
    done["주의 원료 15"] = "적용 완료 (카페인·간 관련만, 11-04)"
    done["성분 구성 관련성 10"] = "적용 완료"
    done["후보를 몇 개까지"] = "영양소 × 대상별 최대 3개 (11-04 대천님 요청), 등급 '하'는 제외 예정"
    add_criteria_sheet(wb, done)
    add_sheet(wb, "점수 분포 (영양소별)", dist.reset_index().rename(columns={"index": "영양소"}), [22] + [9] * 7, freeze="A2")
    add_sheet(wb, "등급 (영양소×대상)", grade_tbl, [22, 8, 8, 8, 8], freeze="A2")
    cols = ["영양소", "대상", "순서", "등급", "점수", "함량 점수", "상한 근접 감점", "편의 점수", "주의 원료 점수", "성분 구성 점수",
            "함량 근거", "상한 80% 이상 성분", "주의 원료", "구분", "품목제조신고번호", "제품명", "업체명", "1일 섭취량",
            "1일 함량", "1일 함량 단위", "기준치 대비(%)"]
    add_sheet(wb, f"점수표 ({len(sc):,}줄)", sc[cols], [20, 8, 6, 6, 6, 8, 8, 8, 8, 8, 30, 16, 8, 18, 18, 32, 20, 26, 10, 8, 10])
    wb.save(out("8단계_점수.xlsx"))
    print(f"8단계 완료: {len(sc):,}줄 점수 매김. 분포: " + " / ".join(f"{k} {v:,}" for k, v in dist_all.items()))
    print(grade_tbl.to_string(index=False))


if __name__ == "__main__":
    main()
