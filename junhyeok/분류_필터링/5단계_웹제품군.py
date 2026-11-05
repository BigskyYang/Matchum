# -*- coding: utf-8 -*-
"""
5단계: 웹용 제품군 만들기
기준: 「영양제_분류_필터링_기준(1104).pdf」 5-1절 + 11-04 대천님(팀장) 요청

웹 개인 결과의 '건강기능식품 정보'에 쓸 영양소 11종 × 대상(일반·남성·여성·시니어)별로 제품 후보를 묶는다.
  · 영양소 9종: 비타민 B군·C·D, 칼슘, 마그네슘, 아연, 철, 엽산, 식이섬유
      - 단일   : 그 영양소가 주성분인 단일 제품
      - 목적형 : 그 영양소와 연결된 목적(예: 철 → 혈행·혈액)의 목적형 중, 그 영양소가 '실제로 든' 제품만
                 (목적 이름만 보고 다른 성분 제품을 연결하지 않음. 예: 혈행 그룹이라고 오메가3 제품을 철에 넣지 않음)
  · 종합비타민 2종: 균형형, 피로회복형 (단일·목적형의 '대안'으로 보여 줌)
  · 웹에서 쓰지 않는 것: 오메가3·유산균·루테인·밀크씨슬 (모델이 부족 위험으로 정하지 않는 성분),
                       비타민 A·E·K·칼륨 단일 (추천 대상 아님)
  · 한 제품이 여러 영양소에 해당하면 영양소마다 한 줄씩 들어감 (웹이 영양소별로 읽기 때문)
  · (11-05) 비타민 B군 칸(단일·목적형)은 B1과 B2가 기준규격에 '둘 다' 든 제품만
      - 재준님 모델은 B1·B2만 예측함. 화면에서는 'B군'으로 묶되, B1이 부족하든 B2가 부족하든 맞는 제품만 남김
  · (11-05) 생활기능 영양제 성분(유산균·오메가3·루테인·밀크씨슬)이 섞인 단일·목적형은 영양제 칸에서 모두 뺌 (종합비타민은 그대로)
      - 영양제와 생활기능 영양제에 같은 제품이 겹치지 않게 하려고 (11-05 결정: 공통 제품 없음)
      - 유산균 + 식이섬유 제품도 식이섬유 칸에 두지 않고 생활기능(유산균) 쪽에만
  · (11-05) 보관 파일: 주 목적이 루테인·유산균·오메가3·밀크씨슬인 제품만 5단계_보관.pkl 로 저장
      - 단일: 주성분이 4가지 중 하나 / 목적형: 눈(루테인)·장(유산균)·혈행(오메가3)·간(밀크씨슬) 목적에 그 성분이 실제로 든 제품
      - 보조 성분이 섞인 건 괜찮음. 나중에 '생활유지 기능성' 제품으로 따로 다룸 (6~9단계는 거치지 않았음)

입력  4단계_결과.pkl
출력  5단계_웹제품군.xlsx, 5단계_결과.pkl (다음 단계 입력), 5단계_보관.pkl (생활유지 기능성용 보관)
"""
import re
import pandas as pd
from 공통 import out, nf, new_book, add_sheet, add_criteria_sheet

TARGETS = ["일반", "남성", "여성", "시니어"]
WEB_NUTRIENTS = ["비타민 B군", "비타민 C", "비타민 D", "칼슘", "마그네슘", "아연", "철", "엽산", "식이섬유"]
WEB_MULTI = ["균형형", "피로회복형"]
# 영양소 → 연결된 목적 (4단계와 같은 표)
PURPOSE_OF = {"비타민 B군": ["피로·활력"], "비타민 C": ["면역"], "비타민 D": ["뼈", "면역"],
              "칼슘": ["뼈"], "마그네슘": ["뼈", "피로·활력"], "아연": ["면역"],
              "철": ["혈행·혈액"], "엽산": ["혈행·혈액"], "식이섬유": ["장"]}
B1 = r"비타민\s*B1(?!\d)|티아민"
B2 = r"비타민\s*B2|리보플라빈"
UNUSED_ALL = ["밀크씨슬", "오메가3", "루테인", "유산균"]   # 단일·목적형에 들어 있으면 영양제 칸에서 모두 뺌 (생활기능 쪽)
HOLD_MAIN = ["루테인", "유산균", "오메가3", "밀크씨슬"]   # 보관: 주 목적이 이 4가지인 제품
HOLD_GOAL = {"눈": "루테인", "장": "유산균", "혈행·혈액": "오메가3", "간": "밀크씨슬"}


