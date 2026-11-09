"""발표 PDF를 쪽마다 이미지로 바꿔 README에 넣는다.
입력: docs/presentation/slides.pdf (최종 발표자료)
출력: docs/presentation/slides/slide-01.jpg … (가로 1280px, JPEG)

발표자료가 바뀌면 PDF를 같은 이름으로 덮어쓴 뒤 다시 실행한다 (저장소 루트에서)
  python scripts/export_slides.py
쪽 수가 줄면 남는 이미지는 지운다. README의 슬라이드 목록은 쪽 수가 바뀔 때만 손보면 된다.
"""
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / 'docs' / 'presentation' / 'slides.pdf'
OUT = ROOT / 'docs' / 'presentation' / 'slides'
WIDTH = 1280

OUT.mkdir(parents=True, exist_ok=True)
doc = pymupdf.open(PDF)
for old in OUT.glob('slide-*.jpg'):
    old.unlink()
for i, page in enumerate(doc, 1):
    zoom = WIDTH / page.rect.width
    page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).save(OUT / f'slide-{i:02d}.jpg', jpg_quality=82)
size = sum(p.stat().st_size for p in OUT.glob('slide-*.jpg'))
sys.stdout.reconfigure(encoding='utf-8')
print(f'{len(doc)}장 → {OUT.relative_to(ROOT)} ({size / 1048576:.1f}MB)')
