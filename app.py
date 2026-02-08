import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np

st.title("🎤 音量メーター付きボイスチャット")

class AudioAmplitudeProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0

    def recv(self, frame):
        # 音声データの取得
        audio_data = frame.to_ndarray()
        if audio_data.size > 0:
            # RMS（音量）の計算
            raw_amplitude = np.sqrt(np.mean(audio_data**2))
            # 0-100に変換（調整用：300を大きくすると感度が下がります）
            self.amplitude = min(int(raw_amplitude / 300 * 100), 100)
        return frame

# 1. ページがリロードされた際のエラーを防ぐため、一意のキーにタイムスタンプ等を混ぜない
# 2. webrtc_streamerを変数に代入
webrtc_ctx = webrtc_streamer(
    key="volume-meter-v2", # キーを変更して一度リセット
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=AudioAmplitudeProcessor,
    media_stream_constraints={"audio": True, "video": False},
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    },
    async_processing=True, # 非同期処理を有効化
)

# プレースホルダーを先に作成
status_area = st.empty()
meter_area = st.empty()

if webrtc_ctx.state.playing:
    if webrtc_ctx.audio_processor:
        # 音量を取得して表示
        amp = webrtc_ctx.audio_processor.amplitude
        meter_area.progress(amp)
        status_area.success(f"接続中 - 現在の音量: {amp}")
        
        # 画面を定期的に更新させるための仕組み
        st.button("メーターを更新") 
        # ※本来は自動ループが理想ですが、Streamlitの制約上、
        # 誰かが音声を送っている間はprocessorの値が更新され続けます。
else:
    status_area.info("Startボタンを押してください")
