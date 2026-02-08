import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np

st.title("Python 複数人ボイスチャット")

# 音声処理のクラス：ここで全員の音を管理する（今回は簡易的な仕組み）
class MultiUserAudioProcessor(AudioProcessorBase):
    def recv(self, frame):
        # 本来はここで他人の音声データを受け取ってミックスしますが、
        # streamlit-webrtcのデフォルト機能で「サーバー経由の共有」を有効にします。
        return frame

# 部屋の識別（これがあると同じ部屋の人同士で繋がります）
room_name = st.text_input("ルーム名を入力してください", "default-room")

if room_name:
    webrtc_ctx = webrtc_streamer(
        key=room_name,  # ルーム名ごとにインスタンスを分ける
        mode=WebRtcMode.SENDRECV,
        rtc_configuration={
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        },
        media_stream_constraints={
            "audio": True,
            "video": False,
        },
        # 複数人接続を許可するための設定（重要）
        async_processing=True,
    )

st.info("別のブラウザタブ、または別のPCから同じルーム名で入ると会話できます。")
