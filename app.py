import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode

st.title("音声疎通テスト（安定重視版）")

# streamlit-webrtcの起動
webrtc_ctx = webrtc_streamer(
    key="stable-test",
    mode=WebRtcMode.SENDRECV,
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    },
    media_stream_constraints={"audio": True, "video": False},
)

# エラーが出る「webrtc_ctx.state.signalling_state」へのアクセスを完全に削除
# 代わりに、再生中かどうかだけを「安全な方法」でチェックします

is_playing = False
if webrtc_ctx is not None:
    try:
        # stateが存在し、かつplaying属性がある場合のみ取得
        if hasattr(webrtc_ctx, "state") and webrtc_ctx.state is not None:
            is_playing = getattr(webrtc_ctx.state, "playing", False)
    except AttributeError:
        # 万が一エラーが起きても無視して進む
        pass

if is_playing:
    st.success("✅ 通信が確立されました！声を出してみてください。")
else:
    st.info("下の『Start』ボタンを押してマイクを許可してください。")
    st.caption("※Startを押したあと、画面のどこかを一度クリックすると音が出やすくなります。")
