// 발표용 웹 화면 캡처 (B안): matchum.vercel.app에 웹 테스트용 예시 응답(src/lib/fixtures.js SAMPLE)을 넣고 찍는다
// 응답은 헤드리스 브라우저의 sessionStorage에만 들어가고 서버로 보내지 않는다
const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');
const os = require('os');

const URL = process.argv[2] || 'http://127.0.0.1:4173';
const OUT = path.join(__dirname, 'img', 'web');
fs.mkdirSync(OUT, { recursive: true });
const SAMPLE = {
  sex: 2, birth_date: '2001-01-01', activity: 2, strength_days: 0, sedentary_min: 480,
  weekday_bed: '22:00', weekday_wake: '07:00', weekend_same: 'no', weekend_bed: '22:00', weekend_wake: '07:00',
  stress: 2, meals: { breakfast: 0, lunch: 3, dinner: 3 }, eating_out: 4,
  smoke_now: 'no', drink_freq: 0, veg: 5, fruit: 3, ffq_meat: 3, ffq_fish: 2, ffq_egg: 3, ffq_legume: 2, ffq_dairy: 2,
};
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless: 'new', userDataDir: fs.mkdtempSync(path.join(os.tmpdir(), 'edge-b-')),
    args: ['--lang=ko-KR', '--no-first-run', '--no-default-browser-check'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  await page.goto(URL + '/', { waitUntil: 'networkidle2' });
  await sleep(1500);
  await page.screenshot({ path: path.join(OUT, 'home.png') });
  await page.goto(URL + '/survey', { waitUntil: 'networkidle2' });
  await sleep(1500);
  await page.screenshot({ path: path.join(OUT, 'survey.png') });
  await page.evaluate((answers) => {
    sessionStorage.setItem('nbti-survey-v4', JSON.stringify({ answers, step: { 1: 0, 2: 0 }, done: { 1: true, 2: true } }));
  }, SAMPLE);
  for (const [route, name] of [['/result', 'result'], ['/result2', 'result2']]) {
    await page.goto(URL + route, { waitUntil: 'networkidle2' });
    await sleep(2500);
    await page.screenshot({ path: path.join(OUT, `${name}_top.png`) });
    await page.screenshot({ path: path.join(OUT, `${name}_full.png`), fullPage: true });
  }
  await page.goto(URL + '/result', { waitUntil: 'networkidle2' });
  await (await page.waitForSelector('main header')).screenshot({path: path.join(OUT, 'r_type.png')});
  await (await page.waitForSelector('main > section')).screenshot({path: path.join(OUT, 'r_signal.png')});
  await browser.close();
  console.log('saved', fs.readdirSync(OUT));
})();
