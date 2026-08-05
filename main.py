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
# 🌳 共融花园守护兽系统 (全智能模糊匹配版)
# ==========================================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

ai_client = None
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    ai_client = genai.Client(api_key=gemini_api_key)

student_data = {}

def clean_name_and_extract_action(content):
    """
    智能分析老师的输入：
    自动从一句话中分离出【学生名字】和【行为动作】
    """
    # 所有的关键词列表（违规 + 正向）
    all_keywords = [
        "吵闹", "过位", "打架", "闹情绪", "不做功课", "没交功课", "讲话",
        "喝水", "小睡", "打瞌睡", "完成功课", "好功课", "帮忙", "帮助", "尊重", "守规矩", "干净", "安静", "乖"
    ]
    
    matched_keyword = None
    for kw in all_keywords:
        if kw in content:
            matched_keyword = kw
            break
            
    if not matched_keyword:
        return None, None, None

    # 提取名字：把关键词和常见口语助词、副词从原话中剔除
    name = content
    for kw in all_keywords:
        name = name.replace(kw, "")
        
    for stop_word in ["不要", "要", "请", "别", "去", "了", "很", "太", "没有", "没", "不"]:
        name = name.replace(stop_word, "")
        
    name = name.strip()
    if not name:
        name = "student"

    # 判断是违规(Negative)还是正向(Positive)
    is_violation = matched_keyword in ["吵闹", "过位", "打架", "闹情绪", "不做功课", "没交功课", "讲话"]
    
    return name, matched_keyword, is_violation

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
    
    # 调动智能解析函数
    name, keyword, is_violation = clean_name_and_extract_action(content)

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
            # ✅ 正向行为增加树叶
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
    # 💙 情绪调节（支持单独输入）
    # ------------------------------------------
    if "badmood" in content.lower() or "心情差" in content:
        name = content.replace("心情差", "").replace("badmood", "").strip() or "同学"
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
        f"🟢 **System Online | 24小时智能模糊识别已开启**\n"
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
        f"✨ *支持自由语句输入，只要包含核心词即可自动识别！*"
    )
    await ctx.send(
        f"❌ **三不监控（扣除树叶）:** `吵闹`、`过位`、`打架`、`闹情绪`、`不做功课`、`讲话`"
    )
    await ctx.send(
        f"✅ **五要监控（培植树叶）:** `喝水`、`小睡`、`完成功课`、`帮忙`、`尊重/安静`"
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
