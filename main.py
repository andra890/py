import os
import json
import asyncio
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# === CONFIG ===
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
OWNER_ID = int(os.getenv("OWNER_ID"))

DB_FILE = "groups.json"
is_running = False

# === INIT CLIENT ===
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# === DB HELPERS ===
def load_groups():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_groups(groups):
    with open(DB_FILE, "w") as f:
        json.dump(groups, f)

# === COMMAND HANDLERS ===
@client.on(events.NewMessage(pattern=r"\.sg", from_users=OWNER_ID))
async def save_group(event):
    if not event.is_reply:
        await event.reply("❌ Reply ke pesan di grup dulu!")
        return
    chat = await event.get_chat()
    groups = load_groups()
    if chat.id not in groups:
        groups.append(chat.id)
        save_groups(groups)
        await event.reply(f"✅ Grup `{chat.title}` disimpan!")
    else:
        await event.reply("⚠️ Grup sudah ada di list.")

@client.on(events.NewMessage(pattern=r"\.lg", from_users=OWNER_ID))
async def list_groups(event):
    groups = load_groups()
    if not groups:
        await event.reply("📭 Belum ada grup yang disimpan.")
        return
    text = "📌 List Group:\n"
    for i, gid in enumerate(groups, 1):
        try:
            chat = await client.get_entity(gid)
            text += f"{i}. {chat.title} (ID: {gid})\n"
        except:
            text += f"{i}. [Tidak diketahui] (ID: {gid})\n"
    await event.reply(text)

@client.on(events.NewMessage(pattern=r"\.hp", from_users=OWNER_ID))
async def delete_group(event):
    if not event.is_reply:
        await event.reply("❌ Reply ke pesan di grup yang mau dihapus!")
        return
    chat = await event.get_chat()
    groups = load_groups()
    if chat.id in groups:
        groups.remove(chat.id)
        save_groups(groups)
        await event.reply(f"🗑 Grup `{chat.title}` dihapus dari list!")
    else:
        await event.reply("⚠️ Grup ini tidak ada di list.")

# === BROADCAST (COPY MODE) ===
@client.on(events.NewMessage(pattern=r"\.sb (\d+) (\d+) (.+)", from_users=OWNER_ID))
async def start_broadcast(event):
    global is_running
    if is_running:
        await event.reply("⚠️ Broadcast masih berjalan. Gunakan .stop dulu.")
        return

    args = event.pattern_match.groups()
    delay_msg = int(args[0])
    delay_group = int(args[1])
    duration_raw = args[2]

    if duration_raw.endswith("j"):
        duration = int(duration_raw[:-1]) * 3600
    elif duration_raw.endswith("m"):
        duration = int(duration_raw[:-1]) * 60
    else:
        duration = int(duration_raw)

    if not event.is_reply:
        await event.reply("❌ Reply ke pesan yang mau disebar!")
        return
    reply = await event.get_reply_message()

    groups = load_groups()
    if not groups:
        await event.reply("📭 Belum ada grup di list.")
        return

    is_running = True
    end_time = datetime.now() + timedelta(seconds=duration)
    await event.reply(f"🚀 Mulai broadcast COPY ke {len(groups)} grup! Durasi {duration_raw}.")

    while is_running and datetime.now() < end_time:
        for gid in groups:
            if not is_running:
                break
            try:
                if reply.text:
                    await client.send_message(gid, reply.text, parse_mode="md")
                elif reply.media:
                    await client.send_file(gid, reply.media, caption=reply.text or "", parse_mode="md")
                await asyncio.sleep(delay_msg)
            except Exception as e:
                print(f"Gagal kirim ke {gid}: {e}")
        await asyncio.sleep(delay_group)

    is_running = False
    await event.reply("✅ Broadcast selesai!")

# === BROADCAST (FORWARD MODE) ===
@client.on(events.NewMessage(pattern=r"\.fw (\d+) (\d+) (.+)", from_users=OWNER_ID))
async def start_forward(event):
    global is_running
    if is_running:
        await event.reply("⚠️ Broadcast masih berjalan. Gunakan .stop dulu.")
        return

    args = event.pattern_match.groups()
    delay_msg = int(args[0])
    delay_group = int(args[1])
    duration_raw = args[2]

    if duration_raw.endswith("j"):
        duration = int(duration_raw[:-1]) * 3600
    elif duration_raw.endswith("m"):
        duration = int(duration_raw[:-1]) * 60
    else:
        duration = int(duration_raw)

    if not event.is_reply:
        await event.reply("❌ Reply ke pesan yang mau di-forward!")
        return
    reply = await event.get_reply_message()

    groups = load_groups()
    if not groups:
        await event.reply("📭 Belum ada grup di list.")
        return

    is_running = True
    end_time = datetime.now() + timedelta(seconds=duration)
    await event.reply(f"🚀 Mulai broadcast FORWARD ke {len(groups)} grup! Durasi {duration_raw}.")

    while is_running and datetime.now() < end_time:
        for gid in groups:
            if not is_running:
                break
            try:
                await client.forward_messages(gid, reply)
                await asyncio.sleep(delay_msg)
            except Exception as e:
                print(f"Gagal forward ke {gid}: {e}")
        await asyncio.sleep(delay_group)

    is_running = False
    await event.reply("✅ Broadcast selesai!")

# === STOP ===
@client.on(events.NewMessage(pattern=r"\.stop", from_users=OWNER_ID))
async def stop_broadcast(event):
    global is_running
    is_running = False
    await event.reply("🛑 Broadcast dihentikan!")

# === MENU ===
@client.on(events.NewMessage(pattern=r"\.menu", from_users=OWNER_ID))
async def menu(event):
    text = """✨ Userbot Menu ✨

📌 Grup Manager
.sg   → Simpan grup (reply pesan di grup)
.lg   → List grup yang tersimpan
.hp   → Hapus grup (reply pesan di grup)

📢 Broadcast
.sb <delay_pesan> <delay_group> <durasi> → Sebar pesan (copy text/media)
.fw <delay_pesan> <delay_group> <durasi> → Sebar pesan (forward asli)
.stop → Hentikan broadcast

ℹ️ Lainnya
.menu → Tampilkan menu
"""
    await event.reply(text)

# === STARTUP MESSAGE ===
async def startup_message():
    try:
        await client.send_message("me", "💌 Sayang, aku udh aktif ~\nKetik .menu ya ✨")
    except Exception as e:
        print(f"Gagal kirim pesan startup: {e}")

print("Userbot ready...")

async def main():
    await startup_message()

with client:
    try:
        client.loop.run_until_complete(main())
        client.run_until_disconnected()
    except Exception:
        client.loop.run_until_complete(client.send_message("me", "😴 Bntar ya, set ulang lagi..."))
        client.loop.run_until_complete(client(JoinChannelRequest("palingg")))
                             
