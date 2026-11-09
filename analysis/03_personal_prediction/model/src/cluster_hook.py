"""Attach an independently computed web cluster without guessing G-to-web IDs."""
import json
from pathlib import Path
SOURCE='bigskyyang/web/src/data/nbti12.json'
def attach_web_cluster(cluster_id=None,nbti12_path=None):
 if cluster_id is None:return {'status':'awaiting_web_cluster','cluster_id':None,'source':SOURCE}
 if nbti12_path is None:raise ValueError('Provide the actual nbti12.json path to validate the web cluster ID')
 data=json.loads(Path(nbti12_path).read_text(encoding='utf-8'));ids=set()
 def visit(obj):
  if isinstance(obj,dict):
   ids.update(k for k in obj if isinstance(k,str) and len(k)==2 and k[0].isupper() and k[1] in '123')
   for k in ('id','cluster_id','type_id','code'):
    if isinstance(obj.get(k),str):ids.add(obj[k])
   for v in obj.values():visit(v)
  elif isinstance(obj,list):
   for v in obj:visit(v)
 visit(data)
 if cluster_id not in ids:raise ValueError(f'Unknown cluster ID in supplied nbti12.json: {cluster_id!r}')
 return {'status':'attached_from_web','cluster_id':cluster_id,'source':SOURCE}
