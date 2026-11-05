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
       원재료 수는 괄호 밖 원료를, 같은 이름은 한 번만 셈 (11-05)
  ⑤ 주의 원료 10 — 카페인·간 관련 내용이 없으면 10 / 있으면 0
  ⑥ 성분 구성 10 — 철 + 비타민 C, 칼슘 + 비타민 D (식약처 문구에 '흡수'가 직접 나오는 짝)
  * 종합비타민: 원재료가 원래 많고 짝 점수를 받을 수 없어서 ④·⑥을 빼고 ①②③⑤(70점 만점)를 100점으로 환산
  * '최신 신고' 점수는 제품 내용과 상관이 없어서 넣지 않음 (11-04)

등급 (11-04 결정 '가'): 상 85점 이상 / 중 70~84점 / 하 70점 미만 → 하는 탈락
순서 (영양소 × 대상 안에서): 등급 → 점수 → 하루 섭취 개수 적은 순 → 기준치 100%에 가까운 순 → 원재료 적은 순
  (의미 없는 신고번호 순은 쓰지 않음. 그래도 같으면 같은 순위로 보고 10단계에서 업체가 겹치지 않게 고름)

웹용 파일 (11-04 결정: '칸마다 3개 고르기'는 폐기 → 사람마다 웹에서 고름)
  · 70점 이상 후보 전체를 junhyeok/output/web_products.csv로 저장 (UTF-8, 모든 칸 따옴표)
  · 열: 영양소, 제품명, 업체명, 품목제조신고번호, 대상, 1일 섭취량, 1일 함량, 기준치 대비(%), 기능성, 섭취 시 주의사항
        + 순서(칸 안에서 먼저 볼 순서, 점수는 넣지 않음), 구분, 제형
        + 제품의 하루 함량 열(비타민 C·D·B1·B2·B6·니아신, 칼슘, 마그네슘, 철, 아연, 엽산, 비타민 A·E)
          → 웹에서 여러 제품을 함께 볼 때 상한 합산 확인, B1·B2가 든 제품 확인에 씀
  · 저장 전 자동 점검: 열 이름·순서, 대상, 영양소, 신고번호 형식, 중복, 어린이·임산부 이름

