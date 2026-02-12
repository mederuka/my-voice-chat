# -*- coding: utf-8 -*-
import streamlit as st
import os
import glob
import uuid

st.set_page_config(page_title="No-Flash Transceiver", layout="centered")

SAVE_DIR = "temp_voices"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

st.title("📟 無点滅トランシーバー")
st.caption("画面は白く光りません。裏側で新着をチェックしています。")

# --- 1. 送信セクション ---
audio_data = st.audio_input("マイクで録音してください")

if audio_data:
    # 古いファイルを掃除
    for f in glob.glob(os.path.join(SAVE_DIR, "*.wav")):
        try: os.remove(f)
        except: pass
    
    # 新しい名前で保存
    unique_id = str(uuid.uuid4())[:8]
    file_path = os.path.join(SAVE_DIR, f"voice_{unique_id}.wav")
    with open(file_path, "wb") as f:
        f.write(audio_data.getbuffer())
    st.success("送信完了！")

st.divider()

# --- 2. 受信セクション (JavaScriptによる無点滅監視) ---
# フォルダ内にファイルがあるか確認
voice_files = glob.glob(os.path.join(SAVE_DIR, "*.wav"))

if voice_files:
    latest_file = voice_files[0]
    with open(latest_file, "rb") as f:
        audio_bytes = f.read()
    
    # 読み込んだら即削除（二度鳴り防止）
    try:
        os.remove(latest_file)
    except:
        pass
    
    # 音声を配置（autoplay=True）
    st.audio(audio_bytes, format="audio/wav", autoplay=True)
    st.info("🆕 新着を再生しました。")

# --- 3. 【核心】点滅させずに「自分自身をリロードする」JavaScript ---
# ページ全体を真っ白にせず、状態だけをサーバーに問い合わせます
st.components.v1.html(
    """
    <script>
    // 3秒ごとにStreamlitの「再計算」をトリガーするが、
    // 画面全体の白いフラッシュを最小限に抑えるためのハック
    setTimeout(function(){
        window.parent.document.querySelector('.stApp').dispatchEvent(new Event('keypress'));
    }, 3000);
    </script>
    """,
    height=0,
)

st.write("💤 待機中...（3秒ごとに自動チェック中）")
