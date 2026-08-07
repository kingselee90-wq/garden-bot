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

# 初始化 Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==================== 核心学生数据结构 ====================
# avatar: 默认头像, trees: 大树数, leaves: 当前叶子数(满20变大树)
# 拥有专属卡通头像设定：大树数量>=1即可解锁/替换专属宠物
CLASS_DATA = {
    "美燕": {"leaves": 0, "trees": 0, "avatar": "🐱", "custom_pet": "🐱"},
    "浩安": {"leaves": 0, "trees": 0, "avatar": "🐶", "custom_pet": "🐶"},
    "伟杰": {"leaves": 0, "trees": 0, "avatar": "🐼", "custom_pet": "🐼"}
}

GUARDIAN_DATA = {
    "health": 100,
    "today_leaves": 0,
    "status": "💚 健康/Thriving"
}

@bot.event
async def on_ready():
    print(f"🌳 园丁守护兽系统已成功启动，当前登录账号：{bot.user}")

# ==================== 免 "!" 自然语言监听区 ====================
@bot.event
async def on_message(message):
    # 避免机器人自己回复自己陷入死循环
    if message.author == bot.user:
        return

    content = message.content.strip()

    # 1. 如果是标准的 ! 指令，交由下面的 commands 处理
    if content.startswith("!"):
        await bot.process_commands(message)
        return

    # 2. 自然语言匹配：例如 "美燕 3 完成功课" 或 "美燕 +3 做功课"
    # 正则表达式匹配格式：名字 [空格] +/-数字 [空格可选] 事迹
    match = re.match(r'^([\u4e00-\u9fa5\w]+)\s*([+-]?\d+)\s*(.*)$', content)
    
    if match:
        name = match.group(1)
        leaves_change = int(match.group(2))
        reason = match.group(3) if match.group(3) else "日常表现"

        if name not in CLASS_DATA:
            # 如果新学生自动注册，默认给个 ⭐ 头像
            CLASS_DATA[name] = {"leaves": 0, "trees": 0, "avatar": "⭐", "custom_pet": "⭐"}

        student = CLASS_DATA[name]
        student["leaves"] += leaves_change
        GUARDIAN_DATA["today_leaves"] += leaves_change

        # 检查是否满 20 片叶子升一颗大树
        tree_leveled_up = False
        if student["leaves"] >= 20:
            gained_trees = student["leaves"] // 20
            student["trees"] += gained_trees
            student["leaves"] = student["leaves"] % 20
            tree_leveled_up = True

        # 如果长出第一棵大树或以上，自动应用专属宠物头像！
        if student["trees"] > 0:
            student["avatar"] = student["custom_pet"]

        # 制作精美嵌入式卡片
        embed = discord.Embed(
            title="🌿 安亲班树叶成长记录 | Garden Progress",
            color=discord.Color.green()
        )
        embed.add_field(name="学生 (Student)", value=f"{student['avatar']} **{name}**", inline=True)
        embed.add_field(name="叶子变动 (Leaves)", value=f"`+{leaves_change}` 🍃", inline=True)
        embed.add_field(name="表现事迹 (Activity)", value=reason, inline=False)
        
        progress_bar = "█" * student["leaves"] + "░" * (20 - student["leaves"])
        embed.add_field(name="大树进度 (Tree Progress)", value=f"[{progress_bar}] {student['leaves']}/20", inline=False)
        embed.add_field(name="目前成就 (Current Status)", value=f"🌳 大树总数: **{student['trees']} 棵**", inline=False)

        if tree_leveled_up:
            embed.add_field(name="🎉 升级喜讯 (Level Up!)", value=f"恭喜 **{name}** 成功长出新大树，并解锁专属宠物头像！", inline=False)

        embed.set_footer(text="Garden Keeper Bot • 守护您的每一个教学瞬间")
        await message.channel.send(embed=embed)
        return

    # 其他消息正常处理
    await bot.process_commands(message)

# ==================== 辅助管理指令区 ====================

@bot.command(name="guardian")
async def guardian_status(ctx):
    """查看守护兽状态: 输入 !guardian"""
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
    """查看全班排行榜: 输入 !summary"""
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
    """为大树学生设置专属宠物头像: 输入 !setpet 美燕 🦊"""
    if name in CLASS_DATA:
        CLASS_DATA[name]["custom_pet"] = pet_emoji
        if CLASS_DATA[name]["trees"] > 0:
            CLASS_DATA[name]["avatar"] = pet_emoji
        await ctx.send(f"✨ 成功为 **{name}** 设置专属大树宠物头像：{pet_emoji}")
    else:
        await ctx.send(f"⚠️ 找不到学生：{name}")

# 启动网页保活
keep_alive()

# 运行机器人
bot.run(DISCORD_TOKEN)
