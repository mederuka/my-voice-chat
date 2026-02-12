# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
import time

st.set_page_config(page_title="Split Voice Room", layout="wide")

# --- 1. プロセッサ (送信レベル測定用) ---
class SendProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0
    def recv(self, frame):
        raw_data = frame.to_ndarray().astype(np.int16)
        if raw_data.size > 0:
            # モノラル化してレベル計算
            if raw_data.ndim == 2: raw_data = raw_data.mean(axis=1)
            self.amplitude = int((np.abs(raw_data[::50]).max() / 15000) * 100)
        return frame

# --- 2. メインUI ---
st.title("Echo-Free Split System")
room_id = st.sidebar.text_input("Room ID", "101")

col_mic, col_speaker = st.columns(2)

with col_mic:
    st.subheader("1. Your Microphone")
    st.info("送信専用：自分の声はここから再生されません。")
    # 【送信専用モード】自分の声は絶対に自分には聞こえません
    mic_ctx = webrtc_streamer(
        key=f"mic-{room_id}",
        mode=WebRtcMode.SENDONLY,  # 送信のみ
        audio_processor_factory=SendProcessor,
        media_stream_constraints={"audio": True, "video": False},
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        async_processing=True,
    )
    if mic_ctx.audio_processor:
        st.write("Mic Level")
        st.progress(min(mic_ctx.audio_processor.amplitude, 100))

with col_speaker:
    st.subheader("2. Room Speaker")
    st.info("受信専用：ルーム内の他の人の声だけが流れます。")
    # 【受信専用モード】相手の声だけを拾います
    sp_ctx = webrtc_streamer(
        key=f"sp-{room_id}",
        mode=WebRtcMode.RECVONLY,  # 受信のみ
        media_stream_constraints={"audio": True, "video": False},
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        async_processing=True,
    )

# --- 3. チャット (共通) ---
st.divider()
if "messages" not in st.session_state: st.session_state.messages = []
prompt = st.chat_input("Message...")
if prompt:
    st.session_state.messages.append(prompt)
    st.rerun()
for m in reversed(st.session_state.messages):
    st.write(f"💬 {m}")
