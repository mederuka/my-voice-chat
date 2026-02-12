# -*- coding: utf-8 -*-
import streamlit as st
import os
import glob
import uuid

st.set_page_config(page_title="Final Transceiver", layout="centered")

# 保存ディレクトリ
SAVE_DIR = "shared_voices"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# --- ユーザー識別 (自分を特定するためのID) ---
if "my_id" not in st.session_state:
    st.session_state["my_id"] = str(uuid.uuid4())[:4]

st.title(f"📟 トランシーバー (ID: {st.session_state['my_id']})")
st.caption("自分の声は自分には聞こえず、相手にだけ届きます。")

# --- 1. 送信セクション ---
audio_data = st.audio_input("マイクを押して話し、チェックで送信")

if audio_data:
    # ファイル名に「送り主ID」と「ユニークID」を入れる
    # 形式: senderID_uniqueID.wav
    unique_id = str(uuid.uuid4())[:8]
    file_name = f"{st.session_state['my_id']}_{unique_id}.wav"
    file_path = os.path.join(SAVE_DIR, file_name)
    
    with open(file_path, "wb") as f:
        f.write(audio_data.getbuffer())
    
    st.success("相手に送信しました！")
    # 送信直後は再生させないよう少し待つか、すぐリセット
    st.toast("Sent!")

st.divider()

# --- 2. 受信 & フィルタリングセクション ---
voice_files = glob.glob(os.path.join(SAVE_DIR, "*.wav"))

if voice_files:
    for latest_file in voice_files:
        fname = os.path.basename(latest_file)
        
        # 【重要】ファイル名の先頭が「自分のID」でなければ再生する
        if not fname.startswith(st.session_state["my_id"]):
            st.warning("🆕 相手からの新着メッセージ")
            
            with open(latest_file, "rb") as f:
                audio_bytes = f.read()
            
            # 読み込んだら即座に物理削除（相手に届いた証拠）
            try:
                os.remove(latest_file)
            except:
                pass
            
            # 再生（相手の声だけが鳴る）
            st.audio(audio_bytes, format="audio/wav", autoplay=True)
        else:
            # 自分のファイルがまだ残っている場合は、何もしない（あるいは古いので消す）
            # ※相手がまだ受け取っていない状態
            st.info("相手が受信するのを待っています...")
else:
    st.write("💤 新着なし")

# --- 3. 無点滅・自動更新JavaScript ---
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
