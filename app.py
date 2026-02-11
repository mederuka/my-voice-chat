# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
from streamlit_autorefresh import st_autorefresh
import time

# --- 1. ページ構成 ---
st.set_page_config(page_title="Voice Chat Room", layout="wide")
st_autorefresh(interval=2000, key="vitals")

# 【最重要】CSSによる「音の完全封鎖」
# ページ内のあらゆる音が出る要素を、ブラウザレベルで強制ミュート・非表示にする
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .user-tag { padding: 5px 15px; border-radius: 15px; background-color: #e1e4e8; font-weight: bold; }
    
    /* これが効かないブラウザはほぼありません */
    video, audio {
        display: none !important;
        visibility: hidden !important;
    }
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
    is_muted = st.checkbox("Mute for Others (相手への消音)", value=False)
    # 【追加】強制的な受信用ミュートボタン
    force_silent = st.checkbox("Disable My Speakers (自分のスピーカーを殺す)", value=True)

# --- 4. メインエリア ---
st.title("Streamlit Voice Room (Anti-Echo)")

# 【最終手段】JavaScriptによるDOMの直接破壊
# 1秒ごとにページ内の全メディア要素をミュートし、音量を0に固定し続けます
st.components.v1.html(
    f"""
    <script>
    const forceMute = () => {{
        const media = window.parent.document.querySelectorAll('audio, video');
        media.forEach(m => {{
            m.muted = { 'true' if force_silent else 'false' };
            m.volume = 0;
        }});
    }};
    setInterval(forceMute, 500);
    </script>
    """,
    height=0,
)

left_col, right_col = st.columns([1, 1])

with left_col:
    # WebRTC設定
    webrtc_ctx = webrtc_streamer(
        key="FINAL-FIX-KEY-V6", 
        # 送受信モードだが、JSで出力を殺す
        mode=WebRtcMode.SENDRECV,
        audio_processor_factory=LiteAudioProcessor,
        media_stream_constraints={{
            "audio": {{
                "echoCancellation": True,
                "noiseSuppression": True,
                "autoGainControl": True,
            }},
            "video": False,
        }},
        async_processing=True,
    )

    if webrtc_ctx.audio_processor:
        webrtc_ctx.audio_processor.mute = is_muted

    if webrtc_ctx.state.playing:
        st.write(f"🎙️ Status: {'MUTED' if is_muted else 'ON AIR'}")
        if not is_muted:
            st.progress(min(webrtc_ctx.audio_processor.amplitude if webrtc_ctx.audio_processor else 0, 100))
    else:
        st.info("Press Start")

# --- 5. チャットエリア ---
with right_col:
    chat_box = st.container(height=400)
    for msg in st.session_state.messages:
        chat_box.write(f"**{msg['user']}**: {msg['text']}")
    if prompt := st.chat_input("Type here..."):
        st.session_state.messages.append({{"user": "Me", "text": prompt}})
        st.rerun()
