import os
import asyncio
from fastapi import FastAPI, HTTPException
from pyrogram import Client, filters

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

app = FastAPI(title="TagAll Engine")

bot = Client(
    "tagall_engine_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_event("startup")
async def startup_event():
    await bot.start()
    print("Pyrogram Engine Berhasil Aktif!")

@app.on_event("shutdown")
async def shutdown_event():
    await bot.stop()

# Handle jika perintah dipanggil langsung di Telegram (/tagall)
@bot.on_message(filters.command(["tagall", "all"]) & filters.group)
async def handle_telegram_command(client, message):
    chat_id = message.chat.id
    args = message.text.split(maxsplit=1)
    custom_msg = args[1] if len(args) > 1 else "Perhatian semuanya!"
    asyncio.create_task(run_tagall_process(chat_id, custom_msg))

# Endpoint API yang akan dipanggil oleh Lovable
@app.post("/api/tagall")
async def trigger_tagall_from_lovable(chat_id: int, message: str = "Perhatian semuanya!"):
    try:
        asyncio.create_task(run_tagall_process(chat_id, message))
        return {"status": "success", "message": f"Proses tagall ke grup {chat_id} berhasil dipicu!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Fungsi Utama TagAll TANPA SCREENING
async def run_tagall_process(chat_id: int, custom_msg: str):
    users_to_tag = []
    try:
        # PENTING: get_chat_members() mengambil daftar anggota LANGSUNG dari server Telegram
        async for member in bot.get_chat_members(chat_id):
            if not member.user.is_bot and not member.user.is_deleted:
                mention = f'<a href="tg://user?id={member.user.id}">{member.user.first_name}</a>'
                users_to_tag.append(mention)
        
        # Kirim per 5 anggota agar tidak terkena pembatasan spam (FloodWait)
        chunk_size = 5
        for i in range(0, len(users_to_tag), chunk_size):
            chunk = users_to_tag[i:i + chunk_size]
            text_payload = f"📢 <b>{custom_msg}</b>\n\n" + " ".join(chunk)
            await bot.send_message(chat_id, text_payload, parse_mode="HTML")
            await asyncio.sleep(1.5)
            
    except Exception as e:
        await bot.send_message(chat_id, f"❌ *Gagal tagall:* {e}\n\n_Pastikan bot sudah diangkat menjadi ADMIN di grup!_", parse_mode="markdown")