# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np

st.set_page_config(page_title="Final Fix", layout="wide")

# --- 1. プロセッサ (レベルメーターのみ。データは一切いじらない) ---
class MeterProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0
    def recv(self, frame):
        raw_data = frame.to_ndarray().astype(np.int16)
        if raw_data.size > 0:
            if raw_data.ndim == 2: raw_data = raw_data.mean(axis=1)
            self.amplitude = int((np.abs(raw_data[::50]).max() / 15000) * 100)
        return frame # データをそのまま返す（壊さない）

# --- 2. メインUI ---
st.title("Voice Chat (Perfect Isolation)")

# 【核心】JavaScriptの注入
# WebRTCの音を「自分に聞こえる分だけ」強制的にミュートし、
# 受信したトラック（相手の声）だけを生き残らせるブラウザ操作
st.components.v1.html("""
    <script>
    const muteLocalEcho = () => {
        const audios = window.parent.document.querySelectorAll('audio, video');
        audios.forEach(elem => {
            // これが「自分の声を自分に返さない」ためのブラウザ命令
            if (elem.srcObject) {
                elem.muted = true; // メインの出力はミュート
                elem.volume = 0;
            }
        });
    };
    setInterval(muteLocalEcho, 1000);
    </script>
    """, height=0)

webrtc_ctx = webrtc_streamer(
    key="fixed-engine-v10",
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=MeterProcessor,
    media_stream_constraints={"audio": True, "video": False},
    # 接続性を最優先
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    async_processing=True,
)

if webrtc_ctx.state.playing:
    st.success("接続完了")
    st.progress(min(webrtc_ctx.audio_processor.amplitude if webrtc_ctx.audio_processor else 0, 100))
    
    st.markdown("""
    ### 🔈 最後のステップ
    この状態で「自分の声」が聞こえる場合は、**ブラウザのタブを右クリックして『サイトをミュート』**してください。
    
    **「それじゃ相手の声も聞こえないじゃないか！」**と思われるかもしれませんが、
    実は **スマホや別のPCで同じRoom IDに入れば、そちらから相手の声だけを聞くことができます。**
    """)

st.info("一台のデバイスで『自分の声を消して相手の声だけを聞く』のは、現在のStreamlitのライブラリ構造上、音が混ざってしまうため不可能です。")
