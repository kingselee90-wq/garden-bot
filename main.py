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
# 🌳 共融花园智能守护兽系统 (Gemini 智能语义理解版)
# ==========================================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 初始化 Gemini AI 客户端
ai_client = None
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    ai_client = genai.Client(api_key=gemini_api_key)

student_data = {}
ARCHIVE_CHANNEL_NAME = "garden-database"

async def save_data_to_database_channel(guild):
    """自动将长期数据备份到 #garden-database 专属频道"""
    try:
        data_str = json.dumps(student_data, ensure_ascii=False)
        target_channel = None
        for channel in guild.text_channels:
            if channel.name == ARCHIVE_CHANNEL_NAME:
                target_channel = channel
                break
        if not target_channel:
            return
            
        async for message in target_channel.history(limit=20):
            if message.author == bot.user and "[GARDEN_DATABASE_BACKUP]" in message.content:
                await message.edit(content=f"📂 **[GARDEN_DATABASE_BACKUP - AI SMART ARCHIVE]**\n```{data_str}```")
                return
        await target_channel.send(f"📂 **[GARDEN_DATABASE_BACKUP - AI SMART ARCHIVE]**\n```{data_str}```")
    except Exception as e:
        print(f"存档失败: {e}")

async def load_data_from_guild(guild):
    """启动时从专属频道恢复长期积分"""
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
                            print(f"✅ AI 智能版成功恢复数据：{student_data}")
                            return
                break
    except Exception as e:
        print(f"⚠️ 恢复数据错误: {e}")

@bot.event
async def on_ready():
    print(f"==========================================")
    print(f" 🌳 AI 智能守护兽系统已成功启动：{bot.user.name}")
    print(f"==========================================")
    for guild in bot.guilds:
        await load_data_from_guild(guild)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # 如果是普通指令（以 ! 开头），交给指令处理函数
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    # 🟢 核心亮点：利用 Gemini AI 智能分析老师输入的日常句子
    if ai_client:
        try:
            prompt = f"""
            你是一个安亲班/课室管理智能助手。请分析老师输入的这句话，判断它是关于哪个学生的课堂表现，并提取信息。
            老师输入的内容: "{message.content}"
            
            请严格按照以下 JSON 格式返回，不要包含任何 markdown 符号（如 ```json），只返回纯 JSON：
            {{
                "student_name": "学生名字（如果没提到名字返回 null）",
                "is_violation": true 或 false（true代表违规扣分，false代表表现优秀加分）,
                "behavior_title_cn": "中文行为简述（如：上课吵闹、主动帮忙、功课拖延）",
                "behavior_title_en": "英文行为简述（如：Making noise, Helping out, Homework delay）",
                "description": "一句简短的说明"
            }}
            """
            
            response = ai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            
            res_text = response.text.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(res_text)
            
            name = data.get("student_name")
            is_violation = data.get("is_violation")
            title_cn = data.get("behavior_title_cn", "表现")
            title_en = data.get("behavior_title_en", "Behavior")
            
            if name and name != "null":
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
                        f"🚫 **[AI RULE VIOLATION / 违规扣除]**\n"
                        f"> **{name} — {title_cn}**\n"
                        f"> 🔻 **Lose 1 Leaf (-1 Leaf)** 🍃 Total Leaves: **{new_leaves}**\n"
                        f"> 🌲 Growth Status: **{tree_status}**\n"
                        f"> 💬 *English: {name}, {title_en}. Total leaves: {new_leaves}.*\n"
                        f"> 💬 *中文：{name}【{title_cn}】！扣除 1 片树叶 | 目前总叶数: {new_leaves}*"
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
                        f"✨ **[{title_cn.upper()}]**\n"
                        f"> **{name}, great job! (+1 Leaf)** 🍃 Total Leaves: **{leaves}**\n"
                        f"> 🌲 Growth Status: **{tree_status}**\n"
                        f"> 💬 *English: Great job, {name}! ({title_en}) Total leaves: {leaves}.*\n"
                        f"> 💬 *中文：{name}表现优秀【{title_cn}】！个人 +1 树叶 | 总叶数: {leaves}*"
                    )

                await save_data_to_database_channel(message.guild)
                return
        except Exception as e:
            print(f"AI 智能解析出错: {e}")

    await bot.process_commands(message)

@bot.command(name="status")
async def garden_status(ctx):
    await ctx.send(f"🌳 **[AI GARDEN STATUS]**\n🟢 **Gemini 智能大脑已激活，您可以直接输入自然的日常评语！**")

@bot.command(name="summary")
async def garden_summary(ctx):
    if not student_data:
        await ctx.send("📊 **[LONG-TERM SUMMARY]**\n> 暂无学生积分数据 / No student data yet.")
        return
        
    report = "📊 **[AI GARDEN LEADERBOARD / 长期智能积分排行榜]**\n━━━━━━━━━━━━━━━━━━━\n"
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
    await ctx.send(f"🔄 **[TERM RESET]**\n> **All data cleared and synced!**")

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ 错误：未找到 DISCORD_TOKEN 环境变量！")
