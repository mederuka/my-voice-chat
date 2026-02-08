import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np

st.title("🎤 安定版：音量メーター")

class AudioAmplitudeProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0

    def recv(self, frame):
        try:
            # 1. データのコピーを作成して処理（元のデータを壊さない）
            audio_data = frame.to_ndarray().flatten().astype(np.float32)
            
            if audio_data.size > 0:
                # 2. 計算を簡略化（絶対値の平均にする。sqrtより軽く、エラーが出にくい）
                abs_max = np.max(np.abs(audio_data))
                
                # 3. 異常な数値（大きな音）が入っても0-100に収まるように制限
                # マイクの感度に合わせて 1000 の部分を調整してください
                normalized_vol = int((abs_max / 1000) * 100)
                self.amplitude = max(0, min(normalized_vol, 100))
        except Exception:
            # 大きな音で計算エラーが起きても、処理を止めずにスルーする
            self.amplitude = 0
            
        return frame

webrtc_ctx = webrtc_streamer(
    key="stable-v4",
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=AudioAmplitudeProcessor,
    media_stream_constraints={
        "audio": {
            # 4. ブラウザ側の自動調整機能をあえて指定（音切れを防ぐ）
            "echoCancellation": True,
            "noiseSuppression": True,
            "autoGainControl": True,
        },
        "video": False,
    },
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    },
    async_processing=True,
)

# 表示部分は前回の「安全な書き方」を維持
if webrtc_ctx and hasattr(webrtc_ctx, "state") and getattr(webrtc_ctx.state, "playing", False):
    if hasattr(webrtc_ctx, "audio_processor") and webrtc_ctx.audio_processor:
        amp = getattr(webrtc_ctx.audio_processor, "amplitude", 0)
        st.progress(amp)
        if amp > 80:
            st.warning("⚠️ 音が大きすぎます！")
    st.button("更新")
