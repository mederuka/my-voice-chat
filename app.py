# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
from streamlit_autorefresh import st_autorefresh
import time

# --- 1. ページ構成 ---
st.set_page_config(page_title="Voice Chat Room", layout="wide")
st_autorefresh(interval=2000, key="vitals")

# --- 2. オーディオプロセッサ (データは加工せず、レベル測定のみ) ---
class LiteAudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0
        self.is_muted = False

    def recv(self, frame):
        raw_data = frame.to_ndarray()
        
        # 相手に送る声の消音（チェックボックス連動）
        if self.is_muted:
            raw_data.fill(0)
            return frame.from_ndarray(raw_data, format=frame.format.name)

        # レベル表示用計算
        data_int16 = raw_data.astype(np.int16)
        if data_int16.ndim == 2:
            data_int16 = data_int16.mean(axis=1).astype(np.int16)
        if data_int16.size > 0:
            max_val = np.abs(data_int16[::50]).max()
            self.amplitude = int((max_val / 15000) * 100)
            
        return frame

# --- 3. セッション管理 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. サイドバー設定 ---
with st.sidebar:
    st.header("Settings")
    room_id = st.text_input("Room ID", value="101")
    is_muted = st.checkbox("Mute My Mic (相手に声を届けない)", value=False)
    
    st.divider()
    st.warning("自分の声が聞こえる場合、この下のボタンを押してください。")
    # ブラウザのオーディオ出力を強制停止するJSを発動
    if st.button("自分の声をスピーカーから消す"):
        st.components.v1.html("""
            <script>
            const audios = window.parent.document.querySelectorAll('audio, video');
            audios.forEach(a => { a.muted = true; a.volume = 0; });
            console.log("All audio muted on browser side.");
            </script>
        """, height=0)

# --- 5. メインエリア ---
st.title("Streamlit Voice Room")

# WebRTC設定
webrtc_ctx = webrtc_streamer(
    key=f"room-{room_id}-final-fix",
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=LiteAudioProcessor,
    media_stream_constraints={
        "audio": {
            "echoCancellation": True,
            "noiseSuppression": True,
            "autoGainControl": True,
        },
        "video": False,
    },
    async_processing=True,
)

if webrtc_ctx.audio_processor:
    webrtc_ctx.audio_processor.is_muted = is_muted

left_col, right_col = st.columns([1, 1])

with left_col:
    if webrtc_ctx.state.playing:
        st.success("ON AIR")
        if not is_muted:
            st.write("Mic Level")
            st.progress(min(webrtc_ctx.audio_processor.amplitude if webrtc_ctx.audio_processor else 0, 100))
    else:
        st.info("Press Start")

# --- 6. チャットエリア ---
with right_col:
    st.subheader("Text Chat")
    chat_box = st.container(height=300)
    for msg in st.session_state.messages:
        chat_box.write(f"**{msg['user']}**: {msg['text']}")
    if prompt := st.chat_input("Message..."):
        st.session_state.messages.append({"user": "Me", "text": prompt})
        st.rerun()
