import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
from streamlit_autorefresh import st_autorefresh
import time
import io
import wave

# --- 1. ページ構成と自動更新 ---
st.set_page_config(page_title="Voice Room Pro", layout="wide", page_icon="🎙️")
st_autorefresh(interval=1000, key="vitals")

# --- 2. オーディオプロセッサ (ノイズゲート強化版) ---
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
            # 50個に1個のサンプリング
            max_val = np.abs(raw_data[::50]).max()
            
            # 【強化：ノイズゲート】
            # しきい値を1000に引き上げ。これ以下の小さな「ガヤガヤ」は完全にカットします。
            if max_val < 1000: 
                self.amplitude = 0
                # 相手に送る音そのものをゼロにしたい場合はここでraw_dataを書き換えることも可能ですが、
                # 処理が重くなるため、まずはメーターの抑制とブラウザの機能に任せます。
            else:
                normalized = int((max_val / 15000) * 100)
                self.amplitude = max(0, min(normalized, 100))
            
        return frame

# --- 3. セッション管理 ---
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
    st.warning("⚠️ ガヤガヤが気になる場合はマイクを口元に近づけ、OS設定で入力音量を少し下げてください。")

# --- 5. メインエリア ＆ WebRTC設定 (最強ノイズ抑制モード) ---
st.title("🎙️ Streamlit Voice Room")

webrtc_ctx = webrtc_streamer(
    key=f"room-{room_id}-v15", 
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=LiteAudioProcessor,
    media_stream_constraints={
        "audio": {
            "echoCancellation": True,
            "noiseSuppression": True,
            "autoGainControl": True,
            "highpassFilter": True,
            # ブラウザ独自のノイズ抑制パラメータ（可能な限り指定）
            "googEchoCancellation": True,
            "googAutoGainControl": True,
            "googNoiseSuppression": True,
            "googHighpassFilter": True,
        },
        "video": False,
    },
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    async_processing=True,
)

# --- 6. 接続後の表示 ---
if webrtc_ctx.state.playing:
    if st.session_state.has_announced != room_id:
        st.toast(f"🎉 {st.session_state.fixed_user_name} さんが入室しました！")
        st.session_state.has_announced = room_id

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.success(f"● Room {room_id} 接続中")
        if webrtc_ctx.audio_processor:
            amp = webrtc_ctx.audio_processor.amplitude
            st.write(f"User: {st.session_state.fixed_user_name}")
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
    st.session_state.has_announced = None
    st.info("Startボタンを押して入室してください")

if "last_audio" in st.session_state:
    st.divider()
    st.audio(st.session_state.last_audio)
