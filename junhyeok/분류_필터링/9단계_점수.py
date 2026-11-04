# -*- coding: utf-8 -*-
"""
9단계: 점수 매기기 + 70점 미만 탈락 (점수는 화면에 공개하지 않음)
기준: 「영양제_분류_필터링_기준(1104).pdf」 6절·8절 + 11-04 팀 결정 (변경안 확정)

점수 (100점) — '많을수록'이 아니라 '적정할수록' 높게
  ① 함량 적정성 40 — 하루 함량이 1일 영양성분 기준치의 몇 %인지
       100~300% 40 / 50~100% 32 / 300~500% 28 / 30~50% 20 / 30% 미만·확인 불가 10
       · 비타민 B군: 들어 있는 B 비타민 각각의 기준치 % 중 가장 낮은 값
       · 식이섬유: 식품으로 먼저 안내하는 항목이라 함량 차등 없이 40
       · 종합비타민: 핵심 8종 중 기준치 30% 이상 든 성분 수 / 8 × 40
  ② 상한 근접 감점 — 상한이 있는 성분 중 하나라도 상한의 80% 이상 −10 / 50% 이상 −5
  ③ 섭취 편의 20 — 하루 1개 20 / 2개 14 / 3개 8 / 4개 이상·미확인 3
  ④ 원료 단순성 20 — 원재료 10개 이하 20 / 11~20개 13 / 21~30개 6 (30개 초과는 8단계에서 제외)
  ⑤ 주의 원료 10 — 카페인·간 관련 내용이 없으면 10 / 있으면 0
  ⑥ 성분 구성 10 — 철 + 비타민 C, 칼슘 + 비타민 D (식약처 문구에 '흡수'가 직접 나오는 짝)
  * 종합비타민: 원재료가 원래 많고 짝 점수를 받을 수 없어서 ④·⑥을 빼고 ①②③⑤(70점 만점)를 100점으로 환산
  * '최신 신고' 점수는 제품 내용과 상관이 없어서 넣지 않음 (11-04)

등급 (11-04 결정 '가'): 상 85점 이상 / 중 70~84점 / 하 70점 미만 → 하는 탈락
순서 (영양소 × 대상 안에서): 등급 → 점수 → 하루 섭취 개수 적은 순 → 기준치 100%에 가까운 순 → 원재료 적은 순
  (의미 없는 신고번호 순은 쓰지 않음. 그래도 같으면 같은 순위로 보고 10단계에서 업체가 겹치지 않게 고름)

입력  8단계_결과.pkl, 6단계_제품별함량.pkl
출력  9단계_점수.xlsx, 9단계_결과.pkl (다음 단계 입력)
"""
import re
import importlib
import numpy as np
import pandas as pd
from 공통 import out, nf, new_book, add_sheet, add_criteria_sheet

step6 = importlib.import_module("6단계_1일환산")      # 기준규격 표시량 읽는 함수를 같이 씀

TARGETS = ["일반", "남성", "여성", "시니어"]
NUTRIENTS = ["비타민 B군", "비타민 C", "비타민 D", "칼슘", "마그네슘", "아연", "철", "엽산", "식이섬유",
             "종합비타민 (균형형)", "종합비타민 (피로회복형)"]
DV = {"비타민 C": 100, "비타민 D": 10, "칼슘": 700, "마그네슘": 315, "철": 12, "아연": 8.5, "엽산": 400}
B_VITAMINS = {"비타민 B1": (r"비타민\s*B1(?!\d)|티아민", 1.2, "mg"), "비타민 B2": (r"비타민\s*B2|리보플라빈", 1.4, "mg"),
              "니아신": (r"나이아신|니아신", 15, "mg"), "비타민 B6": (r"비타민\s*B6", 1.5, "mg"),
              "비타민 B12": (r"비타민\s*B12", 2.4, "μg"), "판토텐산": (r"판토텐산", 5, "mg"),
              "비오틴": (r"비오틴", 30, "μg")}
CORE8 = ["비타민 B군", "비타민 C", "비타민 D", "칼슘", "마그네슘", "아연", "철", "엽산"]
UL = {"비타민 C": 2000, "비타민 D": 100, "칼슘": 2000, "마그네슘": 350, "철": 45, "아연": 35, "엽산": 1000,
      "비타민 B6": 50, "비타민 A": 3000, "비타민 E": 540}
CAUTION_TEXT = r"카페인|간\s*질환|간\s*손상|간\s*기능\s*이상|간에\s*이상"
CAUTION_RAW = r"카페인|과라나|커피|녹차\s*추출"
GRADE = [("상", 85), ("중", 70), ("하", 0)]          # 11-04 결정 '가'
PASS_GRADES = ["상", "중"]


