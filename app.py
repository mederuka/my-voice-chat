# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
from streamlit_autorefresh import st_autorefresh
import time

# --- 1. ページ構成 ---
st.set_page_config(page_title="Echo-Free Voice Room", layout="wide")
st_autorefresh(interval=2000, key="vitals")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .user-tag { padding: 5px 15px; border-radius: 15px; background-color: #e1e4e8; font-weight: bold; }
    .room-label { font-size: 24px; font-weight: bold; color: #1f77b4; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. オーディオプロセッサ (データレベルでの消音) ---
class EchoCancellerProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0
        self.mute_others = False  # 相手（送信側）への消音

    def recv(self, frame):
        # 1. データを ndarray として取得
        raw_data = frame.to_ndarray()
        
        # 2. 【音量表示用】消音する前に現在の入力レベルを計算
        data_int16 = raw_data.astype(np.int16)
        if data_int16.ndim == 2:
            data_int16 = data_int16.mean(axis=1).astype(np.int16)
        
        if data_int16.size > 0:
            max_val = np.abs(data_int16[::50]).max()
            self.amplitude = int((max_val / 15000) * 100)
        
        # 3. 【消音ロジック】データを物理的にゼロ（無音）に上書き
        # このプロセッサは「自分専用」なので、これを0にしても「相手」には届きます。
        # ブラウザに返される「プレビュー音」だけを抹殺します。
        raw_data.fill(0)

        # 4. 無音化したデータをフレームとしてブラウザに返却
        return frame.from_ndarray(raw_data, format=frame.format.name)

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
    # 送信自体のオンオフ（必要なら）
    is_muted = st.checkbox("Mute for Others", value=False)
    
    st.divider()
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 5. メインエリア ---
st.title("Streamlit Voice Room")
st.markdown(f'<p class="room-label">Room: {room_id}</p>', unsafe_allow_html=True)

left_col, right_col = st.columns([1, 1])

with left_col:
    # WebRTC設定
    webrtc_ctx = webrtc_streamer(
        key=f"room-{room_id}-physical-mute", 
        mode=WebRtcMode.SENDRECV,
        audio_processor_factory=EchoCancellerProcessor,
        media_stream_constraints={
            "audio": {
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
        st.success("Mic Connected (Self-Muted)")
        st.markdown(f'<span class="user-tag">{st.session_state.fixed_user_name}</span>', unsafe_allow_html=True)
        
        if webrtc_ctx.audio_processor:
            st.write("Current Input Level (Visual Only)")
            st.progress(min(webrtc_ctx.audio_processor.amplitude, 100))
    else:
        st.info("Press Start to enter the room.")

# --- 6. チャットエリア ---
with right_col:
    st.subheader("Text Chat")
    chat_box = st.container(height=400)
    for msg in st.session_state.messages:
        with chat_box.chat_message(msg["role"]):
            st.write(f"**{msg['user']}**: {msg['text']}")

    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "user": st.session_state.fixed_user_name, "text": prompt})
        st.rerun()
