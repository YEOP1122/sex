import discord
from discord.ext import commands
import sqlite3

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

# SQLite 데이터베이스 연결
conn = sqlite3.connect('userdata.db')
cursor = conn.cursor()

# 사용자 포인트 테이블 생성
cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_points (
        user_id INTEGER PRIMARY KEY,
        points REAL
    )
''')
conn.commit()

# 봇 소유자 또는 관리자의 Discord 사용자 ID
admin_ids = [930002753839857665, 1174544560593063996, 235633003311792129]

@bot.event
async def on_ready():
    print(f'봇이 로그인했습니다: {bot.user.name}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # 모든 채널에서 메시지를 받을 때마다 포인트 추가
    user_id = message.author.id
    cursor.execute('INSERT OR IGNORE INTO user_points (user_id, points) VALUES (?, ?)', (user_id, 0.0))
    cursor.execute('UPDATE user_points SET points = points + 0.1 WHERE user_id = ?', (user_id,))
    conn.commit()

    await bot.process_commands(message)

@bot.command(name='포인트순위')
async def point_rank(ctx):
    # 포인트 순위 조회
    cursor.execute('SELECT user_id, points FROM user_points ORDER BY points DESC LIMIT 10')
    rows = cursor.fetchall()

    embed = discord.Embed(title='포인트 순위', color=discord.Color.purple())

    for rank, (user_id, points) in enumerate(rows, start=1):
        member = ctx.guild.get_member(user_id)

        if member:
            embed.add_field(name=f'{rank}. {member.display_name}', value=f'포인트: {points:.1f}원', inline=False)

    await ctx.send(embed=embed)

@bot.command(name='내순위')
async def my_rank(ctx):
    # 사용자 개별 순위 조회
    user_id = ctx.author.id
    cursor.execute('SELECT RANK() OVER (ORDER BY points DESC) AS rank FROM user_points WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if result:
        await ctx.send(f'{ctx.author.display_name}님은 포인트 순위 {result[0]}위입니다.')
    else:
        await ctx.send('포인트 순위에 등록되어 있지 않습니다.')

@bot.command(name='포인트보유')
async def check_points(ctx):
    # 사용자 포인트 조회
    user_id = ctx.author.id
    cursor.execute('SELECT points FROM user_points WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if result:
        points = result[0]
        embed = discord.Embed(title=f'{ctx.author.display_name}님의 포인트', color=discord.Color.purple())
        embed.add_field(name='포인트 잔액', value=f'{points:.1f}원')
        await ctx.send(embed=embed)
    else:
        await ctx.send('포인트 순위에 등록되어 있지 않습니다.')

@bot.command(name='포인트추가')
async def add_points(ctx, member: discord.Member, amount: float):
    if ctx.author.id not in admin_ids:
        await ctx.send("관리자만 사용 가능한 명령어입니다.")
        return

    # 포인트 추가
    user_id = member.id
    cursor.execute('INSERT OR IGNORE INTO user_points (user_id, points) VALUES (?, ?)', (user_id, 0.0))
    cursor.execute('UPDATE user_points SET points = points + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()

    await ctx.send(f'{member.display_name}님에게 {amount:.1f}원이 추가되었습니다.')

@bot.command(name='포인트차감')
async def remove_points(ctx, member: discord.Member, amount: float):
    if ctx.author.id not in admin_ids:
        await ctx.send("관리자만 사용 가능한 명령어입니다.")
        return

    # 포인트 차감
    user_id = member.id
    cursor.execute('UPDATE user_points SET points = points - ? WHERE user_id = ?', (amount, user_id))
    conn.commit()

    await ctx.send(f'{member.display_name}님의 포인트에서 {amount:.1f}원이 차감되었습니다.')

# 봇 토큰을 입력하세요.
bot.run('MTIwMjI4ODEwNzQ2MzEyNzA5OA.GXiXvh.sLA5dR4jltMMQD3OKMw-bhGWeS20QinI697YBM')
