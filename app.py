# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np

st.set_page_config(page_title="Split Voice System")

# レベル測定用の軽いプロセッサ
class MeterProcessor(AudioProcessorBase):
    def __init__(self): self.amplitude = 0
    def recv(self, frame):
        raw_data = frame.to_ndarray().astype(np.int16)
        if raw_data.size > 0:
            if raw_data.ndim == 2: raw_data = raw_data.mean(axis=1)
            self.amplitude = int((np.abs(raw_data[::50]).max() / 15000) * 100)
        return frame

st.title("Echo-Free: Split Voice Room")

# Python 3.13のエラーを防ぐため、キーを完全に固定
RTC_CONFIG = {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 自分の声を送る")
    st.caption("送信専用：自分の声はスピーカーから出ません")
    # 【SENDONLY】にすることで、ブラウザは「再生」を停止します
    ctx_send = webrtc_streamer(
        key="send-only-v12",
        mode=WebRtcMode.SENDONLY,
        audio_processor_factory=MeterProcessor,
        media_stream_constraints={"audio": True, "video": False},
        rtc_configuration=RTC_CONFIG,
        async_processing=True,
    )
    if ctx_send.audio_processor:
        st.progress(min(ctx_send.audio_processor.amplitude, 100))

with col2:
    st.subheader("2. 相手の声を聞く")
    st.caption("受信専用：ルーム内の音だけを鳴らします")
    # 【RECVONLY】にすることで、自分のマイクは完全に遮断されます
    ctx_recv = webrtc_streamer(
        key="recv-only-v12",
        mode=WebRtcMode.RECVONLY,
        media_stream_constraints={"audio": True, "video": False},
        rtc_configuration=RTC_CONFIG,
        async_processing=True,
    )

st.divider()
st.info("💡 使い方：両方の『Start』を押してください。左で送り、右で聞くという独立した回路になります。")
