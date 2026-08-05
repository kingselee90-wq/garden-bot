import os
import discord
from discord.ext import commands

# ==========================================
# 🌳 共融花园守护兽核心系统 (Guardian Bot)
# ==========================================
# 极简纯中文盲打指令 + 大字双语强同步 + 守护兽与小树图表系统

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"==========================================")
    print(f" 🌳 守护兽花圃系统已成功启动：{bot.user.name}")
    print(f" 🟢 状态：24小时在线中 (Online & Watching)")
    print(f"==========================================")

@bot.event
async def on_message(message):
    # 防止 Bot 自己触发死循环
    if message.author == bot.user:
        return

    content = message.content.strip()
    
    # ------------------------------------------
    # 1. 纪律：过位触发 (例: 信贤过位 / 巫迪过位)
    # ------------------------------------------
    if "过位" in content:
        name = content.replace("过位", "").strip()
        if not name:
            name = "同学"
        
        await message.channel.send(
            f"# ⚠️ 秩序警告 / ORDER ALERT\n\n"
            f"**{name}，请回到座位。**\n"
            f"*{name}, please stay in your seat.*\n\n"
            f"🍂 *(空间特权暂时冻结 / Space privilege temporarily frozen)*"
        )
        return

    # ------------------------------------------
    # 2. 状态：心情差触发 (例: 巫迪badmood / 轩轩心情差)
    # ------------------------------------------
    if "badmood" in content.lower() or "心情差" in content:
        name = content.lower().replace("badmood", "").replace("心情差", "").strip()
        if not name:
            name = "同学"
            
        await message.channel.send(
            f"# 💙 能量重置 / ENERGY RESET\n\n"
            f"**{name}，深呼吸，老师和守护兽陪着你。**\n"
            f"*{name}, take a deep breath. We are here for you.*\n\n"
            f"✨ *(没关系，慢慢调整状态 / It's okay, take your time)*"
        )
        return

    # ------------------------------------------
    # 3. 纪律：打瞌睡触发 (例: 巫迪打瞌睡)
    # ------------------------------------------
    if "打瞌睡" in content:
        name = content.replace("打瞌睡", "").strip()
        if not name:
            name = "同学"
            
        await message.channel.send(
            f"# 💧 能量补充 / ENERGY BOOST\n\n"
            f"**{name}，去洗个脸，精神焕发再出发！**\n"
            f"*{name}, go wash your face and stay fresh!*\n\n"
            f"🦊 *(守护兽提醒：自我调节最棒了 / Guardian says: Self-care is great)*"
        )
        return

    # ------------------------------------------
    # 4. 默认正常指令解析
    # ------------------------------------------
    await bot.process_commands(message)

@bot.command(name="status")
async def garden_status(ctx):
    """显示花园状态与小树图表"""
    await ctx.send(
        f"# 🌳 守护兽花圃状态 / GARDEN STATUS\n\n"
        f"🟢 **Bot 守护兽系统：24小时在线中 (Online & Watching)**\n"
        f"🦊🐾 *(小树与守护兽正在花园里静静守护，随时准备为您效劳)*\n\n"
        f"📊 **【全班树叶里程碑 / Leaf Milestones】**\n"
        f"目标门槛：`30 片叶子` ➡️ 解锁男女专属大树与个性卡通形象！"
    )

# 启动 Bot (安全从 Render 的环境变量中读取 Token)
token = os.getenv("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("❌ 错误：未找到 DISCORD_TOKEN 环境变量，请在 Render 后台检查设置！")
