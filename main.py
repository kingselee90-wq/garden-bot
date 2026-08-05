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
# 🌳 共融花园守护兽系统 (取消甘露，全面回归叶子与全班+5分)
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
    
    # ------------------------------------------
    # ❌ 三不违规监控
    # ------------------------------------------
    if "吵闹" in content:
        name = content.replace("吵闹", "").strip() or "student"
        await message.channel.send(
            f"🚫 **[KEEP QUIET / 保持安静]**\n"
            f"> **{name}, do not make noise!**\n"
            f"> *（中文：{name}，不可以吵闹！）*"
        )
        return

    if "过位" in content:
        name = content.replace("过位", "").strip() or "student"
        await message.channel.send(
            f"🚫 **[STAY IN YOUR SEAT / 请回到座位]**\n"
            f"> **{name}, do not wander around!**\n"
            f"> *（中文：{name}，不可以走过位！）*"
        )
        return

    if "功课" in content and ("不" in content or "没" in content or "拖" in content):
        name = content.replace("功课", "").replace("不", "").replace("没", "").replace("拖", "").strip() or "student"
        await message.channel.send(
            f"🚫 **[COMPLETE HOMEWORK / 按时完成功课]**\n"
            f"> **{name}, do not skip your homework!**\n"
            f"> *（中文：{name}，不可以不做功课！）*"
        )
        return

    # ------------------------------------------
    # ✅ 五要正向行为监控（个人 +1 Leaf，全班 Dojo +5 分）
    # ------------------------------------------
    if "喝水" in content:
        name = content.replace("喝水", "").strip() or "student"
        await message.channel.send(
            f"💧 **[STAY HYDRATED / 保持喝水]**\n"
            f"> **{name}, great job! (+1 Leaf | Class Dojo: +5 Pts)**\n"
            f"> *（中文：{name}，好样保持喝水！个人 +1 树叶 | 全班 Dojo +5 分）*"
        )
        return

    if "小睡" in content or "打瞌睡" in content:
        name = content.replace("小睡", "").replace("打瞌睡", "").strip() or "student"
        await message.channel.send(
            f"💤 **[PRE-CLASS NAP / 课前小睡]**\n"
            f"> **{name}, taking a short rest! (+1 Leaf | Class Dojo: +5 Pts)**\n"
            f"> *（中文：{name}小睡充电！个人 +1 树叶 | 全班 Dojo +5 分）*"
        )
        return

    if "完成功课" in content or "好功课" in content:
        name = content.replace("完成功课", "").replace("好功课", "").strip() or "student"
        await message.channel.send(
            f"📝 **[HOMEWORK COMPLETED / 认真完成功课]**\n"
            f"> **{name}, excellent focus! (+1 Leaf | Class Dojo: +5 Pts)**\n"
            f"> *（中文：{name}专心完成功课！个人 +1 树叶 | 全班 Dojo +5 分）*"
        )
        return

    if "帮忙" in content or "帮助" in content:
        name = content.replace("帮忙", "").replace("帮助", "").strip() or "student"
        await message.channel.send(
            f"🤝 **[GENUINE HELP / 真诚互助]**\n"
            f"> **{name}, thank you for helping genuinely! (+1 Leaf | Class Dojo: +5 Pts)**\n"
            f"> *（中文：{name}真诚帮助大家！个人 +1 树叶 | 全班 Dojo +5 分）*"
        )
        return

    if "尊重" in content or "守规矩" in content or "干净" in content:
        name = content.replace("尊重", "").replace("守规矩", "").replace("干净", "").strip() or "student"
        await message.channel.send(
            f"🌿 **[RESPECT & CLEAN / 尊重与保持整洁]**\n"
            f"> **{name}, keeping environment clean & respectful! (+1 Leaf | Class Dojo: +5 Pts)**\n"
            f"> *（中文：{name}保持环境干净整洁！个人 +1 树叶 | 全班 Dojo +5 分）*"
        )
        return

    # ------------------------------------------
    # 💙 情绪调节
    # ------------------------------------------
    if "badmood" in content.lower() or "心情差" in content:
        name = content.lower().replace("badmood", "").replace("心情差", "").strip() or "student"
        await message.channel.send(
            f"💙 **[ENERGY RESET / 情绪重置]**\n"
            f"> **{name}, take a deep breath and relax.**\n"
            f"> *（中文：{name}，深呼吸调整一下状态）*"
        )
        return

    await bot.process_commands(message)

@bot.command(name="status")
async def garden_status(ctx):
    await ctx.send(
        f"🌳 **[GARDEN STATUS / 花园状态]**\n"
        f"🟢 **System Online | 守护兽24小时在线**\n"
        f"📊 **Leaf Milestones / 全班树叶与 Dojo 积分进度:**\n"
        f"- 🌱 **0-10 Leaves:** Germinating (幼苗期)\n"
        f"- 🌿 **11-29 Leaves:** Growing (成长中)\n"
        f"- 🌳 **30+ Leaves:** UNLOCK BIG TREES & REWARDS! (解锁大树与大奖！)\n\n"
        f"💡 *Type `!rules` to view the 3 Don'ts & 5 Dos.*"
    )

@bot.command(name="rules")
async def garden_rules(ctx):
    """一键查看 3不 & 5要 契约（纯树叶与 Dojo +5 分机制）"""
    await ctx.send(
        f"📜 **[CLASS RULES & CONTRACT / 课室纪律与契约]**\n"
        f"✨ *Simple rules for a clean, quiet, and healthy learning environment.*\n"
        f"✨ *（保持干净、安静、健康的学习环境，我们的规矩很简单）*"
    )
    
    await ctx.send(
        f"❌ **THE 3 DON'TS / 三不（失去树叶与自由）**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"1️⃣ **DO NOT make noise** ➡️ *(中文：不可以吵闹)*\n"
        f"2️⃣ **DO NOT wander around** ➡️ *(中文：不可以走过位)*\n"
        f"3️⃣ **DO NOT skip homework** ➡️ *(中文：不可以不做功课)*"
    )
    
    await ctx.send(
        f"✅ **THE 5 DOS / 五要（获得树叶 + 全班 Dojo +5 分）**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"1️⃣ **Stay hydrated:** Drink water 💧 ➡️ *（中文：保持喝水 | 个人 +1叶，全班Dojo +5分）*\n"
        f"2️⃣ **Pre-class nap:** Rest to prevent sleepiness 💤 ➡️ *（中文：课前小睡 | 个人 +1叶，全班Dojo +5分）*\n"
        f"3️⃣ **Complete homework well:** Focus on tasks 📝 ➡️ *（中文：好好完成功课 | 个人 +1叶，全班Dojo +5分）*\n"
        f"4️⃣ **Be genuinely helpful:** Help peers honestly 🤝 ➡️ *（中文：诚实帮助他人 | 个人 +1叶，全班Dojo +5分）*\n"
        f"5️⃣ **Respect & Keep clean:** Keep environment quiet & clean 🌿 ➡️ *（中文：尊重师生环境 | 个人 +1叶，全班Dojo +5分）* "
    )

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ 错误：未找到 DISCORD_TOKEN 环境变量！")
