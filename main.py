import os
import sqlite3
import json
import io
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
from google import genai
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

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
    c.execute('''CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_name TEXT,
                    action_type TEXT,
                    leaves_delta INTEGER,
                    hp_delta INTEGER
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

def record_history(student_name, action_type, leaves_delta, hp_delta):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO history (student_name, action_type, leaves_delta, hp_delta) VALUES (?, ?, ?, ?)",
              (student_name, action_type, leaves_delta, hp_delta))
    conn.commit()
    conn.close()

def get_all_students():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, leaves FROM students ORDER BY leaves DESC")
    rows = c.fetchall()
    conn.close()
    return rows

# ----------------- 3. 图表生成函数 -----------------
def generate_chart_image():
    data = get_all_students()
    if not data:
        return None
    names = [row[0] for row in data]
    leaves = [row[1] for row in data]

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(names, leaves, color='#4CAF50')
    ax.set_xlabel('Students (同学)', fontsize=12)
    ax.set_ylabel('Leaves (树叶数)', fontsize=12)
    ax.set_title('Class 13 Leaves Overview (全班树叶实时统计)', fontsize=14, fontweight='bold')
    plt.xticks(rotation=30, ha='right')
    
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return buf

# ----------------- 4. AI Client & Bot 初始化 -----------------
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
    print(f"🌸 共融花园高级管理版已上线：{bot.user.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.strip()
    if not content:
        return

    # 1. 数据库重置指令
    if content == "!resetdb":
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM students")
        c.execute("DELETE FROM history")
        c.execute("UPDATE team SET beast_hp=100, dew=0 WHERE id=1")
        conn.commit()
        conn.close()
        await message.channel.send("🧹 **数据已重置！New day, new start for all 13 students!**")
        return

    # 2. 批量清屏指令 (!clear)
    if content == "!clear":
        try:
            deleted = await message.channel.purge(limit=25)
            temp_msg = await message.channel.send(f"🧹 **已成功清理最近 {len(deleted)} 条消息！Channel cleaned!**")
            import asyncio
            await asyncio.sleep(3)
            await temp_msg.delete()
        except Exception as e:
            await message.channel.send("⚠️ 清理失败，请确保 Bot 拥有【管理消息 Manage Messages】权限！")
        return

    # 3. 撤回上一次误操作指令 (!undo)
    if content == "!undo":
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id, student_name, action_type, leaves_delta, hp_delta FROM history ORDER BY id DESC LIMIT 1")
        last_action = c.fetchone()
        if not last_action:
            conn.close()
            await message.channel.send("⚠️ 没有找到可以撤回的操作！No recent action to undo.")
            return
        
        h_id, s_name, a_type, l_delta, h_delta = last_action
        # 回滚学生积分
        if s_name and l_delta != 0:
            c.execute("UPDATE students SET leaves = leaves - ? WHERE name=?", (l_delta, s_name))
        # 回滚守护兽血量
        if h_delta != 0:
            c.execute("UPDATE team SET beast_hp = MIN(100, MAX(0, beast_hp - ?)) WHERE id=1", (h_delta,))
        # 删掉历史记录
        c.execute("DELETE FROM history WHERE id=?", (h_id,))
        conn.commit()
        conn.close()
        
        await message.channel.send(f"↩️ **已成功撤回上一条记录：** 恢复 {s_name} 的树叶与守护兽血量！Undo successful!")
        return

    # 4. 随时查看全班状况汇总指令
    if content in ["!status", "!stats", "!总结"]:
        beast_hp, dew = get_team_status()
        all_s = get_all_students()
        student_list_str = "\n".join([f"• {s[0]}: 🍃 {s[1]} 片" for s in all_s]) if all_s else "• 暂无记录 (No records yet)"
        
        status_reply = (
            f"📊 **【全班共融花园实时总结 Class Real-time Status】**\n"
            f"----------------------------------------\n"
            f"🐾 **守护兽生命值 Beast HP:** ❤️ {beast_hp}/100\n"
            f"💧 **班级甘露 Class Dew:** {dew}%\n\n"
            f"🌿 **各同学树叶积分 Student Leaves:**\n"
            f"{student_list_str}\n"
            f"----------------------------------------\n"
            f"💡 提示：输入 **`!chart`** 看图表，输入 **`!clear`** 清屏，输入 **`!undo`** 撤回！"
        )
        await message.channel.send(status_reply)
        return

    # 5. 随时生成图表指令
    if content in ["!chart", "!图表"]:
        buf = generate_chart_image()
        if buf:
            file = discord.File(buf, filename="class_chart.png")
            await message.channel.send("📊 **全班树叶实时柱状图 Real-time Chart for 13 Students:**", file=file)
        else:
            await message.channel.send("📊 目前还没有任何同学的积分记录哦！No records to chart yet.")
        return

    if not gemini_client:
        return

    # 6. 正常学生表现记录
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
        l_delta = 0
        h_delta = 0

        if student_name == "全体同学" or "全体" in student_name or action_type == "TEAM_WATER":
            update_team(hp_delta=5, dew_delta=10)
            beast_hp, dew = get_team_status()
            h_delta = 5
            status_notice = f"💧 **【全班共融 Team Water】** 13位同学齐心协力！Class Dew +10% | Beast HP +5!"
        else:
            leaves, warnings = get_student(student_name)
            if action_type == "GOOD":
                update_student(student_name, leaves_delta=1, warnings_set=0)
                l_delta = 1
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
                    l_delta = -1
                    h_delta = -5
                    leaves = max(0, leaves - 1)
                    beast_hp, dew = get_team_status()
                    status_notice = f"🍂 **【第{warnings}次掉落 Leaf Lost】** {student_name} -1 Leaf! Beast HP -5! (Leaves: {leaves})"

        # 记录到历史中以便随时 !undo 撤回
        record_history(student_name if student_name != "全体同学" else "Team", action_type, l_delta, h_delta)

        team_reward_status = "🎁 **团队大奖 Team Reward:** 具备资格 Qualified (+5 pts)" if beast_hp >= 70 else "⚠️ **团队大奖 Team Reward:** HP < 70, 奖项暂时冻结!"

        reply = (
            f"{ai_msg}\n"
            f"----------------------------------------\n"
            f"{status_notice}\n"
            f"🐾 **守护兽生命值 Beast HP:** ❤️ {beast_hp}/100 | 💧 **班级甘露 Class Dew:** {dew}%\n"
            f"{team_reward_status}\n"
            f"*(指令菜单: `!status` 总结 | `!chart` 图表 | `!clear` 清屏 | `!undo` 撤回)*"
        )

        await message.channel.send(reply)

    except Exception as e:
        print(f"处理失败: {e}")
        await message.channel.send(f"🌸 **收到您的记录啦！已为同学们送上关爱与鼓励！✨**")

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
