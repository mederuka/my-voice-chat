# -*- coding: utf-8 -*-
import streamlit as st
import os
import glob
import time
import uuid # 毎回違う名前を作るため
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="No-Cache Transceiver", layout="centered")

# 共有フォルダ（この中に一時的に音声ファイルを置く）
SAVE_DIR = "temp_voices"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# 2秒ごとにチェック
st_autorefresh(interval=2000, key="auto_sync")

st.title("📟 履歴ゼロ・トランシーバー")
st.caption("再生した瞬間にファイルを物理削除し、ブラウザのキャッシュも無視します。")

# --- 1. 送信セクション ---
audio_data = st.audio_input("話すときはマイクを押してください")

if audio_data:
    # 既存のファイルを全て掃除してから新しいのを作る
    for f in glob.glob(os.path.join(SAVE_DIR, "*.wav")):
        try: os.remove(f)
        except: pass
    
    # 毎回ユニークなIDをつけて保存（例: voice_abc123.wav）
    unique_id = str(uuid.uuid4())[:8]
    file_path = os.path.join(SAVE_DIR, f"voice_{unique_id}.wav")
    
    with open(file_path, "wb") as f:
        f.write(audio_data.getbuffer())
    st.success("送信しました！")
    st.rerun()

st.divider()

# --- 2. 受信 & 強制削除セクション ---
# フォルダ内にある.wavファイルを探す
voice_files = glob.glob(os.path.join(SAVE_DIR, "*.wav"))

if voice_files:
    latest_file = voice_files[0]
    
    st.warning("🆕 新着メッセージ（再生後に消去）")
    
    with open(latest_file, "rb") as f:
        audio_bytes = f.read()
    
    # 【重要】読み込んだら、そのファイル名を二度と使わないために物理削除
    try:
        os.remove(latest_file)
    except:
        pass
    
    # データを再生。一回限り。
    st.audio(audio_bytes, format="audio/wav", autoplay=True)
    
    # 再読み込みして画面をスッキリさせる
    st.session_state["played"] = True
else:
    st.write("💤 新着なし")

if st.session_state.get("played"):
    st.session_state["played"] = False
    time.sleep(0.1)
    st.rerun()
