import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
from streamlit_autorefresh import st_autorefresh
import time
import io
import wave

# --- 1. ページ構成と自動更新 (CPU負荷軽減のため1秒間隔) ---
st.set_page_config(page_title="Voice Room Pro", layout="wide", page_icon="🎙️")
st_autorefresh(interval=1000, key="vitals")

# CSSデザイン
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
    }
    .room-label { font-size: 24px; font-weight: bold; color: #1f77b4; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. オーディオプロセッサ (ノイズ＆負荷対策済み) ---
class LiteAudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0
        self.is_recording = False
        self.frames = []

    def recv(self, frame):
        # 変換を最小限にして処理落ち(ボツボツ音)を防止
        raw_data = frame.to_ndarray()
        
        if self.is_recording:
            self.frames.append(raw_data.tobytes())

        if raw_data.size > 0:
            # 50個に1個のサンプリングで計算負荷を大幅削減
            max_val = np.abs(raw_data[::50]).max()
            
            # 【ガヤガヤ音対策】一定以下の小さな音は無視（しきい値500）
            if max_val < 500:
                self.amplitude = 0
            else:
                normalized = int((max_val / 15000) * 100)
                self.amplitude = max(0, min(normalized, 100))
            
        return frame

# --- 3. セッション管理 (名前の固定化) ---
if "fixed_user_name" not in st.session_state:
    st.session_state.fixed_user_name = "User_" + str(int(time.time()) % 100)
if "has_announced" not in st.session_state:
    st.session_state.has_announced = None

# --- 4. サイドバー設定 ---
with st.sidebar:
    st.header("👤 Settings")
    u_name = st.text_input("表示名", value=st.session_state.fixed_user_name)
    st.session_state.fixed_user_name = u_name
    room_id = st.text_input("ルームID", value="101")
    st.divider()
    st.caption("イヤホンの使用を推奨します")

# --- 5. メインエリア ＆ WebRTC設定 ---
st.title("🎙️ Streamlit Voice Room")
st.markdown(f'<p class="room-label">🏠 Room: {room_id}</p>', unsafe_allow_html=True)

# 【ガヤガヤ音対策】ブラウザのノイズ抑制機能をフルパワーで設定
webrtc_ctx = webrtc_streamer(
    key=f"room-{room_id}-v13", 
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=LiteAudioProcessor,
    media_stream_constraints={
        "audio": {
            "echoCancellation": True,     # エコー除去
            "noiseSuppression": True,    # ノイズ抑制
            "autoGainControl": True,     # 音量自動調整
            "highpassFilter": True,      # 低音カット
            "typingNoiseDetection": True # 打鍵音カット
        },
        "video": False,
    },
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    async_processing=True,
)

# --- 6. 通知 ＆ ステータス表示 ---
if webrtc_ctx.state.playing:
    # 入室通知 (初回のみ)
    if st.session_state.has_announced != room_id:
        st.toast(f"🎉 {st.session_state.fixed_user_name} さんが Room {room_id} に入室しました！")
        st.session_state.has_announced = room_id

    col1,
