# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
from streamlit_autorefresh import st_autorefresh
import time

st.set_page_config(page_title="Voice Chat", layout="wide")
# 更新間隔 500ms
st_autorefresh(interval=500, key="vitals")

# --- 1. オーディオプロセッサ ---
class LiteAudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0
        self.mute = True

    def recv(self, frame):
        raw_data = frame.to_ndarray().astype(np.int16)
        if raw_data.size > 0:
            peak = np.abs(raw_data).max()
            if peak > 50:
                normalized = np.sqrt(peak / 32767) * 100
                self.amplitude = int(min(normalized * 1.8, 100))
            else:
                self.amplitude = 0
        
        if self.mute:
            return frame.from_ndarray(np.zeros_like(raw_data), format=frame.format.name)
        return frame

# --- 2. セッション管理 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "self_mute" not in st.session_state:
    st.session_state.self_mute = True
if "my_name" not in st.session_state:
    st.session_state.my_name = f"User_{int(time.time()) % 1000}"

# --- 3. サイドバー ---
with st.sidebar:
    st.header("設定")
    new_name = st.text_input("ユーザー名", value=st.session_state.my_name)
    if new_name != st.session_state.my_name:
        st.session_state.my_name = new_name
        
    room_id = st.text_input("ルームID", value="101")
    st.session_state.self_mute = st.checkbox("自分の声を消音", value=st.session_state.self_mute)
    
    if st.button("チャットを消去"):
        st.session_state.messages = []
        st.rerun()

st.title(f"ルーム: {room_id}")

left_col, right_col = st.columns([1, 1])

with left_col:
    webrtc_ctx = webrtc_streamer(
        key=f"v160-{room_id}", 
        mode=WebRtcMode.SENDRECV,
        audio_processor_factory=LiteAudioProcessor,
        media_stream_constraints={"audio": True, "video": False},
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        async_processing=True,
    )

    if webrtc_ctx.audio_processor:
        webrtc_ctx.audio_processor.mute = st.session_state.self_mute

    # --- 4. 入退室ロジック ---
    is_playing = webrtc_ctx.state.playing
    
    # 接続時
    if is_playing and st.session_state.get("_prev_playing") != True:
        msg = f"通知: {st.session_state.my_name} が入室しました"
        st.session_state.messages.append({"role": "system", "text": msg})
        st.session_state._prev_playing = True

    # 切断時
    elif not is_playing and st.session_state.get("_prev_playing") == True:
        msg = f"通知: {st.session_state.my_name} が退室しました"
        st.session_state.messages.append({"role": "system", "text": msg})
        st.session_state._prev_playing = False

    # --- 5. ユーザー状態表示 ---
    st.subheader("参加メンバー")
    if is_playing:
        level = webrtc_ctx.audio_processor.amplitude if webrtc_ctx.audio_processor else 0
        
        # 状態ラベル（絵文字なし）
        if st.session_state.self_mute:
            status_label = "消音中"
        elif level > 30:
            status_label = "発言中"
        else:
            status_label = "オンライン"
        
        st.write(f"名前: {st.session_state.my_name} [ {status_label} ]")
        
        # メーター表示
        st.markdown(f"""
            <div style="width:100%; background:#eee; height:10px; border-radius:5px;">
                <div style="width:{level}%; background:#4CAF50; height:100%; border-radius:5px;"></div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("開始ボタンを押して参加してください")

# --- 6. チャットエリア ---
with right_col:
    st.subheader("テキストチャット")
    chat_box = st.container(height=400)
    with chat_box:
        for m in st.session_state.messages:
            if m["role"] == "system":
                st.caption(m["text"])
            else:
                st.chat_message(m["role"]).write(f"{m['user']}: {m['text']}")

    if prompt := st.chat_input("メッセージを入力"):
        st.session_state.messages.append({"role": "user", "user": st.session_state.my_name, "text": prompt})
        st.rerun()
