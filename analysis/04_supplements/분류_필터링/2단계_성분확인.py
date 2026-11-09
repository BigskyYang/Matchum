# -*- coding: utf-8 -*-
"""
2단계: 성분 확인
기준: 「영양제_분류_필터링_기준(1104).pdf」 3-4절 + 11-04 결정 (확인 필요로 두지 않고 모두 제외)

하는 일 (위에서부터 차례로. 한 제품은 처음 걸린 이유 하나로만 기록)
  ① 제품명-성분 불일치: 제품명에 우리 영양소 이름이 있는데 기능성 칸에서 그 성분이 확인되지 않으면 제외
     (예: '8030칼슘플러스'인데 칼슘 기능성 없음, '프리바이오틱스'인데 유산균 아님, 식물성 오메가3)
  ② 원료 껍데기형: 가이드 성분이 1개뿐이고 그 영양소가 제품명에 없는 제품 중
     - 원재료 맨 앞 2개에 그 영양소 원료가 없거나
     - 원재료에 홍삼·녹용·천마·침향 등 한방·건강원료가 있으면 제외
     (예: 홍삼·침향이 주원료인데 아연만 살짝 넣은 제품)

입력  1단계_결과.pkl (일반 대상)
출력  2단계_성분확인.xlsx, 2단계_결과.pkl (다음 단계 입력)
"""
import re
import pandas as pd
from 공통 import out, nf, new_book, add_sheet, add_criteria_sheet

# 추천 항목 13개
T13 = ["비타민 B군", "비타민 C", "비타민 D", "칼슘", "마그네슘", "아연", "철", "엽산",
       "오메가3", "유산균", "식이섬유", "루테인", "밀크씨슬"]

# 제품명에서 영양소를 찾는 이름 패턴
NAME = {
    "비타민 B군": r"비타민\s*B|B\s*컴플렉스|(?i:b-?complex)|비타민비|B군|비오틴|나이아신|판토텐|(?i:biotin)",
    "비타민 C": r"비타민\s*C|(?i:vitamin\s*c)",
    "비타민 D": r"비타민\s*D|(?i:vitamin\s*d)|\bD3\b",
    "칼슘": r"칼슘|칼마|진주|어골|(?i:calcium)|(?<![A-Za-z])Ca(?![a-z])",
    "마그네슘": r"마그네슘|(?i:magnesium)|(?<![A-Za-z])Mg(?![a-z])",
    "아연": r"아연|(?i:zinc)|(?<![A-Za-z])Zn(?![a-z])",
    "철": r"철분|헴철|(?i:iron)",
    "엽산": r"엽산|(?i:folic|folate)",
    "오메가3": r"오메가|(?i:omega|rTG)",
    "유산균": r"유산균|프로바이오|바이오틱|(?i:probiotic)",
    "식이섬유": r"식이섬유|차전자|화이바|(?i:fiber)",
    "루테인": r"루테인|(?i:lutein)",
    "밀크씨슬": r"밀크\s*[씨시]슬|(?i:milk\s*thistle)|실리마린",
}

# 원료 껍데기형 판단: 영양소별 원재료 이름
SOURCE = {
    "아연": r"아연",
    "비타민 C": r"비타민\s*C|아스코르브|아세로라|(?i:vitamin\s*c)",
    "비타민 D": r"비타민\s*D|콜레칼시페롤|에르고칼시페롤",
    "칼슘": r"칼슘|탄산|해조|난각|패각|우유|진주|어골",
    "마그네슘": r"마그네슘",
    "철": r"철|헴",
    "엽산": r"엽산|폴레이트|MTHF",
    "비타민 B군": r"비타민\s*B|티아민|리보플라빈|니코틴|판토텐|피리독신|코발라민|비오틴",
}
HERB = r"홍삼|인삼|녹용|천마|동충하초|침향|로얄젤리|흑염소|산삼|헛개|도라지|흑마늘|생강|배즙|대추|오가피|감초|당귀|황기|구기자|공진"


def name_mismatch(name, ings):
    """제품명에는 있는데 기능성에서 확인되지 않은 영양소"""
    return [k for k in T13 if k not in ings and re.search(NAME[k], name)]


def shell_reason(name, ings, raw):
    """원료 껍데기형이면 이유를, 아니면 None"""
    if len(ings) != 1 or ings[0] not in SOURCE or re.search(NAME[ings[0]], name):
        return None
    raw = nf(raw)
    first_two = ", ".join([x.strip() for x in raw.split(",")][:2])
    if not re.search(SOURCE[ings[0]], first_two):
        return f"원료 껍데기형 ({ings[0]}: 원재료 앞 2개에 없음)"
    if re.search(HERB, raw):
        herb = re.search(HERB, raw).group(0)
        return f"원료 껍데기형 ({ings[0]}: {herb} 등 주원료)"
    return None


