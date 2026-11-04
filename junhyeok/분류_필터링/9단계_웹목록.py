# -*- coding: utf-8 -*-
"""
9단계: 웹 표시용 제품 목록 만들기 (web_products.csv)
기준: 「영양제_분류_필터링_기준(1104).pdf」 10절 + 11-04 대천님(팀장) 요청 + 11-04 결정

하는 일
  ① 등급 '하'(60점 미만) 제외 (11-04 결정: 상 80점 이상 / 중 60~79 / 하 60 미만)
  ② 영양소 × 대상(일반·남성·여성·시니어)마다 최대 3개 고르기
     - 상 등급에서 먼저, 모자라면 중 등급에서 (같은 등급 안에서는 8단계 순서)
     - 같은 업체(제조사) 제품이 몰리지 않게: 업체가 겹치지 않게 먼저 고르고,
       그래도 3개가 안 되면 남은 제품으로 채움
     - 3개가 안 되면 있는 것만 넣음 (11-04 결정)
  ③ CSV 저장: junhyeok/output/web_products.csv (UTF-8)
     - 열: 영양소, 제품명, 업체명, 품목제조신고번호, 대상, 1일 섭취량, 1일 함량, 기준치 대비(%), 기능성, 섭취 시 주의사항
     - 점수는 넣지 않음 (순서에만 반영). 신고번호는 문자열로 저장 (모든 칸을 따옴표로 감쌈)
     - 1일 함량·기준치 대비(%)는 기준치가 하나로 정해지는 영양소만 채움 (B군·식이섬유·종합비타민은 빈칸)
  ④ 저장 전 자동 점검: 열 이름·순서, 대상(어린이·임산부 없음), 영양소 11종, 칸마다 3개 이하, 신고번호 형식, 중복
     → 하나라도 틀리면 저장하지 않고 멈춤
  ⑤ 같은 폴더에 web_products_정보.md (만든 날짜, 기준, 개수) 저장

입력  8단계_결과.pkl
출력  ../output/web_products.csv, ../output/web_products_정보.md, 9단계_웹목록.xlsx
"""
import os, csv, datetime
import pandas as pd
from 공통 import HERE, out, new_book, add_sheet, add_criteria_sheet

OUT_DIR = os.path.join(os.path.dirname(HERE), "output")       # junhyeok/output
CSV_NAME = "web_products.csv"
TARGETS = ["일반", "남성", "여성", "시니어"]
NUTRIENTS = ["비타민 B군", "비타민 C", "비타민 D", "칼슘", "마그네슘", "아연", "철", "엽산", "식이섬유",
             "종합비타민 (균형형)", "종합비타민 (피로회복형)"]
COLUMNS = ["영양소", "제품명", "업체명", "품목제조신고번호", "대상", "1일 섭취량", "1일 함량", "기준치 대비(%)",
           "기능성", "섭취 시 주의사항"]
PER_CELL = 3
GRADE_RANK = {"상": 0, "중": 1, "하": 2}


def pick(group):
    """한 칸(영양소 × 대상)에서 최대 3개 고르기. 업체가 겹치지 않게 먼저, 모자라면 채움"""
    group = group.sort_values(["_등급순", "순서"])
    chosen, firms = [], set()
    for idx, r in group.iterrows():                 # 1차: 업체 겹치지 않게
        if r["업체명"] not in firms:
            chosen.append(idx)
            firms.add(r["업체명"])
        if len(chosen) == PER_CELL:
            break
    if len(chosen) < PER_CELL:                      # 2차: 모자라면 남은 제품으로
        for idx in group.index:
            if idx not in chosen:
                chosen.append(idx)
            if len(chosen) == PER_CELL:
                break
    return group.loc[chosen]


