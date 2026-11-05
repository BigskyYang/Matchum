# -*- coding: utf-8 -*-
"""
8단계: 품질 거르기 (11-04 팀 결정, 변경안 확정)
기준: 「영양제_분류_필터링_기준(1104).pdf」 + 11-04 결정

점수를 매기기 전에, 화면에 보여 주기 어려운 제품을 근거를 갖고 뺀다. (①→④ 순서대로, 겹치는 건 앞 이유로 한 번만 셈)
  ① 주의사항 정보가 없는 제품 제외
       - 웹은 제품 정보를 보여 주기 전에 주의사항을 확인시키는 구조라, 칸이 비어 있으면 보여 줄 내용이 없음
       - 9단계 '주의 원료' 점수는 주의사항 글을 읽어 감점하므로, 비어 있으면 오히려 감점을 피하는 모순이 생김
  ② 기준치 대비 500% 초과 제외 (줄 단위: 그 영양소 줄만 빠짐)
       - 상한은 안 넘어도 "많을수록 좋다"는 인상을 주지 않기 위해 (상한 미설정 ≠ 무제한 안전)
       - 비타민 B군은 든 B 비타민 중 가장 낮은 기준치 %로 판단, 종합비타민·식이섬유는 해당 없음
  ③ 원재료 30개 초과 제외
       - 부원료가 너무 많으면 알레르기·주의 원료를 사용자가 확인하기 어려움
  ④ 비슷한 제품 제외 (이름만 다른 같은 처방)
       - 같은 업체 제품끼리 비교해서 ⓐ 원재료가 90% 이상 겹치고 (괄호 안 세부 원료는 빼고 비교)
         ⓑ 들어 있는 성분이 같고, 하루 함량(B 비타민 포함) 차이가 모두 10% 이내이면 같은 처방으로 봄
       - 둘 중 **가장 최근에 신고한 제품**을 남김 (11-05: 옛 신고는 단종됐을 가능성이 더 높아서)
         신고일이 같으면 9단계 점수가 높은 쪽 → 원재료가 적은 쪽

입력  7단계_결과.pkl, 6단계_제품별함량.pkl
출력  8단계_품질거르기.xlsx, 8단계_결과.pkl (다음 단계 입력)
"""
import re
import itertools
import importlib
import numpy as np
import pandas as pd
from 공통 import out, nf, new_book, add_sheet, add_criteria_sheet

step9 = importlib.import_module("9단계_점수")       # 점수 계산·제품 정보 함수를 같이 씀

TARGETS = step9.TARGETS
NUTRIENTS = step9.NUTRIENTS
MAX_PCT = 500           # ② 기준치 대비 % 상한
MAX_RAW = 30            # ③ 원재료 개수 상한
SIMILAR = 0.9           # ④ 원재료 겹침 비율
AMOUNT_GAP = 0.1        # ④ 하루 함량 차이
AMOUNT_COLS = ["비타민 C", "비타민 D", "칼슘", "마그네슘", "철", "아연", "엽산", "비타민 B6", "니아신", "비타민 A", "비타민 E", "요오드"]


def raw_set(raw):
    """원재료 → 원료 이름 집합 (괄호 안 세부 원료는 빼고)"""
    t = re.sub(r"\(.*?\)", "", nf(raw if isinstance(raw, str) else ""))
    return frozenset(x.strip() for x in t.split(",") if x.strip())


def amounts(no, amt, info):
    a = amt.loc[no]
    v = {k: float(a[k]) for k in AMOUNT_COLS if k in a.index and pd.notna(a[k])}
    v.update({"B:" + k: val for k, val in info[no]["b"].items()})
    return v


def same_amounts(A, B):
    if set(A) != set(B):
        return False
    return all(abs(A[k] - B[k]) <= AMOUNT_GAP * max(A[k], B[k], 1e-9) for k in A)


