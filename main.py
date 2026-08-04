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
    # 学生表：学生名、树叶数、警告次数
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    name TEXT PRIMARY KEY,
                    leaves INTEGER DEFAULT 0,
                    warnings INTEGER DEFAULT 0
                )''')
    # 团队表：守护兽生命值(默认100)、班级甘露(0-100)
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
你是一位兼具爱心、耐心、包容与公正的五年级班级“共融花园”守护兽 AI 助教（如猫头鹰🦉、小松鼠🐿️）。
班级共有13位同学，有些同学可能华语不太熟练，大家会互相提醒与包容。
老师会实名输入学生的表现，请你按 JSON 格式分析：

分析规则：
1. **学生姓名 (student_name)**：从输入中精准提取被老师点名的实名学生。如果输入中没有具体点名特定个人（或属于全班通用互动/互相提醒），请填写 "全体同学"。
2. **行为性质 (action_type)**：
   - "GOOD": 被点名学生的正向行为（做功课、喝水洗脸、守秩序、互相提醒等）。
   - "BAD": 被点名学生的违纪行为（走过位、吵闹、打架、欺负同学、大声说话等）。
   - "TEAM_WATER": 团队合作、互相提醒、全班共同努力或未被单独点名时的通用鼓励。
3. **教育引导语 (message)**：
   - 必须使用简单、温暖、通俗易懂的华语（字数60字以内），多用表情符号（🦉、🌿、💧），照顾不擅长华语的同学。
   - 绝不讽刺，充满尊重、爱心与公正。

返回格式必须是合法 JSON：
{
  "student_name": "学生名或全体同学",
  "action_type": "GOOD" 或 "BAD" 或 "TEAM_WATER",
  "message": "守护兽的温暖回复"
}
"""

@bot.event
async def on_ready():
    print(f"🌸 共融花园（13人班级包容版）已上线：{bot.user.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # 重置数据库指令
    if message.content.strip() == "!resetdb":
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM students")
        c.execute("UPDATE team SET beast_hp=100, dew=0 WHERE id=1")
        conn.commit()
        conn.close()
        await message.channel.send("🧹 **共融花园数据已全部清空重置！全新一天开始啦，13位同学加油！**")
        return

    if not gemini_client:
        return

    try:
        # 调用 AI 分析
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"老师实名输入：'{message.content}'",
            config={'system_instruction': SYSTEM_PROMPT}
        )
        
        cleaned_text = response.text.strip().lstrip("```json").rstrip("```").strip()
        data = json.loads(cleaned_text)

        student_name = data.get("student_name", "全体同学")
        action_type = data.get("action_type", "GOOD")
        ai_msg = data.get("message", "")

        beast_hp, dew = get_team_status()
        status_notice = ""

        if student_name == "全体同学" or action_type == "TEAM_WATER":
            update_team(hp_delta=5, dew_delta=10)
            beast_hp, dew = get_team_status()
            status_notice = f"💧 **【全班共融浇水】** 13位同学齐心协力！班级甘露增加 10%！守护兽恢复 5 HP！"
        else:
            leaves, warnings = get_student(student_name)
            if action_type == "GOOD":
                update_student(student_name, leaves_delta=1, warnings_set=0)
                leaves += 1
                status_notice = f"✨ **【个人成长】** {student_name} 获得 🍃 1 片树叶！（当前树叶：{leaves} 片）"

            elif action_type == "BAD":
                warnings += 1
                if warnings == 1:
                    update_student(student_name, leaves_delta=0, warnings_set=1)
                    status_notice = f"🌱 **【第 1 次温柔提醒】** 守护兽提醒 {student_name}，不扣树叶，请及时纠正哦。（当前树叶：{leaves} 片）"
                elif warnings == 2:
                    update_student(student_name, leaves_delta=0, warnings_set=2)
                    status_notice = f"⚠️ **【第 2 次爱心警告】** 注意秩序哦！再次违纪将影响守护兽生命值。（当前树叶：{leaves} 片）"
                else:
                    # 第3次及以上：扣除树叶 & 守护兽扣 5 HP
                    update_student(student_name, leaves_delta=-1, warnings_set=warnings)
                    update_team(hp_delta=-5, dew_delta=0)
                    leaves = max(0, leaves - 1)
                    beast_hp, dew = get_team_status()
                    status_notice = f"🍂 **【第 {warnings} 次掉落树叶】** {student_name} 扣除 🍃 1 片树叶！守护兽生命值 -5 HP！（剩余树叶：{leaves} 片）"

        # 团队奖励状态
        team_reward_status = "🎁 **团队大奖：** 具备资格 (+5分/人)" if beast_hp >= 70 else "⚠️ **团队大奖：** 守护兽 HP 低于 70，今日 5 分团队奖暂时冻结！13位同学快互相提醒恢复 HP 吧！"

        reply = (
            f"{ai_msg}\n"
            f"----------------------------------------\n"
            f"{status_notice}\n"
            f"🐾 **守护兽生命值：** ❤️ {beast_hp}/100 HP | 💧 **班级甘露：** {dew}%\n"
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
