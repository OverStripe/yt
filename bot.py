import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, filters

# Gmail SMTP Configuration
smtp_server = "smtp.gmail.com"
smtp_port = 587
email_username = "songindian16@gmail.com"
email_password = os.getenv("EMAIL_PASSWORD", "gxzk hegw vbks pavr")  # App Password (default set for now)

# Telegram Bot Token
telegram_bot_token = "7709293848:AAEBWJgH-InmHjT757rz2szg_gS1e44chdg"  # Replace with your Telegram bot token

# Email settings
recipient_email = "recover@telegram.org"
subject = "Account Recovery Request"

# Default email message template
default_message = """
Hello, Telegram administration

I cannot log into my account nor create an account on Telegram. When I log in, the message comes to Telegram: 
"This number is blocked on Telegram." 
I think I am banned from restricted use of Telegram by accident, and I really don't know why Telegram did this. 

Can you verify my account for that? 
I am using my phone number: {}
"""

# Conversation states
PHONE_NUMBER, CUSTOM_MESSAGE = range(2)

# Function to send email
def send_email(phone_number, custom_message):
    try:
        # Prepare the email content
        if not custom_message.strip():
            message_body = default_message.format(phone_number)
        else:
            message_body = custom_message

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Start TLS encryption
            server.login(email_username, email_password)  # Login to Gmail SMTP server
            
            # Create the email
            msg = MIMEMultipart()
            msg['From'] = email_username
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(message_body, 'plain'))
            
            # Send the email
            server.sendmail(email_username, recipient_email, msg.as_string())
            return "✅ Recovery email sent successfully!"
    except Exception as e:
        return f"❌ Failed to send recovery email: {e}"


# Telegram Bot Handlers
async def start(update: Update, context):
    await update.message.reply_text("Welcome! Please enter the phone number you want to recover.")
    return PHONE_NUMBER


async def phone_number(update: Update, context):
    context.user_data['phone_number'] = update.message.text
    await update.message.reply_text(
        "Got it! Now, you can enter a custom message for the recovery email or type 'default' to use the standard message."
    )
    return CUSTOM_MESSAGE


async def custom_message(update: Update, context):
    custom_message = update.message.text
    if custom_message.lower() == 'default':
        custom_message = ""  # Use the default template

    phone_number = context.user_data['phone_number']
    result = send_email(phone_number, custom_message)
    await update.message.reply_text(result)
    return ConversationHandler.END


async def cancel(update: Update, context):
    await update.message.reply_text("Operation canceled. You can start again by typing /start.")
    return ConversationHandler.END


# Main function to run the bot
def main():
    # Create the application
    application = ApplicationBuilder().token(telegram_bot_token).build()

    # Conversation handler for the interaction
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PHONE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_number)],
            CUSTOM_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_message)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Add the handler to the application
    application.add_handler(conv_handler)

    # Start polling
    application.run_polling()


if __name__ == '__main__':
    main()
