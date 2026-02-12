# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np

st.set_page_config(page_title="Connection Test")

# 接続を安定させるためのSTUNサーバー
RTC_CONFIG = {
    "iceServers": [
        {"urls": ["stun:stun.l.google.com:19302"]},
        {"urls": ["stun:stun1.l.google.com:19302"]}
    ]
}

st.title("Step 1: 相手と繋がるかテスト")

# 重要なのはこの 'key' です。
# 全員が同じ key を使うことで、同じ「仮想ルーム」に入ろうとします。
webrtc_ctx = webrtc_streamer(
    key="global-room-test", 
    mode=WebRtcMode.SENDRECV, # まずは標準の送受信で疎通確認
    rtc_configuration=RTC_CONFIG,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
)

if webrtc_ctx.state.playing:
    st.success("✅ あなたのマイクは起動しました。")
    st.write("この状態で、**別のブラウザ（またはスマホ）から同じURLを開き、Startを押してください。**")
else:
    st.info("Startを押して、相手が来るのを待ってください。")
