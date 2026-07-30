import os
import subprocess
import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def get_duration(filename):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrapped=1:nokey=1", filename],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return float(result.stdout)

async def compress_video(input_path, output_path, status_msg: Message):
    duration = get_duration(input_path)
    start_time = time.time()
    last_update = 0

    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vcodec", "libx264", "-crf", "28", "-preset", "fast",
        "-acodec", "aac", "-b:a", "128k",
        "-progress", "pipe:1", output_path
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    while True:
        line = await process.stdout.readline()
        if not line: break
        line = line.decode().strip()
        
        if line.startswith("out_time_ms="):
            current_ms = int(line.split("=")[1])
            current_sec = current_ms / 1000000
            percent = int((current_sec / duration) * 100)
            
            if time.time() - last_update > 2: # 2 sec baad update
                last_update = time.time()
                elapsed = time.time() - start_time
                speed = current_sec / elapsed if elapsed > 0 else 0
                eta = (duration - current_sec) / speed if speed > 0 else 0
                try:
                    await status_msg.edit_text(f"**Compressing...**\n`{percent}%` done\n`{int(current_sec)}s / {int(duration)}s`\nETA: `{int(eta)}s`")
                except: pass

    await process.wait()

@app.on_message(filters.video | filters.document)
async def handle_video(client, message: Message):
    status = await message.reply("**Downloading...** 0%")
    input_path = await message.download(progress=lambda c,t: asyncio.create_task(status.edit_text(f"**Downloading...** {int(c/t*100)}%")))
    
    await status.edit_text("**Compressing...** 0%")
    output_path = "compressed.mp4"
    await compress_video(input_path, output_path, status)
    
    await status.edit_text("**Uploading...**")
    await message.reply_video(output_path, caption="Compressed ✅")
    
    os.remove(input_path)
    os.remove(output_path)
    await status.delete()

print("Bot started...")
app.run()