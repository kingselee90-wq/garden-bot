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
# 🌳 共融花园守护兽系统 (双语全景版)
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
    """超安全解析：双语标签与精准名字提取"""
    try:
        content_lower = content.lower()
        
        # ❌ 违规核心词及对应的英文说明
        violation_map = {
            "吵闹": ("Noise / 吵闹", "Making noise"),
            "过位": ("Wandering / 走过位", "Wandering around"),
            "打架": ("Fighting / 打架", "Fighting"),
            "情绪": ("Bad Mood / 闹情绪", "Emotional outburst"),
            "功课": ("Homework Issue / 功课问题", "Incomplete or missing homework"),
            "拖": ("Homework Delay / 拖延功课", "Delaying work"),
            "讲话": ("Talking / 讲话", "Talking in class"),
            "欺骗": ("Dishonesty / 不诚实", "Dishonesty")
        }
        
        # ✅ 正向核心词及对应的英文说明
        positive_map = {
            "喝水": ("Stay Hydrated / 保持喝水", "Drinking water"),
            "小睡": ("Pre-class Nap / 课前小睡", "Taking a nap"),
            "打瞌睡": ("Pre-class Nap / 课前小睡", "Taking a nap"),
            "帮忙": ("Genuine Help / 真诚帮忙", "Helping out"),
            "帮助": ("Genuine Help / 真诚帮忙", "Helping out"),
            "尊重": ("Respect / 尊重他人", "Showing respect"),
            "安静": ("Quiet & Focused / 安静专注", "Staying quiet and focused"),
            "乖": ("Good Behavior / 表现乖巧", "Good behavior")
        }

        matched_key = None
        is_violation = True
        action_info = None

        # 检查违规词
        for kw, info in violation_map.items():
            if kw in content_lower:
                matched_key = kw
                action_info = info
                is_violation = True
                break
                
        # 检查正向词
        if not matched_key:
            for kw, info in positive_map.items():
                if kw in content_lower:
                    matched_key = kw
                    action_info = info
                    is_violation = False
                    break

        if not matched_key:
            return None, None, None, None

        # 提取纯名字：把核心词和多余的口语修饰词洗掉
        name = content
        all_keywords = list(violation_map.keys()) + list(positive_map.keys())
        for kw in all_keywords:
            name = name.replace(kw, "")
            
        for stop_word in ["做", "没有", "没", "不", "不要", "要", "请", "别", "去", "了", "很", "太", "欺骗", "老师", "说", "的", "把", "作业"]:
            name = name.replace(stop_word, "")
            
        name = name.strip()
        if not name:
            name = "student"

        return name, matched_key, action_info, is_violation
    except Exception as e:
        print(f"解析出错（已自动拦截）: {e}")
        return None, None, None, None

async def save_data_to_discord(channel):
    """后台静默更新云端存档（不刷屏）"""
    try:
        data_str = json.dumps(student_data, ensure_ascii=False)
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
            try:
                if channel.permissions_for(guild.me).read_message_history:
                    await load_data_from_discord(channel)
                    break
            except:
                continue

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    try:
        content = message.content.strip()
        
        name, keyword, action_info, is_violation = parse_message(content)

        if name and action_info:
            title_str, desc_en = action_info
            
            if is_violation:
                # ------------------------------------------
                # ❌ 违规扣除树叶（双语提示）
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
                    f"> **{name} — {title_str}**\n"
                    f"> 🔻 **Lose 1 Leaf (-1 Leaf)** 🍃 Total Leaves: **{new_leaves}**\n"
                    f"> 🌲 Growth Status: **{tree_status}**\n"
                    f"> 💬 *English: {name}, {desc_en}. You lost 1 leaf. Total leaves: {new_leaves}.*\n"
                    f"> 💬 *中文：{name}【{title_str}】！扣除 1 片树叶 | 目前总叶数: {new_leaves}*"
                )
            else:
                # ------------------------------------------
                # ✅ 正向增加树叶（双语提示）
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
                    f"✨ **[{title_str.upper()}]**\n"
                    f"> **{name}, great job! (+1 Leaf)** 🍃 Total Leaves: **{leaves}**\n"
                    f"> 🌲 Growth Status: **{tree_status}**\n"
                    f"> 💬 *English: Great job, {name}! ({desc_en}) You earned +1 leaf. Total leaves: {leaves}.*\n"
                    f"> 💬 *中文：{name}表现优秀【{title_str}】！个人 +1 树叶 | 总叶数: {leaves}*"
                )

            await save_data_to_discord(message.channel)
            return

        if "badmood" in content.lower():
            await message.channel.send(
                f"💙 **[ENERGY RESET / 情绪重置]**\n"
                f"> **Take a deep breath and relax. / 深呼吸调整一下状态。**"
            )
            return

        await bot.process_commands(message)
    except Exception as e:
        print(f"处理消息时发生异常（已安全拦截）: {e}")

@bot.command(name="status")
async def garden_status(ctx):
    await ctx.send(f"🌳 **[GARDEN STATUS / 花园状态]**\n🟢 **System Online | Bilingual Mode Active (双语模式已开启)**")

@bot.command(name="rules")
async def garden_rules(ctx):
    await ctx.send(
        f"📜 **[CLASS RULES & CONTRACT / 课室纪律与契约]**\n"
        f"❌ **三不扣分词 / Deductions:** `吵闹(Noise)`、`过位(Wandering)`、`打架(Fighting)`、`功课/拖(Homework)`、`情绪/欺骗(Emotions/Dishonesty)`\n"
        f"✅ **五要加分词 / Rewards:** `喝水(Hydrated)`、`小睡(Nap)`、`帮忙(Help)`、`尊重(Respect)`、`安静(Quiet)`"
    )

@bot.command(name="reset")
async def garden_reset(ctx):
    global student_data
    student_data.clear()
    await save_data_to_discord(ctx.channel)
    await ctx.send(
        f"🔄 **[GARDEN ARCHIVE RESET / 云端存档重置]**\n"
        f"> **All student data reset successfully! / 所有学生数据已成功清空重置！**"
    )

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ 错误：未找到 DISCORD_TOKEN 环境变量！")
