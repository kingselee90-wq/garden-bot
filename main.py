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
# 🌳 共融花园守护兽系统 (双通道分离版)
# ==========================================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

ai_client = None
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    ai_client = genai.Client(api_key=gemini_api_key)

student_data = {}

# 专门指定储存数据的频道名称
ARCHIVE_CHANNEL_NAME = "garden-database"

def parse_message(content):
    try:
        content_lower = content.lower()
        
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

        for kw, info in violation_map.items():
            if kw in content_lower:
                matched_key = kw
                action_info = info
                is_violation = True
                break
                
        if not matched_key:
            for kw, info in positive_map.items():
                if kw in content_lower:
                    matched_key = kw
                    action_info = info
                    is_violation = False
                    break

        if not matched_key:
            return None, None, None, None

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
        print(f"解析出错: {e}")
        return None, None, None, None

async def save_data_to_database_channel(guild):
    """自动寻找并锁定 #garden-database 频道，将所有数据打包备份在这里"""
    try:
        data_str = json.dumps(student_data, ensure_ascii=False)
        target_channel = None
        
        for channel in guild.text_channels:
            if channel.name == ARCHIVE_CHANNEL_NAME:
                target_channel = channel
                break
                
        if not target_channel:
            return
            
        # 寻找已有的存档消息进行更新，如果没有则发一条新消息
        async for message in target_channel.history(limit=20):
            if message.author == bot.user and "[GARDEN_DATABASE_BACKUP]" in message.content:
                await message.edit(content=f"📂 **[GARDEN_DATABASE_BACKUP - SYSTEM ARCHIVE]**\n```{data_str}```")
                return
                
        await target_channel.send(f"📂 **[GARDEN_DATABASE_BACKUP - SYSTEM ARCHIVE]**\n```{data_str}```")
    except Exception as e:
        print(f"数据库频道存档失败: {e}")

async def load_data_from_guild(guild):
    """启动时从 #garden-database 读取历史长期存档"""
    global student_data
    try:
        for channel in guild.text_channels:
            if channel.name == ARCHIVE_CHANNEL_NAME:
                async for message in channel.history(limit=50):
                    if message.author == bot.user and "[GARDEN_DATABASE_BACKUP]" in message.content:
                        content = message.content
                        json_start = content.find("```") + 3
                        json_end = content.rfind("```")
                        if json_start != -1 and json_end != -1:
                            json_str = content[json_start:json_end].replace("json", "").strip()
                            student_data = json.loads(json_str)
                            print(f"✅ 成功从 #{ARCHIVE_CHANNEL_NAME} 恢复数据：{student_data}")
                            return
                break
    except Exception as e:
        print(f"⚠️ 读取数据库频道错误: {e}")

@bot.event
async def on_ready():
    print(f"==========================================")
    print(f" 🌳 专属数据库管理系统已启动：{bot.user.name}")
    print(f"==========================================")
    for guild in bot.guilds:
        await load_data_from_guild(guild)

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
                    f"> 💬 *English: {name}, {desc_en}. Total leaves: {new_leaves}.*\n"
                    f"> 💬 *中文：{name}【{title_str}】！扣除 1 片树叶 | 目前总叶数: {new_leaves}*"
                )
            else:
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
                    f"> 💬 *English: Great job, {name}! Total leaves: {leaves}.*\n"
                    f"> 💬 *中文：{name}表现优秀【{title_str}】！个人 +1 树叶 | 总叶数: {leaves}*"
                )

            # 自动同步更新到 #garden-database 专属数据库频道
            await save_data_to_database_channel(message.guild)
            return

        if "badmood" in content.lower():
            await message.channel.send(
                f"💙 **[ENERGY RESET / 情绪重置]**\n"
                f"> **Take a deep breath and relax. / 深呼吸调整一下状态。**"
            )
            return

        await bot.process_commands(message)
    except Exception as e:
        print(f"处理消息异常: {e}")

@bot.command(name="status")
async def garden_status(ctx):
    await ctx.send(f"🌳 **[GARDEN STATUS]**\n🟢 **System Online | 专属数据库频道 [{ARCHIVE_CHANNEL_NAME}] 已绑定**")

@bot.command(name="rules")
async def garden_rules(ctx):
    await ctx.send(
        f"📜 **[CLASS RULES & CONTRACT]**\n"
        f"❌ **扣分词:** `吵闹`、`过位`、`打架`、`功课/拖`、`情绪/欺骗`\n"
        f"✅ **加分词:** `喝水`、`小睡`、`帮忙`、`尊重`、`安静`\n"
        f"📊 **指令:** 输入 `!summary` 查看长期积分榜。"
    )

@bot.command(name="summary")
async def garden_summary(ctx):
    if not student_data:
        await ctx.send("📊 **[LONG-TERM SUMMARY]**\n> 暂无学生积分数据 / No student data yet.")
        return
        
    report = "📊 **[GARDEN LEADERBOARD / 长期积分排行榜]**\n━━━━━━━━━━━━━━━━━━━\n"
    for name, leaves in sorted(student_data.items(), key=lambda x: x[1], reverse=True):
        if leaves <= 10:
            status = "🌱 幼苗"
        elif leaves < 30:
            status = "🌿 成长"
        else:
            status = "🌳 大树"
        report += f"• **{name}**: 🍃 {leaves} leaves ({status})\n"
    
    report += "━━━━━━━━━━━━━━━━━━━\n✨ *Keep growing! / 继续加油成长！*"
    await ctx.send(report)

@bot.command(name="reset")
async def garden_reset(ctx):
    global student_data
    student_data.clear()
    await save_data_to_database_channel(ctx.guild)
    await ctx.send(
        f"🔄 **[TERM RESET / 完全重置]**\n"
        f"> **All data cleared and synced to database!**\n"
        f"> *（中文：所有长期数据已清空并同步至数据库频道！）*"
    )

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ 错误：未找到 DISCORD_TOKEN 环境变量！")
