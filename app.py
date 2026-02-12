# -*- coding: utf-8 -*-
import streamlit as st
import uuid
import time

# --- 全ユーザーで共有するための特殊なメモリ空間 ---
# これにより、ファイル保存なしで相手にデータを渡せます
if "shared_mailbox" not in st.session_state.__class__._shared_state:
    st.session_state.__class__._shared_state["shared_mailbox"] = {}

shared_data = st.session_state.__class__._shared_state["shared_mailbox"]

st.set_page_config(page_title="Cloud Transceiver")

# ユーザーIDの生成
if "my_id" not in st.session_state:
    st.session_state["my_id"] = str(uuid.uuid4())[:4]

st.title(f"📟 クラウド・トランシーバー (ID: {st.session_state['my_id']})")

# --- 1. 送信セクション ---
audio_data = st.audio_input("マイクで話し、送信ボタン（チェック）を押す")

if audio_data:
    # 共有メモリに「送り主ID」と「音声データ」をセット
    # 既存のデータを上書きして、最新の1つだけを保持します
    shared_data["sender"] = st.session_state["my_id"]
    shared_data["audio"] = audio_data.read()
    shared_data["timestamp"] = time.time()
    
    st.success("クラウドへ送信しました！相手の画面で自動再生されます。")

st.divider()

# --- 2. 受信セクション ---
# 最後に再生したメッセージのタイムスタンプを記録
if "last_heard" not in st.session_state:
    st.session_state["last_heard"] = 0

# 共有メモリにデータがあり、かつ「送り主が自分ではない」場合
if "audio" in shared_data:
    if shared_data["sender"] != st.session_state["my_id"]:
        if shared_data["timestamp"] > st.session_state["last_heard"]:
            
            st.warning("🆕 相手からの新着メッセージを受信！")
            st.audio(shared_data["audio"], format="audio/wav", autoplay=True)
            
            # 既読にする
            st.session_state["last_heard"] = shared_data["timestamp"]
        else:
            st.write("💤 待機中（新着なし）")
    else:
        st.write("📤 あなたの送信した声がクラウドにあります（相手の受信待ち）")
else:
    st.write("💤 メッセージを待っています...")

# --- 3. 点滅を抑えた自動更新 ---
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
