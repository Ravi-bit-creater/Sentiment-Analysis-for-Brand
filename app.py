import streamlit as st
import pandas as pd
import joblib
import re
import os
from urllib.parse import urlparse, parse_qs
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import altair as alt

# =========================================================
# PAGE CONFIG (ONCE)
# =========================================================
st.set_page_config(page_title="Brand Sentiment Monitor", layout="wide")

# =========================================================
# THEME STATE
# =========================================================
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# =========================================================
# CSS THEME ENGINE (Fix all light/dark mixing)
# =========================================================
def apply_theme(theme: str):
    if theme == "dark":
        BG = "#0b1220"
        SURFACE = "#111a2c"
        CARD = "#121f36"
        BORDER = "rgba(255,255,255,0.10)"
        TEXT = "#eaf1ff"
        MUTED = "rgba(234,241,255,0.70)"
        INPUT_BG = "#0f1a2d"
        HERO = "linear-gradient(90deg, #0b5cad 0%, #1a86d8 55%, #0b5cad 100%)"
        SHADOW = "0 14px 30px rgba(0,0,0,0.35)"
        RADIO_BG = "rgba(255,255,255,0.06)"
    else:
        BG = "#f5f7fb"
        SURFACE = "#f5f7fb"
        CARD = "#ffffff"
        BORDER = "rgba(10,20,40,0.12)"
        TEXT = "#0b1b3a"
        MUTED = "rgba(11,27,58,0.65)"
        INPUT_BG = "#ffffff"
        HERO = "linear-gradient(90deg, #0b5cad 0%, #1a86d8 55%, #0b5cad 100%)"
        SHADOW = "0 14px 30px rgba(0,0,0,0.12)"
        RADIO_BG = "rgba(255,255,255,0.92)"

    st.markdown(
        f"""
        <style>
        /* ----- GLOBAL RESET ----- */
        .stApp {{
            background: {BG} !important;
            color: {TEXT} !important;
        }}
        html, body, [class*="css"] {{
            color: {TEXT} !important;
        }}
        .block-container {{
            padding-top: 5.2rem;   /* leave space for topbar */
            padding-bottom: 2rem;
        }}

        /* Remove sidebar space if any */
        section[data-testid="stSidebar"] {{display: none;}}

        /* ----- TOPBAR (toggle visible always) ----- */
        .topbar {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 9999;
            background: {SURFACE};
            border-bottom: 1px solid {BORDER};
            padding: 10px 16px;
        }}
        .topbar-inner {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        }}
        .brand {{
            font-weight: 900;
            letter-spacing: .2px;
        }}
        .pill {{
            padding: 4px 10px;
            border-radius: 999px;
            border: 1px solid {BORDER};
            background: {CARD};
            color: {TEXT};
            font-size: 12px;
        }}

        /* ----- HERO HEADER ----- */
        .hero {{
            background: {HERO};
            padding: 22px 18px;
            border-radius: 18px;
            text-align: center;
            color: white !important;
            box-shadow: {SHADOW};
        }}
        .hero h1 {{
            margin: 0;
            font-size: 34px;
            font-weight: 900;
        }}
        .hero p {{
            margin: 8px 0 0 0;
            font-size: 16px;
            opacity: .95;
        }}

        /* ----- GENERAL CARDS ----- */
        .panel {{
            background: {CARD};
            border: 1px solid {BORDER};
            border-radius: 16px;
            padding: 14px;
        }}

        /* ----- INPUTS / SELECT ----- */
        .stTextInput input, .stTextArea textarea {{
            background: {INPUT_BG} !important;
            color: {TEXT} !important;
            border: 1px solid {BORDER} !important;
            border-radius: 12px !important;
        }}
        div[data-baseweb="select"] > div {{
            background: {INPUT_BG} !important;
            border: 1px solid {BORDER} !important;
            border-radius: 12px !important;
        }}

        /* ----- BUTTONS ----- */
        .stButton > button {{
            border-radius: 12px;
            padding: 0.65rem 1.05rem;
            font-weight: 800;
        }}

        /* ----- RADIO NAV (no wrap + selected highlight) ----- */
        div[role="radiogroup"] {{
            display: flex !important;
            justify-content: center !important;
            flex-wrap: nowrap !important;
            gap: 12px !important;
            width: 100%;
        }}
        div[role="radiogroup"] > label {{
            background: {RADIO_BG} !important;
            border: 1px solid {BORDER} !important;
            border-radius: 999px !important;
            padding: 8px 14px !important;
            margin: 0 !important;
            color: {TEXT} !important;
            font-weight: 800 !important;
            opacity: 1 !important;
            transition: 0.15s ease;
        }}
        div[role="radiogroup"] > label:hover {{
            transform: translateY(-1px);
            border-color: rgba(26,134,216,0.6) !important;
        }}
        /* Hide tiny radio circle */
        div[role="radiogroup"] svg {{
            display: none !important;
        }}

        /* ----- METRICS (avoid dark box mismatch) ----- */
        div[data-testid="metric-container"] {{
            background: {CARD} !important;
            border: 1px solid {BORDER} !important;
            border-radius: 16px !important;
            padding: 14px !important;
        }}
        div[data-testid="metric-container"] * {{
            color: {TEXT} !important;
        }}

        /* ----- DATAFRAME ----- */
        [data-testid="stDataFrame"] {{
            background: {CARD} !important;
            border: 1px solid {BORDER} !important;
            border-radius: 16px;
            overflow: hidden;
        }}

        /* ----- CHART BACKGROUND FIX (altair) ----- */
        .vega-embed, canvas {{
            background: transparent !important;
        }}

        /* ----- HEADINGS / MUTED TEXT ----- */
        .muted {{ color: {MUTED} !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

apply_theme(st.session_state.theme)

# =========================================================
# TOPBAR (toggle always visible)
# =========================================================
st.markdown(
    f"""
    <div class="topbar">
      <div class="topbar-inner">
        <div style="display:flex; gap:10px; align-items:center;">
          <div class="brand">📊 Brand Sentiment Monitor</div>
          <span class="pill">{st.session_state.theme.upper()} MODE</span>
        </div>
        <div id="toggle-anchor"></div>
      </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Put the toggle right after topbar (so it appears inside top area)
# (Streamlit can't place widgets inside raw HTML; we align it visually)
_, col_toggle = st.columns([0.85, 0.15])
with col_toggle:
    dark_on = st.toggle("Dark Mode", value=(st.session_state.theme == "dark"))
    new_theme = "dark" if dark_on else "light"
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()

# =========================================================
# HERO
# =========================================================
st.markdown(
    """
    <div class="hero">
        <h1>Sentiment & Sarcasm Analysis for Social Media</h1>
        <p>YouTube Comments Analysis</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

# =========================================================
# YOUTUBE KEY (SAFE)
# =========================================================
def get_youtube_api_key() -> str:
    try:
        key = st.secrets.get("YOUTUBE_API_KEY", "")
        if key:
            return str(key).strip()
    except Exception:
        pass
    return os.getenv("YOUTUBE_API_KEY", "").strip()

YOUTUBE_API_KEY = get_youtube_api_key()

def extract_video_id(url: str):
    try:
        u = urlparse(url.strip())
        host = (u.hostname or "").lower()
        if host in ["www.youtube.com", "youtube.com", "m.youtube.com"]:
            qs = parse_qs(u.query)
            return qs.get("v", [None])[0]
        if host == "youtu.be":
            return u.path.strip("/").split("?")[0]
    except Exception:
        return None
    return None

def fetch_youtube_comments(video_id: str, max_comments: int = 200):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    comments = []
    next_page = None

    while len(comments) < max_comments:
        req = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(100, max_comments - len(comments)),
            pageToken=next_page,
            textFormat="plainText",
            order="relevance",
        )
        res = req.execute()

        for item in res.get("items", []):
            top = item["snippet"]["topLevelComment"]["snippet"]
            comments.append(
                {
                    "text": top.get("textDisplay", ""),
                    "author": top.get("authorDisplayName", ""),
                    "publishedAt": top.get("publishedAt", ""),
                }
            )

        next_page = res.get("nextPageToken")
        if not next_page:
            break

    return pd.DataFrame(comments)

# =========================================================
# SARCASM
# =========================================================
SARCASM_EMOJIS = ["🙃", "😏", "😒", "😂", "🤣", "🤡"]
SARCASM_PHRASES = ["yeah right", "sure", "as if", "totally", "wow", "great", "amazing", "nice", "thanks for nothing"]
NEG_CUES = ["bad", "worst", "waste", "broken", "late", "delay", "refund", "no response", "not good", "poor", "terrible", "scam", "useless", "disappointed"]

def is_sarcastic(text: str) -> bool:
    t = str(text).lower()
    if any(e in str(text) for e in SARCASM_EMOJIS):
        return True
    has_phrase = any(p in t for p in SARCASM_PHRASES)
    has_neg = any(n in t for n in NEG_CUES)
    if has_phrase and has_neg:
        return True
    if ("..." in t or "!!" in t) and has_neg:
        return True
    return False

# =========================================================
# DATA LOADER
# =========================================================
@st.cache_data
def load_data():
    if os.path.exists("brand_sentiment_predictions.csv"):
        df_ = pd.read_csv("brand_sentiment_predictions.csv")
    else:
        df_ = pd.read_csv("brand_sentiment_1000_clean.csv")
    return df_

df = load_data()
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

sent_col = "predicted_sentiment" if "predicted_sentiment" in df.columns else "sentiment"

# =========================================================
# PREPROCESS
# =========================================================
def clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"http\S+|www\S+|https\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = text.replace("#", "")
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def handle_negation(text: str) -> str:
    t = str(text).lower()
    t = t.replace("can’t", "can't").replace("don’t", "don't").replace("didn’t", "didn't")
    t = re.sub(r"\b(not|no|never|cannot|can't|dont|don't|didnt|didn't)\s+(\w+)\b", r"\1_\2", t)
    return t

slang_map = {
    "mass": "very_good",
    "semma": "very_good",
    "vera level": "very_good",
    "super": "good",
    "mokka": "very_bad",
    "waste": "very_bad",
    "kadupu": "annoying",
    "romba mosam": "very_bad",
}

def apply_slang_map(text: str) -> str:
    t = text
    for k, v in slang_map.items():
        t = t.replace(k, v)
    return t

def preprocess(text: str) -> str:
    return apply_slang_map(handle_negation(clean_text(text)))

# =========================================================
# MODEL LOADER
# =========================================================
@st.cache_resource
def load_model_safe(model_path, vec_path):
    m = joblib.load(model_path)
    v = joblib.load(vec_path)
    return m, v

def get_model_and_vectorizer():
    default_model = "sentiment_model.joblib"
    default_vec = "tfidf_vectorizer.joblib"

    if os.path.exists(default_model) and os.path.exists(default_vec):
        return load_model_safe(default_model, default_vec), "local"

    with st.expander("🧩 Model Setup (Upload joblib files if not found)", expanded=True):
        st.info("Model files missing-na upload pannunga.")
        up_model = st.file_uploader("Upload sentiment_model.joblib", type=["joblib"])
        up_vec = st.file_uploader("Upload tfidf_vectorizer.joblib", type=["joblib"])
        if up_model and up_vec:
            with open(default_model, "wb") as f:
                f.write(up_model.getbuffer())
            with open(default_vec, "wb") as f:
                f.write(up_vec.getbuffer())
            st.success("✅ Saved. Rerun once.")
            st.rerun()

    return None, "missing"

result, model_status = get_model_and_vectorizer()
if result:
    model, tfidf = result

def ensure_model():
    if model_status == "missing":
        st.warning("Model files not found. Upload joblib files in Model Setup.")
        st.stop()

# =========================================================
# NAVIGATION (single-line centered)
# =========================================================
nav = st.radio(
    "Navigation",
    ["Dashboard", "Single Prediction", "Bulk Prediction", "YouTube Analysis", "Alerts"],
    horizontal=True,
    label_visibility="collapsed"
)

st.write("")

# =========================================================
# KPI CARDS (HTML)
# =========================================================
def kpi_cards(pos, neg, neu, sarc):
    st.markdown(
        f"""
        <div style="display:grid; grid-template-columns: repeat(4, minmax(160px, 1fr)); gap:14px;">
          <div class="panel" style="background: linear-gradient(135deg, #24a148 0%, #1f8a3d 100%); border:none; color:white;">
            <div style="font-weight:900;">✅ Positive</div>
            <div style="font-size:34px; font-weight:900; margin-top:6px;">{pos}</div>
          </div>

          <div class="panel" style="background: linear-gradient(135deg, #d93f3f 0%, #b83232 100%); border:none; color:white;">
            <div style="font-weight:900;">⛔ Negative</div>
            <div style="font-size:34px; font-weight:900; margin-top:6px;">{neg}</div>
          </div>

          <div class="panel" style="background: linear-gradient(135deg, #2d7dd2 0%, #2568ad 100%); border:none; color:white;">
            <div style="font-weight:900;">⚪ Neutral</div>
            <div style="font-size:34px; font-weight:900; margin-top:6px;">{neu}</div>
          </div>

          <div class="panel" style="background: linear-gradient(135deg, #f39c12 0%, #d9860f 100%); border:none; color:white;">
            <div style="font-weight:900;">😏 Sarcastic</div>
            <div style="font-size:34px; font-weight:900; margin-top:6px;">{sarc}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# PAGES
# =========================================================
def page_dashboard():
    st.markdown("<h3>Dashboard</h3>", unsafe_allow_html=True)
    st.markdown("<div class='muted'>Dataset overview + trend + breakdown</div>", unsafe_allow_html=True)
    st.write("")

    total = len(df)
    neg = int((df[sent_col] == "negative").sum())
    neu = int((df[sent_col] == "neutral").sum())
    pos = int((df[sent_col] == "positive").sum())
    sarc = 0

    kpi_cards(pos, neg, neu, sarc)
    st.write("")

    left, right = st.columns(2)
    with left:
        st.subheader("Sentiment Distribution")
        st.bar_chart(df[sent_col].value_counts())

    with right:
        st.subheader("Negative % Trend (Last 30 Days)")
        if "date" in df.columns and df["date"].notna().any():
            daily = df.groupby([df["date"].dt.date, sent_col]).size().unstack(fill_value=0)
            daily["negative_percent"] = (daily.get("negative", 0) / daily.sum(axis=1).replace(0, 1)) * 100
            daily = daily.sort_index().tail(30)
            st.line_chart(daily["negative_percent"])
        else:
            st.info("No valid date column found.")

def page_single():
    ensure_model()
    st.header("Single Prediction")
    text = st.text_area("Enter your text", height=140, placeholder="Type a comment / review here...")
    if st.button("ANALYZE", use_container_width=True):
        if not text.strip():
            st.error("Text empty-aa iruku.")
            return
        cleaned = preprocess(text)
        vec = tfidf.transform([cleaned])
        pred = model.predict(vec)[0]
        sarc = is_sarcastic(text)
        st.success(f"✅ Sentiment: **{str(pred).upper()}**")
        st.info(f"😏 Sarcasm Flag: **{'YES' if sarc else 'NO'}**")

def page_bulk():
    ensure_model()
    st.header("Bulk Prediction")
    up = st.file_uploader("Upload CSV (must contain a 'text' column)", type=["csv"])
    if not up:
        return
    data = pd.read_csv(up)
    if "text" not in data.columns:
        st.error("CSV-la 'text' column illa.")
        return
    st.dataframe(data.head(10), use_container_width=True)
    if st.button("Run Bulk Prediction", use_container_width=True):
        cleaned = data["text"].astype(str).apply(preprocess)
        vec = tfidf.transform(cleaned)
        data["predicted_sentiment"] = model.predict(vec)
        data["sarcastic_flag"] = data["text"].astype(str).apply(is_sarcastic)
        st.dataframe(data.head(30), use_container_width=True)
        st.download_button("⬇️ Download CSV", data.to_csv(index=False).encode("utf-8-sig"),
                           "bulk_predictions.csv", "text/csv", use_container_width=True)

def page_youtube():
    ensure_model()
    st.header("YouTube Analysis")

    if not YOUTUBE_API_KEY:
        st.error("YouTube API key missing. Use secrets.toml or env var.")
        st.stop()

    a, b, c = st.columns([0.62, 0.22, 0.16])
    with a:
        url = st.text_input("Enter YouTube URL", placeholder="Paste YouTube video URL here...")
    with b:
        max_n = st.selectbox("Fetch Last Comments", [50, 100, 200, 500], index=2)
    with c:
        st.write("")
        run = st.button("ANALYZE", use_container_width=True)

    if not run:
        return

    vid = extract_video_id(url or "")
    if not vid:
        st.error("Invalid YouTube URL.")
        return

    try:
        with st.spinner("Fetching comments..."):
            cdf = fetch_youtube_comments(vid, max_comments=max_n)
    except HttpError as e:
        st.error("YouTube API error (quota/key/video).")
        st.code(str(e))
        return

    if cdf.empty:
        st.warning("No comments fetched.")
        return

    cdf["clean"] = cdf["text"].astype(str).apply(preprocess)
    vec = tfidf.transform(cdf["clean"])
    cdf["sentiment"] = model.predict(vec)
    cdf["sarcastic"] = cdf["text"].astype(str).apply(is_sarcastic)

    pos = int((cdf["sentiment"] == "positive").sum())
    neg = int((cdf["sentiment"] == "negative").sum())
    neu = int((cdf["sentiment"] == "neutral").sum())
    sarc = int(cdf["sarcastic"].sum())

    kpi_cards(pos, neg, neu, sarc)
    st.write("")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Sentiment Distribution")
        st.bar_chart(cdf["sentiment"].value_counts())

    with col2:
        st.subheader("Sarcasm Breakdown")
        st.bar_chart(cdf["sarcastic"].value_counts().rename({True: "Sarcastic", False: "Not Sarcastic"}))

    with col3:
        st.subheader("Sentiment Trend (Weekly)")
        cdf["publishedAt"] = pd.to_datetime(cdf["publishedAt"], errors="coerce", utc=True)
        cdf = cdf.dropna(subset=["publishedAt"]).copy()
        if not cdf.empty:
            cdf["local"] = cdf["publishedAt"].dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
            cdf["week"] = cdf["local"].dt.to_period("W").apply(lambda r: r.start_time)
            wk = cdf.groupby(["week", "sentiment"]).size().reset_index(name="count")

            chart = (
                alt.Chart(wk)
                .mark_line(point=True)
                .encode(
                    x=alt.X("week:T", title="Week"),
                    y=alt.Y("count:Q", title="Count"),
                    color="sentiment:N",
                    tooltip=["week:T", "sentiment:N", "count:Q"],
                )
                .properties(height=280)
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No valid time data for trend.")

    st.write("")
    tabs = st.tabs(["All", "Positive", "Negative", "Sarcastic"])
    with tabs[0]:
        st.dataframe(cdf[["author", "text", "sentiment", "sarcastic"]], use_container_width=True)
    with tabs[1]:
        st.dataframe(cdf[cdf["sentiment"] == "positive"][["author", "text", "sentiment", "sarcastic"]], use_container_width=True)
    with tabs[2]:
        st.dataframe(cdf[cdf["sentiment"] == "negative"][["author", "text", "sentiment", "sarcastic"]], use_container_width=True)
    with tabs[3]:
        st.dataframe(cdf[cdf["sarcastic"] == True][["author", "text", "sentiment", "sarcastic"]], use_container_width=True)

    st.download_button("⬇️ Download Results CSV",
                       cdf.to_csv(index=False).encode("utf-8-sig"),
                       "youtube_results.csv", "text/csv", use_container_width=True)

def page_alerts():
    st.header("Alerts")
    if "date" not in df.columns or df["date"].isna().all():
        st.info("Alerts need valid 'date' column.")
        return

    last_date = df["date"].max()
    last_7 = df[df["date"] >= last_date - pd.Timedelta(days=7)]
    prev_7 = df[(df["date"] < last_date - pd.Timedelta(days=7)) & (df["date"] >= last_date - pd.Timedelta(days=14))]

    last_7_neg = last_7[sent_col].value_counts(normalize=True).get("negative", 0) * 100
    prev_7_neg = prev_7[sent_col].value_counts(normalize=True).get("negative", 0) * 100
    spike = last_7_neg - prev_7_neg

    c1, c2, c3 = st.columns(3)
    c1.metric("Last 7 days Negative %", f"{last_7_neg:.2f}%")
    c2.metric("Previous 7 days Negative %", f"{prev_7_neg:.2f}%")
    c3.metric("Change", f"{spike:.2f}%")

    if spike >= 15:
        st.error("🚨 Alert: High Negative Spike Detected!")
    else:
        st.success("✅ No major negative spike")

# =========================================================
# ROUTER
# =========================================================
if nav == "Dashboard":
    page_dashboard()
elif nav == "Single Prediction":
    page_single()
elif nav == "Bulk Prediction":
    page_bulk()
elif nav == "YouTube Analysis":
    page_youtube()
elif nav == "Alerts":
    page_alerts()