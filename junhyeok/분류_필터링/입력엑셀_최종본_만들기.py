# -*- coding: utf-8 -*-
"""
입력 엑셀 최종본 만들기 (분류·필터링 전 준비)
기준: 「영양제_분류_필터링_기준(1104).pdf」 + 11-03~11-04 토의 결정

하는 일
  1) C003(메인.csv)과 식품영양성분DB를 나눈다
     - C003      → 성분별_영양제_제품목록(최종).xlsx  (메인, 분류·필터링 대상)
     - 영양성분DB → 성분별_영양제_제품목록_보조(식품영양성분DB).xlsx  (보조, 따로 분류·필터링)
  2) C003 범위: 2022년 이후 신고
     - 수출 전용(제품명 '수출')·해외 판매 의심(괄호 안 국가명)은 '제외 목록' 시트에만 기록 (1차 분류 증빙용)
  3) 성분 인식을 최신 규칙으로 다시 한다
     - 기존 목록의 성분 인식([성분] 표시, 성분명 문장, 식약처 문구)
     - + 나이아신·판토텐산·비오틴 등 → 비타민 B군
     - + 기능성 문구 + 원재료로 인정 (유산균·오메가3·루테인·밀크씨슬·식이섬유)
  4) 열 보강: 기능성·주의사항 원본 전문, 원재료·섭취방법·기준규격, 새 키워드 대상,
     '질환 대상 단어'·'임산부·수유부' 표시 (빼는 건 1단계에서)

입력  성분별_영양제_제품목록(수출 제외).xlsx (기존 목록), 메인.csv  ← 이 폴더 또는 바탕화면\\영양제품 자료
출력  (이 폴더) 성분별_영양제_제품목록(최종).xlsx, 성분별_영양제_제품목록_보조(식품영양성분DB).xlsx
"""
import os, re
import pandas as pd
from 공통 import (PRODUCT_XLSX, FINAL_XLSX, DATA, find, load_main, nf, target_of, OVERSEAS, DISEASE,
                new_book, add_sheet)

INFO_SHEETS = {"안내", "점검 결과", "요약", "과거 신고(2021 이전)", "제외 목록(수출 전용)"}
C003 = "C003 품목제조신고"
ORDER = ["비타민 B군", "비타민 C", "비타민 A", "비타민 D", "비타민 E", "비타민 K", "칼슘", "마그네슘",
         "철", "칼륨", "아연", "엽산", "오메가3", "유산균", "식이섬유", "루테인", "밀크씨슬"]
NOT_RECOMMEND = {"비타민 A", "비타민 E", "비타민 K", "칼륨"}

PHRASE_RULES = {
    "밀크씨슬": (r"밀크\s*[씨시]슬|실리마린", r"간 건강"),
    "유산균": (r"프로바이오틱스|유산균|락토바실|비피도|(?i:lactobacillus|bifidobacterium|streptococcus|lactococcus)",
            r"유산균 증식|배변활동|유익균"),
    "오메가3": (r"EPA|DHA|정제어유|어유|오메가|(?i:omega|fish oil)|조류유", r"중성지질|혈행|건조한 눈|기억력"),
    "루테인": (r"루테인|마리골드", r"황반"),
    "식이섬유": (r"식이섬유|차전자피|난소화성말토덱스트린|이눌린|구아검|폴리덱스트로스",
             r"식이섬유|차전자피|폴리덱스트로스|이눌린|구아검|난소화성"),
}
B_EXTRA = r"나이아신|판토텐산|비오틴|비타민\s*B\s*(?:1|2|6|12)(?![0-9])|티아민|리보플라빈"


def phrase_ingredients(raw, func):
    raw, func = nf(raw), nf(func)
    found = {}
    if re.search(B_EXTRA, func):
        found["비타민 B군"] = "기능성 문장(나이아신·판토텐산·비오틴 등)"
    for k, (rp, fp) in PHRASE_RULES.items():
        if re.search(rp, raw) and re.search(fp, func):
            found[k] = "기능성 문구 + 원재료"
    return found


