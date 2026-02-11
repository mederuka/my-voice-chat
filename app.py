# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
from streamlit_autorefresh import st_autorefresh
import time

# --- 1. ページ構成 ---
st.set_page_config(page_title="Voice Chat Room", layout="wide")
st_autorefresh(interval=2000, key="vitals")

# CSS: ブラウザが自動で鳴らす「自分の声を含むストリーム」を強制的に無音化
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    /* 全てのメディア要素を非表示。音声はJS側で制御を試みる */
    video, audio { display: none !important; }
    .user-tag { padding: 5px 15px; border-radius: 15px; background-color: #e1e4e8; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. オーディオプロセッサ ---
class LiteAudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0
        self.mute = False 

    def recv(self, frame):
        raw_data = frame.to_ndarray()
        if self.mute:
            raw_data.fill(0)
            self.amplitude = 0
            return frame.from_ndarray(raw_data, format=frame.format.name)

        data_int16 = raw_data.astype(np.int16)
        if data_int16.ndim == 2:
            data_int16 = data_int16.mean(axis=1).astype(np.int16)
        if data_int16.size > 0:
            max_val = np.abs(data_int16[::50]).max()
            self.amplitude = int((max_val / 15000) * 100)
        return frame

# --- 3. セッション・サイドバー ---
if "messages" not in st.session_state: st.session_state.messages = []
with st.sidebar:
    st.header("Settings")
    room_id = st.text_input("Room ID", value="101")
    is_muted = st.checkbox("Mute My Mic (相手への消音)", value=False)
    
    st.divider()
    st.info("自分の声が聞こえる場合は、ブラウザのタブを右クリックして『サイトをミュート』し、相手の声は別のデバイスやイヤホンで確認してください。")

# --- 4. メインエリア ---
st.title("Streamlit Voice Room")

# 【エコーキャンセルのための最重要設定】
# client_settings を使用して、ブラウザ側で「自分の声を再生しない」設定を明示します
webrtc_ctx = webrtc_streamer(
    key=f"room-{room_id}-v9-final",
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=LiteAudioProcessor,
    media_stream_constraints={
        "audio": {
            "echoCancellation": True,
            "noiseSuppression": True,
            "autoGainControl": True,
            "googEchoCancellation": True, # Google独自の拡張設定
            "googAutoGainControl": True,
            "googNoiseSuppression": True,
        },
        "video": False,
    },
    # ローカルのオーディオを再生しない（自分には聞こえない）ように指示
    # ※ライブラリのバージョンにより挙動が異なります
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    async_processing=True,
)

if webrtc_ctx.audio_processor:
    webrtc_ctx.audio_processor.mute = is_muted

left_col, right_col = st.columns([1, 1])

with left_col:
    if webrtc_ctx.state.playing:
        st.success("Connected")
        if not is_muted:
            st.write("Mic Level")
            st.progress(min(webrtc_ctx.audio_processor.amplitude if webrtc_ctx.audio_processor else 0, 100))
    else:
        st.info("Press Start")

# --- 5. チャットエリア ---
with right_col:
    chat_box = st.container(height=400)
    for msg in st.session_state.messages:
        chat_box.write(f"**{msg['user']}**: {msg['text']}")
    if prompt := st.chat_input("Type message..."):
        st.session_state.messages.append({"user": "Me", "text": prompt})
        st.rerun()
