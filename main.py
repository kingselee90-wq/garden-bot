import discord
from discord.ext import commands
import os

# 初始化 Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 提示语库：聚焦语文关键字，简短公道
KEYWORDS_PROMPTS = {
    "leaf_fall": "🍂 **【提示：静心 | 专注】**\n小树掉了一片叶子。**静心**才能听见花开，收回脚步，把**专注**留给自己。",
    "no_report": "🛡️ **【提示：内省 | 做好自己】**\n别人的树有风，**管好自己的花园**才是智慧。先**内省**，**做好自己**，小树自然常绿。",
    "struggle": "🌱 **【提示：积少成多 | 突破】**\n不用急，**积少成多**，今天完成这一行，就是最棒的**突破**！",
    "water_together": "💧 **【提示：共融 | 提携】**\n独木不成林。用**提携**代替指责，全班**同频**，**共融**的花园最美丽！"
}

@bot.event
async def on_ready():
    print(f"🌸 共融花园系统已上线：{bot.user.name}")

# 1. 掉叶子指令：!掉叶 @学生
@bot.command()
async def 掉叶(ctx, member: discord.Member):
    await ctx.send(f"{member.mention}\n{KEYWORDS_PROMPTS['leaf_fall']}")

# 2. 告状不受理指令：!告状 @学生
@bot.command()
async def 告状(ctx, member: discord.Member):
    await ctx.send(f"{member.mention}\n{KEYWORDS_PROMPTS['no_report']}")

# 3. 突破鼓励指令：!鼓励 @学生
@bot.command()
async def 鼓励(ctx, member: discord.Member):
    await ctx.send(f"{member.mention}\n{KEYWORDS_PROMPTS['struggle']}")

# 4. 集体浇水指令：!浇水
@bot.command()
async def 浇水(ctx):
    await ctx.send(KEYWORDS_PROMPTS['water_together'])

# 读取 Render 的环境变量 TOKEN
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
