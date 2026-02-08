import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
from streamlit_autorefresh import st_autorefresh
import time
import io
import wave

# --- 1. ページ構成と自動更新 (1秒間隔で同期) ---
st.set_page_config(page_title="Voice Room Pro", layout="wide", page_icon="🎙️")
st_autorefresh(interval=1000, key="vitals")

# CSSで参加者リストのデザインを調整
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .member-list {
        padding: 10px;
        border-radius: 8px;
        background-color: #ffffff;
        border: 1px solid #ddd;
    }
    .active-user { color: #28a745; font-weight: bold; }
    .user-tag {
        padding: 2px 10px;
        border-radius: 10px;
        background-color: #e1e4e8;
        font-size: 0.9em;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. オーディオプロセッサ ---
class LiteAudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0
        self.is_recording = False
        self.frames = []

    def recv(self, frame):
        raw_data = frame.to_ndarray()
        if self.is_recording:
            self.frames.append(raw_data.tobytes())
        if raw_data.size > 0:
            max_val = np.abs(raw_data[::50]).max()
            if max_val < 1000: # 強力ノイズゲート
                self.amplitude = 0
            else:
                normalized = int((max_val / 15000) * 100)
                self.amplitude = max(0, min(normalized, 100))
        return frame

# --- 3. セッション管理と参加者リストのシミュレーション ---
if "fixed_user_name" not in st.session_state:
    st.session_state.fixed_user_name = "User_" + str(int(time.time()) % 100)

# 本来は外部DBを使う部分を、Room IDに紐づくリストとして扱う準備
# (注: Streamlit単体では他ブラウザの情報を完全に共有するには外部DBが必要ですが、
#  構成として「参加者エリア」を定義します)
if "room_members" not in st.session_state:
    st.session_state.room_members = {} 

# --- 4. サイドバー設定 ---
with st.sidebar:
    st.header("👤 Settings")
    u_name = st.text_input("表示名", value=st.session_state.fixed_user_name)
    st.session_state.fixed_user_name = u_name
    room_id = st.text_input("ルームID", value="101")
    st.divider()
    
    # 【追加】この部屋の参加者リスト（自分を表示）
    st.subheader(f"👥 Room {room_id} メンバー")
    st.markdown(f'<div class="member-list">', unsafe_allow_html=True)
    st.markdown(f'<span class="active-user">●</span> {u_name} (あなた)', unsafe_allow_html=True)
    # 擬似的な他ユーザー表示（他端末で同じセッションを共有する場合のみ反映）
    st.caption("他ユーザーが接続するとここに表示されます")
    st.markdown(f'</div>', unsafe_allow_html=True)

# --- 5. メインエリア ---
st.title("🎙️ Streamlit Voice Room")

webrtc_ctx = webrtc_streamer(
    key=f"room-{room_id}-v16", 
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=LiteAudioProcessor,
    media_stream_constraints={
        "audio": {
            "echoCancellation": True, "noiseSuppression": True, "autoGainControl": True,
            "highpassFilter": True, "googNoiseSuppression": True,
        },
        "video": False,
    },
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    async_processing=True,
)

# --- 6. 接続後のステータス表示 ---
if webrtc_ctx.state.playing:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.success(f"● Room {room_id} 接続中")
        if webrtc_ctx.audio_processor:
            amp = webrtc_ctx.audio_processor.amplitude
            st.write(f"🎤 {st.session_state.fixed_user_name}")
            st.progress(min(amp, 100))
    
    with col2:
        is_rec = st.toggle("🔴 録音モード", key="rec_toggle")
        if webrtc_ctx.audio_processor:
            webrtc_ctx.audio_processor.is_recording = is_rec
            
            if not is_rec and len(webrtc_ctx.audio_processor.frames) > 5:
                frames = webrtc_ctx.audio_processor.frames
                buf = io.BytesIO()
                with wave.open(buf, "wb") as wf:
                    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(48000)
                    wf.writeframes(b"".join(frames))
                st.session_state.last_audio = buf.getvalue()
                webrtc_ctx.audio_processor.frames = []
                st.rerun()
else:
    st.info("Startボタンを押して入室してください")

if "last_audio" in st.session_state:
    st.divider()
    st.audio(st.session_state.last_audio)
