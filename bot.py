from pytube import YouTube
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import os


# Function to download the video or audio
async def download_media(video_url, media_type="video", resolution="highest", download_path='./'):
    try:
        yt = YouTube(video_url)

        if media_type == "video":
            if resolution == "highest":
                stream = yt.streams.filter(progressive=True, file_extension='mp4').get_highest_resolution()
            else:
                stream = yt.streams.filter(res=resolution, progressive=True, file_extension='mp4').first()
        elif media_type == "audio":
            stream = yt.streams.filter(only_audio=True).first()

        file_path = stream.download(output_path=download_path)
        return file_path, yt.title
    except Exception as e:
        return None, str(e)


# Function to add watermark to the video
async def add_watermark(input_video_path, watermark_text="@MainHunSamay", output_path='./'):
    try:
        video = VideoFileClip(input_video_path)
        watermark = TextClip(watermark_text, fontsize=30, color='white', stroke_color='black', stroke_width=2)
        watermark = watermark.set_position(("right", "bottom")).set_duration(video.duration)
        watermarked_video = CompositeVideoClip([video, watermark])
        output_file_path = os.path.join(output_path, f"watermarked_{os.path.basename(input_video_path)}")
        watermarked_video.write_videofile(output_file_path, codec="libx264", audio_codec="aac")
        return output_file_path
    except Exception as e:
        return None, str(e)


# Command: Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Help", callback_data="help")],
        [InlineKeyboardButton("Start Download", callback_data="download")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome to the Enhanced YouTube Downloader Bot! 🎥\n\n"
                                    "Click a button below to get started:", reply_markup=reply_markup)


# Command: Help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📚 Help:\n"
                                    "1. Send a YouTube video URL to download the video or audio.\n"
                                    "2. Select video or audio format, resolution, and watermark preferences.\n"
                                    "3. The bot will process and send your file.\n"
                                    "Enjoy downloading!")


# Callback for buttons
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "help":
        await help_command(query, context)
    elif query.data == "download":
        await query.edit_message_text("Send me a YouTube video link to start downloading.")


# Handler: Process YouTube links
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video_url = update.message.text
    await update.message.reply_text("Processing your request... Please wait.")

    # Download the video in the highest quality
    file_path, message = await download_media(video_url)

    if file_path:
        # Add watermark
        watermarked_file_path, watermark_message = await add_watermark(file_path, "@MainHunSamay")
        if watermarked_file_path:
            with open(watermarked_file_path, 'rb') as video_file:
                await update.message.reply_video(video=video_file, caption=f"Here is your video with watermark: {message}")
            os.remove(file_path)
            os.remove(watermarked_file_path)
        else:
            await update.message.reply_text(f"Failed to add watermark. Error: {watermark_message}")
    else:
        await update.message.reply_text(f"Failed to download the video. Error: {message}")


# Main function to start the bot
def main():
    BOT_TOKEN = "8082481347:AAGNScjL3LZ5x0sqQh_f2dg2S06cgg_xmBE"

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()
