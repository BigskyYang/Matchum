# -*- coding: utf-8 -*-
"""
생활기능 영양제 분류·필터링 (11-05, 점수 단계는 아직 미정이라 품질 거르기까지만)

생활기능 영양제: 주 목적이 유산균·오메가3·루테인·밀크씨슬인 제품 (5단계에서 따로 보관한 제품)
영양제 1~8단계와 같은 흐름으로 거르되, 영양제에만 해당하는 기준은 건너뜀

  출발   5단계_보관.pkl 중 대상 '일반'만 (11-05 결정: 생활기능은 남성·여성·시니어로 나누지 않음)
  ① 하루 함량 읽기 (영양제 6단계에 해당)
     - 원료용 제품(섭취방법이 '건강기능식품 원료로 사용' 등) 제외: 공장에 납품하는 원료라 소비자 제품이 아님
     - 섭취방법이 없거나 1일 섭취량을 읽지 못한 제품 제외
     - 주 성분 하루 함량: 오메가3 = EPA와 DHA의 합(mg), 루테인(mg), 밀크씨슬 = 실리마린(mg), 유산균 = 프로바이오틱스 수(CFU)
     - 함께 든 비타민·미네랄 하루 함량 (영양제 6단계와 같은 방법)
  ② 인정 섭취량 + 상한 확인 (영양제 7단계에 해당)
     - 주 성분이 식약처 인정 섭취량 범위 밖이면 제외 (개별인정형 원료로 범위가 다른 제품도 확인이 어려워 제외, 11-05)
     - 주 성분 함량을 확인할 수 없으면 제외
     - 함께 든 비타민·미네랄이 상한섭취량(2025 KDRI)을 넘으면 제외
  ③ 품질 거르기 (영양제 8단계에 해당)
     ① 주의사항 정보 없음 / ③ 원재료 30개 초과 / ④ 비슷한 제품(같은 업체·같은 주 성분, 원재료 90% 이상 겹침,
       하루 함량 차이 10% 이내 → 가장 최근 신고만)
     ② 기준치 대비 500% 초과는 영양제 전용이라 건너뜀 (기능성 원료에는 1일 영양성분 기준치가 없음)
  건너뛴 영양제 전용 기준: B군 B1·B2, 한 제품 = 한 칸, 기준치 %, 점수(미정)

입력  5단계_보관.pkl (5단계_웹제품군.py 실행 결과)
출력  생활기능_분류.xlsx, 생활기능_결과.pkl
"""
import re
import importlib
import pandas as pd
from 공통 import out, nf, new_book, add_sheet

s6 = importlib.import_module("6단계_1일환산")
s8 = importlib.import_module("8단계_품질거르기")
s9 = importlib.import_module("9단계_점수")

TARGET = "일반"
# 식약처 인정 섭취량 (하루). 원문 재확인 필요: 유산균·실리마린은 고시 원문 미확인, 루테인은 건강기능식품협회 기준 인용
RANGE = {"유산균": (1e8, 1e10, "1억~100억 CFU"), "오메가3": (500, 2000, "EPA+DHA 0.5~2g"),
         "루테인": (10, 20, "10~20mg"), "밀크씨슬": (130, 130, "실리마린 130mg")}
MAIN_PAT = {"오메가3": r"EPA\s*(?:와|및|\+|&|,)?\s*DHA", "루테인": r"루테인(?!\s*지아잔틴\s*복합)", "밀크씨슬": r"실리마린"}
RAW_USE = r"원료로|제조\s*시"                 # 원료용 제품 표시
MAX_RAW, SIMILAR, AMOUNT_GAP = s8.MAX_RAW, s8.SIMILAR, s8.AMOUNT_GAP
VIT = ["비타민 C", "비타민 D", "칼슘", "마그네슘", "철", "아연", "엽산", "비타민 B6", "니아신", "비타민 A", "비타민 E", "요오드"]
UL = {**s9.UL, "칼슘": 2000}
KUNIT = {"조": 1e12, "억": 1e8, "만": 1e4}


def cfu_number(t):
    t = t.replace(" ", "")
    m = re.match(r"([\d.]+)[xX×*]10\^?(\d+)", t)
    if m:
        return float(m.group(1)) * 10 ** int(m.group(2))
    m = re.match(r"([\d,]{6,})", t)
    if m:
        return float(m.group(1).replace(",", ""))
    m = re.match(r"([\d,.]+)(조|억|만)", t)
    if m:
        return float(m.group(1).replace(",", "")) * KUNIT[m.group(2)]
    return None


