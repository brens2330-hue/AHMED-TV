"""AHMED-TV Telegram administration bot; access restricted by ADMIN_ID."""
import os, logging
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters
from api_client import api_list, api_add, api_delete
load_dotenv(Path(__file__).resolve().parent / '.env')
logging.basicConfig(level=logging.INFO)
ADMIN_ID=int(os.getenv('ADMIN_ID', os.getenv('TELEGRAM_ADMIN_ID','0')))
NAME, URL, IMAGE = range(3)
KEYBOARD=ReplyKeyboardMarkup([[KeyboardButton('📺 إضافة قناة'),KeyboardButton('🗑️ مسح قناة')],[KeyboardButton('🔗 روابط القنوات'),KeyboardButton('📋 قائمة القنوات')]],resize_keyboard=True)

def is_admin(u): return bool(u.effective_user and u.effective_user.id==ADMIN_ID)
async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return await update.message.reply_text('غير مصرح لك باستخدام لوحة الإدارة.')
    await update.message.reply_text('مرحباً بك في إدارة قنوات AHMED-TV.',reply_markup=KEYBOARD)
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
async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error("Unhandled Telegram update error", exc_info=context.error)

def main():
    token=os.getenv('BOT_TOKEN')
    if not token or not ADMIN_ID: raise RuntimeError('Railway Variables required: BOT_TOKEN and ADMIN_ID')
    logging.info('Starting AHMED-TV Telegram polling bot for admin ID %s', ADMIN_ID)
    app=Application.builder().token(token).build()
    conv=ConversationHandler(entry_points=[MessageHandler(filters.Regex('^📺 إضافة قناة$'),add_start)],states={NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND,get_name)],URL:[MessageHandler(filters.TEXT & ~filters.COMMAND,get_url)],IMAGE:[MessageHandler(filters.TEXT & ~filters.COMMAND,get_image)]},fallbacks=[CommandHandler('cancel',cancel)])
    app.add_handler(CommandHandler('start',start)); app.add_handler(conv)
    app.add_error_handler(on_error)
    app.add_handler(MessageHandler(filters.Regex('^🗑️ مسح قناة$'),delete_menu)); app.add_handler(MessageHandler(filters.Regex('^🔗 روابط القنوات$'),links_cmd)); app.add_handler(MessageHandler(filters.Regex('^📋 قائمة القنوات$'),list_cmd)); app.add_handler(CallbackQueryHandler(delete_callback,pattern=r'^del:\d+$'))
    app.run_polling(drop_pending_updates=False, close_loop=True)
if __name__=='__main__': main()
