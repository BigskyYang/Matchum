"""
카카오톡 등에 링크를 보낼 때 뜨는 공유 미리보기 이미지(web/public/og.png, 1200×630)를 만든다.
팀 이름·서비스 이름·부제는 web/src/config.js에서 읽는다. 이름이나 마스코트가 바뀌면 다시 실행한다.

사용법 (저장소 루트에서, Windows의 맑은 고딕 글꼴 사용)
  python scripts/make_share_image.py
"""

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WEB = Path(__file__).resolve().parents[1] / 'web'
FONT_BOLD = 'C:/Windows/Fonts/malgunbd.ttf'
FONT = 'C:/Windows/Fonts/malgun.ttf'
CREAM = (0xFF, 0xF9, 0xF2)
INK = (0x4A, 0x3F, 0x3F)
INK_SOFT = (0x8A, 0x7C, 0x78)
PRIMARY = (0xE0, 0x6A, 0x80)
MINT = (0x4F, 0xAE, 0x8C)

config = (WEB / 'src' / 'config.js').read_text(encoding='utf-8')
const = lambda key: re.search(rf"{key} = '([^']+)'", config).group(1)
team, name, subtitle = const('TEAM_NAME'), const('SERVICE_NAME'), const('SERVICE_SUBTITLE')


def wrap(draw, text, font, width):
    # 어절 단위로 줄바꿈
    lines, line = [], ''
    for word in text.split(' '):
        trial = f'{line} {word}'.strip()
        if draw.textlength(trial, font=font) > width and line:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line]


W, H = 1200, 630
img = Image.new('RGB', (W, H), CREAM)
draw = ImageDraw.Draw(img)

mascot = Image.open(WEB / 'public' / 'mascot' / 'start.png').convert('RGBA')
mascot.thumbnail((440, 440), Image.Resampling.LANCZOS)
img.paste(mascot, (70, (H - mascot.height) // 2), mascot)

x, width = 560, 580
# 제목이 한 줄에 들어가도록 글자 크기를 줄여 가며 맞춘다
size = 68
while size > 44 and draw.textlength(name, font=ImageFont.truetype(FONT_BOLD, size)) > width:
    size -= 2
title_font = ImageFont.truetype(FONT_BOLD, size)
team_font = ImageFont.truetype(FONT_BOLD, 28)
small_font = ImageFont.truetype(FONT_BOLD, 30)
# 부제도 되도록 한 줄에
body_size = 34
while body_size > 26 and draw.textlength(subtitle, font=ImageFont.truetype(FONT, body_size)) > width:
    body_size -= 1
body_font = ImageFont.truetype(FONT, body_size)
body_lines = wrap(draw, subtitle, body_font, width)
title_h = round(size * 1.3)
y = (H - (44 + title_h + 50 + 30 + len(body_lines) * 50)) // 2

draw.text((x, y), f'Team {team}', font=team_font, fill=PRIMARY)
y += 44
# 제목: 앞의 N(Nutrient)만 민트색으로
if name.startswith('N'):
    draw.text((x, y), 'N', font=title_font, fill=MINT)
    draw.text((x + draw.textlength('N', font=title_font), y), name[1:], font=title_font, fill=INK)
else:
    draw.text((x, y), name, font=title_font, fill=INK)
y += title_h
draw.text((x, y), 'Nutrient + MBTI', font=small_font, fill=MINT)
y += 50
draw.rounded_rectangle((x, y, x + 80, y + 8), radius=4, fill=PRIMARY)
y += 30
for line in body_lines:
    draw.text((x, y), line, font=body_font, fill=INK_SOFT)
    y += 50

out = WEB / 'public' / 'og.png'
img.save(out, optimize=True)
print(f'저장: {out} ({out.stat().st_size / 1024:.0f}KB)')
