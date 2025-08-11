import cv2
import torch
from ultralytics import YOLO
import sqlite3
import datetime
import time

# --- 設定項目 ---
POST_INTERVAL_SECONDS = 30 # 人数と混雑状況をデータベースに記録する間隔（秒）
CONFIDENCE_THRESHOLD = 0.4 # YOLOv10の信頼度の閾値
DB_FILE = 'gym_data.db' # データベースファイル名

# 混雑レベルの閾値設定
THRESHOLD_EMPTY = 2
THRESHOLD_SLIGHTLY_CROWDED = 5

# --- データベース初期化関数 ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # テーブルが存在しない場合のみ作成
    c.execute('''
        CREATE TABLE IF NOT EXISTS congestion_log (
            timestamp TEXT PRIMARY KEY,
            person_count INTEGER,
            congestion_level TEXT
        )
    ''')
    conn.commit()
    conn.close()

# --- データをデータベースに挿入する関数 ---
def insert_data(person_count):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 混雑レベルの判定
    congestion_level = ""
    if person_count <= THRESHOLD_EMPTY:
        congestion_level = "空いています😊"
    elif person_count <= THRESHOLD_SLIGHTLY_CROWDED:
        congestion_level = "やや混雑しています🤔"
    else:
        congestion_level = "非常に混雑しています🚨"

    timestamp = datetime.datetime.now().isoformat()
    c.execute("INSERT INTO congestion_log VALUES (?, ?, ?)", (timestamp, person_count, congestion_level))
    conn.commit()
    conn.close()
    return congestion_level

# --- YOLOv10モデルのロード ---
try:
    print("YOLOv10モデルをロードしています...")
    device = 'mps' if torch.backends.mps.is_available() else ('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用するデバイス: {device}")
    model = YOLO('yolov10n.pt').to(device)
    print("モデルのロードが完了しました。")
except Exception as e:
    print(f"モデルのロード中にエラーが発生しました: {e}")
    exit(f"YOLOv10モデルのロードに失敗しました。インターネット接続を確認し、再度実行してください。エラー詳細: {e}")

# --- Webカメラの準備 ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("エラー: Webカメラにアクセスできません。")
    exit()
print("Webカメラに接続しました。")

# --- データベースの初期化 ---
init_db()

last_post_time = time.time()

# --- メインループ ---
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("エラー: フレームを読み込めませんでした。")
            break

        results = model(frame, conf=CONFIDENCE_THRESHOLD, classes=0, verbose=False)
        person_count = len(results[0].boxes) if results and results[0].boxes else 0
        print(f"現在時刻: {datetime.datetime.now().strftime('%H:%M:%S')} - ジム内の人数: {person_count}人")

        # 一定時間ごとにデータベースにデータを記録
        if time.time() - last_post_time >= POST_INTERVAL_SECONDS:
            congestion_level = insert_data(person_count)
            print(f"データベースに記録しました。人数: {person_count}人, 混雑レベル: {congestion_level}")
            last_post_time = time.time()

        time.sleep(1)

except KeyboardInterrupt:
    print("スクリプトを終了します。")
except Exception as e:
    print(f"予期せぬエラーが発生し、スクリプトが停止しました: {e}")
finally:
    cap.release()
    cv2.destroyAllWindows()