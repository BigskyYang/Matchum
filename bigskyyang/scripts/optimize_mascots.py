"""
마스코트 이미지(web/public/mascot)를 휴대폰에서 빨리 뜨도록 WebP로 줄인다.

  start.png → start.webp   (정지 이미지: 화면 표시 176px의 2배인 352px)
  hello.gif → hello.webp   (움직이는 이미지: 화면 표시 256px의 2배인 512px, 프레임·속도 그대로)

웹(Mascot.jsx)은 WebP를 먼저 쓰고, WebP가 없거나 안 열리면 원본 PNG/GIF를 쓴다.
원본은 지우지 않는다. 마스코트 이미지를 새로 넣거나 바꿨으면 다시 실행한다.

사용법 (bigskyyang 폴더에서)
  python scripts/optimize_mascots.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageSequence

MASCOT = Path(__file__).resolve().parents[1] / 'web' / 'public' / 'mascot'
STILL_PX = 352
ANIM_PX = 512
# 움직이는 이미지의 크림색 배경을 투명하게 바꿔, 어떤 화면 배경 위에서도 사각형 경계가 보이지 않게 한다.
# (손실 압축은 배경색을 미세하게 바꾸므로, 색을 맞추는 대신 투명하게 한다)
CLEAR = (0xFF, 0xF9, 0xF2, 0)
BG_TOLERANCE = 14


def clear_background(frame):
    # 네 모서리에서 배경과 비슷한 색을 따라가며 투명하게 만든다 (캐릭터 외곽선 안쪽은 건드리지 않음)
    frame = frame.convert('RGBA')
    for xy in [(0, 0), (frame.width - 1, 0), (0, frame.height - 1), (frame.width - 1, frame.height - 1)]:
        ImageDraw.floodfill(frame, xy, CLEAR, thresh=BG_TOLERANCE)
    return frame


def fit(img, px):
    if max(img.size) <= px:
        return img
    scale = px / max(img.size)
    return img.resize((round(img.width * scale), round(img.height * scale)), Image.Resampling.LANCZOS)


def kb(path):
    return f'{path.stat().st_size / 1024:,.0f}KB'


for src in sorted(MASCOT.glob('*.png')):
    out = src.with_suffix('.webp')
    fit(Image.open(src).convert('RGBA'), STILL_PX).save(out, 'WEBP', quality=88, method=6)
    print(f'{src.name:14} {kb(src):>8} → {out.name:14} {kb(out):>7}')

for src in sorted(MASCOT.glob('*.gif')):
    out = src.with_suffix('.webp')
    gif = Image.open(src)
    frames, durations = [], []
    for frame in ImageSequence.Iterator(gif):
        durations.append(frame.info.get('duration', gif.info.get('duration', 100)))
        frames.append(clear_background(fit(frame.convert('RGB'), ANIM_PX)))
    frames[0].save(
        out,
        'WEBP',
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        quality=82,
        method=6,
    )
    print(f'{src.name:14} {kb(src):>8} → {out.name:14} {kb(out):>7}  ({len(frames)}프레임, {sum(durations) / 1000:.1f}초)')
