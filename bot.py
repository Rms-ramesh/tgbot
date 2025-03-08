import os
import logging
import yt_dlp
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from .env import TOKEN
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  


def download_media(url):
    output_template = f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s"
    
    options = {
        "outtmpl": output_template,
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

            if os.path.exists(file_path):
                return file_path
            else:
                return None

    except yt_dlp.utils.DownloadError:
        logger.error(f"Download failed for: {url}")
        return None


async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Hey there! 🎬🎵 Send me a video or audio link, and I'll download it for you.")


async def handle_message(update: Update, context: CallbackContext):
    url = update.message.text.strip()

    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("⚠️ That doesn't look like a valid URL. Please try again.")
        return

    await update.message.reply_text("⏳ Downloading your media... Please hold on.")

    file_path = download_media(url)

    if not file_path:
        await update.message.reply_text("❌ Oops! I couldn't download the file. Maybe the link is incorrect?")
        return

    file_size = os.path.getsize(file_path)

    if file_size > MAX_FILE_SIZE:
        await update.message.reply_text("❌ Sorry, the file is too big to send (50MB max).")
        os.remove(file_path)
        return

    await update.message.reply_text("✅ Download complete! Sending the file now...")

    try:
        with open(file_path, "rb") as file:
            await update.message.reply_document(document=InputFile(file))
    except Exception as e:
        logger.error(f"Failed to send file: {e}")
        await update.message.reply_text("❌ Hmm... I couldn't send the file. Something went wrong.")

    os.remove(file_path)


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("✅ Bot is up and running!")

    app.run_polling()


if __name__ == "__main__":
    main()
