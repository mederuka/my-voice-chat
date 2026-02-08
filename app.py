import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
from streamlit_autorefresh import st_autorefresh
import time
import io
import wave

# --- 1. ページ構成と自動更新 (0.5秒) ---
st.set_page_config(page_title="Voice Room Pro", layout="wide", page_icon="🎙️")
st_autorefresh(interval=500, key="vitals")

# モダンなUIデザイン
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stProgress > div > div > div > div { background-color: #28a745; }
    .user-tag {
        padding: 5px 15px;
        border-radius: 15px;
        background-color: #e1e4e8;
        font-weight: bold;
        color: #2c3e50;
    }
    .room-label {
        font-size: 24px;
        font-weight: bold;
        color: #1f77b4;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. オーディオプロセッサ (軽量版) ---
class ProAudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0
        self.is_recording = False
        self.frames = []
        self.count = 0 # 内部処理用

    def recv(self, frame):
        try:
            audio_data = frame.to_ndarray()
            self.count += 1
            if audio_data.size > 0:
                max_val = np.abs(audio_data[::10]).max()
                self.amplitude = int((max_val / 15000) * 100)
            if self.is_recording:
                self.frames.append(audio_data.tobytes())
        except Exception:
            pass
        return frame

# --- 3. サイドバー設定 ---
with st.sidebar:
    st.header("👤 ユーザー設定")
    user_name = st.text_input("表示名", value="User_" + str(int(time.time()) % 100))
    room_id = st.text_input("ルームID", value="101")
    st.divider()
    st.caption("※同じルームIDの人とだけ会話できます。")

# --- 4. メインコンテンツ ---
st.title("🎙️ Streamlit Voice Room")

# 現在の場所を分かりやすく表示
st.markdown(f'<p class="room-label">🏠 Room: {room_id}</p>', unsafe_allow_html=True)

col_left, col_right = st.columns([2, 1])

with col_left:
    # 部屋ごとに通信を分離するためのキー
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

# --- 5. ステータスと録音 ---
with col_right:
    st.subheader("ユーザー状態")
    
    if webrtc_ctx.state.playing and webrtc_ctx.audio_processor:
        # 名前を固定表示（カウントアップしない）
        st.markdown(f'<span class="user-tag">● {user_name}</span>', unsafe_allow_html=True)
        
        # 音量メーター
        amp = getattr(webrtc_ctx.audio_processor, "amplitude", 0)
        st.progress(min(amp, 100))
        
        # 通信の安定度をひっそり表示
        count = getattr(webrtc_ctx.audio_processor, "count", 0)
        st.caption(f"Status: 通信中 (Sync: {count})")

        st.divider()
        
        # 録音機能
        if "is_recording" not in st.session_state:
            st.session_state.is_recording = False

        if not st.session_state.is_recording:
            if st.button("🔴 録音開始"):
                webrtc_ctx.audio_processor.frames = []
                webrtc_ctx.audio_processor.is_recording = True
                st.session_state.is_recording = True
                st.rerun()
        else:
            if st.button("⏹️ 録音を停止して保存"):
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
            st.warning("現在録音中です...")
    else:
        st.info("Startを押して入室してください")

# --- 6. 録音再生エリア ---
if "last_audio" in st.session_state and st.session_state.last_audio:
    st.divider()
    st.subheader("📥 録音済み音声の再生")
    st.audio(st.session_state.last_audio, format="audio/wav")
    st.download_button("WAVファイルをダウンロード", st.session_state.last_audio, file_name="rec.wav")
