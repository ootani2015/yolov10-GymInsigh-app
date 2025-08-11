import discord
import sqlite3
import datetime

# --- 設定項目 ---
DISCORD_BOT_TOKEN = "トークンはGitHubで共有する際に一時的に消しています"
DB_FILE = 'gym_data.db'

# 混雑レベルの閾値設定
THRESHOLD_EMPTY = 2
THRESHOLD_SLIGHTLY_CROWDED = 5

# --- Discord Botの初期設定 ---
intents = discord.Intents.default()
intents.message_content = True # メッセージの内容を読み取るためのインテント
client = discord.Client(intents=intents)

# --- データベースから最新の人数を取得する関数 ---
def get_latest_person_count():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT person_count FROM congestion_log ORDER BY timestamp DESC LIMIT 1")
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    # Bot自身のメッセージには反応しない
    if message.author == client.user:
        return

    # '!status' コマンドに反応
    if message.content.startswith('!status'):
        try:
            person_count = get_latest_person_count()
            if person_count is not None:
                # 混雑レベルの判定
                congestion_level = ""
                if person_count <= THRESHOLD_EMPTY:
                    congestion_level = "空いています😊"
                elif person_count <= THRESHOLD_SLIGHTLY_CROWDED:
                    congestion_level = "やや混雑しています🤔"
                else:
                    congestion_level = "非常に混雑しています🚨"

                response_message = (
                    f"現在のジムの混雑状況をお知らせします。\n"
                    f"現在の人数: **{person_count}人**\n"
                    f"混雑レベル: **{congestion_level}**"
                )
            else:
                response_message = "人数データがまだ記録されていません。"

            await message.channel.send(response_message)
        except Exception as e:
            await message.channel.send(f"データの取得中にエラーが発生しました: {e}")

client.run(DISCORD_BOT_TOKEN)
