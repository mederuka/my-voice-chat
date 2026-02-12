# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np

st.set_page_config(page_title="Simple Voice Chat")

# --- 1. 最小限のプロセッサ ---
class SimpleProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0
    def recv(self, frame):
        # 自分のマイク音のレベルを測るだけ（データはいじらない）
        raw_data = frame.to_ndarray().astype(np.int16)
        if raw_data.size > 0:
            if raw_data.ndim == 2: raw_data = raw_data.mean(axis=1)
            self.amplitude = int((np.abs(raw_data[::50]).max() / 15000) * 100)
        return frame

st.title("Stable Voice Chat")

# --- 2. 接続設定 ---
# keyを固定し、複雑な設定を排除してエラーを防ぎます
webrtc_ctx = webrtc_streamer(
    key="fixed-v11", 
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=SimpleProcessor,
    media_stream_constraints={
        "audio": {
            "echoCancellation": True,     # ブラウザに自分の声を消すよう頼む
            "noiseSuppression": True,     # ノイズ抑制
            "autoGainControl": True       # 自動音量調節
        },
        "video": False,
    },
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    async_processing=True,
)

# --- 3. UI表示 ---
if webrtc_ctx.state.playing:
    st.success("接続中")
    if webrtc_ctx.audio_processor:
        st.write("マイク入力レベル")
        st.progress(min(webrtc_ctx.audio_processor.amplitude, 100))
    
    st.info("💡 自分の声が聞こえる場合は、イヤホンを装着するか、ブラウザのタブを右クリックして『サイトをミュート』にしてください。")
else:
    st.info("Startボタンを押してください。")

# --- 4. チャット ---
if "msgs" not in st.session_state: st.session_state.msgs = []
if prompt := st.chat_input("メッセージを入力"):
    st.session_state.msgs.append(prompt)
    st.rerun()
for m in reversed(st.session_state.msgs):
    st.write(f"💬 {m}")
