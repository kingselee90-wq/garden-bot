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
# 🌳 共融花园守护兽系统 (智能姓名清洗 + 后台静默存档)
# ==========================================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

ai_client = None
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    ai_client = genai.Client(api_key=gemini_api_key)

student_data = {}

def clean_student_name(text, keywords_to_remove):
    """智能清洗学生名字，剔除动作词和口语助词"""
    name = text
    for w in keywords_to_remove:
        name = name.replace(w, "")
    # 清理多余的空格、标点、助词
    for stop_word in ["不要", "要", "请", "别", "去", "好好的"]:
        name = name.replace(stop_word, "")
    return name.strip() or "student"

async def save_data_to_discord(channel):
    """将数据打包并更新/发送到后台存档（自动清理旧存档，避免刷屏）"""
    data_str = json.dumps(student_data, ensure_ascii=False)
    try:
        # 寻找最近的一条存档消息进行编辑，如果没有则发一条新消息
        async for message in channel.history(limit=20):
            if message.author == bot.user and "[GARDEN_ARCHIVE_DATA]" in message.content:
                await message.edit(content=f"📂 **[GARDEN_ARCHIVE_DATA - SYSTEM BACKUP]**\n```{data_str}```")
                return
        # 如果没有找到，就发一条
        await channel.send(f"📂 **[GARDEN_ARCHIVE_DATA - SYSTEM BACKUP]**\n```{data_str}```")
    except Exception as e:
        print(f"存档更新失败: {e}")

async def load_data_from_discord(channel):
    """启动时从频道读取最新存档"""
    global student_data
    try:
        async for message in channel.history(limit=50):
            if message.author == bot.user and "[GARDEN_ARCHIVE_DATA]" in message.content:
                content = message.content
                json_start = content.find("```") + 3
                json_end = content.rfind("```")
                if json_start != -1 and json_end != -1:
                    json_str = content[json_start:json_end].replace("json", "").strip()
                    student_data = json.loads(json_str)
                    print(f"✅ 成功从 Discord 恢复数据：{student_data}")
                    break
    except Exception as e:
        print(f"⚠️ 读取存档错误: {e}")

