# -*- coding: utf-8 -*-
"""
전체 실행: 1단계부터 마지막 단계까지 순서대로 한 번에 돌린다.
기준이 바뀌거나 코드가 바뀌면 이 파일 하나만 실행하면 된다.
(각 단계는 앞 단계 결과 파일(.pkl)을 읽기 때문에, 중간 단계만 돌리면 예전 결과가 섞일 수 있음)

  python 전체_실행.py            → 1단계부터 끝까지
  python 전체_실행.py 최종본      → 입력 엑셀 최종본부터 다시 만들고 끝까지 (3~5분 더 걸림)
"""
import os, sys, subprocess, time

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = ["1단계_기본거르기.py", "2단계_성분확인.py", "3단계_목적충돌.py", "4단계_풀나누기.py",
         "5단계_웹제품군.py", "6단계_1일환산.py", "7단계_상한거르기.py", "8단계_품질거르기.py", "9단계_점수.py"]

if len(sys.argv) > 1 and sys.argv[1] == "최종본":
    STEPS = ["입력엑셀_최종본_만들기.py"] + STEPS

start = time.time()
for f in STEPS:
    path = os.path.join(HERE, f)
    if not os.path.exists(path):
        print(f"\n(아직 없는 단계라서 여기서 멈춰요: {f})")
        break
    print(f"\n========== {f} ==========")
    r = subprocess.run([sys.executable, path], cwd=HERE)
    if r.returncode != 0:
        print(f"\n!! {f}에서 오류가 났어요. 위 메시지를 확인해 주세요.")
        sys.exit(1)
print(f"\n전체 실행 끝 ({time.time() - start:.0f}초)")
