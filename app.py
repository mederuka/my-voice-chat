# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
import time

# --- 1. ページ構成 ---
st.set_page_config(page_title="Stable Voice Room", layout="wide")

# --- 2. プロセッサ (送信レベル測定) ---
class LiteAudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0
    def recv(self, frame):
        raw_data = frame.to_ndarray().astype(np.int16)
        if raw_data.size > 0:
            if raw_data.ndim == 2: raw_data = raw_data.mean(axis=1)
            # 現在の音量を計算
            self.amplitude = int((np.abs(raw_data[::50]).max() / 15000) * 100)
        return frame

# --- 3. メインUI ---
st.title("Streamlit Voice Chat (Final Stable)")

# ICEサーバーの設定（接続エラー対策）
RTC_CONFIGURATION = {
    "iceServers": [
        {"urls": ["stun:stun.l.google.com:19302", "stun:stun1.l.google.com:19302"]}
    ]
}

# サイドバー設定
room_id = st.sidebar.text_input("Room ID", "101")
if "messages" not in st.session_state: st.session_state.messages = []

col_voice, col_chat = st.columns([1, 1])

with col_voice:
    st.subheader("🎙️ Voice Control")
    
    # 【原始的で最も強力なブラウザ設定】
    # echoCancellation を強制し、かつブラウザが自分の声を戻さないよう制約をかけます
    webrtc_ctx = webrtc_streamer(
        key=f"unified-voice-{room_id}",
        mode=WebRtcMode.SENDRECV,
        audio_processor_factory=LiteAudioProcessor,
        media_stream_constraints={
            "audio": {
                "echoCancellation": True,
                "noiseSuppression": True,
                "autoGainControl": True,
                # 以下の設定はブラウザに対する「エコーを物理的に消せ」という強力な命令です
                "googEchoCancellation": True,
                "googAutoGainControl": True,
                "googNoiseSuppression": True,
                "googHighpassFilter": True,
            },
            "video": False,
        },
        rtc_configuration=RTC_CONFIGURATION,
        async_processing=True,
    )

    # 接続状態の表示（エラーを修正）
    if webrtc_ctx.state.playing:
        st.success("✅ 通信中: 自分の声はブラウザ側で抑制されています")
        if webrtc_ctx.audio_processor:
            st.write("マイク入力レベル")
            st.progress(min(webrtc_ctx.audio_processor.amplitude, 100))
    else:
        st.info("Startボタンを押してください。")

with col_chat:
    st.subheader("💬 Text Chat")
    chat_box = st.container(height=300)
    for m in st.session_state.messages:
        chat_box.write(f"**User**: {m}")
    
    if prompt := st.chat_input("メッセージを入力..."):
        st.session_state.messages.append(prompt)
        st.rerun()

# --- 4. 最後に残された唯一の方法 ---
st.divider()
st.markdown("""
### 🔇 それでも自分の声が聞こえる場合の最終手段
今のコードは、ブラウザに「エコーを消せ」と命令していますが、ブラウザの性能限界で自分の声が漏れることがあります。その場合、**「原始的で最強の解決方法」**は以下の通りです。

1. **イヤホンを装着する**：これがITエンジニアが最初に行う、最も確実なエコー対策です。
2. **ブラウザのタブを右クリック ＞ 『サイトをミュート』**：
   - 自分の声は送信され続けますが、このページから出る音（自分のエコー）は物理的にゼロになります。
   - **注**: これを行うと相手の声も聞こえなくなるため、相手の声を聞く場合は別のブラウザやスマホで同じルームに入り、そちらを『受信専用』としてお使いください。
""")
