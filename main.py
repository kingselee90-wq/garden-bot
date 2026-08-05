import os
import threading
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
# 🌳 共融花园守护兽系统 (双语防借口 + 心理学正向支持)
# ==========================================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

ai_client = None
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    ai_client = genai.Client(api_key=gemini_api_key)

@bot.event
async def on_ready():
    print(f"==========================================")
    print(f" 🌳 守护兽花圃系统已成功启动：{bot.user.name}")
    print(f" 🟢 状态：24小时在线中")
    print(f"==========================================")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.strip()
    
    # 1. 空间与专注引导（过位 - 严密双语对照）
    if "过位" in content:
        name = content.replace("过位", "").strip() or "同学"
        await message.channel.send(
            f"# 🌿 【空间锚定 / Space Anchor】\n"
            f"> ### **{name}，请回到专属座位。**\n"
            f"> *{name}, please return to your assigned seat immediately.*\n\n"
            f"🌱 **[守护兽微光 / Guardian Note：找回属于你的专心节奏，每一次调整都是成长 / Reconnect with your focus, every adjustment is growth]**"
        )
        return

    # 2. 情绪重置（badmood / 心情差 - 双语对照）
    if "badmood" in content.lower() or "心情差" in content:
        name = content.lower().replace("badmood", "").replace("心情差", "").strip() or "同学"
        await message.channel.send(
            f"# 💙 【情感安全港 / Emotional Safe Haven】\n"
            f"> ### **{name}，允许自己停下，深呼吸调整状态。**\n"
            f"> *{name}, it is okay to pause and take a deep breath to reset your state.*\n\n"
            f"✨ **[守护兽微光 / Guardian Note：接纳此刻的感受，我们支持你 / Accept your feelings, we are here to support you]**"
        )
        return

    # 3. 状态调整（打瞌睡 - 双语对照）
    if "打瞌睡" in content or "不洗脸" in content:
        name = content.replace("打瞌睡", "").replace("不洗脸", "").strip() or "同学"
        await message.channel.send(
            f"# 💧 【能量唤醒 / Energy Renewal】\n"
            f"> ### **{name}，去洗个清爽的脸，充充电！**\n"
            f"> *{name}, go wash your face and recharge your energy.*\n\n"
            f"🦊 **[守护兽微光 / Guardian Note：照顾好自己，对自己负责 / Take care of yourself and be responsible]**"
        )
        return

    await bot.process_commands(message)

@bot.command(name="status")
async def garden_status(ctx):
    """显示全班树叶里程碑与成长图表（双语防借口）"""
    chart_view = (
        f"# 🌳 【共融花园成长图表 / Garden Growth Chart】\n"
        f"```yaml\n"
        f"[ 状态 / Status ] 🟢 守护兽花圃系统：24/7 持续在线 (24/7 Online)\n"
        f"[ 守护 / Guardian ] 🦊 小树与守护兽正在陪伴大家 (Accompanying everyone)\n"
        f"```\n"
        f"### 📊 **全班树叶里程碑进度 / Class Leaf Milestones**\n"
        f"```text\n"
        f" 🌱 幼苗期 (0-10片 / Leaves)  ➡️ 正在萌芽 / Germinating\n"
        f" 🌿 成长中 (11-29片 / Leaves) ➡️ 稳步吸收养分 / Growing steadily\n"
        f" 🌳 大树成林 (30片+ / Leaves) ➡️ 🌟 解锁男女专属大树与个性卡通形象！(Unlock Exclusive Trees)\n"
        f"```\n"
        f"🎨 *提示 / Tip：输入 `!rules` 随时查看【3不 & 5要】获得与失去的纪律契约 (Check Rules & Contract).* "
    )
    await ctx.send(chart_view)

@bot.command(name="rules")
async def garden_rules(ctx):
    """一键 Call 出【3不 & 5要】契约，全套严格中英对照，堵死所有借口"""
    rules_view = (
        f"# 📜 【共融花园纪律与成长契约 / Rules & Growth Contract】\n"
        f"🦊 *“自主选择，为自己的空间与自由负责 / Make independent choices, take responsibility for your space & freedom.”*\n\n"
        f"--- \n\n"
        f"### ❌ **【3不：失去树叶与 Free Time 的行为 / The 3 'Don'ts': Lose Leaves & Free Time】**\n"
        f"```diff\n"
        f"- 1. 不随意离开座位（过位影响秩序）     ➡️ 扣除树叶 & 冻结 Free Time (Lose Leaves & Free Time Freeze)\n"
        f"- 2. 不逃避情绪或无故荒废专注时间       ➡️ 扣除树叶 & 影响团队甘露 (Lose Leaves & Team Dew Affected)\n"
        f"- 3. 不推卸责任或以“不懂”作为借口       ➡️ 重新调整状态并失去当日特权 (Reset & Lose Daily Privileges)\n"
        f"```\n\n"
        f"### ✅ **【5要：获得树叶与 Free Time 的正向行为 / The 5 'Dos': Earn Leaves & Free Time】**\n"
        f"```yaml\n"
        f" 1. 要自我觉察：主动调整情绪与状态 (Badmood自愈) ➡️ 获得树叶 +1 (Earn Leaf +1)\n"
        f" 2. 要积极提神：保持清醒与活力 (洗脸/振作精神)   ➡️ 获得树叶 +1 (Earn Leaf +1)\n"
        f" 3. 要维护空间：遵守座位与秩序 (专注做好本分)     ➡️ 获得团队甘露 ++ (Earn Team Dew ++)\n"
        f" 4. 要承担成长：不找借口，勇敢面对学习与挑战     ➡️ 解锁专属里程碑 (Unlock Growth Milestones)\n"
        f" 5. 要互助共荣：与同伴守护花园，累积 30 片叶子  ➡️ 解锁大树与大奖！(Unlock Big Tree & Grand Reward)\n"
        f"```\n"
        f"📌 **温馨提示 / Note：自由与特权是由自律和负责任换来的，随时查看，做自己的主人！(Freedom & privileges are earned through self-discipline. Be your own master!)**"
    )
    await ctx.send(rules_view)

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ 错误：未找到 DISCORD_TOKEN 环境变量！")
