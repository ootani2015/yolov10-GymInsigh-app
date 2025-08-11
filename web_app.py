import gradio as gr
import pandas as pd
import plotly.express as px
import os
import sqlite3 # 新たに追加

# --- 設定項目 ---
DB_FILE = 'gym_data.db' # data_logger.pyと一致させる
# SQLiteデータベースファイルが保存されている場所に合わせて、必要であればパスを調整してください。

# UIを更新する関数
def update_ui():
    if not os.path.exists(DB_FILE):
        return "データベースファイルが見つかりません。", None
    
    try:
        # データベースに接続
        conn = sqlite3.connect(DB_FILE)
        
        # データベースから全データを読み込む
        df = pd.read_sql_query("SELECT * FROM congestion_log", conn)
        
        conn.close() # 接続を閉じる
        
        # DataFrameのtimestampをdatetime型に変換
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 最新のデータポイントを取得
        latest_data = df.iloc[-1]
        
        # 現在のステータス文字列を作成
        status_text = f"最終更新時刻: {latest_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        status_text += "```\n"
        status_text += f"人数: {latest_data['person_count']}人\n"
        status_text += f"混雑レベル: {latest_data['congestion_level']}\n"
        status_text += "```"

        # 履歴のプロットを作成
        fig = px.line(df, x="timestamp", y="person_count", title="ジム混雑状況の履歴")
        
        return status_text, fig
        
    except Exception as e:
        return f"データベースの読み込み中にエラーが発生しました: {e}", None

# Gradioのインターフェースを作成 (以下は変更不要)
with gr.Blocks() as demo:
    gr.Markdown("# YOLOv10 アプリケーション ステータス")
    
    with gr.Row():
        current_status = gr.Textbox(label="現在のステータス", interactive=False, lines=5)
        history_plot = gr.Plot(label="リソース使用履歴")

    gr.Interface(
        fn=update_ui,
        inputs=None,
        outputs=[current_status, history_plot],
        live=True
    )
    
if __name__ == "__main__":
    demo.launch()