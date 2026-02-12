# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np

st.set_page_config(page_title="Stable Voice Room", layout="wide")

# --- 1. プロセッサ (送信レベル測定) ---
class LiteAudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0
    def recv(self, frame):
        raw_data = frame.to_ndarray().astype(np.int16)
        if raw_data.size > 0:
            if raw_data.ndim == 2: raw_data = raw_data.mean(axis=1)
            self.amplitude = int((np.abs(raw_data[::50]).max() / 15000) * 100)
        return frame

# --- 2. メインUI ---
st.title("Streamlit Voice Room (Final)")

# ICEサーバーの設定（接続エラー対策）
RTC_CONFIGURATION = {
    "iceServers": [
        {"urls": ["stun:stun.l.google.com:19302", "stun:stun1.l.google.com:19302", "stun:stun2.l.google.com:19302"]}
    ]
}

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Voice Connection")
    # モードを SENDRECV に戻し、通信エラーを回避
    webrtc_ctx = webrtc_streamer(
        key="unified-voice-room",
        mode=WebRtcMode.SENDRECV,
        audio_processor_factory=LiteAudioProcessor,
        # ここが重要：自分のプレビュー音声をミュート状態で開始するようブラウザに示唆
        media_stream_constraints={
            "audio": {
                "echoCancellation": True,
                "noiseSuppression": True,
                "autoGainControl": True,
            },
            "video": False,
        },
        rtc_configuration=RTC_CONFIGURATION,
        async_processing=True,
    )

    if webrtc_ctx.state.playing:
        st.success("✅ Connected")
        if webrtc_ctx.audio_processor:
            st.write("Mic Level")
            st.progress(min(webrtc_ctx.audio_processor.amplitude, 100))
    
    # 接続エラー時のアドバイス
    elif webrtc_ctx.state.signalling_state == "stable":
        st.warning("Connecting... ネットワークを確認してください。")

with col2:
    st.subheader("Controls")
    st.info("自分の声が聞こえるのを止めるための『最後の手動操作』です。")
    
    # JavaScriptによる強制的な「後出し」ではない、ブラウザ制御のヒント
    st.markdown("""
        ### エコーを確実に消す手順
        1. **上の 'Start' ボタンを押す**
        2. **ブラウザのタブを右クリック**
        3. **『サイトをミュート』を選択**
        
        **これで、あなたの声は相手に届きますが、このページからの音（自分の声）は一切聞こえなくなります。**
    """)

# --- 3. チャットエリア ---
st.divider()
if "messages" not in st.session_state: st.session_state.messages = []
prompt = st.chat_input("Message...")
if prompt:
    st.session_state.messages.append(prompt)
    st.rerun()
for m in reversed(st.session_state.messages):
    st.write(f"💬 {m}")
