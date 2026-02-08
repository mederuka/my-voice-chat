import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
from streamlit_autorefresh import st_autorefresh

# --- 1. 画面の自動更新設定 (0.1秒ごとに再描画) ---
# これにより、ボタンを押さなくてもメーターが動きます
st_autorefresh(interval=100, key="volumemonitor")

st.title("🎤 リアルタイム・ボイスチャット")
st.caption("Python 3.13 互換 & 安定動作モード")

# --- 2. 音声解析クラス (大きな音でも落ちない設計) ---
class AudioAmplitudeProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0
        self.count = 0

    def recv(self, frame):
        try:
            # データの取得と軽量化
            audio_data = frame.to_ndarray().flatten()
            self.count += 1
            
            if audio_data.size > 0:
                # 振幅の最大値を計測 (計算負荷を最小に)
                max_val = np.max(np.abs(audio_data))
                
                # 感度調整：32768は標準ですが、反応が鈍い場合は5000等に下げてください
                # int型に変換してエラーを防ぐ
                normalized = int((max_val / 15000) * 100)
                self.amplitude = max(0, min(normalized, 100))
        except Exception:
            self.amplitude = 0
        return frame

# --- 3. WebRTCストリーマーの設定 ---
webrtc_ctx = webrtc_streamer(
    key="stable-voice-v5",
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=AudioAmplitudeProcessor,
    media_stream_constraints={
        "audio": {
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

# --- 4. メーターと状態の表示 (安全な属性チェック) ---
st.divider()
col1, col2 = st.columns(2)

# 安全に状態を取得するためのガード
is_playing = False
if webrtc_ctx and hasattr(webrtc_ctx, "state") and webrtc_ctx.state is not None:
    is_playing = getattr(webrtc_ctx.state, "playing", False)

if is_playing:
    with col1:
        st.success("✅ 通信中")
        if hasattr(webrtc_ctx, "audio_processor") and webrtc_ctx.audio_processor:
            amp = getattr(webrtc_ctx.audio_processor, "amplitude", 0)
            count = getattr(webrtc_ctx.audio_processor, "count", 0)
            
            # メーターの表示
            st.metric("受信パケット数", count)
            st.write("あなたの声の大きさ:")
            st.progress(amp)
            
            if amp > 80:
                st.warning("⚠️ 音が大きすぎます")
    
    with col2:
        st.info("ヒント")
        st.write("別の端末で同じURLを開くと会話できます。")
        st.write("音が聞こえない場合は、一度画面をクリックしてください。")
else:
    st.info("下の『Start』ボタンを押して開始してください。")
