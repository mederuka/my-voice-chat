import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
from streamlit_autorefresh import st_autorefresh
import time
import io
import wave

# --- 1. ページ設定と自動更新 ---
st.set_page_config(page_title="Streamlit Room Chat", layout="wide", page_icon="🏠")
st_autorefresh(interval=500, key="vitals")

# CSSデザイン
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 20px; }
    .room-info {
        padding: 10px 20px;
        border-radius: 10px;
        background-color: #007bff;
        color: white;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. オーディオプロセッサ ---
class ProAudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0
        self.is_recording = False
        self.frames = []

    def recv(self, frame):
        try:
            audio_data = frame.to_ndarray()
            if audio_data.size > 0:
                max_val = np.abs(audio_data[::10]).max()
                self.amplitude = int((max_val / 15000) * 100)
            if self.is_recording:
                self.frames.append(audio_data.tobytes())
        except Exception:
            pass
        return frame

# --- 3. サイドバー：部屋と名前の設定 ---
with st.sidebar:
    st.header("⚙️ 設定")
    user_name = st.text_input("あなたの名前", value="User_" + str(int(time.time()) % 100))
    # ルームナンバーの入力
    room_id = st.text_input("ルームナンバー (数字や英字)", value="101")
    
    st.divider()
    st.write(f"現在の設定:")
    st.caption(f"名前: {user_name}")
    st.caption(f"部屋: Room {room_id}")

# --- 4. メインエリア ---
st.title("🎙️ Multi-Room Voice System")

# ルーム情報を目立たせる
st.markdown(f"""
    <div class="room-info">
        現在 <strong>Room {room_id}</strong> に入室準備中です
    </div>
""", unsafe_allow_html=True)

col_main, col_status = st.columns([3, 1])

with col_main:
    # 重要：keyに room_id を含めることで、部屋ごとに通信を分離します
    webrtc_ctx = webrtc_streamer(
        key=f"room-{room_id}-chat", 
        mode=WebRtcMode.SENDRECV,
        audio_processor_factory=ProAudioProcessor,
        media_stream_constraints={"audio": True, "video": False},
        rtc_configuration={
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        },
        async_processing=True,
    )

# --- 5. 録音とメーター (前回の機能を維持) ---
with col_status:
    st.subheader("Control")
    if webrtc_ctx.state.playing and webrtc_ctx.audio_processor:
        amp = getattr(webrtc_ctx.audio_processor, "amplitude", 0)
        st.write("マイク感度")
        st.progress(min(amp, 100))

        if "is_recording" not in st.session_state:
            st.session_state.is_recording = False

        if not st.session_state.is_recording:
            if st.button("🔴 録音開始"):
                webrtc_ctx.audio_processor.frames = []
                webrtc_ctx.audio_processor.is_recording = True
                st.session_state.is_recording = True
                st.rerun()
        else:
            if st.button("⏹️ 停止 & 保存"):
                webrtc_ctx.audio_processor.is_recording = False
                st.session_state.is_recording = False
                frames = webrtc_ctx.audio_processor.frames
                if frames:
                    buf = io.BytesIO()
                    with wave.open(buf, "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(48000)
                        wf.writeframes(b"".join(frames))
                    st.session_state.last_audio = buf.getvalue()
                st.rerun()
            st.warning("録音中...")
    else:
        st.write("Startを押して入室")

# --- 6. 録音再生 & 参加者表示 ---
if "last_audio" in st.session_state and st.session_state.last_audio:
    st.audio(st.session_state.last_audio, format="audio/wav")

st.divider()
if webrtc_ctx.state.playing:
    st.success(f"● {user_name} さんが Room {room_id} で通話中")
else:
    st.info("部屋に参加していません")
