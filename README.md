<div align="center">

# 🥗 NBTI 유형 검사

### 생활습관 분석 기반 맞춤 영양 개선 서비스 · Nutrient + MBTI

<br>

![team](https://img.shields.io/badge/2조-머신2러닝-7C5CFF?style=for-the-badge)
![period](https://img.shields.io/badge/기간-2026.10.29_~_11.10-20C997?style=for-the-badge)
![web](https://img.shields.io/badge/Vite_+_React-웹앱-646CFF?style=for-the-badge)

**[🔗 서비스 바로가기 · matchum.vercel.app](https://matchum.vercel.app)**

<br>

[프로젝트 소개](#-프로젝트-소개) · [핵심 결과](#-핵심-결과) · [분석 흐름](#-분석-흐름) · [폴더 구조](#-폴더-구조) · [실행 방법](#-실행-방법) · [팀원](#-팀원) · [발표자료](#-발표자료)

</div>

<br>

## 📌 프로젝트 소개

건강 정보는 많지만, 내 생활에서 무엇부터 살펴봐야 할지는 잘 보이지 않습니다. 이 프로젝트는 국민건강영양조사(KNHANES) 2022–2024 성인 **15,062명**의 생활습관과 식사 기록을 머신러닝으로 분석해, **혈액검사나 식단 기록 없이 설문만으로** 먼저 살펴볼 영양소와 실천할 습관을 안내합니다.

| 단계 | 누구에게 | 보여 주는 것 |
| :---: | :---: | --- |
| ① 유형 결과 | 모든 사용자 | 12개 생활습관 유형 중 내 유형, 같은 유형에서 부족하기 쉬운 영양소, 이번 주 해볼 습관 |
| ② 개인 결과 | 원하는 사용자 | 내 응답으로 예측한 영양소별 기준 미만·초과 가능성, 챙겨 먹으면 좋은 음식, 관련 건강기능식품 표시 정보, 약사 상담 메모 |

> 결과는 조사 참여자와 비교한 경향 안내이며 의료적 진단이나 처방을 대신하지 않습니다. 건강기능식품은 순위·가격 없이 식약처 표시 정보만 보여 줍니다.

<br>

## 📊 핵심 결과

| 항목 | 결과 |
| --- | --- |
| 분석 대상 | 국민건강영양조사 2022–2024 성인 15,062명 |
| 생활습관 유형 | 7개 지표 → PCA 5차원 → K-medoids 대분류 4개 × 세부 3개 = **12개 유형** (같은 응답이면 항상 같은 유형, 웹 재배정 일치율 100%) |
| 유형별 부족 영양소 | 유형을 더하면 성별·나이만 쓸 때보다 15개 중 **13개 영양소**에서 예측이 좋아짐 (2024년 평가, AUC +0.014~+0.040). 안내 항목이 2024년에도 같은 성별·나이보다 **1.09배** 더 부족 |
| 개인 영양 위험 예측 | 생활습관 모델 평균 AUC **0.664** (영양소 14개), 평소 식사 모델 **0.877** (영양소 10개, 19~64세) |
| 건강기능식품 정보 | 식약처 신고 19,165개 → 9단계 규칙 필터 → **2,227개** (상한섭취량 초과·어린이·임산부 대상 0개), 생활기능 영양제 4,577개 → **2,188개** |
| 웹 서비스 | 서버 없이 휴대폰 안에서 계산, 웹 계산 = 파이썬 결과 (군집 100%, 확률 차이 1e-8 미만) |

자세한 내용은 [최종 결과 보고서](docs/report/최종결과보고서_iM양식.pdf)에 있습니다.

<br>

## 🧭 분석 흐름

```mermaid
flowchart LR
    A[🗂 국민건강영양조사<br>2022–2024] --> B[🧩 생활습관 군집화<br>12개 유형]
    B --> C[🥦 유형별 부족 영양소<br>2024년 검증]
    A2[🗂 국민건강영양조사<br>2012–2016 FFQ] --> D[🔍 개인 영양 위험 예측<br>생활습관·평소 식사 모델]
    A --> D
    E[💊 식약처 건강기능식품<br>신고 자료] --> F[🧹 9단계 분류·필터링]
    C --> W[📱 NBTI 웹앱]
    D --> W
    F --> W
```

| 단계 | 폴더 | 담당 |
| --- | --- | --- |
| 1. 생활습관 군집화 | [`analysis/01_clustering`](analysis/01_clustering) | 최지연 (검증·보완 양대천) |
| 2. 유형별 부족 영양소 | [`analysis/02_type_nutrition`](analysis/02_type_nutrition) | 전유환 |
| 3. 개인 영양 위험 예측 | [`analysis/03_personal_prediction`](analysis/03_personal_prediction) | 황재준 |
| 4. 건강기능식품 분류·필터링 | [`analysis/04_supplements`](analysis/04_supplements) | 박준혁 |
| 5. 웹 서비스 | [`web`](web), [`scripts`](scripts) | 양대천 |

<br>

## 📁 폴더 구조

```
.
├── analysis/
│   ├── 01_clustering/            # 생활습관 군집화 (K-medoids 2단계, 귀무 검정, 검증)
│   │   └── validation/           #   웹 설문 기준 비교안·규칙 대조군·경계 분석, 웹용 12유형 모델
│   ├── 02_type_nutrition/        # 유형별 부족 영양소 예측과 화면 표시 규칙
│   ├── 03_personal_prediction/   # 개인 영양 위험 예측 모델 패키지, 비타민 D 안내
│   └── 04_supplements/           # 건강기능식품 9단계 분류·필터링, 제품 연결 규칙
├── web/                          # NBTI 웹앱 (Vite + React + Tailwind CSS)
├── scripts/                      # 분석 결과 → 웹 데이터 변환, 화면 캡처, 슬라이드 이미지 변환
└── docs/
    ├── presentation/             # 최종 발표자료 (PDF, 슬라이드 이미지)
    ├── report/                   # 최종 결과 보고서, 단계별 개발 설명서
    ├── planning/                 # 프로젝트 기획서
    └── daily_report/             # 일일 진행 일지
```

국민건강영양조사 원자료와 사람 단위 결과(`*.csv`, `*.xlsx`, `*.sas7bdat`)는 이용 규정에 따라 올리지 않습니다. 분석을 다시 돌리려면 원자료를 받아 각 폴더 README에 적힌 위치에 두세요 (원시데이터는 `analysis/raw/`).

<br>

## 🛠 실행 방법

**웹앱**

```bash
cd web
npm install
npm run dev      # 개발 서버 (http://localhost:5173)
npm test         # 응답 변환·유형 판정·결과 계산 + 분석 결과와의 일치 점검
npm run build    # 배포용 빌드 (dist/)
```

**웹 데이터 다시 만들기** (저장소 루트에서)

| 명령 | 하는 일 |
| --- | --- |
| `python scripts/export_nutrition_models.py` | 개인 예측 모델 → `web/src/data/nutritionModels.json` |
| `python scripts/build_nutrient_cells.py` | 유형별 부족 영양소 결과 → `web/src/data/nutrientCells.json` |
| `python scripts/build_supplement_catalog.py` | 건강기능식품 목록 → `web/src/data/supplementCatalog.json` |
| `python scripts/build_survey_stats.py` | 설문 통계 말풍선용 비율 (원자료 필요) |
| `python scripts/export_slides.py` | `docs/presentation/slides.pdf` → README용 슬라이드 이미지 |

**배포**: Vercel (Root Directory `web`). `main`에 push하면 자동 배포됩니다.

<br>

## 🧰 기술 스택

| 분야 | 사용 |
| --- | --- |
| 분석 | Python, pandas, numpy·scipy (K-medoids 직접 구현), scikit-learn (PCA·로지스틱 회귀·HistGradientBoosting), statsmodels |
| 웹 | Vite, React, Tailwind CSS, react-router-dom, Vitest |
| 배포 | Vercel |

<br>

## 👥 팀원

| 사진 | 이름 | GitHub | 역할 |
| :---: | :---: | :---: | --- |
| <img src="https://github.com/BigskyYang.png" width="60"> | 양대천<br>(팀장) | [@BigskyYang](https://github.com/BigskyYang) | 기획·일정, 군집 결과 검증(대안 비교·규칙 대조군·경계 분석), 유형 이름·영양 판정 정리, 웹 서비스 설계·구현·배포 |
| <img src="https://github.com/jyjy8940.png" width="60"> | 최지연 | [@jyjy8940](https://github.com/jyjy8940) | 생활습관 변수 전처리, 2단계 K-medoids 모델, k 선택, 귀무 검정·추가 검증, 웹용 군집 모델 |
| <img src="https://github.com/wjsdbghks2-eng.png" width="60"> | 전유환 | [@wjsdbghks2-eng](https://github.com/wjsdbghks2-eng) | 부족 여부 정의(KDRI), 영양소 15개 부족 확률 모델, 2024 검증·민감도·개선 실험, 화면 표시 규칙, 최종 보고서 |
| <img src="https://github.com/hwangjj3510.png" width="60"> | 황재준 | [@hwangjj3510](https://github.com/hwangjj3510) | 데이터 전처리·설문 설계, 생활습관 모델·평소 식사 모델, 웹 연결 규칙, 비타민 D 안내 |
| <img src="https://github.com/junhyeok-1.png" width="60"> | 박준혁 | [@junhyeok-1](https://github.com/junhyeok-1) | 식약처 제품 자료 1~9단계 분류·필터링·점수, 상한섭취량 정리, 웹용 제품 목록 |

<br>

## 📚 데이터 출처

- 질병관리청 국민건강영양조사 원시자료 (2012–2016, 2022–2024)
- 식품의약품안전처 건강기능식품 품목제조 신고사항
- 보건복지부·한국영양학회 2025 한국인 영양소 섭취기준

<br>

## 🎤 발표자료

[📄 발표자료 PDF 내려받기](docs/presentation/slides.pdf) · 본편 71장, 참고자료 20장

[표지 · 도입](#표지--도입) · [01 데이터 소개 및 전처리](#01-데이터-소개-및-전처리) · [02 생활습관 유형 분석](#02-생활습관-유형-분석) · [03 유형별 영양 특성 분석](#03-유형별-영양-특성-분석) · [04 개인별 영양 위험 예측](#04-개인별-영양-위험-예측) · [05 맞춤 개선안 및 영양 정보 제공](#05-맞춤-개선안-및-영양-정보-제공) · [06 웹 서비스 구현](#06-웹-서비스-구현) · [07 시연](#07-시연) · [08 의의 및 한계](#08-의의-및-한계) · [참고자료](#참고자료)

### 표지 · 도입

<img src="docs/presentation/slides/slide-01.jpg" alt="슬라이드 1" width="100%">

<img src="docs/presentation/slides/slide-02.jpg" alt="슬라이드 2" width="100%">

<img src="docs/presentation/slides/slide-03.jpg" alt="슬라이드 3" width="100%">

<img src="docs/presentation/slides/slide-04.jpg" alt="슬라이드 4" width="100%">

<img src="docs/presentation/slides/slide-05.jpg" alt="슬라이드 5" width="100%">

<img src="docs/presentation/slides/slide-06.jpg" alt="슬라이드 6" width="100%">

<img src="docs/presentation/slides/slide-07.jpg" alt="슬라이드 7" width="100%">

### 01 데이터 소개 및 전처리

<img src="docs/presentation/slides/slide-08.jpg" alt="슬라이드 8" width="100%">

<img src="docs/presentation/slides/slide-09.jpg" alt="슬라이드 9" width="100%">

<img src="docs/presentation/slides/slide-10.jpg" alt="슬라이드 10" width="100%">

<img src="docs/presentation/slides/slide-11.jpg" alt="슬라이드 11" width="100%">

### 02 생활습관 유형 분석

<img src="docs/presentation/slides/slide-12.jpg" alt="슬라이드 12" width="100%">

<img src="docs/presentation/slides/slide-13.jpg" alt="슬라이드 13" width="100%">

<img src="docs/presentation/slides/slide-14.jpg" alt="슬라이드 14" width="100%">

<img src="docs/presentation/slides/slide-15.jpg" alt="슬라이드 15" width="100%">

<img src="docs/presentation/slides/slide-16.jpg" alt="슬라이드 16" width="100%">

<img src="docs/presentation/slides/slide-17.jpg" alt="슬라이드 17" width="100%">

<img src="docs/presentation/slides/slide-18.jpg" alt="슬라이드 18" width="100%">

<img src="docs/presentation/slides/slide-19.jpg" alt="슬라이드 19" width="100%">

### 03 유형별 영양 특성 분석

<img src="docs/presentation/slides/slide-20.jpg" alt="슬라이드 20" width="100%">

<img src="docs/presentation/slides/slide-21.jpg" alt="슬라이드 21" width="100%">

<img src="docs/presentation/slides/slide-22.jpg" alt="슬라이드 22" width="100%">

<img src="docs/presentation/slides/slide-23.jpg" alt="슬라이드 23" width="100%">

<img src="docs/presentation/slides/slide-24.jpg" alt="슬라이드 24" width="100%">

<img src="docs/presentation/slides/slide-25.jpg" alt="슬라이드 25" width="100%">

<img src="docs/presentation/slides/slide-26.jpg" alt="슬라이드 26" width="100%">

<img src="docs/presentation/slides/slide-27.jpg" alt="슬라이드 27" width="100%">

<img src="docs/presentation/slides/slide-28.jpg" alt="슬라이드 28" width="100%">

<img src="docs/presentation/slides/slide-29.jpg" alt="슬라이드 29" width="100%">

<img src="docs/presentation/slides/slide-30.jpg" alt="슬라이드 30" width="100%">

<img src="docs/presentation/slides/slide-31.jpg" alt="슬라이드 31" width="100%">

<img src="docs/presentation/slides/slide-32.jpg" alt="슬라이드 32" width="100%">

### 04 개인별 영양 위험 예측

<img src="docs/presentation/slides/slide-33.jpg" alt="슬라이드 33" width="100%">

<img src="docs/presentation/slides/slide-34.jpg" alt="슬라이드 34" width="100%">

<img src="docs/presentation/slides/slide-35.jpg" alt="슬라이드 35" width="100%">

<img src="docs/presentation/slides/slide-36.jpg" alt="슬라이드 36" width="100%">

<img src="docs/presentation/slides/slide-37.jpg" alt="슬라이드 37" width="100%">

<img src="docs/presentation/slides/slide-38.jpg" alt="슬라이드 38" width="100%">

<img src="docs/presentation/slides/slide-39.jpg" alt="슬라이드 39" width="100%">

<img src="docs/presentation/slides/slide-40.jpg" alt="슬라이드 40" width="100%">

### 05 맞춤 개선안 및 영양 정보 제공

<img src="docs/presentation/slides/slide-41.jpg" alt="슬라이드 41" width="100%">

<img src="docs/presentation/slides/slide-42.jpg" alt="슬라이드 42" width="100%">

<img src="docs/presentation/slides/slide-43.jpg" alt="슬라이드 43" width="100%">

<img src="docs/presentation/slides/slide-44.jpg" alt="슬라이드 44" width="100%">

<img src="docs/presentation/slides/slide-45.jpg" alt="슬라이드 45" width="100%">

<img src="docs/presentation/slides/slide-46.jpg" alt="슬라이드 46" width="100%">

<img src="docs/presentation/slides/slide-47.jpg" alt="슬라이드 47" width="100%">

<img src="docs/presentation/slides/slide-48.jpg" alt="슬라이드 48" width="100%">

<img src="docs/presentation/slides/slide-49.jpg" alt="슬라이드 49" width="100%">

<img src="docs/presentation/slides/slide-50.jpg" alt="슬라이드 50" width="100%">

<img src="docs/presentation/slides/slide-51.jpg" alt="슬라이드 51" width="100%">

<img src="docs/presentation/slides/slide-52.jpg" alt="슬라이드 52" width="100%">

<img src="docs/presentation/slides/slide-53.jpg" alt="슬라이드 53" width="100%">

<img src="docs/presentation/slides/slide-54.jpg" alt="슬라이드 54" width="100%">

<img src="docs/presentation/slides/slide-55.jpg" alt="슬라이드 55" width="100%">

<img src="docs/presentation/slides/slide-56.jpg" alt="슬라이드 56" width="100%">

### 06 웹 서비스 구현

<img src="docs/presentation/slides/slide-57.jpg" alt="슬라이드 57" width="100%">

<img src="docs/presentation/slides/slide-58.jpg" alt="슬라이드 58" width="100%">

<img src="docs/presentation/slides/slide-59.jpg" alt="슬라이드 59" width="100%">

<img src="docs/presentation/slides/slide-60.jpg" alt="슬라이드 60" width="100%">

<img src="docs/presentation/slides/slide-61.jpg" alt="슬라이드 61" width="100%">

<img src="docs/presentation/slides/slide-62.jpg" alt="슬라이드 62" width="100%">

<img src="docs/presentation/slides/slide-63.jpg" alt="슬라이드 63" width="100%">

<img src="docs/presentation/slides/slide-64.jpg" alt="슬라이드 64" width="100%">

<img src="docs/presentation/slides/slide-65.jpg" alt="슬라이드 65" width="100%">

### 07 시연

<img src="docs/presentation/slides/slide-66.jpg" alt="슬라이드 66" width="100%">

### 08 의의 및 한계

<img src="docs/presentation/slides/slide-67.jpg" alt="슬라이드 67" width="100%">

<img src="docs/presentation/slides/slide-68.jpg" alt="슬라이드 68" width="100%">

<img src="docs/presentation/slides/slide-69.jpg" alt="슬라이드 69" width="100%">

<img src="docs/presentation/slides/slide-70.jpg" alt="슬라이드 70" width="100%">

<img src="docs/presentation/slides/slide-71.jpg" alt="슬라이드 71" width="100%">

### 참고자료

<details>
<summary>참고자료 20장 펼치기 (이론 설명·추가 근거)</summary>
<br>

<img src="docs/presentation/slides/slide-72.jpg" alt="슬라이드 72" width="100%">

<img src="docs/presentation/slides/slide-73.jpg" alt="슬라이드 73" width="100%">

<img src="docs/presentation/slides/slide-74.jpg" alt="슬라이드 74" width="100%">

<img src="docs/presentation/slides/slide-75.jpg" alt="슬라이드 75" width="100%">

<img src="docs/presentation/slides/slide-76.jpg" alt="슬라이드 76" width="100%">

<img src="docs/presentation/slides/slide-77.jpg" alt="슬라이드 77" width="100%">

<img src="docs/presentation/slides/slide-78.jpg" alt="슬라이드 78" width="100%">

<img src="docs/presentation/slides/slide-79.jpg" alt="슬라이드 79" width="100%">

<img src="docs/presentation/slides/slide-80.jpg" alt="슬라이드 80" width="100%">

<img src="docs/presentation/slides/slide-81.jpg" alt="슬라이드 81" width="100%">

<img src="docs/presentation/slides/slide-82.jpg" alt="슬라이드 82" width="100%">

<img src="docs/presentation/slides/slide-83.jpg" alt="슬라이드 83" width="100%">

<img src="docs/presentation/slides/slide-84.jpg" alt="슬라이드 84" width="100%">

<img src="docs/presentation/slides/slide-85.jpg" alt="슬라이드 85" width="100%">

<img src="docs/presentation/slides/slide-86.jpg" alt="슬라이드 86" width="100%">

<img src="docs/presentation/slides/slide-87.jpg" alt="슬라이드 87" width="100%">

<img src="docs/presentation/slides/slide-88.jpg" alt="슬라이드 88" width="100%">

<img src="docs/presentation/slides/slide-89.jpg" alt="슬라이드 89" width="100%">

<img src="docs/presentation/slides/slide-90.jpg" alt="슬라이드 90" width="100%">

<img src="docs/presentation/slides/slide-91.jpg" alt="슬라이드 91" width="100%">

</details>
