# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
from streamlit_autorefresh import st_autorefresh
import time

# --- 1. サーバー内共有メモリ（全ユーザー共通） ---
@st.cache_resource
def get_shared_state():
    # チャット履歴とユーザーの状態を保持
    return {"messages": [], "active_users": {}}

shared_state = get_shared_state()

# ページ設定
st.set_page_config(page_title="Voice Chat", layout="wide")
# 画面を1秒ごとに更新してチャットと同期
st_autorefresh(interval=1000, key="vitals")

# --- 2. オーディオプロセッサ（音声レベル解析） ---
class LiteAudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0
        self.mute = True

    def recv(self, frame):
        raw_data = frame.to_ndarray().astype(np.int16)
        if raw_data.size > 0:
            peak = np.abs(raw_data).max()
            if peak > 50:
                # 声の大きさを 0-100 のレベルに変換
                normalized = np.sqrt(peak / 32767) * 100
                self.amplitude = int(min(normalized * 1.8, 100))
            else:
                self.amplitude = 0
        
        if self.mute:
            # ミュート時は無音を返す
            return frame.from_ndarray(np.zeros_like(raw_data), format=frame.format.name)
        return frame

# --- 3. ユーザー設定（セッション） ---
if "my_name" not in st.session_state:
    st.session_state.my_name = f"User_{int(time.time()) % 1000}"
if "self_mute" not in st.session_state:
    st.session_state.self_mute = True

# --- 4. サイドバー ---
with st.sidebar:
    st.header("設定")
    new_name = st.text_input("ユーザー名", value=st.session_state.my_name)
    if new_name != st.session_state.my_name:
        st.session_state.my_name = new_name
        
    room_id = st.text_input("ルームID", value="101")
    st.session_state.self_mute = st.checkbox("自分の声を消音", value=st.session_state.self_mute)
    
    if st.button("チャットを全消去"):
        shared_state["messages"] = []
        st.rerun()

st.title(f"ルーム: {room_id}")

# --- 5. メインレイアウト ---
left_col, right_col = st.columns([1, 1])

with left_col:
    # WebRTCストリーマー設定
    webrtc_ctx = webrtc_streamer(
        key=f"v260-{room_id}", # キーを変えることでキャッシュをクリア
        mode=WebRtcMode.SENDRECV,
        audio_processor_factory=LiteAudioProcessor,
        media_stream_constraints={"audio": True, "video": False},
        rtc_configuration={
            "iceServers": [
                {"urls": ["stun:stun.l.google.com:19302"]},
                {"urls": ["stun:stun1.l.google.com:19302"]},
                {"urls": ["stun:stun2.l.google.com:19302"]},
            ],
            # ICE候補の収集を強化
            "iceCandidatePoolSize": 10,
        },
        async_processing=True,
        # サブパス運用時は重要
        sendback_audio=False, 
    )

    if webrtc_ctx.audio_processor:
        webrtc_ctx.audio_processor.mute = st.session_state.self_mute

    # 入退室の通知
    is_playing = webrtc_ctx.state.playing
    if is_playing and st.session_state.get("_prev_playing") != True:
        shared_state["messages"].append({"role": "system", "text": f"通知: {st.session_state.my_name} が入室しました"})
        st.session_state._prev_playing = True
    elif not is_playing and st.session_state.get("_prev_playing") == True:
        shared_state["messages"].append({"role": "system", "text": f"通知: {st.session_state.my_name} が退室しました"})
        st.session_state._prev_playing = False

    st.subheader("参加メンバー")
    if is_playing:
        level = webrtc_ctx.audio_processor.amplitude if webrtc_ctx.audio_processor else 0
        status_label = "消音中" if st.session_state.self_mute else ("発言中" if level > 30 else "オンライン")
        
        st.write(f"名前: {st.session_state.my_name} [ {status_label} ]")
        st.markdown(f"""
            <div style="width:100%; background:#eee; height:10px; border-radius:5px;">
                <div style="width:{level}%; background:#4CAF50; height:100%; border-radius:5px; transition: width 0.1s;"></div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("STARTボタンを押してボイスチャットを開始してください")

# --- 6. チャットエリア ---
with right_col:
    st.subheader("テキストチャット")
    chat_box = st.container(height=450)
    with chat_box:
        for m in shared_state["messages"]:
            if m["role"] == "system":
                st.caption(m["text"])
            else:
                st.chat_message(m["role"]).write(f"{m['user']}: {m['text']}")

    if prompt := st.chat_input("メッセージを入力..."):
        shared_state["messages"].append({
            "role": "user", 
            "user": st.session_state.my_name, 
            "text": prompt
        })
        st.rerun()
