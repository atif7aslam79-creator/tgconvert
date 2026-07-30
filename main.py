import subprocess
import os
import re
import asyncio
from pyrogram import Client, filters

app = Client("bot")

def get_duration(file):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrapped=1:nokey=1", file], stdout=subprocess.PIPE)
    return float(result.stdout)

async def run_ffmpeg_with_progress(input_file, output_file, message):
    duration = get_duration(input_file)
    cmd = [
        'ffmpeg', '-i', input_file, 
        '-vcodec', 'libx264', '-crf', '28', '-preset', 'fast', '-vf', 'scale=-2:720',
        '-acodec', 'aac', '-b:a', '128k',
        '-progress', 'pipe:1', '-y', output_file
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    
    last_percent = 0
    while True:
        line = await process.stdout.readline()
        if not line: break
        line = line.decode('utf-8')
        
        if 'out_time_ms' in line:
            time_ms = int(line.split('=')[1])
            current_time = time_ms / 1000000
            percent = int((current_time / duration) * 100)
            
            if percent >= last_percent + 20: # Har 20% pe update
                last_percent = percent
                if percent > 100: percent = 100
                await message.edit(f"Compressing... {percent}%")

    await process.wait()

@app.on_message(filters.video | filters.document)
async def compress_video(client, message):
    msg = await message.reply("Downloading... 0%")
    file_path = await message.download()
    output_path = "compressed.mp4"
    
    await msg.edit("Converting to MP4 with ffmpeg... 0%")
    await run_ffmpeg_with_progress(file_path, output_path, msg)
    
    await msg.edit("Uploading... 100%")
    await message.reply_video(output_path, caption="✅ Compressed Ho Gaya")
    
    os.remove(file_path)
    os.remove(output_path)

app.run()