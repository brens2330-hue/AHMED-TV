# نشر AHMED-TV على Railway

هذا المشروع مهيأ لـRailway فقط. توجد خدمتان منفصلتان من نفس الكود حتى يبقى الـAPI متاحاً ويعمل البوت طوال الوقت:

## 1) رفع الملفات
ارفع محتويات هذه الحزمة إلى GitHub خاص أو انشرها من Railway CLI. اجعل `channel_service` هو Root Directory للمشروع، أو استخدم محتويات مجلد الحزمة كجذر المستودع. لا ترفع `.env` ولا التوكن إلى GitHub؛ أضف القيم في Railway → Service → Variables.

## 2) خدمة الـAPI (Web Service)
أنشئ خدمة Railway من المستودع، Root Directory: `channel_service`. الإعداد `railway.toml` يبدأ FastAPI تلقائياً على `$PORT` ويستخدم `/api/health` لفحص الجاهزية. إن لم يكتشف Railway الملف، ضع Start Command يدوياً:
`python -m uvicorn main:app --host 0.0.0.0 --port $PORT`

أنشئ Public Domain لخدمة الـAPI عبر Railway، وخذ عنوان HTTPS. أضف متغيرات:
- `API_ADMIN_TOKEN` = مفتاح سري قوي عشوائي.
- `DATABASE_PATH` = مسار volume الدائم مثلاً `/data/channels.db`.

أضف Railway Volume إلى هذه الخدمة وثبته عند `/data` حتى تبقى قاعدة SQLite بعد إعادة النشر. من إعدادات الخدمة، تأكد أن مسار ملف DB على volume.

## 3) خدمة البوت (Worker دائم)
أنشئ Railway Service ثانية من نفس المستودع (Root Directory نفسه `channel_service`). اجعل Start Command:
`python bot.py`

أضف إلى هذه الخدمة متغيرات:
- `BOT_TOKEN` = توكن BotFather.
- `ADMIN_ID` = رقم Telegram للمسؤول، مثلاً `1697375758`.
- `API_ADMIN_TOKEN` = نفس القيمة حرفياً الموضوعة في خدمة API.
- `API_BASE_URL` = عنوان API الداخلي لـRailway إن كان متاحاً (مثل `http://اسم-خدمة-api.railway.internal:8000`) أو عنوان HTTPS العام.

اجعل Worker بلا Healthcheck HTTP، وسيعيد Railway تشغيله عند تعطل العملية. لا تضبط replica متعددة للبوت الذي يستخدم polling كي لا يحدث تعارض في استقبال تحديثات Telegram (409 Conflict).

## المتغيرات واستخدام .env
في Railway استخدم متغيرات الخدمة؛ لا تحتاج إلى رفع `.env`. محلياً انسخ `.env.example` إلى `.env` فقط للتطوير.

## اختبار بعد النشر
1. افتح `https://<API-domain>/api/health` وتوقع `{"status":"ok"}`.
2. راجع Logs للـWorker؛ يجب أن ترى رسالة بدء polling، ولا تظهر أخطاء `Unauthorized` أو `Conflict`.
3. افتح محادثة البوت في Telegram وأرسل `/start`. يتحقق البوت من أن المرسل يطابق `ADMIN_ID` ثم يرد بلوحة الإدارة.
4. في حال عدم الرد، تحقق من تطابق BOT_TOKEN ومن عدم تشغيل polling على نسخة ثانية.

تم الإبقاء على خصائص إضافة/حذف/قائمة/روابط القنوات. البوت يتصل بقاعدة SQLite عبر API، لذا Worker لا يحتاج لفتح قاعدة البيانات مباشرة.
