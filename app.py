import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np

st.title("🎤 復活！音量メーター付きチャット")

# 音声解析クラス（ここは以前と同じですが、念のため再掲）
class AudioAmplitudeProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0

    def recv(self, frame):
        audio_data = frame.to_ndarray()
        if audio_data.size > 0:
            raw_amplitude = np.sqrt(np.mean(audio_data**2))
            # 感度調整（300の部分を小さくするとバーが動きやすくなります）
            self.amplitude = min(int(raw_amplitude / 300 * 100), 100)
        return frame

# 起動部分
webrtc_ctx = webrtc_streamer(
    key="stable-volume-meter",
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=AudioAmplitudeProcessor,
    media_stream_constraints={"audio": True, "video": False},
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    },
    async_processing=True,
)

# --- 安全な状態チェックと表示 ---
if webrtc_ctx is not None and hasattr(webrtc_ctx, "state") and webrtc_ctx.state is not None:
    if getattr(webrtc_ctx.state, "playing", False):
        st.success("✅ 接続中")
        
        # 音量プロセッサに安全にアクセス
        if hasattr(webrtc_ctx, "audio_processor") and webrtc_ctx.audio_processor is not None:
            amp = getattr(webrtc_ctx.audio_processor, "amplitude", 0)
            
            st.write(f"あなたの声の大きさ: {amp}")
            st.progress(amp)
            
            if amp > 30:
                st.markdown("### 📢 Speaking...")
            
            # メーターを動かし続けるための「更新ボタン」
            st.button("メーターをリフレッシュ")
    else:
        st.info("Startを押してください")
