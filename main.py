import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# 启动 Keep-Alive 网页服务器以符合 Render 免费 Web Service 机制
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# 初始化 Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

KEYWORDS_PROMPTS = {
    "leaf_fall": "🍂 **【提示：静心 | 专注】**\n小树掉了一片叶子。**静心**才能听见花开，收回脚步，把**专注**留给自己。",
    "no_report": "🛡️ **【提示：内省 | 做好自己】**\n别人的树有风，**管好自己的花园**才是智慧。先**内省**，**做好自己**，小树自然常绿。",
    "struggle": "🌱 **【提示：积少成多 | 突破】**\n不用急，**积少成多**，今天完成这一行，就是最棒的**突破**！",
    "water_together": "💧 **【提示：共融 | 提携】**\n独木不成林。用**提携**代替指责，全班**同频**，**共融**的花园最美丽！"
}

@bot.event
async def on_ready():
    print(f"🌸 共融花园系统已上线：{bot.user.name}")

@bot.command()
async def 掉叶(ctx, member: discord.Member):
    await ctx.send(f"{member.mention}\n{KEYWORDS_PROMPTS['leaf_fall']}")

@bot.command()
async def 告状(ctx, member: discord.Member):
    await ctx.send(f"{member.mention}\n{KEYWORDS_PROMPTS['no_report']}")

@bot.command()
async def 鼓励(ctx, member: discord.Member):
    await ctx.send(f"{member.mention}\n{KEYWORDS_PROMPTS['struggle']}")

@bot.command()
async def 浇水(ctx):
    await ctx.send(KEYWORDS_PROMPTS['water_together'])

if __name__ == "__main__":
    keep_alive()  # 启动 Web 服务器
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