def main():
    print("[1/3] 4단계 결과 읽는 중...")
    p = pd.read_pickle(out("4단계_결과.pkl"))
    p["성분 목록"] = p["함께 든 가이드 성분"].str.split(", ")

    print("[2/3] 영양소별 제품군 묶는 중...")
    rows = []
    for k in WEB_NUTRIENTS:
        single = p[(p["풀"] == "단일") & (p["주성분·목적"] == k)].copy()
        single["구분"] = "단일"
        goals = PURPOSE_OF[k]
        is_goal = p["주성분·목적"].map(lambda g: any(x in str(g).split("+") for x in goals))
        has_k = p["성분 목록"].map(lambda s: k in s)
        purpose = p[(p["풀"] == "목적형") & is_goal & has_k].copy()
        purpose["구분"] = "목적형 (" + purpose["주성분·목적"] + ")"
        for d in (single, purpose):
            d["영양소"] = k
            rows.append(d)
    for kind in WEB_MULTI:
        multi = p[(p["풀"] == "종합비타민") & (p["주성분·목적"] == kind)].copy()
        multi["영양소"] = f"종합비타민 ({kind})"
        multi["구분"] = "종합비타민"
        rows.append(multi)
    web = pd.concat(rows, ignore_index=True)
    web["_빠짐"] = ""
    multi_row = web["구분"].eq("종합비타민")
    spec = web["기준규격"].fillna("").map(nf)
    no_b12 = web["영양소"].eq("비타민 B군") & ~multi_row & ~(spec.str.contains(B1) & spec.str.contains(B2))
    web.loc[no_b12, "_빠짐"] = "B1·B2가 둘 다 들어 있지 않은 B군 제품"
    ing = web["성분 목록"]
    has_unused = ing.map(lambda s: any(x in s for x in UNUSED_ALL)) & ~multi_row & web["_빠짐"].eq("")
    web.loc[has_unused, "_빠짐"] = "웹 미사용 성분(" + ing[has_unused].map(lambda s: "·".join(x for x in UNUSED_ALL if x in s)) + ") 혼합"
    cut = web[web["_빠짐"].ne("")]
    web = web[web["_빠짐"].eq("")].drop(columns="_빠짐").reset_index(drop=True)
    order = WEB_NUTRIENTS + [f"종합비타민 ({x})" for x in WEB_MULTI]
    web["영양소"] = pd.Categorical(web["영양소"], order, ordered=True)
    web["대상"] = pd.Categorical(web["대상"], TARGETS, ordered=True)
    web = web.sort_values(["영양소", "대상", "구분", "품목제조신고번호"]).drop(columns="성분 목록").reset_index(drop=True)
    web.to_pickle(out("5단계_결과.pkl"))

    # 보관 (11-05): 주 목적이 루테인·유산균·오메가3·밀크씨슬인 제품만 → 나중에 '생활유지 기능성'으로 다룸
    #   단일: 주성분이 4가지 중 하나 / 목적형: 목적(눈·장·혈행·간)에 맞는 성분이 실제로 든 제품 (보조 성분이 섞여도 괜찮음)
    def keep_reason(r):
        if r["풀"] == "단일":
            return f"{r['주성분·목적']} (단일)" if r["주성분·목적"] in HOLD_MAIN else ""
        if r["풀"] == "목적형":
            goals = str(r["주성분·목적"]).split("+")
            hit = [ing for goal, ing in HOLD_GOAL.items() if goal in goals and ing in r["성분 목록"]]
            return " · ".join(f"{ing} (목적형: {r['주성분·목적']})" for ing in hit)
        return ""
    reason = p.apply(keep_reason, axis=1)
    hold = p[reason.ne("")].drop(columns="성분 목록").copy()
    hold["보관 이유"] = reason[reason.ne("")]
    hold["주 성분"] = hold["보관 이유"].str.extract(r"^(\S+)")[0]
    hold["웹 후보에도 있음"] = hold["품목제조신고번호"].isin(web["품목제조신고번호"]).map({True: "예", False: ""})
    hold = hold.sort_values(["주 성분", "풀", "주성분·목적", "품목제조신고번호"]).reset_index(drop=True)
    hold.to_pickle(out("5단계_보관.pkl"))
    hold_why = hold["주 성분"].value_counts()

    # 영양소 × 대상 개수, 3개 미만 칸
    cnt = pd.crosstab(web["영양소"], web["대상"]).reindex(index=order, columns=TARGETS).fillna(0).astype(int)
    kind_cnt = pd.crosstab(web["영양소"], web["구분"].str.replace(r" \(.*\)", "", regex=True)).reindex(order).fillna(0).astype(int)
    short = [(n, t, int(cnt.loc[n, t])) for n in order for t in TARGETS if cnt.loc[n, t] < 3]
    unused = p[~p["품목제조신고번호"].isin(web["품목제조신고번호"])]
    unused_why = unused.apply(lambda r: f"{r['풀']}: {r['주성분·목적']}", axis=1).str.replace(r"\+.*", " 등", regex=True).value_counts()

    print("[3/3] 결과 엑셀 저장 중... (1~2분, 아무 키도 누르지 마세요)")
    lines = [
        ("5단계: 웹용 제품군 만들기", True), ("", False),
        ("결과", True),
        (f"· 4단계 제품 {len(p):,}개 중 웹 11종에 들어간 제품 {web['품목제조신고번호'].nunique():,}개 (영양소별로 나누면 {len(web):,}줄)", False),
        ("· 이 단계에서는 한 제품이 여러 영양소에 해당하면 영양소마다 한 줄 → 6단계에서 대표 칸 하나로 정리 (11-05)", False),
        ("· 영양소 × 대상 개수는 '영양소×대상' 시트", False),
        ("", False), ("11-05 변경", True),
        (f"· B군 칸: B1·B2가 둘 다 든 제품만 → {int(no_b12.sum()):,}줄 뺌", False),
        (f"· 유산균·오메가3·루테인·밀크씨슬이 섞인 단일·목적형 → {int(has_unused.sum()):,}줄 뺌 (생활기능 영양제 쪽, 공통 제품 없음)", False),
        (f"· 보관 (5단계_보관.pkl, '보관' 시트): 주 목적이 루테인·유산균·오메가3·밀크씨슬인 제품 {len(hold):,}개 → 나중에 생활유지 기능성으로 다룸 ("
         + " · ".join(f"{k} {v:,}" for k, v in hold_why.items()) + ")", False),
        ("", False), ("3개가 안 되는 칸 (참고)", True),
        ("· " + (" / ".join(f"{n}·{t} {c}개" for n, t, c in short) if short else "없음"), False),
        ("", False), ("웹에 쓰지 않는 제품 (4단계에는 있지만 이번에 빠진 것)", True),
    ] + [(f"· {k}: {v:,}개", False) for k, v in unused_why.head(15).items()] + [
        ("", False), ("규칙", True),
        ("· 단일: 그 영양소가 주성분 / 목적형: 연결된 목적 중 그 영양소가 실제로 든 제품 / 종합비타민: 균형형·피로회복형", False),
        ("· 오메가3·유산균·루테인·밀크씨슬, 비타민 A·E·K·칼륨 단일은 웹에서 쓰지 않음", False),
        ("· 같은 결과를 다시 만들려면: python 5단계_웹제품군.py", False),
    ]
    wb = new_book(lines)
    done = {k: "적용 완료 (이전 단계)" for k in [
        "식품영양성분DB", "기능성 문구만 있는 제품도", "원재료·섭취방법·기준규격은", "2022년 이후 신고", "제품명에 '수출'",
        "대상 판별", "임산부·수유부", "제품명이 질환을", "일반·전문 의약품", "성분은 기능성 칸으로", "나이아신·판토텐산·비오틴",
        "식이섬유는 기능성 칸에", "제품명에 나온 영양소가", "원료 껍데기형", "다른 목적 원료·문구", "제품명의 피부·미백",
        "수면·긴장 원료", "오메가3 자체의 기억력", "단일: 성분 1개", "주성분 판단 순서", "제품명에 우리 영양소가 2개",
        "목적형: 성분 2~6개", "종합비타민: 성분 7개", "칼슘+철 제품도"]}
    done.update({
        "13개 항목": "적용 완료 (웹은 11종: B군·C·D·칼슘·마그네슘·아연·철·엽산·식이섬유 + 종합비타민 2종)",
        "목적형은 이름이 아니라": "적용 완료",
        "단백질·인·칼륨·비타민 A·나트륨": "적용 완료 (제품 연결 없음)",
        "비타민 D는 일반 정보로": "비타민 D 포함 / 오메가3·유산균·루테인·밀크씨슬은 웹에서 아직 안 씀 (11-04)",
        "제품 식별자는": "적용 완료 (영양소별로는 한 줄씩, 9단계에서 중복 확인)",
    })
    add_criteria_sheet(wb, done)
    add_sheet(wb, "보관 이유별 개수", hold["보관 이유"].value_counts().rename_axis("보관 이유").reset_index(name="제품 수"), [50, 10], freeze="A2")
    add_sheet(wb, f"보관 ({len(hold):,})", hold[["주 성분", "보관 이유", "웹 후보에도 있음", "풀", "주성분·목적", "대상", "품목제조신고번호", "제품명", "업체명",
                                                "함께 든 가이드 성분", "기능성", "섭취방법", "기준규격", "섭취 시 주의사항"]],
              [10, 34, 10, 10, 16, 8, 18, 32, 20, 30, 60, 30, 40, 40])
    add_sheet(wb, "영양소×대상", cnt.reset_index().rename(columns={"index": "영양소"}), [22, 10, 10, 10, 10], freeze="A2")
    add_sheet(wb, "영양소×구분", kind_cnt.reset_index().rename(columns={"index": "영양소"}), [22, 10, 10, 12], freeze="A2")
    cols = ["영양소", "대상", "구분", "품목제조신고번호", "제품명", "업체명", "가이드 성분 수", "함께 든 가이드 성분",
            "분류 근거", "기능성", "섭취방법", "기준규격", "섭취 시 주의사항"]
    w = [20, 8, 18, 18, 32, 20, 8, 30, 22, 60, 30, 40, 40]
    for n in order:
        d = web[web["영양소"] == n]
        add_sheet(wb, f"{n} ({len(d):,})"[:31], d[cols], w)
    wb.save(out("5단계_웹제품군.xlsx"))
    print(f"5단계 완료: 웹 11종 제품 {web['품목제조신고번호'].nunique():,}개 ({len(web):,}줄)")
    print(cnt.to_string())


if __name__ == "__main__":
    main()
