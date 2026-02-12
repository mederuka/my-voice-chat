# -*- coding: utf-8 -*-
import streamlit as st
import os
import time

st.title("原始的トランシーバー (100%繋がる版)")

# 音声ファイルの保存場所
VOICE_FILE = "shared_voice.wav"

st.info("この方式なら、ネットの制限に関係なく相手に声が届きます。")

# --- 1. 送信機能 ---
st.subheader("1. 声を送る")
audio_value = st.audio_input("マイクボタンを押して喋ってください")

if audio_value:
    # 録音されたデータを保存
    with open(VOICE_FILE, "wb") as f:
        f.write(audio_value.getbuffer())
    st.success("送信完了！相手の画面にあなたの声が届きます。")

st.divider()

# --- 2. 受信機能 ---
st.subheader("2. 相手の声を聞く")
if os.path.exists(VOICE_FILE):
    st.write("最新の受信ボイス:")
    st.audio(VOICE_FILE)
    
    # 最終更新時間を確認
    mtime = time.ctime(os.path.getmtime(VOICE_FILE))
    st.caption(f"更新時刻: {mtime}")
else:
    st.write("まだメッセージはありません。")

# 自動更新ボタン
if st.button("最新の声をチェック"):
    st.rerun()
