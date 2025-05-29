import os
import logging
import pandas as pd
from telethon.sync import TelegramClient
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME", "parsbot_session")

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Надішли мені @username каналу або групи, і я зберу користувачів з останніх 500 повідомлень."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_input = update.message.text.strip()
    if not chat_input.startswith("@"):
        await update.message.reply_text("Напиши @username каналу або групи")
        return

    username = chat_input[1:]
    await update.message.reply_text(f"Читаю повідомлення з {chat_input}...")

    await client.start()
    try:
        entity = await client.get_entity(username)
        messages = []
        async for msg in client.iter_messages(entity, limit=500):
            if msg.sender_id:
                user = await client.get_entity(msg.sender_id)
                messages.append({
                    "User ID": user.id,
                    "Name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
                    "Username": f"@{user.username}" if user.username else ""
                })
        df = pd.DataFrame(messages).drop_duplicates(subset=["User ID"])
        filepath = f"/tmp/{username}_users.xlsx"
        df.to_excel(filepath, index=False)

        with open(filepath, "rb") as f:
            await update.message.reply_document(document=InputFile(f), filename=f"{username}_users.xlsx")
    except Exception as e:
        await update.message.reply_text(f"Помилка: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
