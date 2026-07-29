import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("convert_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply("Bot On Hai 🔥\nMujhe koi audio/video bhejo, main usay convert kar dunga")

@app.on_message(filters.audio | filters.video | filters.document)
async def convert(client, message: Message):
    status = await message.reply("Download ho raha hai...")
    
    file_path = await message.download()
    
    await status.edit("Converting to MP3 with ffmpeg...")
    
    output_path = file_path + ".mp3"
    cmd = ["ffmpeg", "-i", file_path, "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", output_path]
    
    subprocess.run(cmd)
    
    await status.edit("Upload ho raha hai...")
    await message.reply_audio(output_path, caption="Lo ho gaya convert ✅")
    
    await status.delete()
    os.remove(file_path)
    os.remove(output_path)

app.run()