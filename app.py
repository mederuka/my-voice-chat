# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np

st.set_page_config(page_title="Split System", layout="wide")

# --- プロセッサ ---
class SendProcessor(AudioProcessorBase):
    def __init__(self): self.amplitude = 0
    def recv(self, frame):
        raw_data = frame.to_ndarray().astype(np.int16)
        if raw_data.size > 0:
            if raw_data.ndim == 2: raw_data = raw_data.mean(axis=1)
            self.amplitude = int((np.abs(raw_data[::50]).max() / 15000) * 100)
        return frame

st.title("Final Echo-Cancel Solution")

# --- 対策の核心 ---
st.warning("⚠️ 重要: エコーを完全に消すため、以下の2つの『Start』を両方押してください。")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 送信 (マイク)")
    # 【送信専用】にすることで、自分の声は絶対に自分には聞こえません。
    webrtc_streamer(
        key="send-only",
        mode=WebRtcMode.SENDONLY,
        audio_processor_factory=SendProcessor,
        media_stream_constraints={"audio": True, "video": False},
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        async_processing=True,
    )

with col2:
    st.subheader("2. 受信 (スピーカー)")
    # 【受信専用】にすることで、相手の声だけがここから流れます。
    # ここで受信する音の中に自分の声が混ざっている場合、それは「相手」がスピーカーで鳴らしているからです。
    webrtc_streamer(
        key="recv-only",
        mode=WebRtcMode.RECVONLY,
        media_stream_constraints={"audio": True, "video": False},
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        async_processing=True,
    )

st.info("💡 ヒント: これでも自分の声が聞こえる場合、それは『相手のマイク』が、あなたの声を拾って送り返しています。その場合は相手にイヤホンをお願いしてください。")
