# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode

st.set_page_config(page_title="P2P Connection Test")
st.title("Step 1: 通信の開通テスト")

# GoogleのSTUNサーバーを最大数指定して、接続経路をこじ開けます
RTC_CONFIG = {
    "iceServers": [
        {"urls": ["stun:stun.l.google.com:19302"]},
        {"urls": ["stun:stun1.l.google.com:19302"]},
        {"urls": ["stun:stun2.l.google.com:19302"]},
        {"urls": ["stun:stun3.l.google.com:19302"]},
        {"urls": ["stun:stun4.l.google.com:19302"]},
    ]
}

webrtc_ctx = webrtc_streamer(
    key="p2p-test-v14",
    mode=WebRtcMode.SENDRECV,
    rtc_configuration=RTC_CONFIG,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
)

if webrtc_ctx.state.playing:
    st.success("✅ マイク起動成功。相手も同じページでStartを押してください。")
