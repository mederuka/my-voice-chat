# -*- coding: utf-8 -*-
import streamlit as st
import uuid
import time

# --- 全ユーザー共通の「声の置き場」を作成 ---
@st.cache_resource
def get_global_mailbox():
    # サーバーが起動している間、全員で共有される辞書
    return {}

mailbox = get_global_mailbox()

st.set_page_config(page_title="Cloud Transceiver")

# 自分のIDを固定
if "my_id" not in st.session_state:
    st.session_state["my_id"] = str(uuid.uuid4())[:4]

st.title(f"📟 クラウド・トランシーバー (ID: {st.session_state['my_id']})")

# --- 1. 送信：掲示板に声を置く ---
audio_data = st.audio_input("マイクで話し、チェックで送信")

if audio_data:
    # 掲示板の内容を書き換える
    mailbox["sender"] = st.session_state["my_id"]
    mailbox["audio_bytes"] = audio_data.read()
    mailbox["timestamp"] = time.time()
    
    st.success("クラウドに声を置きました。相手に届きます。")

st.divider()

# --- 2. 受信：掲示板を見に行く ---
if "last_heard_ts" not in st.session_state:
    st.session_state["last_heard_ts"] = 0

if "audio_bytes" in mailbox:
    # 「送り主が自分ではない」かつ「まだ聞いていない新しい声」なら再生
    if mailbox["sender"] != st.session_state["my_id"]:
        if mailbox["timestamp"] > st.session_state["last_heard_ts"]:
            
            st.warning("🆕 相手からの新着メッセージを受信")
            st.audio(mailbox["audio_bytes"], format="audio/wav", autoplay=True)
            
            # 既読にする
            st.session_state["last_heard_ts"] = mailbox["timestamp"]
        else:
            st.write("💤 新着なし")
    else:
        st.write("📤 送信済み（相手の受信待ち）")
else:
    st.write("💤 メッセージを待っています...")

# --- 3. 自動更新（点滅を抑える） ---
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
