# تشغيل LANA TV Channels على الاستضافة

## الملفات المطلوب رفعها
ارفع مجلد `channel_service` كاملاً إلى استضافة Python. يحتوي على `main.py` و`bot.py` و`api_client.py` و`requirements.txt` و`.env`. لا ترفع ملف `.env` إلى GitHub أو مستودع عام، ولا ترسله في مجموعات عامة. قاعدة البيانات `channels.db` تنشأ تلقائياً؛ استخدم قرصاً دائماً (Persistent Disk/Volume) وحدد `DATABASE_PATH` لمسار دائم حتى لا تضيع القنوات عند إعادة تشغيل الاستضافة.

## خدمة الويب (API)
- أمر تثبيت الحزم: `pip install -r requirements.txt`
- أمر التشغيل: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- نقطة الصحة: `/api/health`
- بعد نشر الخدمة احصل على عنوان HTTPS العام.

## عامل البوت
شغّل خدمة/Worker مستقلة على نفس الاستضافة ومن نفس مجلد الملفات:
- أمر التثبيت: `pip install -r requirements.txt`
- أمر التشغيل: `python bot.py`

يجب أن يكون `API_BASE_URL` في `.env` عنوان خدمة الـAPI القابل للوصول من عامل البوت (عنوان داخلي إن كانت الاستضافة تدعمه، أو عنوان HTTPS العام).

## ربط تطبيق Android
في `app/src/main/java/com/lanatv/app/ChannelsRepository.java` استبدل `https://YOUR-API-HOST.example.com/api/channels` بعنوان API العام الحقيقي، ثم أعد بناء APK. التطبيق يحتاج GET فقط ولا يحتاج أي أسرار. لا تضف `API_ADMIN_TOKEN` أو Bot Token إلى التطبيق.

## الإدارة والأمان
الإضافة والحذف عبر API محميتان بـ`X-Admin-Token` (المفتاح محفوظ في `.env`). البوت يقبل المسؤول المحدد فقط. لا تعرّض المنفذ عبر HTTP غير مشفر، ولا تفعّل CORS مفتوحاً بلا حاجة. إذا ظهر Bot Token في سجل أو مشاركة عامة، أبطله من BotFather وأصدر بديلاً ثم حدّث `.env`.
