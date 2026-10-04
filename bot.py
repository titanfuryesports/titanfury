import os
import discord
from discord.ext import tasks, commands
import requests
from flask import Flask
from threading import Thread

# --- Flask Keep-Alive Server for Render / Web Hosts ---
app = Flask('')

@app.route('/')
def home():
    return "Titan Fury Schedule Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# --- Discord & WhatsApp Configuration ---
BOT_TOKEN = os.getenv("MTU1NjE0MDA1OTQyNDQ1NjkxNQ.GONWe6.CnT_2eMeWSXqGVMvkdfmGPpA5712rQ34Hmv6hY")
TARGET_CHANNEL_ID = 1517790656695898184  # Your Titan Fury Discord Channel ID

# WhatsApp Gateway Details (e.g., UltraMsg / Green-API)
WHATSAPP_API_URL = os.getenv("https://7107.api.greenapi.com")  # e.g., https://api.ultramsg.com/INSTANCE_ID/messages/chat
WHATSAPP_TOKEN = os.getenv("496f3f563cad44a8b328a953c382a80ae2719fdaffdf4ec597")
WHATSAPP_GROUP_ID = os.getenv("120363410974364515@g.us")  # e.g., 120363xxxxxx@g.us

intents = discord.Intents.default()
intents.guilds = True
intents.scheduled_events = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    daily_event_summary.start()

@tasks.loop(hours=24)
async def daily_event_summary():
    target_channel = bot.get_channel(TARGET_CHANNEL_ID)
    all_events = []

    # 1. Gather events across all connected Discord servers
    for guild in bot.guilds:
        try:
            events = await guild.fetch_scheduled_events()
            for event in events:
                if event.status == discord.EventStatus.scheduled:
                    all_events.append({
                        "server": guild.name,
                        "title": event.name,
                        "time": event.start_time.strftime("%d %b %Y, %I:%M %p UTC"),
                        "location": event.location or "Discord"
                    })
        except Exception as e:
            print(f"Error fetching events for {guild.name}: {e}")

    # 2. Format Messages
    if not all_events:
        discord_embed = discord.Embed(
            title="🏆 Daily Schedule Update",
            description="No scheduled events found across your Discord servers today.",
            color=discord.Color.blue()
        )
        whatsapp_msg = "🏆 *Titan Fury Update*\nNo events or matches scheduled across Discord servers today."
    else:
        discord_embed = discord.Embed(
            title="🏆 Daily Event Schedule Across All Servers",
            description="Here are the upcoming events scheduled across your connected servers:",
            color=discord.Color.gold()
        )
        whatsapp_msg = "🏆 *Titan Fury - Daily Schedule*\n\n"

        for item in all_events:
            # Add field to Discord Embed
            discord_embed.add_field(
                name=f"📌 {item['title']} ({item['server']})",
                value=f"⏰ **Time:** {item['time']}\n📍 **Location:** {item['location']}",
                inline=False
            )
            # Add line to WhatsApp Message
            whatsapp_msg += f"📌 *{item['title']}* ({item['server']})\n⏰ Time: {item['time']}\n📍 Location: {item['location']}\n\n"

    # 3. Send to Discord Channel
    if target_channel:
        await target_channel.send(embed=discord_embed)

    # 4. Send to WhatsApp Group via Gateway API
    if WHATSAPP_API_URL and WHATSAPP_TOKEN and WHATSAPP_GROUP_ID:
        payload = {
            "token": WHATSAPP_TOKEN,
            "to": WHATSAPP_GROUP_ID,
            "body": whatsapp_msg
        }
        try:
            requests.post(WHATSAPP_API_URL, data=payload)
            print("Successfully sent daily schedule to WhatsApp group.")
        except Exception as e:
            print(f"Failed to send to WhatsApp: {e}")

# Start Flask Keep-Alive & Run Bot
keep_alive()
bot.run(BOT_TOKEN)
