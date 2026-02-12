# -*- coding: utf-8 -*-
import streamlit as st
import os
import time

st.set_page_config(page_title="Auto-Transceiver", layout="centered")

# 音声ファイルの保存パス
VOICE_PATH = "shared_msg.wav"

st.title("📟 自動同期トランシーバー")
st.caption("マイクで録音してチェック（送信）を押すと、即座に相手に届きます。")

# --- 1. 送信セクション ---
# st.audio_input は録音完了時にデータを返します
audio_data = st.audio_input("話すときはマイクを押してください")

if audio_data:
    # 録音データをサーバーに保存
    with open(VOICE_PATH, "wb") as f:
        f.write(audio_data.getbuffer())
    st.success("送信しました！")
    # 送信直後に一度リロードして状態を確定させる
    st.rerun()

st.divider()

# --- 2. 受信セクション ---
st.subheader("👂 受信メッセージ")

if os.path.exists(VOICE_PATH):
    # ファイルの更新日時を「部屋の鍵」として利用する
    last_mod_time = os.path.getmtime(VOICE_PATH)
    
    # 相手が新しい声を送ったことを検知するために、
    # 前回再生した時刻と照合（簡易的に最新の1つを表示）
    st.write(f"最新の受信音 (更新: {time.ctime(last_mod_time)})")
    
    # st.audio は autoplay=True にすることで、
    # 画面にこのプレイヤーが現れた瞬間に再生を開始します
    st.audio(VOICE_PATH, format="audio/wav", autoplay=True)
else:
    st.write("待機中... 相手の声を待っています。")

# --- 3. 自動更新ロジック ---
# 2秒ごとに画面をチェックして、相手からの新着がないか確認する
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=2000, key="auto_sync")