def probiotic(spec, total):
    """기준규격 → (하루 CFU, 읽은 방법). total = 하루 먹는 총 무게(mg) 또는 None"""
    s = re.sub(r"(?i)cfu", "CFU", nf(str(spec)))
    m = re.search(r"(프로바이오틱스|유산균|생균)\s*수?", s)
    if not m:
        return None, "원문에 없음"
    seg = s[m.end():m.end() + 160]
    m2 = re.search(r"([\d][\d,.\sxX×*^]*(?:\([^)]*\))?\s*(?:조|억|만)?)\s*\)?\s*CFU\s*(?:\)|\s)*(?:/\s*([\d,.]*)\s*(mg|g|ml|mL))?", seg)
    if not m2:
        return None, "읽지 못함"
    num = cfu_number(re.sub(r"\([^)]*\)", "", m2.group(1)))
    if num is None:
        k = re.search(r"\(([\d,.]+\s*(?:조|억|만))\)", m2.group(1))
        num = cfu_number(k.group(1)) if k else None
    if num is None:
        return None, "읽지 못함"
    w, u = m2.group(2), m2.group(3)
    if u:
        wv = float(w.replace(",", "")) if w else 1.0
        wmg = wv * 1000 if u.lower() == "g" else wv
        if total:
            return num * total / wmg, "섭취량 무게로 환산"
        if not w or wv == 1:
            return None, "g당 표시인데 하루 무게 모름"
    return num, "표시량 = 1일 기준"


def clean_method(text):
    """섭취방법 표기 흔들림 정리 ('1회, 1정', '1캡', '1일 1회, 1캡슐')"""
    s = nf(str(text))
    s = re.sub(r"1회\s*,\s*", "1회 ", s)
    s = re.sub(r"(\d)\s*캡(?!슐)", r"\1캡슐", s)
    if not re.search(r"1회\s*\d", s):
        s = re.sub(r"(1일\s*\d+\s*회\s*,?\s*)(\d)", r"\1 1회 \2", s)
    return s


def step1(h):
    rows = []
    for _, r in h.iterrows():
        k = r["주 성분"]
        rec = {"품목제조신고번호": r["품목제조신고번호"], "1일 섭취량": "", "주성분 하루 함량": None, "읽은 방법": "", "판정": ""}
        sm = nf(str(r["섭취방법"]))
        if not sm.strip():
            rec["판정"] = "섭취방법 없음"
        elif re.search(RAW_USE, sm):
            rec["판정"] = "원료용 (소비자 제품 아님)"
        if rec["판정"]:
            rows.append(rec)
            continue
        times, cnt, unit, label, total = s6.daily_intake(clean_method(sm))
        rec["1일 섭취량"] = label
        if not label:
            rec["판정"] = "1일 섭취량 읽지 못함"
            rows.append(rec)
            continue
        if k == "유산균":
            rec["주성분 하루 함량"], rec["읽은 방법"] = probiotic(r["기준규격"], total)
        else:
            f = s6.find_amount(r["기준규격"], MAIN_PAT[k])
            if f == s6.NOT_IN_SPEC or not f or f[0] is None:
                rec["읽은 방법"] = "원문에 없음" if f == s6.NOT_IN_SPEC else "읽지 못함"
            else:
                v, u, _ = f
                if u == "μg":
                    v = v / 1000
                if k == "오메가3" and v < 10:          # '1.0 g'처럼 g로 적은 경우
                    v = v * 1000
                rec["주성분 하루 함량"], rec["읽은 방법"] = v, "표시량 = 1일 기준"
        for n, (pat, std) in s6.NUTRIENTS.items():
            f = s6.find_amount(r["기준규격"], pat)
            if f == s6.NOT_IN_SPEC or not f or f[0] is None:
                continue
            v, u, _ = f
            if n == "비타민 D" and u == "IU":
                v, u = v / 40, "μg"
            if u == "μg" and std == "mg":
                v /= 1000
            elif u == "mg" and std == "μg":
                v *= 1000
            rec[n] = v
        rec["니아신 형태"] = s6.niacin_form(r["원재료"])
        rows.append(rec)
    return pd.DataFrame(rows)


def judge(r, k):
    if r["판정"]:
        return r["판정"]
    v = r["주성분 하루 함량"]
    if pd.isna(v):
        return "주성분 함량 확인 불가"
    lo, hi, _ = RANGE[k]
    if v < lo * 0.999:
        return "인정 섭취량보다 적음"
    if v > hi * 1.001:
        return "인정 섭취량보다 많음"
    over = [n for n, lim in UL.items() if n in r and pd.notna(r[n]) and r[n] > lim]
    if pd.notna(r.get("니아신")) and r["니아신"] > s9.NIACIN_UL.get(r.get("니아신 형태"), 35):
        over.append("니아신")
    return f"상한 초과 ({'·'.join(over)})" if over else ""


def close(a, b):
    if pd.isna(a) and pd.isna(b):
        return True
    if pd.isna(a) or pd.isna(b):
        return False
    return abs(a - b) <= AMOUNT_GAP * max(a, b)