@bot.event
async def on_ready():
    print(f"==========================================")
    print(f" 🌳 守护兽花圃系统已成功启动：{bot.user.name}")
    print(f"==========================================")
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
    violation_type = None
    if any(word in content for word in ["吵闹", "讲话", "安静", "不要讲"]):
        name = clean_student_name(content, ["吵闹", "讲话", "安静", "不要讲话", "不要讲", "别讲"])
        violation_type = "Noise / Talking (吵闹讲话)"
    elif "过位" in content:
        name = clean_student_name(content, ["过位"])
        violation_type = "Wandering (走过位)"
    elif "功课" in content and ("不" in content or "没" in content or "拖" in content):
        name = clean_student_name(content, ["功课", "不", "没", "拖"])
        violation_type = "Skip Homework (不做功课)"

    if violation_type and name:
        current_leaves = student_data.get(name, 0)
        new_leaves = max(0, current_leaves - 1)
        student_data[name] = new_leaves

        if new_leaves <= 10:
            tree_status = "🌱 幼苗期 (Germinating)"
        elif new_leaves < 30:
            tree_status = "🌿 成长中 (Growing)"
        else:
            tree_status = "🌳 参天大树 (Big Tree)"

        await message.channel.send(
            f"🚫 **[RULE VIOLATION / 违规扣除]**\n"
            f"> **{name}, {violation_type}!**\n"
            f"> 🔻 **Lose 1 Leaf (-1 Leaf)** 🍃 Total Leaves: **{new_leaves}**\n"
            f"> 🌲 Growth Status: **{tree_status}**\n"
            f"> *（中文：{name}违规！扣除 1 片树叶 | 目前总叶数: {new_leaves}）*"
        )
        await save_data_to_discord(message.channel)
        return

    # ------------------------------------------
    # ✅ 五要正向行为监控
    # ------------------------------------------
    action_type = None
    if "喝水" in content:
        name = clean_student_name(content, ["喝水"])
        action_type = "Stay Hydrated (保持喝水)"
    elif "小睡" in content or "打瞌睡" in content:
        name = clean_student_name(content, ["小睡", "打瞌睡"])
        action_type = "Pre-class Nap (课前小睡)"
    elif "完成功课" in content or "好功课" in content:
        name = clean_student_name(content, ["完成功课", "好功课"])
        action_type = "Complete Homework (认真功课)"
    elif "帮忙" in content or "帮助" in content:
        name = clean_student_name(content, ["帮忙", "帮助"])
        action_type = "Genuine Help (真诚互助)"
    elif "尊重" in content or "守规矩" in content or "干净" in content:
        name = clean_student_name(content, ["尊重", "守规矩", "干净"])
        action_type = "Respect & Clean (尊重整洁)"

    if action_type and name:
        student_data[name] = student_data.get(name, 0) + 1
        leaves = student_data[name]
        
        if leaves <= 10:
            tree_status = "🌱 幼苗期 (Germinating)"
        elif leaves < 30:
            tree_status = "🌿 成长中 (Growing)"
        else:
            tree_status = "🌳 参天大树解锁！(Big Tree Unlocked!)"

        await message.channel.send(
            f"✨ **[{action_type.upper()}]**\n"
            f"> **{name}, great job! (+1 Leaf)** 🍃 Total Leaves: **{leaves}**\n"
            f"> 🌲 Growth Status: **{tree_status}**\n"
            f"> *（中文：{name}表现优秀！个人 +1 树叶 | 总叶数: {leaves} | 状态: {tree_status}）*"
        )

        await save_data_to_discord(message.channel)
        return

    # ------------------------------------------
    # 💙 情绪调节
    # ------------------------------------------
    if "badmood" in content.lower() or "心情差" in content:
        name = clean_student_name(content, ["badmood", "心情差"])
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
        f"🟢 **System Online | 24小时在线（智能存档已启动）**\n"
        f"📊 **Leaf Milestones / 培植成长规则:**\n"
        f"- 🌱 **0-10 Leaves:** 幼苗期 (Germinating)\n"
        f"- 🌿 **11-29 Leaves:** 成长中 (Growing)\n"
        f"- 🌳 **30+ Leaves:** 解锁参天大树与大奖！(Big Tree Unlocked!)\n\n"
        f"💡 *Type `!rules` for rules, `!reset` to clear archive.*"
    )

@bot.command(name="rules")
async def garden_rules(ctx):
    await ctx.send(
        f"📜 **[CLASS RULES & CONTRACT / 课室纪律与契约]**\n"
        f"✨ *Simple rules for a clean, quiet, and healthy learning environment.*"
    )
    await ctx.send(
        f"❌ **THE 3 DON'TS / 三不（扣除树叶）**\n"
        f"1️⃣ **DO NOT make noise / talk** ➡️ *(中文：不可以吵闹、讲话)*\n"
        f"2️⃣ **DO NOT wander around** ➡️ *(中文：不可以走过位)*\n"
        f"3️⃣ **DO NOT skip homework** ➡️ *(中文：不可以不做功课)*"
    )
    await ctx.send(
        f"✅ **THE 5 DOS / 五要（培植树叶，从小树变大树）**\n"
        f"1️⃣ **Stay hydrated** 💧 | 2️⃣ **Pre-class nap** 💤 | 3️⃣ **Complete homework** 📝\n"
        f"4️⃣ **Genuine help** 🤝 | 5️⃣ **Respect & Clean** 🌿"
    )

@bot.command(name="reset")
async def garden_reset(ctx):
    global student_data
    student_data.clear()
    await save_data_to_discord(ctx.channel)
    await ctx.send(
        f"🔄 **[GARDEN ARCHIVE RESET / 云端存档重置]**\n"
        f"> **All student leaves and tree data have been completely reset!**\n"
        f"> *（中文：所有学生的树叶与小树成长数据已全部清空重置！）*"
    )

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ 错误：未找到 DISCORD_TOKEN 环境变量！")
