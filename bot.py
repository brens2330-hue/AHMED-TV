"""Telegram administration bot; only ADMIN_ID can use it."""
import os, logging
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters
from api_client import api_list, api_add, api_delete
load_dotenv(Path(__file__).resolve().parent / '.env')
logging.basicConfig(level=logging.INFO)
ADMIN_ID=int(os.getenv('ADMIN_ID') or '0')
NAME, URL, IMAGE = range(3)
KEYBOARD=ReplyKeyboardMarkup([[KeyboardButton('📺 إضافة قناة'),KeyboardButton('🗑️ مسح قناة')],[KeyboardButton('🔗 روابط القنوات'),KeyboardButton('📋 قائمة القنوات')]],resize_keyboard=True)

def is_admin(u): return bool(u.effective_user and u.effective_user.id==ADMIN_ID)
async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return await update.message.reply_text('غير مصرح لك باستخدام لوحة الإدارة.')
    await update.message.reply_text('مرحباً بك في إدارة قنوات LANA TV.',reply_markup=KEYBOARD)
async def add_start(update,context):
    if not is_admin(update): return
    await update.message.reply_text('أرسل اسم القناة:'); return NAME
async def get_name(update,context):
    if not is_admin(update): return ConversationHandler.END
    context.user_data['name']=update.message.text.strip(); await update.message.reply_text('أرسل رابط القناة أو البث (https://):'); return URL
async def get_url(update,context):
    if not is_admin(update): return ConversationHandler.END
    context.user_data['url']=update.message.text.strip(); await update.message.reply_text('أرسل رابط صورة القناة أو اكتب - للتخطي:'); return IMAGE
async def get_image(update,context):
    if not is_admin(update): return ConversationHandler.END
    image=update.message.text.strip(); image_url=None if image=='-' else image
    try:
        result=await api_add(context.user_data['name'],context.user_data['url'],image_url)
        await update.message.reply_text(f"تمت إضافة {result['name']} بنجاح.",reply_markup=KEYBOARD)
    except Exception as e: await update.message.reply_text(f'تعذرت الإضافة: {e}',reply_markup=KEYBOARD)
    context.user_data.clear(); return ConversationHandler.END
async def cancel(update,context):
    await update.message.reply_text('تم الإلغاء.',reply_markup=KEYBOARD); return ConversationHandler.END
async def listing(update,context,links=False):
    if not is_admin(update): return
    try: channels=await api_list()
    except Exception as e: return await update.message.reply_text(f'تعذر الاتصال بالخدمة: {e}')
    if not channels: return await update.message.reply_text('لا توجد قنوات حالياً.')
    text='\n\n'.join(f"{x['name']}\n{x['url']}" if links else f"{x['id']}. {x['name']}" for x in channels)
    await update.message.reply_text(text,disable_web_page_preview=True)
async def list_cmd(u,c): await listing(u,c,False)
async def links_cmd(u,c): await listing(u,c,True)
async def delete_menu(update,context):
    if not is_admin(update): return
    try: channels=await api_list()
    except Exception as e: return await update.message.reply_text(f'تعذر الاتصال بالخدمة: {e}')
    if not channels: return await update.message.reply_text('لا توجد قنوات لحذفها.')
    kb=[[InlineKeyboardButton(x['name'],callback_data=f"del:{x['id']}")] for x in channels]
    await update.message.reply_text('اختر القناة المطلوب حذفها:',reply_markup=InlineKeyboardMarkup(kb))
async def delete_callback(update,context):
    q=update.callback_query
    if not is_admin(update): return await q.answer('غير مصرح',show_alert=True)
    await q.answer()
    try:
        cid=int(q.data.split(':')[1]); await api_delete(cid); await q.edit_message_text('تم حذف القناة وتحديث قاعدة البيانات.')
    except Exception as e: await q.edit_message_text(f'تعذر الحذف: {e}')
async def post_init(app):
    me=await app.bot.get_me()  # raises InvalidToken on a bad BOT_TOKEN
    await app.bot.delete_webhook(drop_pending_updates=True)  # polling and webhook are exclusive
    logging.getLogger('bot').warning('Connected to Telegram as @%s; polling',me.username)
def build_app():
    token=(os.getenv('BOT_TOKEN') or '').strip()
    if not token or not ADMIN_ID: raise RuntimeError('Set BOT_TOKEN and ADMIN_ID')
    app=Application.builder().token(token).post_init(post_init).base_url(os.getenv("TELEGRAM_API_BASE","https://api.telegram.org/bot")).build()
    conv=ConversationHandler(entry_points=[MessageHandler(filters.Regex('^📺 إضافة قناة$'),add_start)],states={NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND,get_name)],URL:[MessageHandler(filters.TEXT & ~filters.COMMAND,get_url)],IMAGE:[MessageHandler(filters.TEXT & ~filters.COMMAND,get_image)]},fallbacks=[CommandHandler('cancel',cancel)])
    app.add_handler(CommandHandler('start',start)); app.add_handler(conv)
    app.add_handler(MessageHandler(filters.Regex('^🗑️ مسح قناة$'),delete_menu)); app.add_handler(MessageHandler(filters.Regex('^🔗 روابط القنوات$'),links_cmd)); app.add_handler(MessageHandler(filters.Regex('^📋 قائمة القنوات$'),list_cmd)); app.add_handler(CallbackQueryHandler(delete_callback,pattern=r'^del:\d+$'))
    return app
def main():
    build_app().run_polling()
if __name__=='__main__': main()
