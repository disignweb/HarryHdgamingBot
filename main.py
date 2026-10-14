import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import feedparser
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Abilita i log dettagliati
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- CONFIGURAZIONE ---
# Metti qui dentro il token corretto che ti ha dato BotFather
TELEGRAM_BOT_TOKEN = "8914103258:AAEfe20telSqoAcJTJFqPjxpI7hBq-D3SzQ"
CHANNEL_ID = "UCNDXC4L8bA_X4vEh9_cJBqg"

# --- SERVER FITTIZIO PER RENDER ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

# --- HANDLER DEL COMANDO /STATS (VIA RSS - ZERO QUOTE) ---
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(">>> RICEVUTO COMANDO /stats! <<<")
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
    feed = feedparser.parse(feed_url)
    
    if feed.entries:
        channel_title = feed.feed.title
        latest_video = feed.entries[0]
        video_title = latest_video.title
        video_link = latest_video.link
        
        message = (
            f"📊 **Statistiche Canale: {channel_title}**\n\n"
            f"🎬 **Ultimo video pubblicato:**\n"
            f"[{video_title}]({video_link})\n\n"
            f"✅ *Stato del bot:* Online e operativo (Senza limiti API)!"
        )
    else:
        message = "Impossibile recuperare i dati del canale al momento."
        
    await update.message.reply_text(message, parse_mode="Markdown")

# --- DEBUG: LOGGA I MESSAGGI NEL GRUPPO ---
async def log_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        print(f">>> MESSAGGIO RICEVUTO: {update.message.text} <<<")

# --- MAIN ---
def main():
    # Avvia il server HTTP per Render in background
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    # Inizializza il bot Telegram
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Registra i comandi e gli handler
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), log_all_messages))
    
    print("Bot avviato con successo e libero da quote API!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