def main():
    print("[1/4] 7단계 결과 읽는 중...")
    web = pd.read_pickle(out("7단계_결과.pkl"))
    amt = pd.read_pickle(out("6단계_제품별함량.pkl"))
    web["영양소"] = pd.Categorical(web["영양소"].astype(str), NUTRIENTS, ordered=True)
    web["대상"] = pd.Categorical(web["대상"].astype(str), TARGETS, ordered=True)
    prod = web.drop_duplicates("품목제조신고번호").set_index("품목제조신고번호")
    info = step9.product_info(prod, amt)
    web["원재료 수"] = web["품목제조신고번호"].map({n: d["raw"] for n, d in info.items()})
    web["_pct"] = [info[no]["pct"].get(str(k)) for no, k in zip(web["품목제조신고번호"], web["영양소"])]
    web["빠진 이유"] = ""

    print("[2/4] ①~③ 거르는 중...")
    m1 = web["섭취 시 주의사항"].fillna("").str.strip().eq("")
    web.loc[m1, "빠진 이유"] = "① 주의사항 정보 없음"
    m2 = web["빠진 이유"].eq("") & (pd.to_numeric(web["_pct"], errors="coerce") > MAX_PCT)
    web.loc[m2, "빠진 이유"] = web.loc[m2, "_pct"].map(lambda v: f"② 기준치 대비 {v:.0f}% ({MAX_PCT}% 초과)")
    m3 = web["빠진 이유"].eq("") & (web["원재료 수"] > MAX_RAW)
    web.loc[m3, "빠진 이유"] = web.loc[m3, "원재료 수"].map(lambda v: f"③ 원재료 {v}개 ({MAX_RAW}개 초과)")

    print("[3/4] ④ 비슷한 제품 찾는 중... (1~2분)")
    left = web[web["빠진 이유"].eq("")]
    best = step9.score_table(left, info).groupby("품목제조신고번호")["점수"].max()
    P = prod.loc[left["품목제조신고번호"].unique()]
    T = {n: raw_set(r) for n, r in P["원재료"].items()}
    M = {n: amounts(n, amt, info) for n in P.index}
    why, pairs = {}, []
    for firm, g in P.groupby("업체명"):
        for x, y in itertools.combinations(sorted(g.index), 2):
            if x in why or y in why:
                continue
            j = len(T[x] & T[y]) / max(1, len(T[x] | T[y]))
            if j < SIMILAR or not same_amounts(M[x], M[y]):
                continue
            keep, lose = sorted([x, y], key=lambda n: (-int(str(P.loc[n, "신고일자"]).replace("-", "")[:8] or 0), -best[n], info[n]["raw"], n))
            why[lose] = f"④ 비슷한 제품 (원재료 {j * 100:.0f}% 겹침) → 남긴 제품 「{P.loc[keep, '제품명']}」 {keep}"
            pairs.append({"업체명": firm, "원재료 겹침(%)": round(j * 100), "빠진 제품": P.loc[lose, "제품명"], "빠진 신고번호": lose,
                          "남긴 제품": P.loc[keep, "제품명"], "남긴 신고번호": keep})
    m4 = web["빠진 이유"].eq("") & web["품목제조신고번호"].isin(why)
    web.loc[m4, "빠진 이유"] = web.loc[m4, "품목제조신고번호"].map(why)

    keep = web[web["빠진 이유"].eq("")].drop(columns=["빠진 이유", "_pct"]).sort_values(
        ["영양소", "대상", "품목제조신고번호"]).reset_index(drop=True)
    keep.to_pickle(out("8단계_결과.pkl"))
    gone = web[web["빠진 이유"].ne("")]

    steps = [("시작 (7단계 결과)", web)]
    rest = web
    for tag, m in [("① 주의사항 정보 없음", m1), ("② 기준치 대비 500% 초과", m2), ("③ 원재료 30개 초과", m3), ("④ 비슷한 제품", m4)]:
        rest = rest[~m.reindex(rest.index)]
        steps.append((tag, rest))
    flow = pd.DataFrame([{"단계": t, "빠진 줄": (0 if i == 0 else len(steps[i - 1][1]) - len(d)),
                          "남은 제품": d["품목제조신고번호"].nunique(), "남은 줄": len(d)} for i, (t, d) in enumerate(steps)])
    after = pd.crosstab(keep["영양소"], keep["대상"]).reindex(index=NUTRIENTS, columns=TARGETS).fillna(0).astype(int)
    n0, n1 = web["품목제조신고번호"].nunique(), keep["품목제조신고번호"].nunique()

    print("[4/4] 결과 엑셀 저장 중... (1~2분, 아무 키도 누르지 마세요)")
    lines = [
        ("8단계: 품질 거르기", True), ("", False),
        ("결과", True),
        (f"· 7단계 제품 {n0:,}개 ({len(web):,}줄) → 남은 제품 {n1:,}개 ({len(keep):,}줄)", False),
    ] + [(f"· {r['단계']}: 빠진 줄 {r['빠진 줄']:,} → 남은 제품 {r['남은 제품']:,}개 ({r['남은 줄']:,}줄)", False) for _, r in flow.iloc[1:].iterrows()] + [
        ("· ②는 줄 단위라, 한 제품이 어떤 영양소 줄에서만 빠지고 다른 줄로는 남을 수 있음", False),
        ("", False), ("기준과 이유", True),
        ("① 주의사항 정보가 없는 제품: 웹에서 주의사항을 보여 줄 수 없고, 9단계 주의 원료 감점을 피하는 모순이 생김", False),
        (f"② 기준치 대비 {MAX_PCT}% 초과: 상한은 안 넘어도 '많을수록 좋다'는 인상을 주지 않기 위해 (B군은 가장 낮은 B 비타민 %)", False),
        (f"③ 원재료 {MAX_RAW}개 초과: 알레르기·주의 원료를 확인하기 어려움", False),
        (f"④ 비슷한 제품: 같은 업체, 원재료 {SIMILAR * 100:.0f}% 이상 겹침, 같은 성분에 하루 함량 차이 {AMOUNT_GAP * 100:.0f}% 이내 → 가장 최근 신고 하나만 남김 (옛 신고는 단종 가능성)", False),
        ("", False), ("· 같은 결과를 다시 만들려면: python 전체_실행.py", False),
    ]
    wb = new_book(lines)
    done = {k: "적용 완료 (이전 단계)" for k in [
        "식품영양성분DB", "기능성 문구만 있는 제품도", "원재료·섭취방법·기준규격은", "2022년 이후 신고", "제품명에 '수출'",
        "대상 판별", "임산부·수유부", "제품명이 질환을", "일반·전문 의약품", "성분은 기능성 칸으로", "나이아신·판토텐산·비오틴",
        "식이섬유는 기능성 칸에", "제품명에 나온 영양소가", "원료 껍데기형", "다른 목적 원료·문구", "제품명의 피부·미백",
        "수면·긴장 원료", "오메가3 자체의 기억력", "단일: 성분 1개", "주성분 판단 순서", "제품명에 우리 영양소가 2개",
        "목적형: 성분 2~6개", "종합비타민: 성분 7개", "칼슘+철 제품도", "13개 항목", "목적형은 이름이 아니라",
        "단백질·인·칼륨·비타민 A·나트륨", "제품 식별자는", "압축된 후보만 표시량", "상한섭취량 초과 제품 제외"]}
    done["주의사항 정보가 없는"] = f"적용 완료 ({int(m1.sum()):,}줄)"
    done["기준치 대비 500%"] = f"적용 완료 ({int(m2.sum()):,}줄)"
    done["원재료가 30개"] = f"적용 완료 ({int(m3.sum()):,}줄)"
    done["비슷한 제품"] = f"적용 완료 (제품 {len(why):,}개, {int(m4.sum()):,}줄)"
    done["비타민 D는 일반 정보로"] = "비타민 D 포함 / 오메가3·유산균·루테인·밀크씨슬은 웹에서 아직 안 씀 (11-04)"
    done["기능성 원료는 상한이 아니라"] = "해당 없음 (웹에서 오메가3·루테인 등을 쓰지 않음)"
    add_criteria_sheet(wb, done)
    add_sheet(wb, "단계별 개수", flow, [26, 10, 10, 10], freeze="A2")
    add_sheet(wb, "영양소×대상 (8단계 후)", after.reset_index().rename(columns={"index": "영양소"}), [24, 8, 8, 8, 8], freeze="A2")
    cols = ["영양소", "대상", "구분", "품목제조신고번호", "제품명", "업체명", "제형", "1일 섭취량", "1일 함량", "1일 함량 단위",
            "기준치 대비(%)", "원재료 수", "섭취 시 주의사항"]
    add_sheet(wb, f"남은 제품 ({len(keep):,}줄)", keep[cols], [22, 8, 18, 18, 32, 20, 10, 26, 10, 8, 10, 8, 50])
    gcols = ["빠진 이유", "영양소", "대상", "품목제조신고번호", "제품명", "업체명", "제형", "1일 섭취량", "기준치 대비(%)", "원재료 수", "섭취 시 주의사항"]
    for tag, name in [("①", "빠짐-① 주의사항 없음"), ("②", "빠짐-② 500% 초과"), ("③", "빠짐-③ 원재료 30개 초과")]:
        g = gone[gone["빠진 이유"].str.startswith(tag)]
        add_sheet(wb, f"{name} ({len(g):,})", g[gcols], [30, 22, 8, 18, 32, 20, 10, 26, 10, 8, 50])
    add_sheet(wb, f"빠짐-④ 비슷한 제품 ({len(pairs):,}쌍)", pd.DataFrame(pairs), [20, 10, 34, 18, 34, 18], freeze="A2")
    wb.save(out("8단계_품질거르기.xlsx"))
    print(f"8단계 완료: 제품 {n0:,} → {n1:,} ({len(web):,}줄 → {len(keep):,}줄)")
    print(flow.to_string(index=False))


if __name__ == "__main__":
    main()
