# -*- coding: utf-8 -*-
import streamlit as st
import os
import time
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="One-Time Player", layout="centered")

# ファイル保存パス
VOICE_PATH = "shared_msg.wav"
TEMP_PATH = "playing_msg.wav" # 再生中に一時的に避難させる用

# 2秒ごとにチェック（反応速度を優先）
st_autorefresh(interval=2000, key="auto_sync")

st.title("📟 使い切りトランシーバー")
st.caption("再生した音声は即座に削除され、二度と繰り返しません。")

# --- 1. 送信セクション ---
audio_data = st.audio_input("話すときはマイクを押してください")

if audio_data:
    # 既存の古いファイルがあれば消してから保存
    if os.path.exists(VOICE_PATH):
        os.remove(VOICE_PATH)
    
    with open(VOICE_PATH, "wb") as f:
        f.write(audio_data.getbuffer())
    st.success("送信完了！")
    st.rerun()

st.divider()

# --- 2. 受信 & 即時削除セクション ---
if os.path.exists(VOICE_PATH):
    st.warning("🆕 新着メッセージを再生中（再生後、自動消去されます）")
    
    # 【核心】ファイルを読み込んでから、すぐに物理ファイルを削除する
    with open(VOICE_PATH, "rb") as f:
        audio_bytes = f.read()
    
    # 読み込んだら即削除（これでリフレッシュしても二度と出現しません）
    os.remove(VOICE_PATH)
    
    # メモリ上のデータを再生
    st.audio(audio_bytes, format="audio/wav", autoplay=True)
    
    # 画面を一度クリーンにするためのフラグ
    st.session_state["just_played"] = True
else:
    st.write("💤 次のメッセージを待っています...")
    st.caption(f"最終チェック: {time.strftime('%H:%M:%S')}")

# 無限ループ防止：再生直後の状態をリセット
if st.session_state.get("just_played"):
    st.session_state["just_played"] = False
    time.sleep(0.5) # 再生開始の猶予
    st.rerun()
