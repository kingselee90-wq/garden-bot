# ==================== 免 "!" 自然语言监听区 ====================
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.strip()

    # 如果是标准的 ! 指令，交由下面的 commands 处理
    if content.startswith("!"):
        await bot.process_commands(message)
        return

    # 兼容两种习惯的正则匹配：
    # 方案 A: 名字 + 数字 + 原因 (例如: 慧玫 3 完成功课)
    # 方案 B: 名字 + 原因 + 数字 (例如: 俓轩 完成功课 3 或 巫迪 讲骗话 -1)
    match_a = re.match(r'^([\u4e00-\u9fa5\w]+)\s+([+-]?\d+)\s+(.+)$', content)
    match_b = re.match(r'^([\u4e00-\u9fa5\w]+)\s+(.+?)\s+([+-]?\d+)$', content)
    
    name, leaves_change, reason = None, None, "日常表现"

    if match_a:
        name = match_a.group(1)
        leaves_change = int(match_a.group(2))
        reason = match_a.group(3)
    elif match_b:
        name = match_b.group(1)
        reason = match_b.group(2)
        leaves_change = int(match_b.group(3))

    if name and leaves_change is not None:
        if name not in CLASS_DATA:
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

        # 如果长出大树，自动应用专属宠物头像
        if student["trees"] > 0:
            student["avatar"] = student["custom_pet"]

        # 制作精美嵌入式卡片
        embed = discord.Embed(
            title="🌿 安亲班树叶成长记录 | Garden Progress",
            color=discord.Color.green()
        )
        embed.add_field(name="学生 (Student)", value=f"{student['avatar']} **{name}**", inline=True)
        embed.add_field(name="叶子变动 (Leaves)", value=f"`{'+' if leaves_change > 0 else ''}{leaves_change}` 🍃", inline=True)
        embed.add_field(name="表现事迹 (Activity)", value=reason, inline=False)
        
        progress_bar = "█" * student["leaves"] + "░" * (20 - student["leaves"])
        embed.add_field(name="大树进度 (Tree Progress)", value=f"[{progress_bar}] {student['leaves']}/20", inline=False)
        embed.add_field(name="目前成就 (Current Status)", value=f"🌳 大树总数: **{student['trees']} 棵**", inline=False)

        if tree_leveled_up:
            embed.add_field(name="🎉 升级喜讯 (Level Up!)", value=f"恭喜 **{name}** 成功长出新大树，并解锁专属宠物头像！", inline=False)

        embed.set_footer(text="Garden Keeper Bot • 守护您的每一个教学瞬间")
        await message.channel.send(embed=embed)
        return

    await bot.process_commands(message)
