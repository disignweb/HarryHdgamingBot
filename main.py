import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from googleapiclient.discovery import build
import feedparser  # Libreria per leggere i feed RSS di YouTube

# Configurazioni
TELEGRAM_BOT_TOKEN = "8914103258:AAGNhhu9FOjqcHpD0yalZMzHlutKZpkMBHw"
YOUTUBE_API_KEY = "AIzaSyB_8mhAshv1fadfwuhs0D6GwDk8BhTfUrg"
CHANNEL_ID = "UCNDXC4L8bA_X4vEh9_cJBqg"
TELEGRAM_CHAT_ID = "-5382886391"  # L'ID della chat o del gruppo dove mandare la notifica

# Variabile per memorizzare l'ultimo video notificato
last_video_id = None

# 1. Funzione per le statistiche (API YouTube)
def get_youtube_stats():
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.channels().list(
        part="statistics,snippet",
        id=CHANNEL_ID
    )
    response = request.execute()
    
    if response["items"]:
        stats = response["items"][0]["statistics"]
        title = response["items"][0]["snippet"]["title"]
        return {
            "title": title,
            "subscribers": stats["subscriberCount"],
            "views": stats["viewCount"],
            "videos": stats["videoCount"]
        }
    return None

# 2. Comando /stats di Telegram
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_youtube_stats()
    if data:
        msg = (
            f"📊 **Analitica Canale: {data['title']}**\n\n"
            f"👥 Iscritti: `{data['subscribers']}`\n"
            f"👁️ Visualizzazioni totali: `{data['views']}`\n"
            f"🎬 Video pubblicati: `{data['videos']}`"
        )
    else:
        msg = "Impossibile recuperare i dati al momento."
    
    await update.message.reply_text(msg, parse_mode="Markdown")

# 3. Funzione di controllo periodico per i nuovi video
async def check_new_videos(context: ContextTypes.DEFAULT_TYPE):
    global last_video_id
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
    
    # Legge il feed RSS del canale
    feed = feedparser.parse(rss_url)
    
    if feed.entries:
        latest_entry = feed.entries[0]
        video_id = latest_entry.yt_videoid
        video_title = latest_entry.title
        video_link = latest_entry.link
        
        # Al primo avvio impostiamo il video corrente senza inviare notifiche
        if last_video_id is None:
            last_video_id = video_id
            return
            
        # Se troviamo un video con un ID diverso dall'ultimo salvato -> Nuovo video!
        if video_id != last_video_id:
            last_video_id = video_id
            
            message = (
                f"🚨 **NUOVO VIDEO ONLINE!** 🎬\n\n"
                f"*{video_title}*\n\n"
                f"🔗 Guardalo subito: {video_link}"
            )
            
            # Invia la notifica alla chat configurata
            await context.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode="Markdown"
            )

# Un piccolo server HTTP fittizio per soddisfare il controllo delle porte di Render
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Registra il comando /stats
    app.add_handler(CommandHandler("stats", stats_command))
    
    # Configura il Job Queue per controllare i nuovi video ogni 10 minuti
    job_queue = app.job_queue
    job_queue.run_repeating(check_new_videos, interval=600, first=10)
    
    print("Bot avviato e in ascolto per statistiche e nuovi video...")
    
    # Forza il polling a ricevere messaggi dai gruppi e comandi
    app.run_polling(allowed_updates=["message", "edited_message", "channel_post"])

if __name__ == "__main__":
    # Avvia il server HTTP fittizio in background per Render
    server_thread = threading.Thread(target=run_dummy_server, daemon=True)
    server_thread.start()
    print("Server web fittizio avviato per Render sulla porta:", os.environ.get("PORT", 10000))

    # Avvia il bot Telegram
    main()
