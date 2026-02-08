import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
from streamlit_autorefresh import st_autorefresh

# --- 1. 画面の自動更新設定 (0.1秒ごとに再描画) ---
# これにより、ユーザーが何もしなくてもメーターがリアルタイムで動きます
st_autorefresh(interval=100, key="volumemonitor")

st.title("🎤 リアルタイム・ボイスチャット (安定版)")
st.caption("接続設定を強化しました。ネットワークの壁を越えやすくしています。")

# --- 2. 音声解析クラス ---
class AudioAmplitudeProcessor(AudioProcessorBase):
    def __init__(self):
        self.amplitude = 0
        self.count = 0

    def recv(self, frame):
        # 1. 処理を極限まで速くするため、データのコピーや型変換を最小限にする
        try:
            # データの読み取り（読み取り専用として扱う）
            audio_data = frame.to_ndarray()
            self.count += 1
            
            # 2. 計算負荷を減らすため、全データではなく一部をサンプリングして計算
            # (10個おきにデータを間引いて計算しても音量計測には十分です)
            if audio_data.size > 0:
                # ndarrayのまま最大値を計算（これが一番速い）
                max_val = np.abs(audio_data[::10]).max()
                
                # 感度調整
                normalized = int((max_val / 15000) * 100)
                self.amplitude = max(0, min(normalized, 100))
        except Exception:
            pass
            
        # 3. 重要なポイント：frameをそのまま返す（加工しない）ことで
        # 音声データの整合性を保ち、ポツポツ音を防ぐ
        return frame

# --- 3. WebRTCストリーマーの設定 (接続強化版) ---
webrtc_ctx = webrtc_streamer(
    key="voice-chat-v7", # キーを新しくしてセッションをリセット
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=AudioAmplitudeProcessor,
    media_stream_constraints={
        "audio": {
            "echoCancellation": True,
            "noiseSuppression": True,
            "autoGainControl": True,
        },
        "video": False,
    },
    # 接続先(STUNサーバー)を増やして、つながる確率を最大化
    rtc_configuration={
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["stun:stun1.l.google.com:19302"]},
            {"urls": ["stun:stun2.l.google.com:19302"]},
            {"urls": ["stun:stun3.l.google.com:19302"]},
            {"urls": ["stun:stun4.l.google.com:19302"]},
        ],
        "iceTransportPolicy": "all",
    },
    async_processing=True,
)

# --- 4. メーターと状態の表示 ---
st.divider()

# 安全な状態チェック (Python 3.13対策)
is_playing = False
if webrtc_ctx and hasattr(webrtc_ctx, "state") and webrtc_ctx.state is not None:
    # state内のplaying属性を安全に取得
    try:
        is_playing = getattr(webrtc_ctx.state, "playing", False)
    except:
        is_playing = False

if is_playing:
    col1, col2 = st.columns(2)
    with col1:
        st.success("✅ 通信確立！")
        if hasattr(webrtc_ctx, "audio_processor") and webrtc_ctx.audio_processor:
            amp = getattr(webrtc_ctx.audio_processor, "amplitude", 0)
            count = getattr(webrtc_ctx.audio_processor, "count", 0)
            
            st.metric("受信パケット数", count)
            st.write("声の大きさメーター:")
            st.progress(amp)
            
            if amp > 80:
                st.warning("⚠️ 音が大きすぎます（音割れ注意）")
    
    with col2:
        st.info("通信のヒント")
        st.write("・自分の声がスピーカーから聞こえれば成功です。")
        st.write("・相手と話すには、同じURLを別の端末で開いてください。")
else:
    st.warning("🔄 接続待機中...")
    st.info("『Start』ボタンを押してください。Connectingから進まない場合は、Wi-Fiを切り替えるか、ブラウザをリロードしてみてください。")
