import csv,json,hashlib,shutil,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];source=R/'source/stage9_final.csv'
rows=list(csv.DictReader(source.open(encoding='utf-8-sig',newline='')))
categories=[('magnesium','마그네슘'),('vitamin_b','비타민 B군'),('vitamin_c','비타민 C'),('vitamin_d','비타민 D'),('fiber','식이섬유'),('zinc','아연'),('folate','엽산'),('multi_balance','종합비타민 (균형형)'),('multi_energy','종합비타민 (피로회복형)'),('iron','철'),('calcium','칼슘')]
catmap={label:key for key,label in categories}
products={};links=[];seen=set()
def num(s): return None if not s.strip() else float(s)
def norm(s): return s.replace('\\r\\n','\n').replace('\\n','\n').replace('\r\n','\n')
for r in rows:
 pid=r['품목제조신고번호']; assert pid.isdigit()
 p={'product_id':pid,'product_name':r['제품명'],'manufacturer':r['업체명'],'form':r['제형'],'target':r['대상'],'intake_label':norm(r['1일 섭취량']),'ingredient_count':int(r['원재료 수']),'caution_ingredient_label':norm(r['주의 원료']) or None,'functionality_text':norm(r['기능성']),'cautions_text':norm(r['섭취 시 주의사항'])}
 if pid in products: assert products[pid]==p
 else: products[pid]=p
 key=(catmap[r['영양소']],r['대상'],pid); assert key not in seen;seen.add(key)
 links.append({'category_id':key[0],'target':key[1],'product_id':pid,'source_order':int(r['순서']),'source_product_type':r['구분'],'daily_amount':num(r['1일 함량']),'daily_unit':r['1일 함량 단위'] or None,'daily_reference_percent':num(r['기준치 대비(%)'])})
for key in set((x['category_id'],x['target']) for x in links):
 orders=sorted(x['source_order'] for x in links if (x['category_id'],x['target'])==key);assert orders==list(range(1,len(orders)+1))
catmeta=[{'category_id':k,'label':label,'order':i,'connection_kind':'information_only' if k in ['vitamin_d','multi_balance','multi_energy'] else 'model_nutrient'} for i,(k,label) in enumerate(categories)]
catalog={'catalog_version':'nutrition-products-2026-11-04-final-stage9','bridge_version':'1.0.0','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_status':'user_confirmed_final_despite_original_filename','product_count':len(products),'link_count':len(links),'targets':['일반','남성','여성','시니어'],'categories':catmeta,'products':products,'links':links}
(R/'data/nutritionProducts.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
# Source CSV is already retained; leave it unchanged.
meta={'product_count':len(products),'link_count':len(links),'source_sha256':catalog['source_sha256'],'counts':[{'category_id':k,'label':label,'by_target':dict(collections.Counter(x['target'] for x in links if x['category_id']==k))} for k,label in categories]}
(R/'data/catalog_summary.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'products':len(products),'links':len(links),'categories':len(categories)},ensure_ascii=False))
