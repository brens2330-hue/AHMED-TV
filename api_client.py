import os
from pathlib import Path
import httpx
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent/'.env')
BASE=os.getenv('API_BASE_URL') or f"http://127.0.0.1:{os.getenv('PORT') or os.getenv('API_PORT') or '8000'}"
BASE=BASE.rstrip('/')
def headers(): return {'X-Admin-Token':os.getenv('API_ADMIN_TOKEN','')}
async def api_list():
    async with httpx.AsyncClient(timeout=12) as c:
        r=await c.get(BASE+'/api/channels'); r.raise_for_status(); return r.json()['channels']
async def api_add(name,url,image_url=None):
    data={'name':name,'url':url,'image_url':image_url}
    async with httpx.AsyncClient(timeout=12) as c:
        r=await c.post(BASE+'/api/channels',json=data,headers=headers()); r.raise_for_status(); return r.json()
async def api_delete(cid):
    async with httpx.AsyncClient(timeout=12) as c:
        r=await c.delete(f'{BASE}/api/channels/{cid}',headers=headers()); r.raise_for_status(); return r.json()
