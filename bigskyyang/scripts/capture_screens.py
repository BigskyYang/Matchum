"""최종 점검·발표 캡처: 빌드한 웹(dist)을 이 PC에서 띄워 휴대폰 크기(390×844, 3배)로 모든 화면을 돌며
   1) 접근성 검사(axe, WCAG 2 A·AA)  2) 첫 화면 내려받는 양·시간(압축 없이, 빠른 4G 정도로 제한)  3) 발표용 화면 캡처
결과: 바탕화면 NBTI_발표캡처/ (PNG) + 점검결과.json
설문 응답은 아래 SURVEY 예시(30대 여성)를 넣어 둔다. 실제 사람 자료는 쓰지 않는다.

준비: pip install playwright (Chrome이 설치돼 있으면 따로 브라우저를 받지 않아도 된다)
사용법 (bigskyyang 폴더에서): cd web && npm run build && cd .. && python scripts/capture_screens.py
"""
import json
import sys
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
DIST = Path(__file__).resolve().parents[1] / 'web' / 'dist'
OUT = Path.home() / 'Desktop' / 'NBTI_발표캡처'
OUT.mkdir(exist_ok=True)
AXE = 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js'


class SPA(SimpleHTTPRequestHandler):
    # 없는 주소(/result 등)는 index.html로 (앱 안에서 주소를 처리한다)
    def send_head(self):
        path = Path(self.translate_path(self.path))
        if not path.exists() and '.' not in Path(self.path.split('?')[0]).name:
            self.path = '/index.html'
        return super().send_head()

    def log_message(self, *a):
        pass


server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SPA, directory=str(DIST)))
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = f'http://127.0.0.1:{server.server_address[1]}'

SURVEY = {
    'answers': {
        'sex': 2, 'birth_date': '1994-03-15', 'activity': 1, 'strength_days': 0, 'sedentary_min': 600,
        'weekday_bed': '01:00', 'weekday_wake': '07:00', 'weekend_same': 'no', 'weekend_bed': '02:00', 'weekend_wake': '10:00',
        'stress': 2, 'meals': {'breakfast': 0, 'lunch': 3, 'dinner': 3}, 'eating_out': 4,
        'smoke_now': 'no', 'drink_freq': 3, 'drink_amount': 2, 'veg': 5, 'fruit': 3,
        'ffq_meat': 3, 'ffq_fish': 2, 'ffq_egg': 3, 'ffq_legume': 2, 'ffq_dairy': 2,
    },
    'step': {'1': 0, '2': 0},
    'done': {'1': True, '2': True},
}
PICKS = {'ids': ['20220010222177'], 'gate': 'ok', 'mine': [{'id': '200400200073012'}, {'name': '우리집 오메가3'}]}
SEED = f"""
if (!sessionStorage.getItem('__seeded')) {{
  sessionStorage.setItem('nbti-survey-v4', {json.dumps(json.dumps(SURVEY, ensure_ascii=False), ensure_ascii=False)});
  sessionStorage.setItem('nbti-picks-v1', {json.dumps(json.dumps(PICKS, ensure_ascii=False), ensure_ascii=False)});
  sessionStorage.setItem('__seeded', '1');
}}
"""

report = {'axe': {}, 'load': {}, 'shots': []}


def axe(page, name):
    page.add_script_tag(url=AXE)
    v = page.evaluate("async () => (await axe.run(document, { runOnly: ['wcag2a', 'wcag2aa'] })).violations.map(v => ({ id: v.id, n: v.nodes.length, where: v.nodes[0].target.join(' ') }))")
    report['axe'][name] = v
    print('axe', name, v or '없음')


def shot(page, name, full=False, el=None):
    path = OUT / f'{len(report["shots"]) + 1:02d}_{name}.png'
    (el or page).screenshot(path=str(path), **({} if el else {'full_page': full}))
    report['shots'].append(path.name)


def settle(page, ms=900):
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(ms)


def click_text(page, text):
    page.get_by_text(text, exact=True).first.click()