def main():
    print("[1/4] 5단계 보관 제품 읽는 중...")
    h = pd.read_pickle(out("5단계_보관.pkl")).drop_duplicates("품목제조신고번호")
    n_all = len(h)
    h = h[h["대상"] == TARGET].reset_index(drop=True)
    n0 = len(h)

    print("[2/4] 하루 함량 읽기 + 인정 섭취량·상한 확인...")
    a = step1(h)
    p = h.merge(a, on="품목제조신고번호", how="left")
    p["빠진 이유"] = [judge(r, r["주 성분"]) for _, r in p.iterrows()]
    p["원재료 수"] = p["원재료"].map(s9.raw_count)

    print("[3/4] 품질 거르기...")
    no_caution = p["섭취 시 주의사항"].fillna("").astype(str).str.strip().isin(["", "-", "해당없음", "없음"])
    p.loc[(p["빠진 이유"] == "") & no_caution, "빠진 이유"] = "① 주의사항 정보 없음"
    p.loc[(p["빠진 이유"] == "") & (p["원재료 수"] > MAX_RAW), "빠진 이유"] = f"③ 원재료 {MAX_RAW}개 초과"
    live = p[p["빠진 이유"] == ""]
    raws = {i: s8.raw_set(x) for i, x in live["원재료"].items()}
    pairs = []
    for _, g in live.groupby(["업체명", "주 성분"]):
        ids = list(g.index)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                x, y = ids[i], ids[j]
                if p.at[x, "빠진 이유"] or p.at[y, "빠진 이유"]:
                    continue
                A, B = raws[x], raws[y]
                if not A or not B or len(A & B) / max(len(A), len(B)) < SIMILAR:
                    continue
                if not close(p.at[x, "주성분 하루 함량"], p.at[y, "주성분 하루 함량"]):
                    continue
                if not all(close(p.at[x, v] if v in p else None, p.at[y, v] if v in p else None) for v in VIT):
                    continue
                keep, lose = sorted([x, y], key=lambda n: (-int(str(p.at[n, "신고일자"]).replace("-", "")[:8] or 0),
                                                         p.at[n, "원재료 수"], n))
                p.at[lose, "빠진 이유"] = f"④ 비슷한 제품 (남긴 제품: {p.at[keep, '제품명']})"
                pairs.append(lose)

    keep = p[p["빠진 이유"] == ""].copy()
    removed = p[p["빠진 이유"] != ""].copy()
    keep.to_pickle(out("생활기능_결과.pkl"))

    print("[4/4] 결과 엑셀 저장 중...")
    reason = removed["빠진 이유"].str.replace(r" \((?!소비자).*", "", regex=True)
    order = ["원료용 (소비자 제품 아님)", "섭취방법 없음", "1일 섭취량 읽지 못함", "주성분 함량 확인 불가",
             "인정 섭취량보다 많음", "인정 섭취량보다 적음", "상한 초과", "① 주의사항 정보 없음", f"③ 원재료 {MAX_RAW}개 초과", "④ 비슷한 제품"]
    tab = pd.crosstab(reason, removed["주 성분"]).reindex(order).fillna(0).astype(int)
    fin = keep["주 성분"].value_counts()
    lines = [("생활기능 영양제 분류·필터링 (품질 거르기까지, 점수는 미정)", True), ("", False), ("결과", True),
             (f"· 5단계 보관 {n_all:,}개 중 일반 대상 {n0:,}개 → 남은 제품 {len(keep):,}개", False),
             ("· 주 성분별 남은 제품: " + " / ".join(f"{k} {v:,}" for k, v in fin.items()), False),
             ("", False), ("빠진 이유 (위에서부터 차례로, 한 제품은 처음 걸린 이유 하나로만)", True)]
    for rsn, row in tab.iterrows():
        lines.append((f"· {rsn}: {int(row.sum()):,}개 (" + " · ".join(f"{k} {int(v)}" for k, v in row.items() if v) + ")", False))
    lines += [("", False), ("기준", True),
              ("· 인정 섭취량: " + " / ".join(f"{k} {v[2]}" for k, v in RANGE.items()) + " (원문 재확인 필요)", False),
              ("· 개별인정형 원료로 범위가 다른 제품도 확인이 어려워 제외 (11-05)", False),
              ("· 함께 든 비타민·미네랄 상한: 영양제 7단계와 같은 2025 KDRI", False),
              ("· 건너뛴 영양제 전용 기준: B군 B1·B2, 한 제품 = 한 칸, 기준치 500% 초과, 점수", False),
              ("· 같은 결과를 다시 만들려면: python 생활기능_분류.py (5단계까지 먼저 실행)", False)]
    wb = new_book(lines)
    cols = ["주 성분", "제품명", "업체명", "품목제조신고번호", "신고일자", "풀", "제형", "1일 섭취량", "주성분 하루 함량", "읽은 방법",
            "원재료 수", "기능성", "섭취 시 주의사항"]
    w = [10, 34, 22, 18, 11, 8, 8, 24, 14, 16, 8, 60, 60]
    add_sheet(wb, f"남은 제품 ({len(keep):,})", keep.sort_values(["주 성분", "제품명"])[cols], w)
    add_sheet(wb, f"빠진 제품 ({len(removed):,})", removed.sort_values(["빠진 이유", "주 성분"])[["빠진 이유"] + cols], [30] + w)
    wb.save(out("생활기능_분류.xlsx"))
    print(f"생활기능 완료: 일반 {n0:,} → 남은 제품 {len(keep):,}개 (" + " · ".join(f"{k} {v:,}" for k, v in fin.items()) + ")")
    print(tab.to_string())


if __name__ == "__main__":
    main()
