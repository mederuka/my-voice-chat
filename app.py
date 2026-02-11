# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
from streamlit_autorefresh import st_autorefresh
import time

# --- 1. ページ構成 ---
st.set_page_config(page_title="Voice Chat Room", layout="wide")
st_autorefresh(interval=2000, key="vitals")

# CSS: UIデザインと、ブラウザによる自動再生を視覚的に隠す設定
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .user-tag {
        padding: 5px 15px;
        border-radius: 15px;
        background-color: #e1e4e8;
        font-weight: bold;
        color: #2c3e50;
        display: inline-block;
        margin-bottom: 10px;
    }
    .room-label { font-size: 24px; font-weight: bold; color: #1f77b4; }
    
    /* ページ内のオーディオ・ビデオ要素を強制的に非表示 */
    video, audio {
        display: none !important;
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
        
        # 相手に送る声を消音（送信ミュート）
        if self.mute:
            raw_data.fill(0)
            self.amplitude = 0
            return frame.from_ndarray(raw_data, format=frame.format.name)

        data_int16 = raw_data.astype(np.int16)
        if data_int16.ndim == 2:
            data_int16 = data_int16.mean(axis=1).astype(np.int16)

        if data_int16.size > 0:
            max_val = np.abs(data_int16[::50]).max()
            normalized = int((max_val / 15000) * 100)
            self.amplitude = max(0, min(normalized, 100))
            
        return frame

# --- 3. セッション管理 ---
if "fixed_user_name" not in st.session_state:
    st.session_state.fixed_user_name = "User_" + str(int(time.time()) % 100)
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. サイドバー設定 ---
with st.sidebar:
    st.header("Settings")
    u_name = st.text_input("Name", value=st.session_state.fixed_user_name)
    st.session_state.fixed_user_name = u_name
    room_id = st.text_input("Room ID", value="101")
    
    st.divider()
    # 相手に自分の声を届けないスイッチ
    is_muted = st.checkbox("Mute My Mic (相手への消音)", value=False)
    
    # 自分のスピーカーから一切の音を出さないスイッチ（これがエコー対策の鍵）
    force_silent = st.checkbox("Mute My Speakers (自分への消音)", value=True)
    
    st.divider()
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 5. メインエリア ---
st.title("Streamlit Voice Room")
st.markdown(f'<p class="room-label">Room: {room_id}</p>', unsafe_allow_html=True)

# 自分のスピーカーを殺すためのJavaScriptを注入
# force_silent が True の間、全メディア要素をミュートし続けます
st.components.v1.html(
    f"""
    <script>
    const muteFunc = () => {{
        const media = window.parent.document.querySelectorAll('audio, video');
        media.forEach(m => {{
            m.muted = {str(force_silent).lower()};
            m.volume = 0;
        }});
    }};
    setInterval(muteFunc, 500);
    </script>
    """,
    height=0,
)

left_col, right_col = st.columns([1, 1])

with left_col:
    # WebRTC設定
    webrtc_ctx = webrtc_streamer(
        key=f"room-{room_id}-final-v7", 
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
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        async_processing=True,
    )

    if webrtc_ctx.audio_processor:
        webrtc_ctx.audio_processor.mute = is_muted

    if webrtc_ctx.state.playing:
        status_label = "🔇 Muted" if is_muted else "🎙️ On Air"
        st.markdown(f'<span class="user-tag">{st.session_state.fixed_user_name} ({status_label})</span>', unsafe_allow_html=True)
        if force_silent:
            st.warning("自分のスピーカーはミュートされています")
        
        if not is_muted:
            st.write("Mic Level")
            st.progress(min(webrtc_ctx.audio_processor.amplitude if webrtc_ctx.audio_processor else 0, 100))
    else:
        st.info("Press Start to enter.")

# --- 6. チャットエリア ---
with right_col:
    st.subheader("Text Chat")
    chat_box = st.container(height=400)
    for msg in st.session_state.messages:
        with chat_box.chat_message(msg["role"]):
            st.write(f"**{msg['user']}**: {msg['text']}")

    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({
            "role": "user", 
            "user": st.session_state.fixed_user_name, 
            "text": prompt
        })
        st.rerun()
