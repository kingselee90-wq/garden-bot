import os
import threading
from flask import Flask
import discord
from discord.ext import commands
from google import genai

# ==========================================
# 🌳 网页端口维持器 (应付 Render 检查)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "🌳 Garden Bot is running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ==========================================
# 🌳 共融花园守护兽核心系统 (Guardian Bot)
# ==========================================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 初始化 Google GenAI
ai_client = None
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    ai_client = genai.Client(api_key=gemini_api_key)

@bot.event
async def on_ready():
    print(f"==========================================")
    print(f" 🌳 守护兽花圃系统已成功启动：{bot.user.name}")
    print(f" 🟢 状态：24小时在线中")
    print(f"==========================================")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.strip()
    
    # 1. 华语指令触发 (华语 + 强制英文对照，杜绝“老师我看不懂”的借口)
    if "过位" in content:
        name = content.replace("过位", "").strip() or "同学"
        await message.channel.send(
            f"# ⚠️ 秩序提醒 / ORDER ALERT\n\n"
            f"**{name}，请回到自己的座位。**\n"
            f"*{name}, please stay in your assigned seat immediately.*\n\n"
            f"📌 *(规则明确，拒绝借口 / Rules are clear, no excuses)*"
        )
        return

    # 2. 国际英文通用词触发 (纯英文/国际化，直接执行)
    if "badmood" in content.lower() or "心情差" in content:
        name = content.lower().replace("badmood", "").replace("心情差", "").strip() or "同学"
        await message.channel.send(
            f"# 💙 ENERGY RESET\n\n"
            f"**{name}, take a deep breath and adjust your state. Responsibility starts with self-awareness.**\n\n"
            f"✨ *(情绪可以调整，态度必须负责 / Emotions can be managed, attitude must be responsible)*"
        )
        return

    # 3. 华语指令触发 (打瞌睡 + 英文防借口对照)
    if "打瞌睡" in content:
        name = content.replace("打瞌睡", "").strip() or "同学"
        await message.channel.send(
            f"# 💧 提神提醒 / ENERGY BOOST\n\n"
            f"**{name}，去洗个脸，精神焕发对自己负责！**\n"
            f"*{name}, go wash your face and take responsibility for your own alertness.*\n\n"
            f"🦊 *(对自己负责，从不找借口开始 / Be responsible, start with no excuses)*"
        )
        return

    await bot.process_commands(message)

@bot.command(name="status")
async def garden_status(ctx):
    await ctx.send(
        f"# 🌳 守护兽花圃状态 / GARDEN STATUS\n\n"
        f"🟢 **系统状态 / System Status：24/7 Online**\n"
        f"📊 **【全班树叶里程碑 / Leaf Milestones】**\n"
        f"目标门槛 / Target：`30 片叶子 / Leaves` ➡️ 解锁专属大树与责任成长档案！"
    )

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ 错误：未找到 DISCORD_TOKEN 环境变量！")
