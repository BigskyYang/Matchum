"""General food information; no disease, supplement, or dosage recommendations."""
FOODS={
 'protein':('단백질',['콩·두부','달걀','생선','육류']),
 'calcium':('칼슘',['우유·요구르트','칼슘 강화 식품','칼슘 함유 두부']),
 'magnesium':('마그네슘',['콩류','견과류','통곡물']),
 'iron':('철',['육류','콩류','철 강화 식품']),
 'zinc':('아연',['육류','해산물','콩류']),
 'phosphorus':('인',['유제품','콩류','생선','달걀']),
 'vitamin_a':('비타민 A',['당근','단호박','녹색 잎채소']),
 'vitamin_b1':('비타민 B1',['돼지고기','콩류','통곡물']),
 'vitamin_b2':('비타민 B2',['우유·요구르트','달걀','콩류']),
 'folate':('엽산',['녹색 잎채소','콩류']),
 'vitamin_c':('비타민 C',['과일','파프리카','브로콜리']),
 'fiber':('식이섬유',['통곡물','콩류','채소','과일']),
 'potassium':('칼륨',['채소','과일','콩류']),
 'sodium_excess':('나트륨',[])}
def build_food_guidance(lifestyle,habitual):
 items=[]
 for n,ls in lifestyle.items():
  ffq=habitual.get(n) if habitual else None
  chosen=ffq if ffq else ls
  state='review_food_sources' if chosen['risk_band']=='High' else 'general_information'
  name,foods=FOODS[n]
  target='above_CDRR' if n=='sodium_excess' else ('below_AI' if n in ('fiber','potassium') else 'below_EAR')
  message='나트륨 섭취를 점검할 때는 국물·소스·가공식품의 영양표시를 살펴볼 수 있습니다.' if n=='sodium_excess' else f'{name}을 제공하는 일반적인 식품 예시입니다. 개인의 필요 섭취량이나 추가 섭취 필요를 확정한 결과는 아닙니다.'
  items.append({'nutrient_id':n,'nutrient_name':name,'target':target,'display_state':state,'food_examples':foods,'message':message})
 return items
