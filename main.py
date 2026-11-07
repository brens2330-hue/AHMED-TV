"""LANA TV channels API. Public read; mutations require X-Admin-Token."""
import os, sqlite3
import asyncio, logging
from contextlib import contextmanager, asynccontextmanager
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel, Field, HttpUrl
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
DB_PATH = Path(os.getenv("DATABASE_PATH", str(ROOT / "channels.db")))
ADMIN_TOKEN = os.getenv("API_ADMIN_TOKEN", "")
if not ADMIN_TOKEN and os.getenv("BOT_TOKEN"):
    import hashlib
    ADMIN_TOKEN = hashlib.sha256(("ahmed-tv:" + os.environ["BOT_TOKEN"]).encode()).hexdigest()
    os.environ["API_ADMIN_TOKEN"] = ADMIN_TOKEN
os.environ.setdefault("API_BASE_URL", f"http://127.0.0.1:{os.getenv('PORT', '8000')}")
log = logging.getLogger("ahmed-tv")

@asynccontextmanager
async def lifespan(_app):
    """Run the Telegram bot (long polling) in the same process as the API."""
    bot = None
    if os.getenv("BOT_TOKEN") and os.getenv("ADMIN_ID", os.getenv("TELEGRAM_ADMIN_ID")):
        from bot import build_application
        bot = build_application()
        await bot.initialize(); await bot.start()
        await bot.updater.start_polling(drop_pending_updates=False)
        log.info("Telegram polling started")
    else:
        log.error("BOT_TOKEN/ADMIN_ID missing: bot NOT started")
    try:
        yield
    finally:
        if bot:
            await bot.updater.stop(); await bot.stop(); await bot.shutdown()

app = FastAPI(title="AHMED-TV Channels API", version="1.0.0", lifespan=lifespan)

@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""CREATE TABLE IF NOT EXISTS channels (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          url TEXT NOT NULL,
          image_url TEXT,
          created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        )""")
        conn.commit()
        yield conn
    finally: conn.close()

class ChannelIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    url: HttpUrl
    image_url: Optional[HttpUrl] = None

def admin_auth(x_admin_token: Optional[str] = Header(default=None)):
    if not ADMIN_TOKEN or not x_admin_token or x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

def serialize(row):
    return dict(row)

@app.get('/api/health')
def health(): return {"status":"ok"}

@app.get('/api/channels')
def get_channels():
    with db() as c: rows = c.execute('SELECT id,name,url,image_url,created_at FROM channels ORDER BY id DESC').fetchall()
    return {"channels":[serialize(r) for r in rows], "count":len(rows)}

@app.post('/api/channels', status_code=201, dependencies=[Depends(admin_auth)])
def add_channel(item: ChannelIn):
    name = item.name.strip()
    if not name: raise HTTPException(422, detail="Name cannot be blank")
    with db() as c:
        cur = c.execute('INSERT INTO channels(name,url,image_url) VALUES(?,?,?)', (name,str(item.url),str(item.image_url) if item.image_url else None))
        row = c.execute('SELECT id,name,url,image_url,created_at FROM channels WHERE id=?',(cur.lastrowid,)).fetchone(); c.commit()
    return serialize(row)

@app.delete('/api/channels/{channel_id}', dependencies=[Depends(admin_auth)])
def delete_channel(channel_id:int):
    with db() as c:
        cur=c.execute('DELETE FROM channels WHERE id=?',(channel_id,)); c.commit()
    if cur.rowcount == 0: raise HTTPException(404, detail="Channel not found")
    return {"deleted":True,"id":channel_id}
