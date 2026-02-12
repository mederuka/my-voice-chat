# -*- coding: utf-8 -*-
import streamlit as st
import os
import time
from streamlit_autorefresh import st_autorefresh

# ページ設定でレイアウトを固定し、ガタつきを抑える
st.set_page_config(page_title="Quiet Transceiver", layout="centered")

VOICE_PATH = "shared_msg.wav"

# --- 画面の点滅対策 ---
# 間隔を5秒(5000ms)に広げ、リフレッシュ回数を制限せずに回します
# これにより、点滅の頻度を下げます
st_autorefresh(interval=5000, key="silent_sync")

st.title("📟 静かなトランシーバー")

# --- 送信エリア ---
# st.audio_input 自体もリロードでリセットされないよう、安定した位置に配置
audio_data = st.audio_input("マイクで録音してください")

if audio_data:
    with open(VOICE_PATH, "wb") as f:
        f.write(audio_data.getbuffer())
    # 自分が送った時間を記録して、自分への自動再生をブロック
    st.session_state["last_seen"] = os.path.getmtime(VOICE_PATH)
    st.success("送信しました！")
    # 送信時は即座に反映させるため rerun
    st.rerun()

st.divider()

# --- 受信・自動再生エリア ---
if os.path.exists(VOICE_PATH):
    mtime = os.path.getmtime(VOICE_PATH)
    
    if "last_seen" not in st.session_state:
        st.session_state["last_seen"] = mtime # 最初は今のファイルを「既読」にする

    # 本当に新しいファイルが来た時だけ、プレイヤーを表示して再生
    if mtime > st.session_state["last_seen"]:
        st.warning("🆕 新しい声が届きました")
        st.audio(VOICE_PATH, format="audio/wav", autoplay=True)
        
        # 再生ボタン（手動）も一応置いておく
        if st.button("既読にする"):
            st.session_state["last_seen"] = mtime
            st.rerun()
    else:
        st.write("💤 新着なし")
        st.caption(f"最終チェック: {time.strftime('%H:%M:%S')}")
