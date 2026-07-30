import os
import subprocess
import asyncio
import re
from pyrogram import Client, filters
from pyrogram.types import Message

# Railway Variables yahan se leni hain
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("tgcompress_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def get_duration(filename):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrapped=1:nokey=1", filename],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    return float(result.stdout)

async def compress_with_progress(input_file, output_file, status_msg: Message):
    duration = get_duration(input_file)
    last_percent = 0

    # Video compress command: 720p, crf28 = size kam
    cmd = [
        "ffmpeg", "-i", input_file,
        "-vcodec", "libx264", "-crf", "28", "-preset", "fast", "-vf", "scale=-2:720",
        "-acodec", "aac", "-b:a", "128k",
        "-progress", "pipe:1", "-y", output_file
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    while True:
        line = await process.stdout.readline()
        if not line:
            break
        line = line.decode("utf-8").strip()

        if line.startswith("out_time_ms="):
            time_ms = int(line.split("=")[1])
            current_sec = time_ms / 1_000_000
            percent = int((current_sec / duration) * 100)

            # Har 20% pe update karo
            if percent >= last_percent + 20 or percent == 100:
                last_percent = percent
                if percent > 100: percent = 100
                await status_msg.edit_text(f"🔄 Compressing... {percent}%")

    await process.wait()

@app.on_message(filters.video | filters.document)
async def handle_video(client, message: Message):
    # Sirf video file lo
    if not message.video and not (message.document and message.document.mime_type.startswith("video/")):
        return

    status = await message.reply("📥 Downloading... 0%")

    try:
        # 1. Download
        file_path = await message.download(progress=lambda c, t: asyncio.create_task(
            status.edit_text(f"📥 Downloading... {int(c*100/t)}%") if t > 0 and int(c*100/t) % 25 == 0 else None
        ))

        output_path = "compressed.mp4"

        # 2. Compress with progress
        await status.edit_text("🔄 Compressing... 0%")
        await compress_with_progress(file_path, output_path, status)

        # 3. Upload
        await status.edit_text("📤 Uploading... 100%")
        await message.reply_video(
            output_path,
            caption="✅ Compressed Ho Gaya\nSize kam, Quality theek"
        )

        # Cleanup
        os.remove(file_path)
        os.remove(output_path)
        await status.delete()

    except Exception as e:
        await status.edit_text(f"❌ Error: {e}")

print("Bot started")
app.run()