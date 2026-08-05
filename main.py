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
# 🌳 共融花园守护兽系统 (多卡片大字 + 英文视觉主导)
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
            f"# 🌿 SPACE ANCHOR\n"
            f"### **{name}, please return to your assigned seat immediately.**\n"
            f"*（中文：{name}，请回到专属座位）*"
        )
        return

    # 2. 心情差
    if "badmood" in content.lower() or "心情差" in content:
        name = content.lower().replace("badmood", "").replace("心情差", "").strip() or "student"
        await message.channel.send(
            f"# 💙 EMOTIONAL SAFE HAVEN\n"
            f"### **{name}, take a deep breath and reset your state.**\n"
            f"*（中文：{name}，深呼吸，调整状态）*"
        )
        return

    # 3. 打瞌睡
    if "打瞌睡" in content or "不洗脸" in content:
        name = content.replace("打瞌睡", "").replace("不洗脸", "").strip() or "student"
        await message.channel.send(
            f"# 💧 ENERGY RENEWAL\n"
            f"### **{name}, go wash your face and recharge!**\n"
            f"*（中文：{name}，去洗个脸充电）*"
        )
        return

    await bot.process_commands(message)

@bot.command(name="status")
async def garden_status(ctx):
    """大字化状态看板"""
    await ctx.send(
        f"# 🌳 GARDEN GROWTH STATUS\n"
        f"### **System Online | Guardian Beast Active**\n"
        f"📊 **Leaf Milestones / 全班树叶里程碑:**\n"
        f"- 🌱 **0-10 Leaves:** Germinating (幼苗期)\n"
        f"- 🌿 **11-29 Leaves:** Growing Steadily (成长中)\n"
        f"- 🌳 **30+ Leaves:** UNLOCK EXCLUSIVE BIG TREES! (解锁专属大树与大奖！)\n\n"
        f"*Type `!rules` to check the contract.*"
    )

@bot.command(name="rules")
async def garden_rules(ctx):
    """分段发送大字卡片，英文绝对主导，彻底杜绝借口"""
    
    # 卡片 1：总契约大标题
    await ctx.send(
        f"# 📜 GARDEN RULES & GROWTH CONTRACT\n"
        f"> **Make independent choices. Take responsibility for your space & freedom.**\n"
        f"> *（中文总则：自主选择，为自己的空间与自由负责）*"
    )
    
    # 卡片 2：3不（红色警示，英文超大字，华语缩小做对比）
    await ctx.send(
        f"## ❌ THE 3 'DON'TS' (Lose Leaves & Free Time)\n"
        f"### **1. Do not leave your seat randomly**\n"
        f"👉 *Result: Lose Leaves & Free Time Freeze* | *(中文：随意过位 ➡️ 扣树叶 & 冻结自由)*\n\n"
        f"### **2. Do not avoid emotions or waste focus time**\n"
        f"👉 *Result: Lose Leaves & Affect Team Dew* | *(中文：逃避情绪 ➡️ 扣树叶 & 影响团队)*\n\n"
        f"### **3. Do not make excuses like 'I don't understand'**\n"
        f"👉 *Result: Reset state & Lose daily privileges* | *(中文：拒绝借口 ➡️ 失去当日特权)*"
    )
    
    # 卡片 3：5要（绿色正向，英文超大字）
    await ctx.send(
        f"## ✅ THE 5 'DOS' (Earn Leaves & Free Time)\n"
        f"### **1. Self-Awareness:** Adjust your mood proactively ➡️ **Earn Leaf +1** *(主动调整情绪)*\n"
        f"### **2. Energy Boost:** Wash your face and stay fresh ➡️ **Earn Leaf +1** *(保持清醒提神)*\n"
        f"### **3. Space Respect:** Keep your seat and order ➡️ **Earn Team Dew ++** *(维护空间秩序)*\n"
        f"### **4. Responsibility:** Face challenges without excuses ➡️ **Unlock Milestones** *(勇敢承担成长)*\n"
        f"### **5. Teamwork:** Protect the garden together (30 Leaves) ➡️ **Unlock Big Tree & Grand Prize!** *(互助共荣大奖)*"
    )

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ 错误：未找到 DISCORD_TOKEN 环境变量！")
