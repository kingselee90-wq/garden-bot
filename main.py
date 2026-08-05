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
# 🌳 共融花园守护兽系统 (超稳定核心词识别版)
# ==========================================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

ai_client = None
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    ai_client = genai.Client(api_key=gemini_api_key)

student_data = {}

def parse_message(content):
    """
    超稳定解析：
    直接抓取核心违规或正向动作，并把名字干净剥离
    """
    content_lower = content.lower()
    
    # ❌ 违规核心词（扣叶子）
    violation_keywords = ["吵闹", "过位", "打架", "情绪", "功课", "讲话"]
    # ✅ 正向核心词（加叶子）
    positive_keywords = ["喝水", "小睡", "打瞌睡", "帮忙", "帮助", "尊重", "安静", "乖"]

    matched_kw = None
    is_violation = True

    # 先检查违规词
    for kw in violation_keywords:
        if kw in content_lower:
            matched_kw = kw
            is_violation = True
            break
            
    # 如果没有违规词，再检查正向词
    if not matched_kw:
        for kw in positive_keywords:
            if kw in content_lower:
                matched_kw = kw
                is_violation = False
                break

    if not matched_kw:
        return None, None, None

    # 提取纯名字：把核心词和多余的描述性词汇全部去掉
    name = content
    for kw in violation_keywords + positive_keywords:
        name = name.replace(kw, "")
        
    for stop_word in ["不要", "要", "请", "别", "去", "了", "很", "太", "没有", "没", "不", "欺骗", "老师", "说", "的"]:
        name = name.replace(stop_word, "")
        
    name = name.strip()
    if not name:
        name = "student"

    return name, matched_kw, is_violation

async def save_data_to_discord(channel):
    """后台静默更新云端存档（不刷屏）"""
    data_str = json.dumps(student_data, ensure_ascii=False)
    try:
        async for message in channel.history(limit=20):
            if message.author == bot.user and "[GARDEN_ARCHIVE_DATA]" in message.content:
                await message.edit(content=f"📂 **[GARDEN_ARCHIVE_DATA - SYSTEM BACKUP]**\n```{data_str}```")
                return
        await channel.send(f"📂 **[GARDEN_ARCHIVE_DATA - SYSTEM BACKUP]**\n```{data_str}```")
    except Exception as e:
        print(f"存档更新失败: {e}")

async def load_data_from_discord(channel):
    """启动时从频道读取存档"""
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
    
    name, keyword, is_violation = parse_message(content)

    if name and keyword:
        if is_violation:
            # ------------------------------------------
            # ❌ 违规扣除树叶
            # ------------------------------------------
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
                f"> **{name} - {keyword}**\n"
                f"> 🔻 **Lose 1 Leaf (-1 Leaf)** 🍃 Total Leaves: **{new_leaves}**\n"
                f"> 🌲 Growth Status: **{tree_status}**\n"
                f"> *（中文：{name}【{keyword}】！扣除 1 片树叶 | 目前总叶数: {new_leaves}）*"
            )
        else:
            # ------------------------------------------
            # ✅ 正向增加树叶
            # ------------------------------------------
            student_data[name] = student_data.get(name, 0) + 1
            leaves = student_data[name]
            
            if leaves <= 10:
                tree_status = "🌱 幼苗期 (Germinating)"
            elif leaves < 30:
                tree_status = "🌿 成长中 (Growing)"
            else:
                tree_status = "🌳 参天大树解锁！(Big Tree Unlocked!)"

            await message.channel.send(
                f"✨ **[{keyword.upper()}]**\n"
                f"> **{name}, great job! (+1 Leaf)** 🍃 Total Leaves: **{leaves}**\n"
                f"> 🌲 Growth Status: **{tree_status}**\n"
                f"> *（中文：{name}表现优秀【{keyword}】！个人 +1 树叶 | 总叶数: {leaves}）*"
            )

        await save_data_to_discord(message.channel)
        return

    # ------------------------------------------
    # 💙 情绪调节
    # ------------------------------------------
    if "badmood" in content.lower():
        await message.channel.send(
            f"💙 **[ENERGY RESET / 情绪重置]**\n"
            f"> **Take a deep breath and relax.**\n"
            f"> *（中文：深呼吸调整一下状态）*"
        )
        return

    await bot.process_commands(message)

@bot.command(name="status")
async def garden_status(ctx):
    await ctx.send(
        f"🌳 **[GARDEN STATUS / 花园状态]**\n"
        f"🟢 **System Online | 超稳定核心词识别已就绪**"
    )

@bot.command(name="rules")
async def garden_rules(ctx):
    await ctx.send(
        f"📜 **[CLASS RULES & CONTRACT / 课室纪律与契约]**\n"
        f"❌ **违规词:** `吵闹`、`过位`、`打架`、`情绪`、`功课`、`讲话`\n"
        f"✅ **正向词:** `喝水`、`小睡`、`帮忙`、`尊重`、`安静`"
    )

@bot.command(name="reset")
async def garden_reset(ctx):
    global student_data
    student_data.clear()
    await save_data_to_discord(ctx.channel)
    await ctx.send(
        f"🔄 **[GARDEN ARCHIVE RESET / 云端存档重置]**\n"
        f"> **All student data reset successfully!**\n"
        f"> *（中文：所有学生数据已成功清空重置！）*"
    )

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ 错误：未找到 DISCORD_TOKEN 环境变量！")
