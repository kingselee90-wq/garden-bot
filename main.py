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
你是一位极具爱心、心理洞察力、公正与双语包容的五年级班级“共融花园”资深守护兽 AI 助教。
老师输入的文本中可能包含【多位同学】或复合行为。请你仔细分析，将所有提到的学生及其行为提取为一个【学生列表】。

分析规则：
1. **students (列表)**：提取所有被点名的学生。每个人包含：
   - "name": 学生名字
   - "type": "GOOD"（正向行为）或 "BAD"（违纪/危险/不当行为，如玩闹、推门、走过位等）
2. **message (教育引导语)**：
   - 针对老师输入的情境，给出一段充满人性关怀、耐心引导、兼顾安全与尊重的【中英双语】回复（60字以内，多用表情符号 🦉、🌿、⚠️）。

返回格式必须是合法的 JSON：
{
  "students": [
    {"name": "学生A", "type": "BAD"},
    {"name": "学生B", "type": "BAD"}
  ],
  "message": "双语温柔且有原则的班级引导语"
}
"""

@bot.event
async def on_ready():
    print(f"🌸 共融花园人性化多维版已上线：{bot.user.name}")

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

        students_data = data.get("students", [])
        ai_msg = data.get("message", "")

        beast_hp, dew = get_team_status()
        action_summaries = []

        # 逐个处理被点名的每一位同学
        for s in students_data:
            s_name = s.get("name")
            s_type = s.get("type", "GOOD")
            if not s_name:
                continue

            leaves, warnings = get_student(s_name)
            if s_type == "GOOD":
                update_student(s_name, leaves_delta=1, warnings_set=0)
                action_summaries.append(f"✨ {s_name}: 🍃 +1 Leaf (Total: {leaves + 1})")
            else:
                warnings += 1
                if warnings == 1:
                    update_student(s_name, leaves_delta=0, warnings_set=1)
                    action_summaries.append(f"🌱 {s_name}: 第1次温柔提醒 1st Reminder (No leaf lost)")
                elif warnings == 2:
                    update_student(s_name, leaves_delta=0, warnings_set=2)
                    action_summaries.append(f"⚠️ {s_name}: 第2次爱心警告 2nd Warning (Keep order)")
                else:
                    update_student(s_name, leaves_delta=-1, warnings_set=warnings)
                    update_team(hp_delta=-5, dew_delta=0)
                    leaves = max(0, leaves - 1)
                    action_summaries.append(f"🍂 {s_name}: 第{warnings}次掉落 -1 Leaf! Beast HP -5!")

        if not students_data:
            # 如果没有提取到具体学生，作为全班共融处理
            update_team(hp_delta=5, dew_delta=10)
            action_summaries.append("💧 全班共融 Team Water +10%")

        beast_hp, dew = get_team_status()
        team_reward_status = "🎁 **团队大奖 Team Reward:** 具备资格 Qualified (+5 pts)" if beast_hp >= 70 else "⚠️ **团队大奖 Team Reward:** HP < 70, 奖项暂时冻结!"

        summary_text = "\n".join(action_summaries)
        reply = (
            f"{ai_msg}\n"
            f"----------------------------------------\n"
            f"{summary_text}\n"
            f"🐾 **守护兽生命值 Beast HP:** ❤️ {beast_hp}/100 | 💧 **班级甘露 Class Dew:** {dew}%\n"
            f"{team_reward_status}"
        )

        await message.channel.send(reply)

    except Exception as e:
        print(f"处理失败: {e}")

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