입력  8단계_결과.pkl, 6단계_제품별함량.pkl
출력  9단계_점수.xlsx, 9단계_결과.pkl, ../output/web_products.csv, ../output/web_products_정보.md
"""
import os, re, csv, datetime
import importlib
import numpy as np
import pandas as pd
from 공통 import HERE, out, nf, new_book, add_sheet, add_criteria_sheet

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
      "비타민 B6": 50, "비타민 A": 3000, "비타민 E": 540, "요오드": 2400}
CAUTION_TEXT = r"카페인|간\s*질환|간\s*손상|간\s*기능\s*이상|간에\s*이상"
CAUTION_RAW = r"카페인|과라나|커피|녹차\s*추출"
GRADE = [("상", 85), ("중", 70), ("하", 0)]          # 11-04 결정 '가'
PASS_GRADES = ["상", "중"]

# 웹용 CSV
OUT_DIR = os.path.join(os.path.dirname(HERE), "output")       # junhyeok/output
CSV_NAME = "web_products.csv"
BASE_COLUMNS = ["영양소", "제품명", "업체명", "품목제조신고번호", "대상", "1일 섭취량", "1일 함량", "기준치 대비(%)",
                "기능성", "섭취 시 주의사항"]
AMOUNT_COLUMNS = [("비타민 C", "mg"), ("비타민 D", "μg"), ("비타민 B1", "mg"), ("비타민 B2", "mg"), ("비타민 B6", "mg"),
                  ("니아신", "mg"), ("칼슘", "mg"), ("마그네슘", "mg"), ("철", "mg"), ("아연", "mg"), ("엽산", "μg"),
                  ("비타민 A", "μg RAE"), ("비타민 E", "mg α-TE"), ("요오드", "μg")]
COLUMNS = BASE_COLUMNS + ["순서", "구분", "제형", "상한 여유", "상한 50% 이상 성분"] + [f"하루 {k}({u})" for k, u in AMOUNT_COLUMNS]
# 상한 여유 (11-05): 모든 성분이 상한의 50% 미만이면 '있음' → 이런 제품 두 개를 함께 먹어도 상한을 넘지 않음
HEADROOM_UL = {**UL, "칼슘": 2000}
NIACIN_UL = {"니코틴산": 35, "니코틴산아미드": 850, "형태 모름": 35}


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
    """원재료 개수 = 괄호 밖에서 쉼표로 나뉜 원료 중 서로 다른 이름의 수 (11-05)
    예) '비타민D3혼합제제(비타민D3, 덱스트린), 탄산칼슘, 향료, 향료' → 3개
    - 괄호 안 세부 원료는 세지 않음 (라벨을 자세히 쓴 제품이 불리하지 않게)
    - 같은 이름(향료·혼합제제 등)이 여러 번 적혀 있으면 한 번만 셈"""
    t = nf(raw if isinstance(raw, str) else "")
    prev = None
    while prev != t:                                   # 겹친 괄호도 안쪽부터 지움
        prev = t
        t = re.sub(r"\([^()]*\)|\[[^\[\]]*\]", "", t)
    t = re.sub(r"[()\[\]]", "", t)                    # 짝이 안 맞는 괄호 정리
    return len({re.sub(r"\s", "", x) for x in t.split(",") if x.strip()})


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


def amount_text(r):
    if pd.isna(r["1일 함량"]) or r["1일 함량"] in ("", None):
        return ""
    return f"{float(r['1일 함량']):g} {r['1일 함량 단위']}".strip()


def product_amounts(no, amt, info):
    """제품의 하루 함량 → {열 이름: 값 글자}"""
    a = amt.loc[no]
    res = {}
    for k, u in AMOUNT_COLUMNS:
        if k in ("비타민 B1", "비타민 B2"):
            p = info[no]["b"].get(k)
            v = None if p is None else p * B_VITAMINS[k][1] / 100
        else:
            v = a[k] if k in a.index and pd.notna(a[k]) else None
        res[f"하루 {k}({u})"] = "" if v is None else f"{float(v):.4g}"
    return res


def headroom(no, amt):
    """(상한 여유, 상한 50% 이상 성분)"""
    a = amt.loc[no]
    over = []
    for k, lim in list(HEADROOM_UL.items()) + [("니아신", None)]:
        if k not in a.index or pd.isna(a[k]):
            continue
        if k == "니아신":
            form = a.get("니아신 형태", "형태 모름")
            lim = NIACIN_UL.get(form if isinstance(form, str) else "형태 모름", 35)
        r = a[k] / lim
        if r >= 0.5:
            over.append((k, r))
    over.sort(key=lambda t: -t[1])
    return ("있음" if not over else "적음"), ", ".join(f"{k} {r * 100:.0f}%" for k, r in over)


def check(df):
    """저장 전 점검. 문제 목록을 돌려줌 (비어 있으면 통과)"""
    problems = []
    if list(df.columns) != COLUMNS:
        problems.append(f"열 이름·순서가 다름: {list(df.columns)}")
    bad_t = set(df["대상"]) - set(TARGETS)
    if bad_t:
        problems.append(f"허용하지 않는 대상: {bad_t}")
    bad_n = set(df["영양소"]) - set(NUTRIENTS)
    if bad_n:
        problems.append(f"허용하지 않는 영양소: {bad_n}")
    if not df["품목제조신고번호"].str.fullmatch(r"\d{10,20}").all():
        problems.append("품목제조신고번호 형식이 이상한 줄이 있음")
    if df.duplicated(["영양소", "대상", "품목제조신고번호"]).any():
        problems.append("같은 칸에 같은 제품이 두 번 들어감")
    if df["제품명"].str.contains("임산부|수유|키즈|어린이", na=False).any():
        problems.append("어린이·임산부 제품으로 보이는 이름이 있음")
    return problems


def write_web_csv(keep, amt, info):
    """70점 이상 후보 전체 → junhyeok/output/web_products.csv"""
    base = pd.DataFrame({
        "영양소": keep["영양소"].astype(str), "제품명": keep["제품명"], "업체명": keep["업체명"],
        "품목제조신고번호": keep["품목제조신고번호"].astype(str), "대상": keep["대상"].astype(str),
        "1일 섭취량": keep["1일 섭취량"].fillna(""), "1일 함량": keep.apply(amount_text, axis=1),
        "기준치 대비(%)": keep["기준치 대비(%)"].map(lambda v: "" if pd.isna(v) else f"{int(v)}"),
        "기능성": keep["기능성"].fillna("").str.strip(), "섭취 시 주의사항": keep["섭취 시 주의사항"].fillna("").str.strip(),
        "순서": keep["순서"].astype(int).astype(str), "구분": keep["구분"].fillna(""), "제형": keep["제형"].fillna(""),
    })
    hr = [headroom(no, amt) for no in keep["품목제조신고번호"]]
    base["상한 여유"] = [h[0] for h in hr]
    base["상한 50% 이상 성분"] = [h[1] for h in hr]
    amounts = pd.DataFrame([product_amounts(no, amt, info) for no in keep["품목제조신고번호"]], index=keep.index)
    web = pd.concat([base, amounts], axis=1)
    problems = check(web)
    if problems:
        print("!! 점검에서 문제가 있어 CSV를 저장하지 않았어요:")
        for p in problems:
            print("   -", p)
        raise SystemExit(1)
    os.makedirs(OUT_DIR, exist_ok=True)
    csv_path = os.path.join(OUT_DIR, CSV_NAME)
    web.to_csv(csv_path, index=False, encoding="utf-8", quoting=csv.QUOTE_ALL, lineterminator="\n")
    cnt = pd.crosstab(web["영양소"], web["대상"]).reindex(index=NUTRIENTS, columns=TARGETS).fillna(0).astype(int)
    lines = [
        "# web_products.csv 정보", "",
        f"- 만든 날짜: {datetime.date.today().isoformat()}",
        "- 만든 코드: `junhyeok/분류_필터링/전체_실행.py` (1단계 → 9단계)",
        "- 기준: 「영양제_분류_필터링_기준(1104).pdf」 + 11-04 팀 결정, 상한섭취량은 2025 한국인 영양소 섭취기준",
        f"- 줄 수: {len(web):,} (제품 {web['품목제조신고번호'].nunique():,}개). 한 제품 = 한 줄 (11-05: 여러 영양소에 해당하는 제품은 목적에 맞는 대표 칸 하나에만)",
        "- 생활기능 영양제(유산균·오메가3·루테인·밀크씨슬)와 겹치는 제품 없음 (11-05)",
        "- **9단계를 통과한(70점 이상) 후보 전체**예요. '칸마다 3개'는 폐기했고(11-04), 웹에서 사람마다 필요한 제품을 골라요",
        "- `순서`: 같은 영양소·대상 안에서 먼저 볼 순서 (등급 → 점수 → 하루 섭취 개수 → 기준치 100% 근접 → 원재료 수). 점수 자체는 넣지 않음",
        "- `상한 여유` (11-05): 상한이 있는 모든 성분이 상한의 50% 미만이면 **있음**. '있음' 제품끼리는 두 개를 함께 먹어도 상한을 넘지 않아요",
        "  - 웹에서 제품을 두 개 이상 함께 보여 줄 때는 '있음' 제품을 우선 써 주세요. '적음' 제품은 `상한 50% 이상 성분`(예: 마그네슘 78%)을 보고 '다른 영양제와 겹치는지 확인' 안내를 붙여 주세요",
        f"  - 있음 {(web['상한 여유'] == '있음').sum():,}개 / 적음 {(web['상한 여유'] == '적음').sum():,}개",
        "- `하루 ○○` 열: 그 제품을 하루 섭취량대로 먹을 때 든 양. 여러 제품을 함께 볼 때 **상한을 합쳐서 확인**하는 데 써 주세요",
        "  - 상한(2025 KDRI 성인): 비타민 C 2,000mg · D 100μg · B6 50mg · 니아신 35mg(니코틴산) · 칼슘 2,000mg(남성 2,500) · 마그네슘 350mg(식품 외) · 철 45mg · 아연 35mg · 엽산 1,000μg · A 3,000μg RAE · E 540mg α-TE · 요오드 2,400μg",
        "  - 비타민 B1·B2 열이 비어 있으면 그 제품에 B1·B2가 없거나 양을 읽지 못한 것",
        "- 대상: 일반·남성·여성·시니어 (어린이·임산부·수유부 제외). 웹에서는 성별·나이(50세 이상은 시니어 포함)로 맞춤",
        "- 1일 함량·기준치 대비(%)는 기준치가 하나로 정해지는 영양소만 채움 (비타민 B군·식이섬유·종합비타민은 빈칸)",
        "- 품목제조신고번호는 문자열. **엑셀로 열어서 저장하면 숫자로 바뀌어 깨지니 저장하지 마세요.**",
        "- 화면에서는 점수·순위·'베스트' 같은 표현을 쓰지 않고, 제품을 하나씩 '이런 제품도 있어요' 톤으로 안내",
        "", "## 영양소 × 대상 개수", "",
        "| 영양소 | " + " | ".join(TARGETS) + " |", "|---|" + "---:|" * len(TARGETS),
    ] + [f"| {k} | " + " | ".join(f"{cnt.loc[k, t]:,}" for t in TARGETS) + " |" for k in NUTRIENTS]
    with open(os.path.join(OUT_DIR, "web_products_정보.md"), "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")
    with open(os.path.join(OUT_DIR, ".gitignore"), "w", encoding="utf-8") as fp:
        fp.write("# 팀 .gitignore는 *.csv를 막지만, 웹용 결과 파일 하나만은 올림 (11-04 대천님 요청)\n!web_products.csv\n")
    return web, csv_path


def main():
    print("[1/3] 8단계 결과 읽는 중...")
    web = pd.read_pickle(out("8단계_결과.pkl"))
    amt = pd.read_pickle(out("6단계_제품별함량.pkl"))
    prod = web.drop_duplicates("품목제조신고번호").set_index("품목제조신고번호")

    print("[2/3] 점수 매기는 중...")
    info = product_info(prod, amt)
    sc = score_table(web, info)
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
    webcsv, csv_path = write_web_csv(keep, amt, info)

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
        ("· 한 제품 = 한 줄 (6단계에서 대표 칸 하나로 정리). 생활기능 영양제와 겹치는 제품 없음", False),
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
        ("", False), ("웹용 파일", True),
        (f"· {csv_path}", False),
        (f"· 70점 이상 후보 전체 {len(webcsv):,}줄. '칸마다 3개 고르기'는 폐기 (11-04) → 웹에서 사람마다 고름", False),
        ("· 제품별 하루 함량 열을 붙여서, 웹에서 여러 제품을 함께 볼 때 상한 합산을 확인할 수 있음", False),
        (f"· 상한 여유 (11-05): 모든 성분이 상한의 50% 미만인 제품 {(webcsv['상한 여유'] == '있음').sum():,}개 / 적음 {(webcsv['상한 여유'] == '적음').sum():,}개", False),
        ("· 저장 전 자동 점검 통과: 열 이름·순서 / 대상 / 영양소 / 신고번호 형식 / 중복 / 어린이·임산부 이름", False),
        ("", False),
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
    done["70점 이상 후보 전체"] = f"적용 완료 ({len(webcsv):,}줄)"
    done["후보를 몇 개까지"] = "폐기 (11-04): 칸마다 3개 대신 70점 이상 후보 전체를 웹으로 넘기고 사람마다 고름"
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
    add_sheet(wb, "web_products 미리보기 (앞 300줄)", webcsv.head(300), [22, 34, 22, 18, 8, 26, 12, 10, 50, 50, 6, 18, 8, 8, 24] + [10] * len(AMOUNT_COLUMNS))
    wb.save(out("9단계_점수.xlsx"))
    print(f"9단계 완료: {len(sc):,}줄 → 상 {gc.get('상', 0):,} · 중 {gc.get('중', 0):,} · 탈락 {gc.get('하', 0):,} → 제품 {n_keep:,}개 ({len(keep):,}줄)")
    print(f"웹용 파일: {csv_path} ({len(webcsv):,}줄)")
    print(after.to_string())


if __name__ == "__main__":
    main()