def main():
    print("[1/4] 기존 제품목록과 메인.csv 읽는 중... (30초 정도)")
    # ── 기존 목록 읽기
    book = pd.ExcelFile(find(PRODUCT_XLSX))
    rows = []
    for s in [x for x in book.sheet_names if x not in INFO_SHEETS]:
        d = pd.read_excel(book, sheet_name=s, dtype=str)
        d["성분"] = s
        rows.append(d)
    old = pd.concat(rows, ignore_index=True)
    past = pd.read_excel(book, sheet_name="과거 신고(2021 이전)", dtype=str)
    db_rows = old[old["출처"] != C003]
    old = old[old["출처"] == C003]

    # ── C003 범위 (2022년 이후)
    m = load_main()
    m = m[m.PRMS_DT.str[:4] >= "2022"].copy()
    is_export = m.PRDLST_NM.str.contains("수출", na=False)
    is_overseas = m.PRDLST_NM.str.contains(OVERSEAS, regex=True, na=False) & ~is_export
    excl = m[is_export | is_overseas].copy()
    excl["제외 이유"] = ["수출 전용 (제품명에 '수출')" if e else "해외 판매 의심 (괄호 안 국가명)"
                     for e in is_export[is_export | is_overseas]]
    scope = m[~(is_export | is_overseas)]

    print("[2/4] 성분 인식 다시 하는 중...")
    # ── 성분 인식: 기존 목록 + 최신 규칙
    have = {}   # (신고번호, 성분) → 인식 근거
    for no, k, why in zip(old["품목제조신고번호"], old["성분"], old["분류 근거"]):
        have[(no, k)] = why
    n_old_pairs = len(have)
    for no, r in scope.iterrows():
        for k, why in phrase_ingredients(r.RAWMTRL_NM, r.PRIMARY_FNCLTY).items():
            have.setdefault((no, k), why + " (최종본 추가)")
    pairs = pd.DataFrame([(no, k, why) for (no, k), why in have.items()], columns=["품목제조신고번호", "성분", "성분 인식 근거"])
    pairs = pairs[pairs["품목제조신고번호"].isin(scope.index)]          # 수출·해외 제외
    added_pairs = pairs["성분 인식 근거"].str.endswith("(최종본 추가)")

    # ── 제품당 한 줄 (마스터)
    ing = pairs.groupby("품목제조신고번호")["성분"].apply(lambda s: [k for k in ORDER if k in set(s)])
    prod = scope.loc[ing.index]
    master = pd.DataFrame({
        "품목제조신고번호": ing.index,
        "제품명": prod.PRDLST_NM.values, "업체명": prod.BSSH_NM.values,
        "신고일자": pd.to_datetime(prod.PRMS_DT, format="%Y%m%d").dt.strftime("%Y-%m-%d").values,
        "제형": prod.PRDT_SHAP_CD_NM.values,
    })
    master["대상"] = master["제품명"].map(target_of)
    master["임산부·수유부"] = (master["대상"] == "임산부·수유부").map({True: "예", False: ""})
    master["질환 대상 단어"] = master["제품명"].str.extract(f"({DISEASE})", expand=False).fillna("")
    master["가이드 성분 수"] = ing.map(len).values
    master["함께 든 가이드 성분"] = ing.map(", ".join).values
    master["기능성"] = prod.PRIMARY_FNCLTY.values
    master["원재료"] = prod.RAWMTRL_NM.values
    master["섭취방법"] = prod.NTK_MTHD.values
    master["기준규격"] = prod.STDR_STND.values
    master["섭취 시 주의사항"] = prod.IFTKN_ATNT_MATR_CN.values
    master = master.sort_values("품목제조신고번호").reset_index(drop=True)
    info = master.set_index("품목제조신고번호")

    # ── 성분별 시트
    amt = old.drop_duplicates(["품목제조신고번호", "성분"]).set_index(["품목제조신고번호", "성분"])[["함량", "함량 단위", "표시량(원문)"]]
    sheet_cols = ["품목제조신고번호", "제품명", "업체명", "신고일자", "제형", "대상", "임산부·수유부", "질환 대상 단어",
                  "성분 인식 근거", "가이드 성분 수", "함께 든 가이드 성분", "함량", "함량 단위", "표시량(원문)", "기능성", "섭취 시 주의사항"]
    sheets = {}
    for k in ORDER:
        d = pairs[pairs["성분"] == k].copy()
        d = d.join(info, on="품목제조신고번호")
        a = amt.reindex(list(zip(d["품목제조신고번호"], d["성분"])))
        d["함량"], d["함량 단위"], d["표시량(원문)"] = a["함량"].values, a["함량 단위"].values, a["표시량(원문)"].values
        sheets[k] = d[sheet_cols].sort_values("품목제조신고번호").reset_index(drop=True)

    # ── 요약
    summ = []
    for k in ORDER:
        d = sheets[k]
        summ.append({"성분": k, "추천 대상": "아님 (보조 성분 확인용)" if k in NOT_RECOMMEND else "예",
                     "제품 수": len(d),
                     "최종본에서 추가": int(d["성분 인식 근거"].str.endswith("(최종본 추가)").sum()),
                     "가이드 성분 1개 제품": int((d["가이드 성분 수"] == 1).sum()),
                     "함량·표시량 있음": int((d["함량"].notna() | d["표시량(원문)"].notna()).sum()),
                     "대상 '일반'": int((d["대상"] == "일반").sum())})
    summ = pd.DataFrame(summ)
    tg = " / ".join(f"{a} {b:,}" for a, b in master["대상"].value_counts().items())
    dis = (master["질환 대상 단어"] != "").sum()
    preg = (master["임산부·수유부"] == "예").sum()
    lines = [
        ("성분별 영양제 제품 목록 (최종본)", True),
        ("생활습관 기반 개인 맞춤 영양관리 추천 시스템 · 개인별 영양제 제안 파트 · 2026-11-04", False),
        ("기준: 「영양제_분류_필터링_기준(1104).pdf」. 이 파일이 분류·필터링 1단계의 입력이에요.", False), ("", False),
        ("무엇이 들어 있나", True),
        (f"· 식약처 C003 건강기능식품 품목제조 신고 중 2022년 이후 신고, 가이드 성분이 1개 이상인 제품 {len(master):,}개", False),
        ("· 성분 17개별 시트 (한 제품이 여러 성분이면 여러 시트에 나옴) + '제품 목록' 시트 (제품당 한 줄, 원재료·섭취방법·기준규격 포함)", False),
        ("· 식품영양성분DB(보조 출처, 대부분 수입)는 '성분별_영양제_제품목록_보조(식품영양성분DB).xlsx'로 분리해 따로 분류·필터링", False), ("", False),
        ("이전 목록에서 바뀐 점", True),
        (f"· 성분 인식 보강: 나이아신·판토텐산·비오틴 → 비타민 B군, 기능성 문구 + 원재료로 유산균·오메가3·루테인·밀크씨슬·식이섬유 인정 → 성분 {int(added_pairs.sum()):,}건 추가", False),
        ("· 기능성·섭취 시 주의사항을 원본 전문으로 바꿈 (이전 목록은 일부 문구가 잘려 있었음)", False),
        ("· 대상 키워드 보강 (어린이에 '우리 아이·앙팡·Kid's' 추가)", False),
        (f"· 수출 전용·해외 판매 의심 {len(excl):,}개는 '제외 목록' 시트에만 기록 (분류·필터링하지 않음, 1차 분류 증빙용)", False),
        (f"· 표시 열 추가: '임산부·수유부' {preg:,}개, '질환 대상 단어' {dis:,}개 → 1단계에서 제외", False), ("", False),
        ("대상", True), (f"· {tg}", False), ("", False),
        ("열 설명", True),
        ("· 성분 인식 근거: 기능성 [성분] 표시 / 기능성 문장(성분명) / 기능성 문장(식약처 문구) / … (최종본 추가)", False),
        ("· 질환 대상 단어: 제품명에 질환(혈당·혈압·전립선·갑상선 등)을 내세운 경우 그 단어", False),
        ("· 함량·함량 단위·표시량(원문): 기준규격 문장의 표시량. 최종본에서 추가된 성분은 비어 있음 (기준규격 원문은 '제품 목록' 시트에 있음)", False), ("", False),
        ("사용 시 주의", True),
        ("· 함량은 1일 섭취량 기준이 아님 (표시량이 '함량/기준 중량' 형식). 1일 환산은 후보를 압축한 뒤 진행", False),
        ("· 함량은 내부 필터용이며, 결과 화면에서 '하루 몇 mg 드세요' 같은 복용 지시로 쓰지 않음", False),
        ("· 비타민 A·E·K·칼륨 시트는 보조 성분 확인용이며 추천 대상이 아님. 인·단백질·나트륨은 제품 없이 식습관 안내", False),
        ("· 가격·판매처·브랜드 정보는 쓰지 않음 (홍보성 방지)", False),
        ("· 일반·전문 의약품 없음 (C003은 건강기능식품 품목제조 신고 자료)", False),
    ]
    wb = new_book(lines)
    wb.active.title = "안내"
    add_sheet(wb, "요약", summ, [12, 22, 10, 14, 18, 10, 10])
    w = [18, 32, 20, 11, 10, 8, 8, 10, 26, 8, 30, 8, 8, 24, 60, 40]
    add_sheet(wb, f"제품 목록 ({len(master):,})", master, [18, 32, 20, 11, 10, 8, 8, 10, 8, 30, 60, 40, 30, 40, 40])
    for k in ORDER:
        add_sheet(wb, k, sheets[k], w)
    ex = excl.reset_index()[["제외 이유", "PRDLST_REPORT_NO", "PRDLST_NM", "BSSH_NM", "PRMS_DT"]]
    ex.columns = ["제외 이유", "품목제조신고번호", "제품명", "업체명", "신고일자"]
    add_sheet(wb, f"제외 목록(수출·해외 {len(ex):,})", ex.sort_values(["제외 이유", "품목제조신고번호"]), [30, 18, 40, 25, 11])
    add_sheet(wb, f"과거 신고(2021 이전)", past, [40, 25, 18, 11, 30])
    path_main = os.path.join(DATA, FINAL_XLSX)
    print("[3/4] 최종본 엑셀 저장 중... (파일이 커서 1~3분 걸려요. 아무 키도 누르지 말고 기다려 주세요)")
    wb.save(path_main)

    # ── 보조 파일 (식품영양성분DB)
    bl = [("성분별 영양제 제품 목록 — 보조 (식품영양성분DB)", True),
          ("식약처 식품영양성분 데이터베이스 건강기능식품 편 (기준일 2026-06-23). 대부분 수입 제품이라 메인(C003)과 따로 분류·필터링해요.", False),
          (f"· 제품 {db_rows['품목제조신고번호'].nunique():,}개, 성분 시트 행 {len(db_rows):,}개. 메인 목록과 겹치는 제품 없음", False),
          ("· 함량은 영양성분DB의 1회 분량 기준 값", False)]
    wb2 = new_book(bl)
    wb2.active.title = "안내"
    s2 = db_rows.groupby("성분").size().reindex(ORDER).fillna(0).astype(int).reset_index()
    s2.columns = ["성분", "제품 수"]
    add_sheet(wb2, "요약", s2, [14, 10])
    cols2 = [c for c in db_rows.columns if c not in ("성분", "출처")]
    for k in ORDER:
        d = db_rows[db_rows["성분"] == k][cols2]
        if len(d):
            add_sheet(wb2, k, d, [32, 20, 18, 11, 10, 18, 8, 30, 10, 8, 24, 10, 8, 50, 40])
    path_db = os.path.join(DATA, "성분별_영양제_제품목록_보조(식품영양성분DB).xlsx")
    print("[4/4] 보조 엑셀 저장 중...")
    wb2.save(path_db)

    print(f"최종본: 제품 {len(master):,}개 (성분 추가 {int(added_pairs.sum()):,}건), 제외 목록 {len(ex):,}개, 임산부 {preg}, 질환 단어 {dis}")
    print(f"보조: 제품 {db_rows['품목제조신고번호'].nunique():,}개")
    print(summ.to_string(index=False))


if __name__ == "__main__":
    main()
