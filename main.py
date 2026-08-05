import os
import threading
import json
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
# 🌳 共融花园守护兽系统 (Discord 频道永久存档机制)
# ==========================================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

ai_client = None
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    ai_client = genai.Client(api_key=gemini_api_key)

# 内存数据字典：格式 { "学生名字": 树叶数 }
student_data = {}

async def save_data_to_discord(channel):
    """将当前所有学生的分数打包成一段 JSON 密文，发送到 Discord 频道作为永恒存档"""
    data_str = json.dumps(student_data, ensure_ascii=False)
    # 用一个特殊的标记包裹，方便 Bot 以后重启时自动读取
    await channel.send(f"📂 **[GARDEN_ARCHIVE_DATA]**\n```{data_str}```")

async def load_data_from_discord(channel):
    """当 Bot 启动时，自动去频道里搜寻最近的一条存档消息，恢复所有学生的树叶数据"""
    global student_data
    try:
        async for message in channel.history(limit=50):
            if message.author == bot.user and "[GARDEN_ARCHIVE_DATA]" in message.content:
                # 提取代码块中的 JSON 数据
                content = message.content
                json_start = content.find("```") + 3
                json_end = content.rfind("```")
                if json_start != -1 and json_end != -1:
                    json_str = content[json_start:json_end].replace("json", "").strip()
                    student_data = json.loads(json_str)
                    print(f"✅ 成功从 Discord 频道恢复存档数据：{student_data}")
                    break
    except Exception as e:
        print(f"⚠️ 读取存档时发生错误: {e}")

@bot.event
async def on_ready():
    print(f"==========================================")
    print(f" 🌳 守护兽花圃系统已成功启动：{bot.user.name}")
    print(f" 🟢 状态：24小时在线中（Discord 云端存档已就绪）")
    print(f"==========================================")
    # 启动时自动尝试从当前服务器的所有文本频道恢复数据
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).read_message_history:
                await load_data_from_discord(channel)
                break

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
    # ✅ 五要正向行为监控（自动累积 + 触发存档）
    # ------------------------------------------
    action_type = None
    if "喝水" in content:
        name = content.replace("喝水", "").strip() or "student"
        action_type = "Stay Hydrated (保持喝水)"
    elif "小睡" in content or "打瞌睡" in content:
        name = content.replace("小睡", "").replace("打瞌睡", "").strip() or "student"
        action_type = "Pre-class Nap (课前小睡)"
    elif "完成功课" in content or "好功课" in content:
        name = content.replace("完成功课", "").replace("好功课", "").strip() or "student"
        action_type = "Complete Homework (认真功课)"
    elif "帮忙" in content or "帮助" in content:
        name = content.replace("帮忙", "").replace("帮助", "").strip() or "student"
        action_type = "Genuine Help (真诚互助)"
    elif "尊重" in content or "守规矩" in content or "干净" in content:
        name = content.replace("尊重", "").replace("守规矩", "").replace("干净", "").strip() or "student"
        action_type = "Respect & Clean (尊重整洁)"

    if action_type and name:
        # 1. 内存中加分
        student_data[name] = student_data.get(name, 0) + 1
        leaves = student_data[name]
        
        # 2. 判定小树变大树等级
        if leaves <= 10:
            tree_status = "🌱 幼苗期 (Germinating)"
        elif leaves < 30:
            tree_status = "🌿 成长中 (Growing)"
        else:
            tree_status = "🌳 参天大树解锁！(Big Tree Unlocked!)"

        # 3. 发送双语卡片
        await message.channel.send(
            f"✨ **[{action_type.upper()}]**\n"
            f"> **{name}, great job! (+1 Leaf)** 🍃 Total Leaves: **{leaves}**\n"
            f"> 🌲 Growth Status: **{tree_status}**\n"
            f"> *（中文：{name}表现优秀！个人 +1 树叶 | 总叶数: {leaves} | 状态: {tree_status}）*"
        )

        # 4. 自动把最新数据存档到 Discord 频道中
        await save_data_to_discord(message.channel)
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
        f"🟢 **System Online | 守护兽24小时在线（Discord 云端存档已开启）**\n"
        f"📊 **Leaf Milestones / 培植成长规则:**\n"
        f"- 🌱 **0-10 Leaves:** 幼苗期 (Germinating)\n"
        f"- 🌿 **11-29 Leaves:** 成长中 (Growing)\n"
        f"- 🌳 **30+ Leaves:** 解锁参天大树与大奖！(Big Tree Unlocked!)\n\n"
        f"💡 *Type `!rules` for rules, `!reset` to clear archive.*"
    )

@bot.command(name="rules")
async def garden_rules(ctx):
    """一键查看 3不 & 5要 契约"""
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
        f"✅ **THE 5 DOS / 五要（培植树叶，从小树变大树）**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"1️⃣ **Stay hydrated:** Drink water 💧 ➡️ *（中文：保持喝水 | 个人 +1叶）*\n"
        f"2️⃣ **Pre-class nap:** Rest to prevent sleepiness 💤 ➡️ *（中文：课前小睡 | 个人 +1叶）*\n"
        f"3️⃣ **Complete homework well:** Focus on tasks 📝 ➡️ *（中文：好好完成功课 | 个人 +1叶）*\n"
        f"4️⃣ **Be genuinely helpful:** Help peers honestly 🤝 ➡️ *（中文：诚实帮助他人 | 个人 +1叶）*\n"
        f"5️⃣ **Respect & Keep clean:** Keep environment quiet & clean 🌿 ➡️ *（中文：尊重师生环境 | 个人 +1叶）* "
    )

@bot.command(name="reset")
async def garden_reset(ctx):
    """只有当您主动输入 !reset 时，才会清空所有存档"""
    global student_data
    student_data.clear()
    # 同时在频道发一条清空后的存档
    await save_data_to_discord(ctx.channel)
    await ctx.send(
        f"🔄 **[GARDEN ARCHIVE RESET / 云端存档重置]**\n"
        f"> **All student leaves and tree data have been completely reset!**\n"
        f"> *（中文：所有学生的树叶与小树成长数据已通过指令彻底清空重置！）*"
    )

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ 错误：未找到 DISCORD_TOKEN 环境变量！")
