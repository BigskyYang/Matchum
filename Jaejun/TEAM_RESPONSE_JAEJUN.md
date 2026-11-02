# 재준님 항목 최종 답변

✅ 누수 이슈 해결 및 FFQ 추가 검증 완료

1. `HEI_PROTF`, `HEI_DAIRY`는 정답과 동일한 24시간 회상자료에서 산출된 변수이므로 서비스용 모델에서 제외함.

2. 2022–2024 기준:
- 서비스용 survey-only 모델 평균 AUC: 약 0.665
- HEI 포함 연구용 full-information 모델 평균 AUC: 약 0.792

3. Q25·Q26을 HEI로 임의 변환하지 않고, KNHANES 2012–2016 FFQ 및 ALL 자료를 추가 확보하여 같은 대상자에서 habitual food-frequency 방식으로 검증함.

4. 동일 대상자 incremental validation:
- richer lifestyle only: 평균 AUC 0.664
- + 3개 habitual food-frequency 문항: 0.856
- + 5개 habitual food-frequency 문항: 0.881

5. 최종 mini-FFQ 5문항:
- 육류
- 생선·해산물
- 달걀
- 콩·두부·콩제품
- 우유·유제품

6. 주의:
- 0.881은 2012–2016 FFQ 기반 habitual nutrient-risk 검증 성능이며 현재 2022–2024 웹 서비스 전체 성능으로 직접 해석하지 않음.
- lifestyle model과 mini-FFQ model의 probability는 단순 평균하지 않고 별도 signal로 유지함.
- mini-FFQ 검증 연령은 19–64세이므로 65세 이상은 lifestyle-only fallback을 적용함.
