# -*- coding: utf-8 -*-
import streamlit as st
import os
import time
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Auto-Clear Transceiver", layout="centered")

# ファイル保存パス
VOICE_PATH = "shared_msg.wav"

# 3秒ごとにチェック（点滅と反応速度のバランス）
st_autorefresh(interval=3000, key="auto_sync")

st.title("📟 自動既読トランシーバー")
st.caption("新着メッセージを1回だけ再生し、終わったら自動で待機状態に戻ります。")

# --- 1. 送信セクション ---
audio_data = st.audio_input("話すときはマイクを押してください")

if audio_data:
    with open(VOICE_PATH, "wb") as f:
        f.write(audio_data.getbuffer())
    # 自分が送信したものは「既読」として即座に登録
    st.session_state["last_played_time"] = os.path.getmtime(VOICE_PATH)
    st.success("送信完了！")
    st.rerun()

st.divider()

# --- 2. 受信 & 自動既読セクション ---
if os.path.exists(VOICE_PATH):
    current_mtime = os.path.getmtime(VOICE_PATH)
    
    # 初回起動時の既読設定
    if "last_played_time" not in st.session_state:
        st.session_state["last_played_time"] = current_mtime

    # 【重要】未読（ファイル更新時刻 > 既読時刻）の場合のみ再生
    if current_mtime > st.session_state["last_played_time"]:
        st.warning("🆕 新着メッセージを再生中...")
        
        # autoplayで再生。プレイヤーが表示された瞬間に音が鳴ります
        st.audio(VOICE_PATH, format="audio/wav", autoplay=True)
        
        # 3秒（autorefreshの間隔）後に次のサイクルが来た時、
        # ここで既読時間を更新するため、プレイヤーは消えます。
        st.session_state["last_played_time"] = current_mtime
    else:
        st.write("💤 次のメッセージを待っています...")
        st.caption(f"最終受信: {time.strftime('%H:%M:%S', time.localtime(st.session_state['last_played_time']))}")
else:
    st.write("待機中... 相手の声を待っています。")

# --- 3. 履歴のクリア（任意） ---
if st.button("履歴をリセット"):
    if os.path.exists(VOICE_PATH):
        os.remove(VOICE_PATH)
    st.session_state["last_played_time"] = 0
    st.rerun()
