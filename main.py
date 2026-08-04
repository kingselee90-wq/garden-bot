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
你会自动监听老师发出的关于学生行为的任何描述（如：不听话、走过位、捣蛋、吵闹，或是累了、洗脸、喝水、做好功课、小进步、课前小睡等）。

请根据老师发送的内容，生成一段带有“花园、小树、落叶、甘露、果实”意象的精炼温馨引导语。

回复格式要求：
1. 第一行为提示词主题，例如：🌱 **【提示：专注 | 积少成多】** 或 🛡️ **【提示：内省 | 自律】**
2. 第二行为简短温情的引导语，结合花园/小树的比喻，字数在50字以内，语言精练，适合小学生。
3. 保持正面、坚定且富有同理心，不讽刺、不责备。
"""

@bot.event
async def on_ready():
    print(f"🌸 共融花园 全自动 AI 助教已上线：{bot.user.name}")

@bot.event
async def on_message(message):
    # 忽略 Bot 自己发送的消息，防止无限循环
    if message.author == bot.user:
        return

    # 如果未检测到 API KEY 则跳过
    if not gemini_client:
        return

    # 自动识别消息并调用 AI 生成响应
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"老师描述的情况是：'{message.content}'，请给出班级助教引导语。",
            config={'system_instruction': SYSTEM_PROMPT}
        )
        if response.text:
            await message.channel.send(response.text)
    except Exception as e:
        print(f"AI 生成失败: {e}")

    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
