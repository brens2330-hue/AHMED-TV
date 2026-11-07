# خدمة قنوات LANA TV

## الملفات
- `main.py`: واجهة FastAPI وSQLite؛ قراءة عامة وكتابة محمية بـ `X-Admin-Token`.
- `bot.py`: بوت Telegram بلوحة المسؤول، مقيد بالمعرّف `ADMIN_ID`.
- `api_client.py`: اتصال البوت بالـAPI.
- `.env`: أسرار التشغيل (أنشئه من `.env.example` ولا تشاركه).
- `channels.db`: ينشأ تلقائياً عند أول طلب.

## التشغيل
1. أنشئ بيئة Python: `python -m venv .venv` ثم فعّلها وثبت `pip install -r requirements.txt`.
2. انسخ `.env.example` إلى `.env`، وضع التوكن الذي أنشأته من BotFather ومفتاح API عشوائياً قوياً.
3. شغّل الخدمة: `uvicorn main:app --host 0.0.0.0 --port 8000`.
4. شغّل البوت في طرفية أخرى: `python bot.py`، أو شغّل الاثنين معاً بـ `python run.py`.
5. انشر API على HTTPS عام، ثم حدّث `API_BASE_URL` في `.env` وأعد تشغيل البوت. ضع عنوان HTTPS المنشور في `CHANNELS_API_BASE_URL` في Android `MainActivity.java` ثم أعد بناء APK.

## الواجهات
`GET /api/channels` عام ويرجع `{channels:[...],count:n}`.
`POST /api/channels` محمي، JSON: `{"name":"...","url":"https://...","image_url":"https://..."}`.
`DELETE /api/channels/{id}` محمي. أرسل المفتاح في `X-Admin-Token`.
`GET /api/health` فحص صحة.

لا تعرض مفتاح الإدارة أو Bot Token داخل التطبيق. لا تستخدم HTTP غير مشفر خارج التطوير. الاتصال المحلي ليس استضافة: يلزم نشر الخدمة بعنوان HTTPS يمكن للهاتف الوصول إليه.
