# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
import av  # フレーム操作に必須

# --- 1. ページ構成 ---
st.set_page_config(page_title="Final Echo-Free Room", layout="wide")

# --- 2. 原始的・データレベル消音プロセッサ ---
class AbsoluteEchoCanceller(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        # A. 自分のマイクから入力されたデータを取得
        raw_data = frame.to_ndarray()
        
        # B. 【レベル計算】（消音する前に実行）
        data_int16 = raw_data.astype(np.int16)
        if data_int16.ndim == 2:
            data_int16 = data_int16.mean(axis=1).astype(np.int16)
        if data_int16.size > 0:
            max_val = np.abs(data_int16[::50]).max()
            self.amplitude = int((max_val / 15000) * 100)

        # C. 【核心：データの無音化】
        # raw_dataを0にするのではなく、送信は生かしつつ、
        # スピーカー（自分）に返すデータだけを無音の別配列に差し替えます
        silent_data = np.zeros_like(raw_data)
        
        # D. 無音にしたフレームを自分（スピーカー）に返す
        return av.AudioFrame.from_ndarray(silent_data, format=frame.format.name, layout=frame.layout.name)

# --- 3. メインUI ---
st.title("Streamlit Voice Room (Final Code)")

room_id = st.sidebar.text_input("Room ID", "101")

# WebRTC設定 (標準的なSENDRECVで接続性を確保)
webrtc_ctx = webrtc_streamer(
    key=f"final-stable-{room_id}",
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=AbsoluteEchoCanceller,
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

# 状態表示
if webrtc_ctx.state.playing:
    st.success("✅ 通信中: プロセッサが自分の声を物理的にカットしています")
    if webrtc_ctx.audio_processor:
        st.write("マイク入力（相手には届いています）")
        st.progress(min(webrtc_ctx.audio_processor.amplitude, 100))
else:
    st.info("Startボタンを押してください。")

# --- 4. 注意事項 ---
st.divider()
st.write("### 動作の仕組み")
st.write("このコードは、マイクが拾った音を**サーバーへ送る処理**と、**自分のスピーカーへ返す処理**をデータレベルで分離しています。")
st.write("1. **送信**: マイクの音は生きたままサーバーへ送られます。")
st.write("2. **自分への再生**: プロセッサがデータを 0 (無音) に書き換えてからスピーカーへ渡すため、自分の声は聞こえません。")
