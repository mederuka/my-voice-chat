# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
from streamlit_autorefresh import st_autorefresh
import time

# --- 1. ページ構成と自動更新 ---
st.set_page_config(page_title="Voice Chat Room", layout="wide")
st_autorefresh(interval=1000, key="vitals")

# CSSデザイン
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .user-tag {
        padding: 5px 15px;
        border-radius: 15px;
        background-color: #e1e4e8;
        font-weight: bold;
        color: #2c3e50;
        display: inline-block;
    }
    .room-label { font-size: 24px; font-weight: bold; color: #1f77b4; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. オーディオプロセッサ (音量レベル表示用のみ) ---
class LiteAudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0

    def recv(self, frame):
        raw_data = frame.to_ndarray().astype(np.int16)
        
        # ステレオならモノラルに変換して音量を計算
        if raw_data.ndim == 2:
            raw_data = raw_data.mean(axis=1).astype(np.int16)

        if raw_data.size > 0:
            max_val = np.abs(raw_data[::50]).max()
            normalized = int((max_val / 15000) * 100)
            self.amplitude = max(0, min(normalized, 100))
            
        return frame

# --- 3. セッション管理 ---
if "fixed_user_name" not in st.session_state:
    st.session_state.fixed_user_name = "User_" + str(int(time.time()) % 100)
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. サイドバー設定 ---
with st.sidebar:
    st.header("Settings")
    u_name = st.text_input("Name", value=st.session_state.fixed_user_name)
    st.session_state.fixed_user_name = u_name
    room_id = st.text_input("Room ID", value="101")
    st.divider()
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 5. メインエリア ---
st.title("Streamlit Voice Room")
st.markdown(f'<p class="room-label">Room: {room_id}</p>', unsafe_allow_html=True)

# 2カラムレイアウト
left_col, right_col = st.columns([1, 1])

with left_col:
    # WebRTC設定（録音バッファなし）
    webrtc_ctx = webrtc_streamer(
        key=f"room-{room_id}-audio-only", 
        mode=WebRtcMode.SENDRECV,
        audio_processor_factory=LiteAudioProcessor,
        media_stream_constraints={
            "audio": {
                "sampleRate": 16000,
                "channelCount": 1,
                "echoCancellation": True,
                "noiseSuppression": True,
                "autoGainControl": True,
            },
            "video": False,
        },
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        async_processing=True,
    )

    if webrtc_ctx.state.playing:
        st.markdown(f'<span class="user-tag">{st.session_state.fixed_user_name} (You)</span>', unsafe_allow_html=True)
        if webrtc_ctx.audio_processor:
            st.write("Voice Level")
            st.progress(min(webrtc_ctx.audio_processor.amplitude, 100))
    else:
        st.info("Press Start to enter the voice room.")

# --- 6. チャットエリア ---
with right_col:
    st.subheader("Text Chat")
    
    # メッセージ表示（スクロール可能なコンテナ風）
    chat_box = st.container(height=400)
    for msg in st.session_state.messages:
        with chat_box.chat_message(msg["role"]):
            st.write(f"**{msg['user']}**: {msg['text']}")

    # 入力フォーム
    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({
            "role": "user", 
            "user": st.session_state.fixed_user_name, 
            "text": prompt
        })
        st.rerun()
