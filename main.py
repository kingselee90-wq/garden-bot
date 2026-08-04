import os
import sqlite3
import json
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
from google import genai

# ----------------- 1. Keep-Alive 网页服务 -----------------
app = Flask('')

@app.route('/')
def home():
    return "共融花园守护系统运行中！"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# ----------------- 2. 数据库初始化 -----------------
DB_FILE = "garden.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    name TEXT PRIMARY KEY,
                    leaves INTEGER DEFAULT 0,
                    warnings INTEGER DEFAULT 0
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS team (
                    id INTEGER PRIMARY KEY,
                    beast_hp INTEGER DEFAULT 100,
                    dew INTEGER DEFAULT 0
                )''')
    c.execute("INSERT OR IGNORE INTO team (id, beast_hp, dew) VALUES (1, 100, 0)")
    conn.commit()
    conn.close()

init_db()

def get_student(name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT leaves, warnings FROM students WHERE name=?", (name,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO students (name, leaves, warnings) VALUES (?, 0, 0)", (name,))
        conn.commit()
        leaves, warnings = 0, 0
    else:
        leaves, warnings = row
    conn.close()
    return leaves, warnings

def update_student(name, leaves_delta, warnings_set=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if warnings_set is not None:
        c.execute("UPDATE students SET leaves = leaves + ?, warnings = ? WHERE name=?", (leaves_delta, warnings_set, name))
    else:
        c.execute("UPDATE students SET leaves = leaves + ? WHERE name=?", (leaves_delta, name))
    conn.commit()
    conn.close()

def get_team_status():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT beast_hp, dew FROM team WHERE id=1")
    beast_hp, dew = c.fetchone()
    conn.close()
    return beast_hp, dew

def update_team(hp_delta, dew_delta):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE team SET beast_hp = MIN(100, MAX(0, beast_hp + ?)), dew = MIN(100, MAX(0, dew + ?)) WHERE id=1", (hp_delta, dew_delta))
    conn.commit()
    conn.close()

# ----------------- 3. AI Client & Bot 初始化 -----------------
gemini_client = None
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    gemini_client = genai.Client(api_key=gemini_api_key)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SYSTEM_PROMPT = """
你是一位兼具爱心与公正的五年级班级“共融花园”守护兽 AI 助教。
老师会实名输入学生的表现。请按以下固定 JSON 格式返回：
{
  "student_name": "提取被点名的学生名字",
  "action_type": "GOOD" 或 "BAD" 或 "TEAM_WATER",
  "message": "双语温柔回复（60字以内，含表情 🦉🌿💧）"
}
"""

@bot.event
async def on_ready():
    print(f"🌸 共融花园稳定版已上线：{bot.user.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.strip()
    if not content:
        return

    if content == "!resetdb":
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM students")
        c.execute("UPDATE team SET beast_hp=100, dew=0 WHERE id=1")
        conn.commit()
        conn.close()
        await message.channel.send("🧹 **数据已重置！New day, new start for all 13 students!**")
        return

    if not gemini_client:
        return

    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"老师实名输入：'{content}'",
            config={'system_instruction': SYSTEM_PROMPT}
        )
        
        cleaned_text = response.text.strip().lstrip("```json").rstrip("```").strip()
        data = json.loads(cleaned_text)

        student_name = data.get("student_name", "全体同学")
        action_type = data.get("action_type", "GOOD")
        ai_msg = data.get("message", "做得好！Keep it up! 🌿")

        beast_hp, dew = get_team_status()
        status_notice = ""

        if student_name == "全体同学" or "全体" in student_name or action_type == "TEAM_WATER":
            update_team(hp_delta=5, dew_delta=10)
            beast_hp, dew = get_team_status()
            status_notice = f"💧 **【全班共融 Team Water】** 13位同学齐心协力！Class Dew +10% | Beast HP +5!"
        else:
            leaves, warnings = get_student(student_name)
            if action_type == "GOOD":
                update_student(student_name, leaves_delta=1, warnings_set=0)
                leaves += 1
                status_notice = f"✨ **【个人成长 Personal Growth】** {student_name} 获得 🍃 +1 Leaf! (Total: {leaves})"

            elif action_type == "BAD":
                warnings += 1
                if warnings == 1:
                    update_student(student_name, leaves_delta=0, warnings_set=1)
                    status_notice = f"🌱 **【第1次温柔提醒 1st Reminder】** 守护兽提醒 {student_name}，不扣树叶 No leaf lost. (Total: {leaves})"
                elif warnings == 2:
                    update_student(student_name, leaves_delta=0, warnings_set=2)
                    status_notice = f"⚠️ **【第2次爱心警告 2nd Warning】** 注意秩序 Keep order please! (Total: {leaves})"
                else:
                    update_student(student_name, leaves_delta=-1, warnings_set=warnings)
                    update_team(hp_delta=-5, dew_delta=0)
                    leaves = max(0, leaves - 1)
                    beast_hp, dew = get_team_status()
                    status_notice = f"🍂 **【第{warnings}次掉落 Leaf Lost】** {student_name} -1 Leaf! Beast HP -5! (Leaves: {leaves})"

        team_reward_status = "🎁 **团队大奖 Team Reward:** 具备资格 Qualified (+5 pts)" if beast_hp >= 70 else "⚠️ **团队大奖 Team Reward:** HP < 70, 奖项暂时冻结!"

        reply = (
            f"{ai_msg}\n"
            f"----------------------------------------\n"
            f"{status_notice}\n"
            f"🐾 **守护兽生命值 Beast HP:** ❤️ {beast_hp}/100 | 💧 **班级甘露 Class Dew:** {dew}%\n"
            f"{team_reward_status}"
        )

        await message.channel.send(reply)

    except Exception as e:
        print(f"处理失败: {e}")
        # 即使报错也给老师回复，确保绝不哑火
        await message.channel.send(f"🌸 **收到您的记录啦！已为同学们送上关爱与鼓励！✨**")

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
