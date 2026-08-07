import os
import re
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# ==================== 网页保活配置 (防止Render休眠) ====================
app = Flask('')

@app.route('/')
def home():
    return "Garden Keeper Bot is running!"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==================== 配置区 ====================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
# 已自动填入你刚才提供的 #garden-database 频道 ID
DATABASE_CHANNEL_ID = 1534749623988519105

# 初始化 Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==================== 核心学生数据结构 ====================
CLASS_DATA = {
    "美燕": {"leaves": 0, "trees": 0, "avatar": "🐱", "custom_pet": "🐱"},
    "浩安": {"leaves": 0, "trees": 0, "avatar": "🐶", "custom_pet": "🐶"},
    "伟杰": {"leaves": 0, "trees": 0, "avatar": "🐼", "custom_pet": "🐼"},
    "慧玫": {"leaves": 0, "trees": 0, "avatar": "⭐", "custom_pet": "⭐"}
}

GUARDIAN_DATA = {
    "health": 100,
    "today_leaves": 0,
    "status": "💚 健康/Thriving"
}

@bot.event
async def on_ready():
    print(f"🌳 园丁守护兽系统已成功启动，当前登录账号：{bot.user}")

# ==================== 免 "!" 自然语言监听与数据收集区 ====================
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.strip()

    if content.startswith("!"):
        await bot.process_commands(message)
        return

    # 兼容两种输入格式：
    # 1. 名字 + 数字 + 原因 (例如: 慧玫 3 完成功课)
    # 2. 名字 + 原因 + 数字 (例如: 俓轩 完成功课 3 或 巫迪 讲骗话 -1)
    match_a = re.match(r'^([\u4e00-\u9fa5\w]+)\s+([+-]?\d+)\s+(.+)$', content)
    match_b = re.match(r'^([\u4e00-\u9fa5\w]+)\s+(.+?)\s+([+-]?\d+)$', content)
    
    name, leaves_change, reason = None, None, "日常表现"

    if match_a:
        name = match_a.group(1)
        leaves_change = int(match_a.group(2))
        reason = match_a.group(3)
    elif match_b:
        name = match_b.group(1)
        reason = match_b.group(2)
        leaves_change = int(match_b.group(3))

    if name and leaves_change is not None:
        if name not in CLASS_DATA:
            CLASS_DATA[name] = {"leaves": 0, "trees": 0, "avatar": "⭐", "custom_pet": "⭐"}

        student = CLASS_DATA[name]
        student["leaves"] += leaves_change
        GUARDIAN_DATA["today_leaves"] += leaves_change

        tree_leveled_up = False
        if student["leaves"] >= 20:
            gained_trees = student["leaves"] // 20
            student["trees"] += gained_trees
            student["leaves"] = student["leaves"] % 20
            tree_leveled_up = True

        if student["trees"] > 0:
            student["avatar"] = student["custom_pet"]

        # 制作精美嵌入式卡片
        embed = discord.Embed(
            title="🌿 安亲班树叶成长记录 | Garden Progress",
            color=discord.Color.green()
        )
        embed.add_field(name="学生 (Student)", value=f"{student['avatar']} **{name}**", inline=True)
        embed.add_field(name="叶子变动 (Leaves)", value=f"`{'+' if leaves_change > 0 else ''}{leaves_change}` 🍃", inline=True)
        embed.add_field(name="表现事迹 (Activity)", value=reason, inline=False)
        
        progress_bar = "█" * student["leaves"] + "░" * (20 - student["leaves"])
        embed.add_field(name="大树进度 (Tree Progress)", value=f"[{progress_bar}] {student['leaves']}/20", inline=False)
        embed.add_field(name="目前成就 (Current Status)", value=f"🌳 大树总数: **{student['trees']} 棵**", inline=False)

        if tree_leveled_up:
            embed.add_field(name="🎉 升级喜讯 (Level Up!)", value=f"恭喜 **{name}** 成功长出新大树，并解锁专属宠物头像！", inline=False)

        embed.set_footer(text="Garden Keeper Bot • 守护您的每一个教学瞬间")
        
        # 1. 在当前互动频道发送卡片
        await message.channel.send(embed=embed)
        
        # 2. 自动同步备份到 #garden-database 数据频道
        db_channel = bot.get_channel(DATABASE_CHANNEL_ID)
        if db_channel:
            await db_channel.send(embed=embed)
            
        return

    await bot.process_commands(message)

# ==================== 辅助与管理指令区 ====================
@bot.command(name="guardian")
async def guardian_status(ctx):
    embed = discord.Embed(
        title="🐾 班级守护兽状态 | Guardian Spirit",
        color=discord.Color.blue()
    )
    embed.add_field(name="健康指数 (Health Level)", value=f"❤️ **{GUARDIAN_DATA['health']}%** ({GUARDIAN_DATA['status']})", inline=False)
    embed.add_field(name="今日核心叶子总数 (Today's Total Leaves)", value=f"🍃 **{GUARDIAN_DATA['today_leaves']} / 30 片**", inline=False)
    embed.set_footer(text="守护兽随着全班表现共同成长！")
    await ctx.send(embed=embed)

@bot.command(name="summary")
async def class_summary(ctx):
    embed = discord.Embed(
        title="📊 安亲班总排行榜 | Class Leaderboard",
        color=discord.Color.gold()
    )
    for name, data in CLASS_DATA.items():
        embed.add_field(
            name=f"{data['avatar']} {name}",
            value=f"🌳 大树: **{data['trees']}** 棵 | 🍃 现有叶子: **{data['leaves']}** /20",
            inline=False
        )
    embed.set_footer(text="品学兼优，绿意盎然！")
    await ctx.send(embed=embed)

@bot.command(name="setpet")
async def set_pet(ctx, name: str, pet_emoji: str):
    if name in CLASS_DATA:
        CLASS_DATA[name]["custom_pet"] = pet_emoji
        if CLASS_DATA[name]["trees"] > 0:
            CLASS_DATA[name]["avatar"] = pet_emoji
        await ctx.send(f"✨ 成功为 **{name}** 设置专属大树宠物头像：{pet_emoji}")
    else:
        await ctx.send(f"⚠️ 找不到学生：{name}")

@bot.command(name="reset")
async def reset_database(ctx, confirm: str = ""):
    if confirm == "YES":
        for name in CLASS_DATA:
            CLASS_DATA[name]["leaves"] = 0
            CLASS_DATA[name]["trees"] = 0
        GUARDIAN_DATA["today_leaves"] = 0
        await ctx.send("🔄 **【系统提示】数据库已成功清空！今天是全新的一天，所有同学叶子和大树已归零。**")
    else:
        await ctx.send("⚠️ **安全提示：** 清空数据库需要输入 `!reset YES`，避免不小心删掉数据哦！")

keep_alive()
bot.run(DISCORD_TOKEN)
