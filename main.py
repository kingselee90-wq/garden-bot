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
# 🌳 共融花园守护兽系统 (精确3不5要 + 纯正双语小卡片)
# ==========================================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

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
    
    # 1. 过位
    if "过位" in content:
        name = content.replace("过位", "").strip() or "student"
        await message.channel.send(
            f"🚫 **[STAY IN YOUR SEAT / 请回到座位]**\n"
            f"> **{name}, do not wander around!**\n"
            f"> *（中文：{name}，不可以走过位！）*"
        )
        return

    # 2. 心情差/badmood
    if "badmood" in content.lower() or "心情差" in content:
        name = content.lower().replace("badmood", "").replace("心情差", "").strip() or "student"
        await message.channel.send(
            f"💙 **[ENERGY RESET / 情绪重置]**\n"
            f"> **{name}, take a deep breath and relax.**\n"
            f"> *（中文：{name}，深呼吸调整一下状态）*"
        )
        return

    # 3. 打瞌睡
    if "打瞌睡" in content or "不洗脸" in content:
        name = content.replace("打瞌睡", "").replace("不洗脸", "").strip() or "student"
        await message.channel.send(
            f"💧 **[STAY AWAKE / 提神醒脑]**\n"
            f"> **{name}, go wash your face and stay fresh!**\n"
            f"> *（中文：{name}，去洗个脸防打瞌睡！）*"
        )
        return

    await bot.process_commands(message)

@bot.command(name="status")
async def garden_status(ctx):
    """状态与里程碑看板"""
    await ctx.send(
        f"🌳 **[GARDEN STATUS / 花园状态]**\n"
        f"🟢 **System Online | 守护兽24小时在线**\n"
        f"📊 **Leaf Milestones / 全班树叶进度:**\n"
        f"- 🌱 **0-10 Leaves:** Germinating (幼苗期)\n"
        f"- 🌿 **11-29 Leaves:** Growing (成长中)\n"
        f"- 🌳 **30+ Leaves:** UNLOCK BIG TREES & REWARDS! (解锁大树与大奖！)\n\n"
        f"💡 *Type `!rules` to view the 3 Don'ts & 5 Dos.*"
    )

@bot.command(name="rules")
async def garden_rules(ctx):
    """完美对应老师您的 3不 & 5要，卡片式双语大字呈现"""
    
    # 标题卡片
    await ctx.send(
        f"📜 **[CLASS RULES & CONTRACT / 课室纪律与契约]**\n"
        f"✨ *Simple rules for a clean, quiet, and healthy learning environment.*\n"
        f"✨ *（保持干净、安静、健康的学习环境，我们的规矩很简单）*"
    )
    
    # ❌ 3不卡片 (模拟小图卡视觉)
    await ctx.send(
        f"❌ **THE 3 DON'TS (Lose Leaves & Free Time) / 三不（失去树叶与自由）**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"1️⃣ **DO NOT make noise** \n"
        f"👉 *（中文：不可以吵闹）*\n\n"
        f"2️⃣ **DO NOT wander around (过位)** \n"
        f"👉 *（中文：不可以走过位）*\n\n"
        f"3️⃣ **DO NOT skip homework** \n"
        f"👉 *（中文：不可以不做功课）*"
    )
    
    # ✅ 5要卡片 (模拟小图卡视觉)
    await ctx.send(
        f"✅ **THE 5 DOS (Earn Leaves & Free Time) / 五要（获得树叶与自由）**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"1️⃣ **Stay hydrated:** Drink enough water 💧 \n"
        f"👉 *（中文：保持喝水）*\n\n"
        f"2️⃣ **Pre-class nap:** Rest before class to prevent sleepiness 💤 \n"
        f"👉 *（中文：课前小睡防打瞌睡）*\n\n"
        f"3️⃣ **Complete homework well:** Focus and finish tasks 📝 \n"
        f"👉 *（中文：好好完成功课）*\n\n"
        f"4️⃣ **Be genuinely helpful:** Help peers and teachers honestly (Not fake) 🤝 \n"
        f"👉 *（中文：诚实帮助同学老师，不虚假）*\n\n"
        f"5️⃣ **Respect & Keep clean:** Respect others, keep the environment quiet & clean 🌿 \n"
        f"👉 *（中文：尊重师生，保持环境安静干净）*"
    )

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ 错误：未找到 DISCORD_TOKEN 环境变量！")
