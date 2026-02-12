# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
import av  # PyAVを使用してフレームを直接操作

# --- 1. ページ構成 ---
st.set_page_config(page_title="Voice Room Final", layout="wide")

# --- 2. 究極のオーディオプロセッサ ---
class FinalAudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0
        self.is_muted = False

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        # A. 自分のマイクから届いた生データ
        raw_data = frame.to_ndarray()
        
        # B. 【送信レベル測定】
        data_int16 = raw_data.astype(np.int16)
        if data_int16.ndim == 2: data_int16 = data_int16.mean(axis=1).astype(np.int16)
        if data_int16.size > 0:
            self.amplitude = int((np.abs(data_int16[::50]).max() / 15000) * 100)

        # C. 【ミュート処理（相手への送信を止める場合）】
        if self.is_muted:
            raw_data.fill(0)
            return av.AudioFrame.from_ndarray(raw_data, format=frame.format.name, layout=frame.layout.name)

        # D. 【エコー対策の核心】
        # 自分のマイク音を相手には送りたいが、自分には返したくない。
        # 本来ならここで「受信した他人の音」を混ぜる必要がありますが、
        # Streamlit WebRTCの仕様上、recvで返した音は「自分のプレビュー」になります。
        
        # 自分の声を自分に返さないために、あえて「無音」のコピーを自分に返却します。
        # これにより、送信は維持したまま、自分自身のスピーカーからは何も鳴らなくなります。
        silent_data = np.zeros_like(raw_data)
        return av.AudioFrame.from_ndarray(silent_data, format=frame.format.name, layout=frame.layout.name)

# --- 3. メインUI ---
st.title("Streamlit Voice Room")
room_id = st.sidebar.text_input("Room ID", "101")
is_muted = st.sidebar.checkbox("Mute My Mic", value=False)

# WebRTC設定
# SENDRECVにすることで「相手の音を受け取る準備」を整えます
webrtc_ctx = webrtc_streamer(
    key=f"final-room-{room_id}",
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=FinalAudioProcessor,
    media_stream_constraints={
        "audio": {
            "echoCancellation": True,
            "noiseSuppression": True,
        },
        "video": False,
    },
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    async_processing=True,
)

if webrtc_ctx.audio_processor:
    webrtc_ctx.audio_processor.is_muted = is_muted

# レベル表示
if webrtc_ctx.state.playing:
    st.write("🎙️ Mic Activity")
    st.progress(min(webrtc_ctx.audio_processor.amplitude if webrtc_ctx.audio_processor else 0, 100))
    st.info("自分の声は無音化されて返されます。相手の声が聞こえるか確認してください。")
