# -*- coding: utf-8 -*-
import streamlit as st
import os
import time
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Smart Transceiver", layout="centered")

# 音声ファイルの保存パス
VOICE_PATH = "shared_msg.wav"

st.title("📟 既読判定トランシーバー")
st.caption("新しいメッセージが届いた時だけ、1回だけ自動再生します。")

# 2秒ごとに画面をチェック
st_autorefresh(interval=2000, key="auto_sync")

# --- 1. 送信セクション ---
audio_data = st.audio_input("話すときはマイクを押してください")

if audio_data:
    with open(VOICE_PATH, "wb") as f:
        f.write(audio_data.getbuffer())
    # 送信した時刻を「既読」として保存し、自分の声が自分に返るのを防ぐ
    st.session_state["last_played_time"] = os.path.getmtime(VOICE_PATH)
    st.success("送信完了！")
    st.rerun()

st.divider()

# --- 2. 受信セクション（既読判定ロジック） ---
if os.path.exists(VOICE_PATH):
    current_mod_time = os.path.getmtime(VOICE_PATH)
    
    # セッション状態で「最後に再生した時刻」を管理
    if "last_played_time" not in st.session_state:
        st.session_state["last_played_time"] = 0

    # 【重要】サーバーのファイルが、自分の既読時刻より新しければ再生
    if current_mod_time > st.session_state["last_played_time"]:
        st.write("🆕 新着メッセージを受信中...")
        st.audio(VOICE_PATH, format="audio/wav", autoplay=True)
        
        # 再生したら、今の時刻を既読にする
        st.session_state["last_played_time"] = current_mod_time
        st.info(f"受信時刻: {time.ctime(current_mod_time)}")
    else:
        st.write("💤 新着なし（待機中）")
        st.caption(f"最終受信: {time.ctime(st.session_state['last_played_time'])}")
else:
    st.write("待機中... 相手の声を待っています。")