def main():
    print("[1/3] 1단계 결과 읽는 중...")
    p = pd.read_pickle(out("1단계_결과.pkl"))
    n0 = len(p)
    ings = p["함께 든 가이드 성분"].str.split(", ")

    print("[2/3] 성분 확인 중...")
    reason = []
    for name, ing, raw in zip(p["제품명"], ings, p["원재료"]):
        miss = name_mismatch(name, ing)
        if miss:
            reason.append("제품명-성분 불일치 (" + "/".join(miss) + ")")
            continue
        reason.append(shell_reason(name, ing, raw) or "")
    p["빠진 이유"] = reason

    removed = p[p["빠진 이유"] != ""].copy()
    keep = p[p["빠진 이유"] == ""].drop(columns="빠진 이유").reset_index(drop=True)
    keep.to_pickle(out("2단계_결과.pkl"))

    is_mis = removed["빠진 이유"].str.startswith("제품명")
    mis = removed[is_mis]
    shell = removed[~is_mis]
    mis_cnt = mis["빠진 이유"].str.extract(r"\((.+)\)")[0].value_counts()
    shell_kind = shell["빠진 이유"].str.contains("앞 2개").map({True: "원재료 앞 2개에 없음", False: "한방·건강원료 주원료"}).value_counts()
    shell_ing = shell["빠진 이유"].str.extract(r"\((.+?):")[0].value_counts()

    print("[3/3] 결과 엑셀 저장 중... (1~2분, 아무 키도 누르지 마세요)")
    lines = [
        ("2단계: 성분 확인", True), ("", False),
        ("결과", True),
        (f"· 시작 {n0:,}개 → 빠진 제품 {len(removed):,}개 → 다음 단계로 {len(keep):,}개", False),
        ("· 11-04 결정: '확인 필요'로 따로 두지 않고 모두 제외", False),
        ("", False), ("빠진 이유", True),
        (f"· 제품명-성분 불일치: {len(mis):,}개 ({' · '.join(f'{k} {v}' for k, v in mis_cnt.items())})", False),
        ("   - 제품명에 영양소 이름이 있는데 기능성 칸에서 그 성분이 확인되지 않음 (예: 프리바이오틱스, 식물성 오메가3)", False),
        (f"· 원료 껍데기형: {len(shell):,}개 ({' · '.join(f'{k} {v}' for k, v in shell_kind.items())})", False),
        (f"   - 성분별: {' · '.join(f'{k} {v}' for k, v in shell_ing.items())}", False),
        ("   - 가이드 성분이 1개이고 제품명에 없는데, 원재료 앞 2개에 없거나 홍삼·녹용·천마 등이 주원료인 제품", False),
        ("", False), ("참고", True),
        ("· 성분 인식 규칙(기능성 칸 기준, 나이아신 등 → B군, 식이섬유 엄격 인정)은 최종본을 만들 때 이미 적용됨", False),
        ("· 같은 결과를 다시 만들려면: python 2단계_성분확인.py", False),
    ]
    wb = new_book(lines)
    done = {
        "식품영양성분DB": "적용 완료 (최종본)", "기능성 문구만 있는 제품도": "적용 완료 (최종본)",
        "원재료·섭취방법·기준규격은": "적용 완료 (최종본)", "2022년 이후 신고": "적용 완료 (최종본)",
        "제품명에 '수출'": "적용 완료 (최종본 제외 목록)", "대상 판별": "적용 완료 (1단계)",
        "임산부·수유부": "적용 완료 (1단계)", "제품명이 질환을": "적용 완료 (1단계)",
        "일반·전문 의약품": "적용 완료 (의약품 0개)",
        "성분은 기능성 칸으로": "적용 완료 (최종본)", "나이아신·판토텐산·비오틴": "적용 완료 (최종본)",
        "식이섬유는 기능성 칸에": "적용 완료 (최종본)",
        "제품명에 나온 영양소가": f"적용 완료 ({len(mis):,}개 제외, 11-04: 확인 필요 대신 제외)",
        "원료 껍데기형": f"적용 완료 ({len(shell):,}개 제외, 11-04: 확인 필요 대신 제외)",
    }
    add_criteria_sheet(wb, done)
    w = [18, 32, 20, 11, 10, 8, 8, 10, 8, 30, 60, 40, 30, 40, 40]
    add_sheet(wb, f"남은 제품 ({len(keep):,})", keep, w)
    cols = ["빠진 이유", "품목제조신고번호", "제품명", "업체명", "함께 든 가이드 성분", "원재료", "기능성"]
    cw = [36, 18, 36, 20, 26, 50, 60]
    add_sheet(wb, f"빠짐-이름 불일치 ({len(mis):,})", mis[cols].sort_values("빠진 이유"), cw)
    add_sheet(wb, f"빠짐-껍데기형 ({len(shell):,})", shell[cols].sort_values("빠진 이유"), cw)
    wb.save(out("2단계_성분확인.xlsx"))
    print(f"2단계 완료: {n0:,} → 빠짐 {len(removed):,} (이름 불일치 {len(mis):,} · 껍데기형 {len(shell):,}) → 다음 단계 {len(keep):,}")


if __name__ == "__main__":
    main()
