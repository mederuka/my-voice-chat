import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
from streamlit_autorefresh import st_autorefresh
import time
import io
import wave

# --- 1. ページ設定と自動更新 ---
st.set_page_config(page_title="Streamlit Voice Pro", layout="wide", page_icon="🎙️")
st_autorefresh(interval=500, key="vitals")

# モダンなデザインのためのCSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; }
    .user-card {
        padding: 15px;
        border-radius: 10px;
        background-color: white;
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 高機能オーディオプロセッサ ---
class ProAudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0
        self.is_recording = False
        self.frames = []

    def recv(self, frame):
        try:
            audio_data = frame.to_ndarray()
            
            # 軽量音量計算
            if audio_data.size > 0:
                max_val = np.abs(audio_data[::10]).max()
                self.amplitude = int((max_val / 15000) * 100)
            
            # 録音処理
            if self.is_recording:
                # 録音用に生データを保存
                self.frames.append(audio_data.tobytes())
                
        except Exception:
            pass
        return frame

# --- 3. サイドバー：名前設定 ---
with st.sidebar:
    st.header("👤 Profile")
    user_name = st.text_input("あなたの名前", value="Guest_User")
    st.divider()
    st.write("### 使い方")
    st.caption("1. Startでマイクを起動")
    st.caption("2. 名前を入力して入室")
    st.caption("3. 録音ボタンで音声をキャプチャ")

# --- 4. メインエリアのレイアウト ---
st.title("🎙️ Pro Voice Room")

col_main, col_status = st.columns([3, 1])

with col_main:
    # デザインされたユーザー表示
    st.markdown(f"""
        <div class="user-card">
            <h3>ようこそ {user_name} さん</h3>
            <p>ステータス: 🟢 オンライン</p>
        </div>
    """, unsafe_allow_html=True)

    webrtc_ctx = webrtc_streamer(
        key="pro-voice-v10",
        mode=WebRtcMode.SENDRECV,
        audio_processor_factory=ProAudioProcessor,
        media_stream_constraints={"audio": True, "video": False},
        rtc_configuration={
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        },
        async_processing=True,
    )

# --- 5. 録音とステータス制御 ---
with col_status:
    st.subheader("Control")
    
    if webrtc_ctx.state.playing and webrtc_ctx.audio_processor:
        # 音量メーター
        amp = getattr(webrtc_ctx.audio_processor, "amplitude", 0)
        st.write("マイク感度")
        st.progress(min(amp, 100))

        # 録音ボタンの制御
        if "is_recording" not in st.session_state:
            st.session_state.is_recording = False

        if not st.session_state.is_recording:
            if st.button("🔴 録音開始"):
                webrtc_ctx.audio_processor.frames = [] # バッファをクリア
                webrtc_ctx.audio_processor.is_recording = True
                st.session_state.is_recording = True
                st.rerun()
        else:
            if st.button("⏹️ 停止 & 生成"):
                webrtc_ctx.audio_processor.is_recording = False
                st.session_state.is_recording = False
                
                # 録音データをWAV形式に変換
                frames = webrtc_ctx.audio_processor.frames
                if frames:
                    buf = io.BytesIO()
                    with wave.open(buf, "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2) # 16-bit
                        wf.setframerate(48000) # 標準的なレート
                        wf.writeframes(b"".join(frames))
                    
                    st.session_state.last_audio = buf.getvalue()
                st.rerun()
            st.warning("録音中...")

    else:
        st.write("準備完了")

# --- 6. 録音した音声の再生・ダウンロード ---
if "last_audio" in st.session_state and st.session_state.last_audio:
    st.divider()
    st.subheader("📥 録音済み音声")
    st.audio(st.session_state.last_audio, format="audio/wav")
    st.download_button(
        label="WAVファイルをダウンロード",
        data=st.session_state.last_audio,
        file_name=f"record_{int(time.time())}.wav",
        mime="audio/wav"
    )

# --- 7. 参加者リスト ---
st.divider()
st.subheader("👥 参加中のメンバー")
if webrtc_ctx.state.playing:
    st.info(f"● {user_name} がマイクを使用中")
else:
    st.write("現在、アクティブなユーザーはいません。")
