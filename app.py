import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np

# 音声解析クラス
class AudioAmplitudeProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0
        self.count = 0  # 処理回数カウント（デバッグ用）

    def recv(self, frame):
        try:
            audio_data = frame.to_ndarray().flatten()
            self.count += 1 # 1パケット受信するごとにカウントアップ
            
            if audio_data.size > 0:
                # 振幅の最大値を取得（最も計算が軽く、反応が良い）
                # 32768は16bit音声の最大値。これで割って100を掛ける
                max_val = np.max(np.abs(audio_data))
                self.amplitude = int((max_val / 32768) * 100)
        except Exception as e:
            pass
            
        return frame

st.title("音量メーター動作確認")

webrtc_ctx = webrtc_streamer(
    key="meter-test",
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=AudioAmplitudeProcessor,
    media_stream_constraints={"audio": True, "video": False},
)

# 表示ループ
if webrtc_ctx.audio_processor:
    # プレースホルダーで書き換え
    placeholder = st.empty()
    
    # 処理回数が止まっていなければ、Python側は動いています
    count = webrtc_ctx.audio_processor.count
    amp = webrtc_ctx.audio_processor.amplitude
    
    with placeholder.container():
        st.write(f"パケット受信数: {count}") # ここがガシガシ増えていればOK
        st.write(f"現在の数値: {amp}")
        st.progress(min(amp * 2, 100)) # 反応を良くするために2倍にして表示
    
    # 【重要】Streamlitを強制再描画させるためのボタン
    if st.button("数値を更新"):
        st.rerun()
else:
    st.info("Startボタンを押して、マイクを許可してください。")
