import discord
from discord.ext import commands, tasks
from google import genai
from datetime import datetime, timedelta, timezone
import re
import asyncio
import os
from dotenv import load_dotenv


GENAI_API_KEY = "AIzaSyCW4kp7Vsk-rKdUd_qwXMQbhWIuytaupu8"
genai_client = genai.Client(api_key=GENAI_API_KEY)

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

reminder = {}

@bot.event
async def on_ready():
    print(f'Logged on as {bot.user}')
    reminder_check.start()


@tasks.loop(seconds=10)
async def reminder_check():
    while True:
        now =  datetime.now()
        reminder_outdated = []
        for reminder_time , (channel, reminder_text) in reminder.items():
            if now>= reminder_time:
                await channel.send(f'⏰ Reminder!!: {reminder_text}')
                reminder_outdated.append(reminder_time)
        for reminder_time in reminder_outdated:
            del reminder[reminder_time]
        await asyncio.sleep(10)


@bot.command()
async def remind(ctx, *args):
    if len(args) < 2:
        await ctx.send("Invalid format! Use: `!remind YYYY-MM-DD HH:MM <message>`")
        return
    time = args[0] + " " + args[1]
    message = " ".join(args[2:])
    if not re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", time):
        await ctx.send("Invalid format! Use: `!remind YYYY-MM-DD HH:MM <message>`")
        return
    try:
        print(time, message)
        reminder_time = datetime.strptime(time, "%Y-%m-%d %H:%M")
        print(reminder_time)
        now = datetime.now()
        if reminder_time <= now:
            await ctx.send("Reminder time must be in the future!")
            return
        reminder[reminder_time] = (ctx.channel, message)
        await ctx.send(f"Reminder set for {time}: {message}")
    except ValueError:
        await ctx.send("Invalid format! Use: `!remind YYYY-MM-DD HH:MM <message>`")
        
@bot.command()
async def updatereminder(ctx, *args):
    if len(args) < 2:
        await ctx.send("Invalid format! Use: `!remind YYYY-MM-DD HH:MM <message>`")
        return
    time = args[0] + " " + args[1]
    message = " ".join(args[2:])
    if not re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", time):
        await ctx.send("Invalid format! Use: `!remind YYYY-MM-DD HH:MM <message>`")
        return
    try:
        reminder_time = datetime.strptime(time, "%Y-%m-%d %H:%M")
        if reminder_time in reminder:
            reminder[reminder_time] = (ctx.channel, message)
            await ctx.send(f'Reminder updated for time: {reminder_time}\nReminder message: {message}')
        else:
            await ctx.send(f'No reminder found for this time.')
    except ValueError:
         await ctx.send("Invalid format. Use: !modifyreminder YYYY-MM-DD HH:MM <message>")
    

@bot.command()
async def deletereminder(ctx, *args):
    if len(args) < 2:
        await ctx.send("Invalid format! Use: `!remind YYYY-MM-DD HH:MM <message>`")
        return
    time = args[0] + " " + args[1]
    if not re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", time):
        await ctx.send("Invalid format! Use: `!remind YYYY-MM-DD HH:MM <message>`")
        return
    try:
        reminder_time = datetime.strptime(time, "%Y-%m-%d %H:%M")
        if reminder_time in reminder:
            del reminder[reminder_time]
            await ctx.send(f'Reminder deleted for {reminder_time}')
        else:
            await ctx.send(f'No reminder found at this time')
    except ValueError:
        await ctx.send("Invalid format. Use: !deletereminder YYYY-MM-DD HH:MM <message>")


@bot.command()
async def poll(ctx, *, poll_input: str):   
    parts = poll_input.split("|")
    if len(parts) < 2:
        await ctx.send("❌ Invalid format! Use: `!poll Question | Option1 | Option2 | ...`")
        return

    question = parts[0].strip()
    options = [opt.strip() for opt in parts[1:]]

    if len(options) > 10:
        await ctx.send("❌ Maximum 10 options allowed.")
        return

    poll_embed = discord.Embed(title="📊 Poll", description=f"**{question}**", color=0x00ff00)
    emoji_numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    option_text = ""
    i=0
    for option in options:
        option_text += f"{emoji_numbers[i]} {option}\n"
        i+=1

    poll_embed.add_field(name="Options:", value=option_text, inline=False)
    poll_message = await ctx.send(embed=poll_embed)

    for i in range(len(options)):
        await poll_message.add_reaction(emoji_numbers[i])


@bot.event
async def on_message(message):
    print(message.content)
    if(message.author == bot.user):
        return
    await bot.process_commands(message)
    if message.content.startswith('!'):
        return
    response = genai_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=message.content
        )
    await message.channel.send(f'{response.text}')



bot.run(DISCORD_TOKEN)