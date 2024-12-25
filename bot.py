import os
import time
import smtplib
import itertools
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telethon.sync import TelegramClient
from telethon.errors import PhoneNumberBannedError
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, filters

# Configuration
smtp_server = "smtp.gmail.com"
smtp_port = 587
email_username = "songindian16@gmail.com"
email_password = os.getenv("EMAIL_PASSWORD", "gxzk hegw vbks pavr")  # App Password
telegram_bot_token = "7605917834:AAHc537VnNebF4U-T-nu64MSSLYtAZruwEk"
API_ID = "28142132"
API_HASH = "82fe6161120bd237293a4d6da61808e3"
OWNER_ID = 7222795580   # Only this user can use the bot

# Email and Recovery Settings
subject = "Account Recovery Request"
default_message = """
Hello, Telegram administration

I cannot log into my account nor create an account on Telegram. When I log in, the message comes to Telegram: 
"This number is blocked on Telegram." 
I think I am banned from restricted use of Telegram by accident, and I really don't know why Telegram did this. 

Can you verify my account for that? 
I am using my phone number: {}
"""
recipients_cycle = itertools.cycle(["support@telegram.org", "recover@telegram.org"])

# Conversation states
PHONE_NUMBER, CUSTOM_MESSAGE = range(2)

# Global variables
phone_number = None
custom_message = None
auto_send = False

# Function to send email
def send_email(phone_number, custom_message):
    try:
        recipient_email = next(recipients_cycle)
        message_body = custom_message.strip() or default_message.format(phone_number)

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_username, email_password)

            msg = MIMEMultipart()
            msg['From'] = email_username
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(message_body, 'plain'))

            server.sendmail(email_username, recipient_email, msg.as_string())
            return f"✅ Recovery email sent successfully to {recipient_email}!"
    except Exception as e:
        return f"❌ Failed to send recovery email: {e}"

# Permission check
def is_owner(update: Update):
    return update.effective_user.id == OWNER_ID

# Command Handlers
async def start(update: Update, context):
    if not is_owner(update):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return ConversationHandler.END

    await update.message.reply_text("Welcome! Please enter the phone number you want to recover.")
    return PHONE_NUMBER

async def phone_number_handler(update: Update, context):
    global phone_number
    if not is_owner(update):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return ConversationHandler.END

    phone_number = update.message.text
    await update.message.reply_text(
        "Got it! Now, you can enter a custom message for the recovery email or type 'default' to use the standard message."
    )
    return CUSTOM_MESSAGE

async def custom_message_handler(update: Update, context):
    global custom_message, auto_send
    if not is_owner(update):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return ConversationHandler.END

    custom_message = update.message.text
    if custom_message.lower() == 'default':
        custom_message = ""  # Use default template

    result = send_email(phone_number, custom_message)
    await update.message.reply_text(result)

    auto_send = True
    await update.message.reply_text("Auto-sending emails every 15 minutes. Type /stop to cancel.")
    while auto_send:
        time.sleep(900)  # 15 minutes
        result = send_email(phone_number, custom_message)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=result)

    return ConversationHandler.END

async def stop(update: Update, context):
    global auto_send
    if not is_owner(update):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return ConversationHandler.END

    auto_send = False
    await update.message.reply_text("Auto-sending stopped. You can start again by typing /start.")
    return ConversationHandler.END

async def check(update: Update, context):
    if not is_owner(update):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Please provide the phone number to check. Usage: /check <phone_number>")
        return

    phone_number_to_check = context.args[0]

    try:
        async with TelegramClient("temp_session", API_ID, API_HASH) as client:
            await client.send_code_request(phone_number_to_check)
            await update.message.reply_text(f"✅ The phone number {phone_number_to_check} is not banned. OTP was successfully sent.")
    except PhoneNumberBannedError:
        await update.message.reply_text(f"⚠️ The phone number {phone_number_to_check} is banned. Please contact Telegram support.")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to check phone number: {e}")

# Main function to run the bot
def main():
    application = ApplicationBuilder().token(telegram_bot_token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PHONE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_number_handler)],
            CUSTOM_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_message_handler)],
        },
        fallbacks=[CommandHandler('stop', stop)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('check', check))

    application.run_polling()

if __name__ == '__main__':
    main()
