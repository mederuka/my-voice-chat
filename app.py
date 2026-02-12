# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np

# --- 1. ページ構成 ---
st.set_page_config(page_title="Voice Chat Stable", layout="wide")

# --- 2. 原始的・データレベル消音プロセッサ ---
class EchoFreeProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0

    def recv(self, frame):
        # A. マイク入力データを取得
        raw_data = frame.to_ndarray()
        
        # B. 音量レベルを計算 (表示用)
        data_int16 = raw_data.astype(np.int16)
        if data_int16.ndim == 2:
            data_int16 = data_int16.mean(axis=1).astype(np.int16)
        if data_int16.size > 0:
            self.amplitude = int((np.abs(data_int16[::50]).max() / 15000) * 100)

        # C. 【重要】自分に返る音だけを無音化
        # 新しい配列を作り、0で埋める。これを return することで
        # スピーカーから自分の声が出るのを防ぎます。
        silent_data = np.zeros_like(raw_data)
        
        # 新しいデータでフレームを再構築して返す
        return frame.from_ndarray(silent_data, format=frame.format.name)

# --- 3. メインUI ---
st.title("Voice Chat: Echo-Free Mode")

# エラーを避けるため、keyは固定にします
webrtc_ctx = webrtc_streamer(
    key="stable-voice-engine", 
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=EchoFreeProcessor,
    media_stream_constraints={
        "audio": {
            "echoCancellation": True,
            "noiseSuppression": True,
        },
        "video": False,
    },
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    },
    async_processing=True,
)

# 状態表示
if webrtc_ctx.state.playing:
    st.success("✅ 通信中")
    if webrtc_ctx.audio_processor:
        st.write("Mic Level (送信中)")
        st.progress(min(webrtc_ctx.audio_processor.amplitude, 100))
        st.info("プロセッサが自分の声をカットしています。相手の声だけが聞こえるはずです。")
else:
    st.info("STARTボタンを押してください。")

# --- 4. 注意事項 ---
st.divider()
st.caption("※接続エラーが出る場合は、ページをリロード（F5）してください。")
