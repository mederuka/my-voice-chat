# -*- coding: utf-8 -*-
import streamlit as st
import uuid
import os
import time
import base64

st.set_page_config(page_title="Final Survival Transceiver")

# 保存先（Streamlitが実行されているディレクトリ）
SAVE_FILE = "global_shared_voice.wav"

if "my_id" not in st.session_state:
    st.session_state["my_id"] = str(uuid.uuid4())[:4]

st.title(f"📟 最終通信 (ID: {st.session_state['my_id']})")

# --- 1. 送信：物理ファイルを上書き保存 ---
audio_data = st.audio_input("マイクで話し、送信（チェック）")

if audio_data:
    # 誰が送ったかの情報をファイル名の代わりに「中身」で判定するのは難しいため
    # 送信時に「送信者ID」を別の小さなファイルに書き出します
    with open(SAVE_FILE, "wb") as f:
        f.write(audio_data.read())
    
    with open("sender_id.txt", "w") as f:
        f.write(st.session_state["my_id"])
        
    st.success("サーバーへ物理的に書き込みました。")
    st.rerun()

st.divider()

# --- 2. 受信：物理ファイルを監視 ---
if "last_check" not in st.session_state:
    st.session_state["last_check"] = 0

if os.path.exists(SAVE_FILE) and os.path.exists("sender_id.txt"):
    mtime = os.path.getmtime(SAVE_FILE)
    
    with open("sender_id.txt", "r") as f:
        current_sender = f.read()

    # 「他人が送った」かつ「まだ聞いていない新着」なら再生
    if current_sender != st.session_state["my_id"] and mtime > st.session_state["last_check"]:
        st.warning("🆕 相手からの声を検知！")
        
        # ファイルを読み込んで再生
        with open(SAVE_FILE, "rb") as f:
            audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/wav", autoplay=True)
        
        st.session_state["last_check"] = mtime
    else:
        st.write("💤 新着を待っています...")
else:
    st.write("準備中：まだ誰も送信していません")

# --- 3. 無点滅更新（JavaScript） ---
st.components.v1.html(
    """
    <script>
    setTimeout(function(){
        window.parent.document.querySelector('.stApp').dispatchEvent(new Event('keypress'));
    }, 3000);
    </script>
    """,
    height=0,
)