def amount_text(r):
    if pd.isna(r["1일 함량"]) or r["1일 함량"] in ("", None):
        return ""
    return f"{float(r['1일 함량']):g} {r['1일 함량 단위']}".strip()


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
    over = df.groupby(["영양소", "대상"]).size()
    if (over > PER_CELL).any():
        problems.append(f"칸마다 {PER_CELL}개 초과: {over[over > PER_CELL].to_dict()}")
    if not df["품목제조신고번호"].str.fullmatch(r"\d{10,20}").all():
        problems.append("품목제조신고번호 형식이 이상한 줄이 있음")
    if df.duplicated(["영양소", "대상", "품목제조신고번호"]).any():
        problems.append("같은 칸에 같은 제품이 두 번 들어감")
    if df["제품명"].str.contains("임산부|수유|키즈|어린이", na=False).any():
        problems.append("어린이·임산부 제품으로 보이는 이름이 있음")
    return problems


def main():
    print("[1/3] 8단계 결과 읽는 중...")
    sc = pd.read_pickle(out("8단계_결과.pkl"))
    sc["영양소"] = sc["영양소"].astype(str)
    sc["대상"] = sc["대상"].astype(str)
    n_low = int((sc["등급"] == "하").sum())
    cand = sc[sc["등급"] != "하"].copy()
    cand["_등급순"] = cand["등급"].map(GRADE_RANK)

    print("[2/3] 영양소 × 대상별 최대 3개 고르는 중...")
    picked = []
    for (k, t), g in cand.groupby(["영양소", "대상"]):
        picked.append(pick(g))
    sel = pd.concat(picked)
    sel["영양소"] = pd.Categorical(sel["영양소"], NUTRIENTS, ordered=True)
    sel["대상"] = pd.Categorical(sel["대상"], TARGETS, ordered=True)
    sel = sel.sort_values(["영양소", "대상", "_등급순", "순서"]).reset_index(drop=True)
    firm_dup = sel.groupby(["영양소", "대상"], observed=True)["업체명"].apply(lambda s: s.duplicated().sum()).sum()

    web = pd.DataFrame({
        "영양소": sel["영양소"].astype(str), "제품명": sel["제품명"], "업체명": sel["업체명"],
        "품목제조신고번호": sel["품목제조신고번호"].astype(str), "대상": sel["대상"].astype(str),
        "1일 섭취량": sel["1일 섭취량"].fillna(""), "1일 함량": sel.apply(amount_text, axis=1),
        "기준치 대비(%)": sel["기준치 대비(%)"].map(lambda v: "" if pd.isna(v) else f"{int(v)}"),
        "기능성": sel["기능성"].fillna("").str.strip(), "섭취 시 주의사항": sel["섭취 시 주의사항"].fillna("").str.strip(),
    })
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
    today = datetime.date.today().isoformat()
    info = [
        "# web_products.csv 정보", "",
        f"- 만든 날짜: {today}",
        "- 만든 코드: `junhyeok/분류_필터링/전체_실행.py` (1단계 → 9단계)",
        "- 기준: 「영양제_분류_필터링_기준(1104).pdf」, 상한섭취량은 2025 한국인 영양소 섭취기준",
        f"- 줄 수: {len(web)} (제품 {web['품목제조신고번호'].nunique()}개, 한 제품이 여러 영양소·대상에 나올 수 있음)",
        "- 한 줄 = 제품 하나. 영양소 × 대상마다 최대 3개, 위에 있을수록 먼저 보여 줄 제품 (점수는 넣지 않음)",
        "- 대상: 일반·남성·여성·시니어 (어린이·임산부·수유부 제외). 웹에서는 성별·나이(50세 이상은 시니어 포함)로 맞춤",
        "- 1일 함량·기준치 대비(%)는 기준치가 하나로 정해지는 영양소만 채움 (비타민 B군·식이섬유·종합비타민은 빈칸)",
        "- 품목제조신고번호는 문자열. **엑셀로 열어서 저장하면 숫자로 바뀌어 깨지니 저장하지 마세요.**",
        "- 화면에서는 점수·순위·'베스트' 같은 표현을 쓰지 않고, 제품 정보를 펼치기 전에 임신·질환·복용약을 확인해 해당되면 상담 안내",
        "", "## 영양소 × 대상 개수", "",
        "| 영양소 | " + " | ".join(TARGETS) + " |", "|---|" + "---:|" * len(TARGETS),
    ] + [f"| {k} | " + " | ".join(str(cnt.loc[k, t]) for t in TARGETS) + " |" for k in NUTRIENTS]
    with open(os.path.join(OUT_DIR, "web_products_정보.md"), "w", encoding="utf-8") as fp:
        fp.write("\n".join(info) + "\n")
    # 이 폴더의 CSV만 깃허브에 올라가도록 예외 규칙 (팀 .gitignore의 *.csv 예외)
    with open(os.path.join(OUT_DIR, ".gitignore"), "w", encoding="utf-8") as fp:
        fp.write("# 팀 .gitignore는 *.csv를 막지만, 웹용 결과 파일 하나만은 올림 (11-04 대천님 요청)\n!web_products.csv\n")

    print("[3/3] 결과 엑셀 저장 중...")
    lines = [
        ("9단계: 웹 표시용 제품 목록", True), ("", False),
        ("결과", True),
        (f"· 8단계 {len(sc):,}줄 → 등급 '하'(60점 미만) {n_low:,}줄 제외 → 영양소 × 대상별 최대 3개 → {len(web)}줄 (제품 {web['품목제조신고번호'].nunique()}개)", False),
        (f"· 저장: {csv_path}", False),
        (f"· 같은 칸에 같은 업체가 2번 이상 들어간 경우: {int(firm_dup)}건 (업체가 다른 제품이 모자라서 채운 경우)", False),
        ("· 칸별 개수는 '영양소×대상' 시트. 3개가 안 되는 칸은 있는 것만 넣음", False),
        ("", False), ("자동 점검 (통과)", True),
        ("· 열 이름·순서 / 대상 4종 / 영양소 11종 / 칸마다 3개 이하 / 신고번호 형식 / 중복 / 어린이·임산부 이름", False),
        ("", False), ("주의", True),
        ("· web_products.csv를 엑셀로 열고 저장하면 신고번호가 숫자로 바뀌어 깨짐. 보기만 하고 고칠 게 있으면 코드를 다시 돌릴 것", False),
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
        "함량 기준 충족 50", "섭취 편의 25", "주의 원료 15", "성분 구성 관련성 10"]}
    done["비타민 D는 일반 정보로"] = "비타민 D 포함 / 오메가3·유산균·루테인·밀크씨슬은 웹에서 아직 안 씀 (11-04)"
    done["기능성 원료는 상한이 아니라"] = "해당 없음 (웹에서 오메가3·루테인 등을 쓰지 않음)"
    done["후보를 몇 개까지"] = "적용 완료 (영양소 × 대상별 최대 3개, 등급 '하' 제외)"
    done["화면에 보여 줄 제품 선택"] = f"적용 완료 ({len(web)}줄, 업체 겹치지 않게 우선)"
    add_criteria_sheet(wb, done)
    add_sheet(wb, "영양소×대상", cnt.reset_index().rename(columns={"index": "영양소"}), [22, 8, 8, 8, 8], freeze="A2")
    show = sel[["영양소", "대상", "등급", "점수", "구분", "제품명", "업체명", "품목제조신고번호", "1일 섭취량", "함량 근거"]].copy()
    show["영양소"] = show["영양소"].astype(str)
    show["대상"] = show["대상"].astype(str)
    add_sheet(wb, f"고른 제품 ({len(web)}줄)", show, [22, 8, 6, 6, 18, 34, 22, 18, 26, 30])
    add_sheet(wb, "web_products 미리보기", web, [22, 34, 22, 18, 8, 26, 12, 10, 60, 60])
    wb.save(out("9단계_웹목록.xlsx"))
    print(f"9단계 완료: {len(web)}줄 (제품 {web['품목제조신고번호'].nunique()}개) → {csv_path}")
    print(cnt.to_string())


if __name__ == "__main__":
    main()