# ── 제품 단위 정보 (8단계 ④ 비슷한 제품 판단에도 같이 씀)
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


def raw_count(raw):
    """원재료 개수 = 쉼표로 나뉜 항목 수 (괄호 안의 세부 원료도 1개로 셈)"""
    t = nf(raw if isinstance(raw, str) else "").strip()
    return t.count(",") + 1 if t else 0


def daily_count(label):
    m = re.search(r"하루\s*([\d\.]+)", str(label))
    return float(m.group(1)) if m else None


def product_info(prod, amt):
    """prod: 품목제조신고번호를 인덱스로 한 제품 표 → {번호: 정보}"""
    info = {}
    for no, r in prod.iterrows():
        a = amt.loc[no]
        ings = set(str(r["함께 든 가이드 성분"]).split(", "))
        bp = b_percent(r["기준규격"]) if "비타민 B군" in ings else {}
        pct = {k: (a[k] / dv * 100 if k in a.index and pd.notna(a[k]) else None) for k, dv in DV.items()}
        pct["비타민 B군"] = min(bp.values()) if bp else None
        ul_ratio = {k: a[k] / lim for k, lim in UL.items() if k in a.index and pd.notna(a[k])}
        info[no] = dict(
            pct=pct, b=bp, ings=ings, cnt=daily_count(r["1일 섭취량"]), raw=raw_count(r["원재료"]),
            core_ok=sum(1 for k in CORE8 if k in ings and pct.get(k) is not None and pct[k] >= 30),
            ul_max=max(ul_ratio.values()) if ul_ratio else 0.0,
            near_ul=[k for k, v in ul_ratio.items() if v >= 0.5],
            caution=bool(re.search(CAUTION_TEXT, nf(r["섭취 시 주의사항"])) or re.search(CAUTION_RAW, nf(r["원재료"]))))
    return info


def amount_score(pct):
    if pct is None:
        return 10
    if 100 <= pct <= 300:
        return 40
    if 50 <= pct < 100:
        return 32
    if 300 < pct <= 500:
        return 28
    if 30 <= pct < 50:
        return 20
    return 10


def score_row(k, d):
    """영양소 k 줄의 점수 → dict"""
    multi = k.startswith("종합비타민")
    if multi:
        s_amt, why = round(d["core_ok"] / 8 * 40), f"핵심 8종 중 기준치 30% 이상 {d['core_ok']}종"
    elif k == "식이섬유":
        s_amt, why = 40, "식이섬유: 함량 차등 없음"
    else:
        p = d["pct"].get(k)
        s_amt = amount_score(p)
        why = (f"기준치 {p:.0f}%" if p is not None else "함량 확인 불가") + (" (B 비타민 중 가장 낮은 값)" if k == "비타민 B군" else "")
    pen = -10 if d["ul_max"] >= 0.8 else -5 if d["ul_max"] >= 0.5 else 0
    c = d["cnt"]
    s_conv = 20 if c is not None and c <= 1 else 14 if c is not None and c <= 2 else 8 if c is not None and c <= 3 else 3
    s_raw = 20 if d["raw"] <= 10 else 13 if d["raw"] <= 20 else 6
    s_caut = 0 if d["caution"] else 10
    s_pair = 10 if (k == "철" and "비타민 C" in d["ings"]) or (k == "칼슘" and "비타민 D" in d["ings"]) else 0
    if multi:
        total = round((s_amt + pen + s_conv + s_caut) / 70 * 100)
        s_raw = s_pair = None
        how = "종합비타민: 원료 단순성·성분 구성 제외 70점 → 100점 환산"
    else:
        total = s_amt + pen + s_conv + s_raw + s_caut + s_pair
        how = ""
    pct = d["pct"].get(k)
    return {"함량 점수": s_amt, "상한 근접 감점": pen, "편의 점수": s_conv, "원료 단순성 점수": s_raw,
            "주의 원료 점수": s_caut, "성분 구성 점수": s_pair, "점수": max(0, int(total)), "점수 계산": how,
            "함량 근거": why, "상한 50% 이상 성분": ", ".join(d["near_ul"]), "주의 원료": "있음" if d["caution"] else "",
            "핵심 8종 충족": d["core_ok"], "원재료 수": d["raw"],
            "_섭취개수": c if c is not None else 99, "_100근접": abs(pct - 100) if pct is not None else 9999}


def score_table(web, info):
    rows = [{**r.to_dict(), **score_row(str(r["영양소"]), info[r["품목제조신고번호"]])} for _, r in web.iterrows()]
    return pd.DataFrame(rows)


