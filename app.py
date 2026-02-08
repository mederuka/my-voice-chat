
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np

st.title("🎤 音量メーター付きボイスチャット")

# 音声を解析するクラス
class AudioAmplitudeProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0

    def recv(self, frame):
        # 音声データを数値配列（numpy）に変換
        audio_data = frame.to_ndarray()
        
        # 音量の計算 (RMS: 二乗平均平方根)
        if audio_data.size > 0:
            # 振幅の平均を計算し、扱いやすい数値に変換
            raw_amplitude = np.sqrt(np.mean(audio_data**2))
            # 0〜100の範囲にスケーリング（マイク感度に合わせて調整）
            self.amplitude = min(int(raw_amplitude / 500 * 100), 100)
        
        return frame

# UI部分
col1, col2 = st.columns([2, 1])

with col1:
    webrtc_ctx = webrtc_streamer(
        key="volume-check",
        mode=WebRtcMode.SENDRECV,
        audio_processor_factory=AudioAmplitudeProcessor, # ここで解析クラスを指定
        media_stream_constraints={"audio": True, "video": False},
        rtc_configuration={
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        }
    )

with col2:
    st.subheader("あなたの声の大きさ")
    # リアルタイムで音量バーを更新
    if webrtc_ctx.audio_processor:
        # プレースホルダーを使ってバーを動かす
        bar_placeholder = st.empty()
        # 簡易的なループで値を表示（Streamlitの再描画を利用）
        amp = webrtc_ctx.audio_processor.amplitude
        bar_placeholder.progress(amp)
        if amp > 50:
            st.write("📢 しゃべっています")
        elif amp > 5:
            st.write("💡 音声を検知中")
    else:
        st.write("Startを押してください")
