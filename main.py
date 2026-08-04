import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread
from google import genai

# 启动 Keep-Alive 网页服务器
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# 初始化 Gemini AI Client
gemini_client = None
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    gemini_client = genai.Client(api_key=gemini_api_key)

# 初始化 Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SYSTEM_PROMPT = """
你是一位温暖、富有教育智慧的五年级班级“共融花园”助教 Bot。
你的任务是根据老师输入的学生行为描述（如：不听话、走过位、捣蛋、吵闹，或是洗脸、喝水、认真做功课、课前小睡、小进步等），生成一段充满鼓励、正向引导且带有语文精炼提示的回复。

回复格式要求：
1. 第一行为提示词主题，例如：🌱 **【提示：专注 | 积少成多】** 或 🛡️ **【提示：内省 | 自律】**
2. 第二行为简短温情的引导语，结合“小树/落叶/甘露/花园”的比喻，字数在50字以内，语言要精练、适合小学生的语文修养。
3. 保持正面、坚定且富有同理心，不讽刺、不责备。
"""

@bot.event
async def on_ready():
    print(f"🌸 共融花园 AI 智能助教已上线：{bot.user.name}")

@bot.command()
async def 记(ctx, member: discord.Member, *, text: str):
    """用法：!记 @学生名字 行为描述"""
    if not gemini_client:
        await ctx.send("⚠️ 未检测到 GEMINI_API_KEY，请在 Render 中确认配置。")
        return

    prompt = f"针对学生 {member.display_name} 的行为描述：'{text}'，生成一段助教引导语。"
    
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={'system_instruction': SYSTEM_PROMPT}
        )
        await ctx.send(f"{member.mention}\n{response.text}")
    except Exception as e:
        await ctx.send(f"生成回复时出错：{e}")

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
