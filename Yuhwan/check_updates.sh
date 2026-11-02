#!/usr/bin/env bash
# 팀 저장소(BigskyYang/Matchum)에서 '내 폴더(Yuhwan) 말고' 바뀐 것을 보여준다.
# 마지막으로 확인한 커밋을 .last_checked_commit에 저장해서, 다음엔 그 이후 변경만 보여줌.
# 사용: bash check_updates.sh        (처음이면 최근 10개 커밋 기준)
set -e
REPO="C:/python-course/Matchum"
STATE="$(cd "$(dirname "$0")" && pwd)/.last_checked_commit"

cd "$REPO"
git pull --rebase --autostash -q   # 작업 중인 변경이 있어도 pull (임시 보관 후 복원)
HEAD=$(git rev-parse HEAD)
if [ -f "$STATE" ] && git cat-file -e "$(cat "$STATE")" 2>/dev/null; then
  BASE=$(cat "$STATE")
else
  BASE=$(git rev-list --max-count=11 HEAD | tail -1)
fi

echo "== 확인 범위: ${BASE:0:7} → ${HEAD:0:7}"
if [ "$BASE" = "$HEAD" ]; then
  echo "새 커밋 없음"
else
  echo; echo "== 커밋 (Yuhwan 제외 변경이 있는 것)"
  git log --format='%h %ad %an: %s' --date=format:'%m-%d %H:%M' "$BASE..$HEAD" -- . ':(exclude)Yuhwan'
  echo; echo "== 바뀐 파일 (Yuhwan 제외)"
  git diff --stat "$BASE" "$HEAD" -- . ':(exclude)Yuhwan' | tail -n 30
  echo; echo "== 우리 분석에 영향 줄 수 있는 파일"
  git diff --name-only "$BASE" "$HEAD" -- 'Jiyeon' 'Jaejun' 'bigskyyang/web/src/data' 'docs' || true
fi
echo "$HEAD" > "$STATE"
echo; echo "슬랙도 확인: #머신러닝-2조, #머신러닝2조-github(push 알림)"
