import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode

st.title("音声疎通テスト")

# 接続設定
webrtc_ctx = webrtc_streamer(
    key="test-connection",
    mode=WebRtcMode.SENDRECV, # 自分の声を自分で聞くループバック
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    },
    media_stream_constraints={
        "audio": True,
        "video": False,
    },
)

# 状態をテキストで表示（どこで止まっているか特定する）
status = st.empty()

if webrtc_ctx.state.playing:
    status.success("✅ 実行中：声を出してスピーカーから聞こえるか確認してください。")
elif webrtc_ctx.state.signalling_state:
    status.warning(f"⏳ 接続準備中... (状態: {webrtc_ctx.state.signalling_state})")
else:
    status.info("❄️ Startボタンを押してください。")
