import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
from streamlit_autorefresh import st_autorefresh
import time
import io
import wave

# --- 1. ページ構成と自動更新 ---
st.set_page_config(page_title="Voice Room Pro", layout="wide", page_icon="🎙️")
st_autorefresh(interval=1000, key="vitals") # 通知を確認しやすくするため1秒に調整

# --- 2. ユーザー名の固定化 ---
if "fixed_user_name" not in st.session_state:
    st.session_state.fixed_user_name = "User_" + str(int(time.time()) % 100)

# --- 3. 【新機能】入室管理システム ---
# サーバー側で全ユーザー共通の「入室中リスト」をシミュレート
if "room_members" not in st.session_state:
    st.session_state.room_members = {}

# --- 4. サイドバー設定 ---
with st.sidebar:
    st.header("👤 ユーザー設定")
    user_name = st.text_input("表示名", value=st.session_state.fixed_user_name)
    st.session_state.fixed_user_name = user_name
    room_id = st.text_input("ルームID", value="101")
    st.divider()
    st.caption("※同じルームIDの人とだけ会話できます。")

# --- 5. オーディオプロセッサ ---
class ProAudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0
        self.is_recording = False
        self.frames = []
        self.count = 0 

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

# --- 6. メインエリア ---
st.title("🎙️ Streamlit Voice Room")

# 入室通知の処理
if "last_notified_room" not in st.session_state:
    st.session_state.last_notified_room = None

# 接続状態をチェックして通知を出す
webrtc_ctx = webrtc_streamer(
    key=f"room-{room_id}-chat", 
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=ProAudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    async_processing=True,
)

# ログイン成功時の通知処理
if webrtc_ctx.state.playing:
    # 以前と違う部屋に入った、または初めて入った時だけ通知
    if st.session_state.last_notified_room != room_id:
        st.toast(f"🎉 {user_name} さんが Room {room_id} に入室しました！")
        st.session_state.last_notified_room = room_id
        # ここで本来はDB等に「入室中」を記録すると他者にも見えます
else:
    st.session_state.last_notified_room = None

st.divider()

col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown(f"### 🏠 Room: {room_id}")
    if webrtc_ctx.state.playing:
        st.success(f"接続中: {user_name}")
    else:
        st.info("Startを押して入室してください")

with col_right:
    st.subheader("ステータス")
    if webrtc_ctx.state.playing and webrtc_ctx.audio_processor:
        amp = getattr(webrtc_ctx.audio_processor, "amplitude", 0)
        st.write("マイク感度")
        st.progress(min(amp, 100))
        
        # 録音機能 (前回のコードを維持)
        if st.button("🔴 録音開始" if not getattr(st.session_state, 'is_recording', False) else "⏹️ 停止して保存"):
            if not getattr(st.session_state, 'is_recording', False):
                webrtc_ctx.audio_processor.frames = []
                webrtc_ctx.audio_processor.is_recording = True
                st.session_state.is_recording = True
            else:
                webrtc_ctx.audio_processor.is_recording = False
                st.session_state.is_recording = False
                # 保存処理
                frames = webrtc_ctx.audio_processor.frames
                if frames:
                    buf = io.BytesIO()
                    with wave.open(buf, "wb") as wf:
                        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(48000)
                        wf.writeframes(b"".join(frames))
                    st.session_state.last_audio = buf.getvalue()
            st.rerun()

if "last_audio" in st.session_state:
    st.audio(st.session_state.last_audio)