def grade_of(score):
    for g, cut in GRADE:
        if score >= cut:
            return g
    return "하"


def main():
    print("[1/3] 8단계 결과 읽는 중...")
    web = pd.read_pickle(out("8단계_결과.pkl"))
    amt = pd.read_pickle(out("6단계_제품별함량.pkl"))
    prod = web.drop_duplicates("품목제조신고번호").set_index("품목제조신고번호")

    print("[2/3] 점수 매기는 중...")
    sc = score_table(web, product_info(prod, amt))
    sc["등급"] = sc["점수"].map(grade_of)
    sc["영양소"] = pd.Categorical(sc["영양소"].astype(str), NUTRIENTS, ordered=True)
    sc["대상"] = pd.Categorical(sc["대상"].astype(str), TARGETS, ordered=True)
    sc["_등급순"] = sc["등급"].map({"상": 0, "중": 1, "하": 2})
    sc = sc.sort_values(["영양소", "대상", "_등급순", "점수", "_섭취개수", "_100근접", "원재료 수"],
                        ascending=[True, True, True, False, True, True, True], kind="stable")
    sc["순서"] = sc.groupby(["영양소", "대상"], observed=True).cumcount() + 1
    sc = sc.drop(columns=["_등급순"]).reset_index(drop=True)

    keep = sc[sc["등급"].isin(PASS_GRADES)].reset_index(drop=True)
    drop = sc[~sc["등급"].isin(PASS_GRADES)].reset_index(drop=True)
    keep["순서"] = keep.groupby(["영양소", "대상"], observed=True).cumcount() + 1
    keep.to_pickle(out("9단계_결과.pkl"))

    labels = ["50 미만", "50~59", "60~69", "70~74", "75~79", "80~84", "85~89", "90~100"]
    band = pd.cut(sc["점수"], [0, 50, 60, 70, 75, 80, 85, 90, 101], labels=labels, right=False)
    dist_all = band.value_counts().reindex(labels).fillna(0).astype(int)
    dist = pd.crosstab(sc["영양소"], band).reindex(index=NUTRIENTS, columns=labels).fillna(0).astype(int)
    grade_tbl = pd.crosstab(sc["영양소"], sc["등급"]).reindex(index=NUTRIENTS, columns=["상", "중", "하"]).fillna(0).astype(int)
    after = pd.crosstab(keep["영양소"], keep["대상"]).reindex(index=NUTRIENTS, columns=TARGETS).fillna(0).astype(int)
    n_prod, n_keep = sc["품목제조신고번호"].nunique(), keep["품목제조신고번호"].nunique()
    gc = sc["등급"].value_counts()

    print("[3/3] 결과 엑셀 저장 중... (1~2분, 아무 키도 누르지 마세요)")
    lines = [
        ("9단계: 점수 매기기 + 70점 미만 탈락 (점수는 화면에 공개하지 않음)", True), ("", False),
        ("결과", True),
        (f"· 8단계 제품 {n_prod:,}개 ({len(sc):,}줄) → 상 {gc.get('상', 0):,} · 중 {gc.get('중', 0):,} · 하(탈락) {gc.get('하', 0):,}줄 → 남은 제품 {n_keep:,}개 ({len(keep):,}줄)", False),
        ("· 한 제품이 여러 영양소 줄에 있을 때, 일부 줄만 탈락하면 그 제품은 남은 줄로 계속 후보가 됨", False),
        ("· 점수 분포: " + " / ".join(f"{k} {v:,}" for k, v in dist_all.items()), False),
        ("", False), ("점수 (100점, 적정할수록 높게)", True),
        ("· 함량 적정성 40: 기준치 100~300% 40 / 50~100% 32 / 300~500% 28 / 30~50% 20 / 30% 미만·확인 불가 10", False),
        ("   - B군은 든 B 비타민 중 가장 낮은 %, 식이섬유는 모두 40, 종합비타민은 핵심 8종 중 30% 이상 성분 수 / 8 × 40", False),
        ("· 상한 근접 감점: 상한의 80% 이상 −10 / 50% 이상 −5", False),
        ("· 섭취 편의 20: 하루 1개 20 / 2개 14 / 3개 8 / 4개 이상 3", False),
        ("· 원료 단순성 20: 원재료 10개 이하 20 / 11~20개 13 / 21~30개 6", False),
        ("· 주의 원료 10: 카페인·간 관련 내용이 없으면 10", False),
        ("· 성분 구성 10: 철 + 비타민 C, 칼슘 + 비타민 D", False),
        ("· 종합비타민: 원료 단순성·성분 구성을 빼고 70점 만점 → 100점으로 환산", False),
        ("", False), ("등급 (11-04 결정 '가')", True),
        ("· 상 85점 이상 / 중 70~84점 / 하 70점 미만 → 하는 탈락", False),
        ("", False), ("순서 (영양소 × 대상 안에서)", True),
        ("· 등급 → 점수 → 하루 섭취 개수 적은 순 → 기준치 100%에 가까운 순 → 원재료 적은 순", False),
        ("· 엑셀·결과의 영양소 순서: B군 → C → D → 칼슘 → 마그네슘 → 아연 → 철 → 엽산 → 식이섬유 → 종합비타민", False),
        ("", False), ("참고", True),
        ("· 마그네슘은 기준치(315mg)와 상한(350mg)이 가까워서 상한 근접 감점을 거의 항상 받음 → 상 등급이 적음", False),
        ("· 단일 제품은 성분 구성 10점을 받을 수 없어 최고 90점", False),
        ("· 같은 결과를 다시 만들려면: python 전체_실행.py", False),
    ]
    wb = new_book(lines)
    done = {k: "적용 완료 (이전 단계)" for k in [
        "식품영양성분DB", "기능성 문구만 있는 제품도", "원재료·섭취방법·기준규격은", "2022년 이후 신고", "제품명에 '수출'",
        "대상 판별", "임산부·수유부", "제품명이 질환을", "일반·전문 의약품", "성분은 기능성 칸으로", "나이아신·판토텐산·비오틴",
        "식이섬유는 기능성 칸에", "제품명에 나온 영양소가", "원료 껍데기형", "다른 목적 원료·문구", "제품명의 피부·미백",
        "수면·긴장 원료", "오메가3 자체의 기억력", "단일: 성분 1개", "주성분 판단 순서", "제품명에 우리 영양소가 2개",
        "목적형: 성분 2~6개", "종합비타민: 성분 7개", "칼슘+철 제품도", "13개 항목", "목적형은 이름이 아니라",
        "단백질·인·칼륨·비타민 A·나트륨", "제품 식별자는", "압축된 후보만 표시량", "상한섭취량 초과 제품 제외",
        "주의사항 정보가 없는", "기준치 대비 500%", "원재료가 30개", "비슷한 제품"]}
    done.update({k: "적용 완료" for k in ["함량 적정성 40", "상한 근접 감점", "섭취 편의 20", "원료 단순성 20",
                                         "주의 원료 10", "성분 구성 10", "종합비타민 점수", "등급"]})
    done["비타민 D는 일반 정보로"] = "비타민 D 포함 / 오메가3·유산균·루테인·밀크씨슬은 웹에서 아직 안 씀 (11-04)"
    done["기능성 원료는 상한이 아니라"] = "해당 없음 (웹에서 오메가3·루테인 등을 쓰지 않음)"
    add_criteria_sheet(wb, done)
    add_sheet(wb, "점수 분포 (영양소별)", dist.reset_index().rename(columns={"index": "영양소"}), [24] + [9] * 8, freeze="A2")
    add_sheet(wb, "등급 (영양소별)", grade_tbl.reset_index().rename(columns={"index": "영양소"}), [24, 8, 8, 10], freeze="A2")
    add_sheet(wb, "남은 후보 (영양소×대상)", after.reset_index().rename(columns={"index": "영양소"}), [24, 8, 8, 8, 8], freeze="A2")
    cols = ["영양소", "대상", "순서", "등급", "점수", "함량 점수", "상한 근접 감점", "편의 점수", "원료 단순성 점수",
            "주의 원료 점수", "성분 구성 점수", "점수 계산", "함량 근거", "상한 50% 이상 성분", "주의 원료", "구분",
            "품목제조신고번호", "제품명", "업체명", "제형", "1일 섭취량", "1일 함량", "1일 함량 단위", "기준치 대비(%)", "원재료 수"]
    w = [22, 8, 6, 6, 6, 8, 8, 8, 8, 8, 8, 30, 30, 16, 8, 18, 18, 32, 20, 10, 26, 10, 8, 10, 8]
    add_sheet(wb, f"통과 ({len(keep):,}줄)", keep[cols], w)
    add_sheet(wb, f"탈락 ({len(drop):,}줄)", drop[cols], w)
    wb.save(out("9단계_점수.xlsx"))
    print(f"9단계 완료: {len(sc):,}줄 → 상 {gc.get('상', 0):,} · 중 {gc.get('중', 0):,} · 탈락 {gc.get('하', 0):,} → 제품 {n_keep:,}개 ({len(keep):,}줄)")
    print(after.to_string())


if __name__ == "__main__":
    main()
