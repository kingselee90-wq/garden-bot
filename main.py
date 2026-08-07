import os
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

# 初始化 Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==================== 核心数据结构 ====================
CLASS_DATA = {
    "美燕": {"leaves": 0, "trees": 0, "avatar": "🐱"},
    "浩安": {"leaves": 0, "trees": 0, "avatar": "🐶"},
    "伟杰": {"leaves": 0, "trees": 0, "avatar": "🐼"}
}

GUARDIAN_DATA = {
    "health": 100,
    "today_leaves": 0,
    "status": "💚 健康/Thriving"
}

@bot.event
async def on_ready():
    print(f"🌳 园丁守护兽系统已成功启动，当前登录账号：{bot.user}")

# ==================== 核心指令区 ====================

@bot.command(name="add")
async def add_score(ctx, name: str, leaves: int, *, reason: str = "日常表现"):
    """
    加分指令格式: !add 美燕 3 完成功课
    """
    if name not in CLASS_DATA:
        CLASS_DATA[name] = {"leaves": 0, "trees": 0, "avatar": "⭐"}
    
    student = CLASS_DATA[name]
    student["leaves"] += leaves
    GUARDIAN_DATA["today_leaves"] += leaves

    # 检查是否满 20 片叶子升一颗大树
    tree_leveled_up = False
    if student["leaves"] >= 20:
        student["trees"] += student["leaves"] // 20
        student["leaves"] = student["leaves"] % 20
        tree_leveled_up = True

    # 制作精美嵌入式卡片
    embed = discord.Embed(
        title="🌿 安亲班树叶成长记录 | Garden Progress",
        color=discord.Color.green()
    )
    embed.add_field(name="学生 (Student)", value=f"{student['avatar']} **{name}**", inline=True)
    embed.add_field(name="获得叶子 (Leaves Added)", value=f"`+{leaves}` 🍃", inline=True)
    embed.add_field(name="表现事迹 (Activity)", value=reason, inline=False)
    
    progress_bar = "█" * student["leaves"] + "░" * (20 - student["leaves"])
    embed.add_field(name="大树进度 (Tree Progress)", value=f"[{progress_bar}] {student['leaves']}/20", inline=False)
    embed.add_field(name="目前成就 (Current Status)", value=f"🌳 大树总数: **{student['trees']} 棵**", inline=False)

    if tree_leveled_up:
        embed.add_field(name="🎉 升级喜讯 (Level Up!)", value=f"恭喜 **{name}** 成功长出一颗新大树！", inline=False)

    embed.set_footer(text="Garden Keeper Bot • 守护您的每一个教学瞬间")
    await ctx.send(embed=embed)

@bot.command(name="guardian")
async def guardian_status(ctx):
    """
    查看守护兽状态: !guardian
    """
    embed = discord.Embed(
        title="🐾 班级守护兽状态 | Guardian Spirit",
        color=discord.Color.blue()
    )
    embed.add_field(name="健康指数 (Health Level)", value=f"❤️ **{GUARDIAN_DATA['health']}%** ({GUARDIAN_DATA['status']})", inline=False)
    embed.add_field(name="今日核心叶子总数 (Today's Total Leaves)", value=f"🍃 **{GUARDIAN_DATA['today_leaves']} / 30 片** (目标: 核心10人达标)", inline=False)
    embed.set_footer(text="守护兽随着全班表现共同成长！")
    await ctx.send(embed=embed)

@bot.command(name="summary")
async def class_summary(ctx):
    """
    全班排行榜: !summary
    """
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

# 启动网页保活
keep_alive()

# 运行机器人
bot.run(DISCORD_TOKEN)