with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome')

    # ── 1) 첫 화면 내려받는 양·시간 (캐시 없음, 빠른 4G 정도로 제한) ──
    for route, label in [('/', '첫 화면'), ('/result2', '개인 결과(모델 포함)')]:
        ctx = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        ctx.add_init_script(SEED)
        page = ctx.new_page()
        cdp = ctx.new_cdp_session(page)
        cdp.send('Network.enable')
        cdp.send('Network.emulateNetworkConditions', {'offline': False, 'latency': 150, 'downloadThroughput': 9_000_000 / 8, 'uploadThroughput': 750_000 / 8})
        sizes = {}
        page.on('response', lambda r, sizes=sizes: sizes.__setitem__(r.url, len(r.body()) if r.ok and r.request.method == 'GET' else 0))
        t0 = time.time()
        page.goto(BASE + route)
        page.wait_for_load_state('networkidle')
        elapsed = time.time() - t0
        own = {u: s for u, s in sizes.items() if u.startswith(BASE)}
        report['load'][label] = {
            'seconds': round(elapsed, 2),
            'own_kb': round(sum(own.values()) / 1024),
            'files': sorted(((u.replace(BASE, ''), round(s / 1024)) for u, s in own.items()), key=lambda x: -x[1])[:8],
        }
        print('load', label, report['load'][label])
        ctx.close()

    # ── 2) 화면 돌기: 접근성 + 캡처 (아이폰 13/14 크기, 3배 해상도) ──
    ctx = browser.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=3, is_mobile=True, has_touch=True, locale='ko-KR')
    ctx.add_init_script(SEED)
    page = ctx.new_page()

    page.goto(BASE + '/')
    settle(page, 1500)
    axe(page, '시작')
    shot(page, '시작')

    page.goto(BASE + '/survey?q=strength_days')
    settle(page)
    axe(page, '설문(통계 말풍선)')
    shot(page, '설문_통계말풍선')

    page.goto(BASE + '/reveal')
    page.wait_for_timeout(700)
    shot(page, '공개_분석중')
    page.wait_for_timeout(2400)
    settle(page, 700)
    axe(page, '공개 카드')
    for i in range(6):
        shot(page, f'공개_카드{i + 1}')
        if i < 5:
            page.get_by_role('button', name='다음').click()
            page.wait_for_timeout(700)

    page.goto(BASE + '/result')
    settle(page, 1200)
    axe(page, '유형 결과')
    shot(page, '유형결과_첫화면')
    shot(page, '유형결과_전체', full=True)
    page.get_by_role('tab', name='평균과 비교').click()
    page.wait_for_timeout(500)
    axe(page, '유형 결과(평균과 비교)')
    shot(page, '유형결과_평균비교', el=page.locator('section', has=page.get_by_role('tab', name='평균과 비교')))
    shot(page, '유형결과_내유형위치', el=page.locator('section', has_text='내 유형 위치'))
    page.get_by_role('button', name='이미지').click()
    page.wait_for_timeout(1800)
    shot(page, '유형결과_공유이미지')
    page.keyboard.press('Escape')

    page.goto(BASE + '/types')
    settle(page)
    axe(page, '유형 모두 보기')
    shot(page, '유형모두보기', full=True)

    page.goto(BASE + '/result2')
    settle(page, 1800)
    axe(page, '개인 결과')
    shot(page, '개인결과_첫화면')
    shot(page, '개인결과_전체', full=True)

    page.goto(BASE + '/simulate')
    settle(page, 1500)
    for name in ['운동을 주 2시간 반 이상', '우유·유제품 하루 1번']:
        page.get_by_role('button', name=name).click()
        page.wait_for_timeout(300)
    page.wait_for_timeout(600)
    axe(page, '시뮬레이터')
    shot(page, '시뮬레이터', full=True)

    page.goto(BASE + '/supplements')
    settle(page, 1800)
    axe(page, '건강기능식품')
    shot(page, '건강기능식품')

    page.goto(BASE + '/my-supplements')
    settle(page, 1800)
    axe(page, '내가 먹는 제품')
    shot(page, '내가먹는제품', full=True)
    page.get_by_role('button', name='약사 상담 메모 만들기').click()
    page.get_by_label('약사에게 물어보고 싶은 것').fill('혈압약을 먹고 있는데 마그네슘을 같이 먹어도 되나요?')
    page.wait_for_timeout(2000)
    axe(page, '약사 상담 메모')
    shot(page, '약사상담메모')
    # 메모 이미지 원본도 저장
    src = page.locator('img[alt="약사 상담 메모 미리보기"]').get_attribute('src')
    data = page.evaluate("async (u) => { const b = await (await fetch(u)).blob(); return Array.from(new Uint8Array(await b.arrayBuffer())) }", src)
    (OUT / f'{len(report["shots"]) + 1:02d}_약사상담메모_원본.png').write_bytes(bytes(data))
    report['shots'].append('약사상담메모_원본.png')

    browser.close()

server.shutdown()
(OUT / '점검결과.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print('캡처', len(report['shots']), '장 →', OUT)
