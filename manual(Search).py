import streamlit as st
import os
import json
import base64
import requests
import html

# ── 페이지 설정 ──
st.set_page_config(page_title="설비 관리 시스템", layout="wide")

# ── CSS ──
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    .header-title {
        font-size: 24px !important;
        font-weight: bold;
        color: #1E1E1E;
        text-align: center;
        margin-bottom: 12px;
    }
    div.stButton > button {
        width: 100%;
        height: 72px;
        font-size: 18px !important;
        font-weight: bold;
        border-radius: 15px;
        background: #ffffff;
        border: 1px solid #ddd;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 10px;
        transition: 0.2s;
    }
    .menu-section div.stButton > button {
        border: 2px solid #2E7D32 !important;
        color: #2E7D32 !important;
        height: 72px !important;
    }
    .detail-card-content {
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        font-family: inherit;
        white-space: pre-wrap;   /* ← 줄바꿈 보존 */
        word-wrap: break-word;
        word-break: keep-all;
        margin: 0;
        font-size: 15px;
        line-height: 1.7;
    }
    </style>
    """, unsafe_allow_html=True)

# ── GitHub API 설정 ──
GITHUB_TOKEN     = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO      = st.secrets["GITHUB_REPO"]
GITHUB_FILE_PATH = st.secrets["GITHUB_FILE_PATH"]
GITHUB_API_URL   = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
HEADERS          = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# ── GitHub에서 data.json 불러오기 ──
@st.cache_data(ttl=60)
def load_data_from_github():
    res = requests.get(GITHUB_API_URL, headers=HEADERS)
    if res.status_code == 200:
        content = res.json()["content"]
        decoded = base64.b64decode(content).decode("utf-8")
        return json.loads(decoded)
    else:
        st.error(f"data.json 불러오기 실패: {res.status_code}")
        return {}

# ── GitHub에 data.json 저장하기 ──
def save_data_to_github(data: dict):
    res = requests.get(GITHUB_API_URL, headers=HEADERS)
    if res.status_code != 200:
        st.error("저장 실패: 파일 SHA를 가져올 수 없습니다.")
        return False

    sha = res.json()["sha"]
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    encoded  = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

    payload = {
        "message": "Update data.json via Streamlit app",
        "content": encoded,
        "sha": sha
    }
    put_res = requests.put(GITHUB_API_URL, headers=HEADERS, json=payload)

    if put_res.status_code in (200, 201):
        st.cache_data.clear()
        return True
    else:
        st.error(f"저장 실패: {put_res.status_code} {put_res.text}")
        return False

# ── 줄바꿈 안전 렌더링 함수 ──
def render_content(text: str) -> str:
    """
    1) html.escape() 로 <, >, & 등 특수문자 이스케이프
    2) \n → <br> 변환
    → <pre> 없이 <div> 사용해도 줄바꿈이 100% 보장됨
    """
    escaped = html.escape(text)          # XSS 방지 + 특수문자 보호
    return escaped.replace("\n", "<br>") # 줄바꿈 변환

# ── 데이터 로드 ──
details = load_data_from_github()
DB_KEYS = list(details.keys())

if 'page' not in st.session_state:
    st.session_state.page = 'main'

# ── 관리자 팝업 ──
@st.dialog("🔐 관리자 모드")
def admin_dialog():
    pw = st.text_input("비밀번호", type="password")
    if pw == "7895":
        t_main = st.selectbox("계통", DB_KEYS)
        t_sub  = st.selectbox("항목", list(details[t_main].keys()))
        new_text = st.text_area(
            "내용 수정 (엔터로 줄바꿈 가능)",
            value=details[t_main][t_sub],
            height=200
        )
        if st.button("💾 저장 (GitHub 반영)"):
            details[t_main][t_sub] = new_text  # \n 그대로 저장
            ok = save_data_to_github(details)
            if ok:
                st.success("저장 완료! GitHub data.json이 업데이트됐습니다.")

# ── 요약도 팝업 ──
@st.dialog("📋 전체 요약도")
def summary_dialog():
    image_path = "summary.png"
    if os.path.exists(image_path):
        st.image(image_path, use_container_width=True)
        
        with open(image_path, "rb") as f:
            img_bytes = f.read()
        st.download_button(
            label="⬇️ 이미지 다운로드",
            data=img_bytes,
            file_name="summary.png",
            mime="image/png",
            use_container_width=True
        )
    else:
        st.error(f"'{image_path}' 파일을 찾을 수 없습니다.")

# ── 화면 구성 ──
st.markdown("<p class='header-title'>⚡ 설비 유지보수 시스템</p>", unsafe_allow_html=True)

st.markdown('<div class="menu-section">', unsafe_allow_html=True)
if st.button("🏠 메인", use_container_width=True):
    st.session_state.page = 'main'
    st.rerun()
if st.button("📋 요약도", use_container_width=True):
    summary_dialog()
if st.button("⚙️ 설정", use_container_width=True):
    admin_dialog()
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

search_query = st.text_input(
    "🔍 문제점 검색",
    placeholder="단어 입력",
    label_visibility="collapsed"
)

# ── 메인 / 상세 로직 ──
if st.session_state.page == 'main':
    if search_query:
        found = False
        for cat, items in details.items():
            for sub, content in items.items():
                if search_query in content or search_query in sub:
                    found = True
                    with st.expander(f"✅ {cat} > {sub}", expanded=True):
                        st.markdown(
                            f'<div class="detail-card-content">{render_content(content)}</div>',
                            unsafe_allow_html=True
                        )
        if not found:
            st.info("검색 결과가 없습니다.")
        st.divider()

    for cat in DB_KEYS:
        if st.button(cat, use_container_width=True):
            st.session_state.selected_main = cat
            st.session_state.page = 'detail'
            st.rerun()

elif st.session_state.page == 'detail':
    main_cat = st.session_state.selected_main
    st.subheader(f"📍 {main_cat}")
    for sub, content in details[main_cat].items():
        with st.expander(f"🔎 {sub}", expanded=False):
            st.markdown(
                f'<div class="detail-card-content">{render_content(content)}</div>',
                unsafe_allow_html=True
            )
