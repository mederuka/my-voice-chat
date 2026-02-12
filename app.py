# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode

st.set_page_config(page_title="Connection Test")

st.title("Step 1: 相手と繋がるかテスト")

# 接続エラーを回避するため、外部のSTUNサーバーを複数指定
RTC_CONFIG = {
    "iceServers": [
        {"urls": ["stun:stun.l.google.com:19302"]},
        {"urls": ["stun:stun1.l.google.com:19302"]}
    ]
}

# 複雑な処理をすべて排除し、通信の確立だけに集中
webrtc_ctx = webrtc_streamer(
    key="fixed-v13",  # エラー防止のためキーを固定
    mode=WebRtcMode.SENDRECV,
    rtc_configuration=RTC_CONFIG,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
)

if webrtc_ctx.state.playing:
    st.success("✅ 通信準備完了")
    st.write("1. このURLをコピーして、スマホや別のPCで開いてください。")
    st.write("2. 両方で『Start』を押してください。")
