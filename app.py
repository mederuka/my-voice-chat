import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
from streamlit_autorefresh import st_autorefresh
import time
import io
import wave

# --- 1. ページ構成と自動更新 (ノイズ対策のため1秒間隔) ---
st.set_page_config(page_title="Voice Room Pro", layout="wide", page_icon="🎙️")
st_autorefresh(interval=1000, key="vitals")

# --- 2. ユーザー名の固定化 ---
if "fixed_user_name" not in st.session_state:
    st.session_state.fixed_user_name = "User_" + str(int(time.time()) % 100)

# --- 3. 音声プロセッサ (極限まで軽量化) ---
class LiteAudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0
        self.is_recording = False
        self.frames = []

    def recv(self, frame):
        # 変換を最小限にしてノイズを防ぐ
        raw_data = frame.to_ndarray()
        
        # 録音中なら即座に保存 (型変換なし)
        if self.is_recording:
            self.frames.append(raw_data.tobytes())

        # 音量計算はさらに間引く (50個に1個だけ見る)
        if raw_data.size > 0:
            max_val = np.abs(raw_data[::50]).max()
            self.amplitude = int((max_val / 15000) * 100)
            
        return frame

# --- 4. サイドバー設定 ---
with st.sidebar:
    st.header("👤 Settings")
    u_name = st.text_input("表示名", value=st.session_state.fixed_user_name)
    st.session_state.fixed_user_name = u_name
    room_id = st.text_input("ルームID", value="101")

# --- 5. メインエリア ---
st.title("🎙️ Streamlit Voice Room")

# WebRTCストリーマー
webrtc_ctx = webrtc_streamer(
    key=f"room-{room_id}-v11", # キーを更新してセッションリフレッシュ
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=LiteAudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    async_processing=True,
)

# --- 6. 通知 ＆ ステータス表示 (ノイズに影響しないよう後半に配置) ---
if webrtc_ctx.state.playing:
    # 初回接続時のみ通知
    if "has_announced" not in st.session_state or st.session_state.has_announced != room_id:
        st.toast(f"🎉 {st.session_state.fixed_user_name} さんが入室しました！")
        st.session_state.has_announced = room_id

    col1, col2 = st.columns([2, 1])
    with col1:
        st.success(f"● Room {room_id} で通話中")
        if webrtc_ctx.audio_processor:
            amp = webrtc_ctx.audio_processor.amplitude
            st.progress(min(amp, 100))
    
    with col2:
        # 録音ボタン (session_stateを直接操作してノイズ回避)
        is_rec = st.toggle("🔴 録音モード", key="rec_toggle")
        if webrtc_ctx.audio_processor:
            webrtc_ctx.audio_processor.is_recording = is_rec
            
            # 録音停止時にWAV作成
            if not is_rec and len(webrtc_ctx.audio_processor.frames) > 10:
                frames = webrtc_ctx.audio_processor.frames
                buf = io.BytesIO()
                with wave.open(buf, "wb") as wf:
                    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(48000)
                    wf.writeframes(b"".join(frames))
                st.session_state.last_audio = buf.getvalue()
                webrtc_ctx.audio_processor.frames = [] # クリア
                st.rerun()

# 録音再生
if "last_audio" in st.session_state:
    st.audio(st.session_state.last_audio)
