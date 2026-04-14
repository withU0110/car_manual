import streamlit as st
import os, json, base64, html, re, requests
from io import BytesIO
from PIL import Image, ImageOps

# ════════════════════════════════════════
#  1. 환경 설정 및 CSS (배경색 고정 포함)
# ════════════════════════════════════════
st.set_page_config(page_title="설비 관리 시스템", layout="wide")

st.markdown("""<style>
.stApp,[data-testid="stAppViewContainer"]{background:#333;color:#E8E8E8}
[data-testid="stHeader"],[data-testid="stSidebar"]{background:#2A2A2A}
.block-container{padding:2.5rem 1rem 1rem;background:#333}
.header-title{font-size:22px;font-weight:bold;color:#FFD966;text-align:center;
  margin-bottom:10px;letter-spacing:1px;text-shadow:0 1px 3px rgba(0,0,0,.5)}

/* 버튼 스타일 */
div.stButton>button{width:100%;height:68px;font-size:17px!important;font-weight:bold;
  border-radius:12px;background:#444!important;border:1px solid #555!important;
  color:#E8E8E8!important;box-shadow:2px 2px 8px rgba(0,0,0,.4);margin-bottom:8px;transition:.2s}
div.stButton>button:hover{background:#505050!important;border-color:#FFD966!important;color:#FFD966!important}

/* 상단 메뉴 버튼 */
.menu-section div.stButton>button{border:1.5px solid #FFD966!important;color:#FFD966!important;
  background:#3A3A3A!important;height:52px!important;font-size:15px!important;border-radius:10px!important}

/* 뒤로가기 버튼 */
.back-btn div.stButton>button{height:36px!important;font-size:14px!important;
  border:1px solid #7CB9E8!important;color:#7CB9E8!important;border-radius:8px!important;
  background:#3A3A3A!important;box-shadow:none!important;margin-bottom:8px!important;
  width:auto!important;padding:0 16px!important}

/* Expander 배경색 고정 (클릭 전후 색상 유지) */
[data-testid="stExpander"] {
    background:#3A3A3A!important;
    border:1px solid #4A4A4A!important;
    border-radius:10px!important;
    margin-bottom:6px;
}
[data-testid="stExpander"] summary:hover {
    background: transparent !important;
    color: #FFD966 !important;
}
[data-testid="stExpander"] summary {
    color:#E8E8E8!important;
    font-weight:bold;
}

.detail-card-content{padding:16px 18px;background:#3E3E3E;border-radius:10px;
  border-left:5px solid #FFD966;font-family:'Nanum Gothic','Malgun Gothic',sans-serif;
  white-space:pre-wrap;word-break:keep-all;font-size:15px;line-height:1.85;color:#E8E8E8}

.cat-header{font-size:20px;font-weight:bold;color:#FFD966;margin:6px 0 10px;
  padding-bottom:4px;border-bottom:1px solid #555}
</style>""", unsafe_allow_html=True)

# ════════════════════════════════════════
#  2. GitHub API 및 데이터 처리 함수
# ════════════════════════════════════════
# Secrets가 설정되어 있어야 합니다.
try:
    GITHUB_TOKEN     = st.secrets["GITHUB_TOKEN"]
    GITHUB_REPO      = st.secrets["GITHUB_REPO"]
    GITHUB_FILE_PATH = st.secrets["GITHUB_FILE_PATH"]
except:
    st.error("Secrets 설정(GITHUB_TOKEN 등)이 누락되었습니다.")
    st.stop()

API_URL  = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
HEADERS  = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

@st.cache_data(ttl=60)
def load_data():
    try:
        res = requests.get(API_URL, headers=HEADERS)
        if res.status_code == 200:
            content = base64.b64decode(res.json()["content"]).decode('utf-8')
            return json.loads(content)
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
    return {}

# ════════════════════════════════════════
#  3. 텍스트 포맷팅 및 헬퍼 함수
# ════════════════════════════════════════
FORMATS = [
    (r'\^\^\^(.+?)\^\^\^', r'<span style="font-size:28px;font-weight:bold;color:#FFD966">\1</span>'),
    (r'##(.+?)##',          r'<span style="font-size:22px;font-weight:bold;color:#FFD966">\1</span>'),
    (r'!!(.+?)!!',          r'<span style="color:#FF6B6B;font-weight:bold">\1</span>'),
    (r'\*\*(.+?)\*\*',      r'<strong>\1</strong>'),
]

def render_content(text: str) -> str:
    s = html.escape(text)
    for pat, rep in FORMATS: s = re.sub(pat, rep, s)
    return s.replace('\n', '<br>')

def clean_key(key: str) -> str:
    # 버튼 등에 표시할 때 특수 기호 제거
    return re.sub(r'\^\^\^|##', '', key).strip()

def parse_content(content) -> tuple[str, list]:
    if isinstance(content, dict):
        return content.get("text", ""), content.get("images", [])
    return str(content), []

def render_card(content):
    text, images = parse_content(content)
    st.markdown(f'<div class="detail-card-content">{render_content(text)}</div>', unsafe_allow_html=True)
    for url in images: st.image(url, use_container_width=True)

# ════════════════════════════════════════
#  4. 메인 로직 및 세션 관리
# ════════════════════════════════════════
ss = st.session_state # ss 정의 (NameError 방지)
if "page" not in ss: ss.page = "main"
if "search_query" not in ss: ss.search_query = ""

details = load_data()
DB_KEYS = [k for k in details.keys() if k != "__meta__"]

st.markdown("<p class='header-title'>⚡ 설비 유지보수 시스템</p>", unsafe_allow_html=True)

# 상단 메뉴
st.markdown('<div class="menu-section">', unsafe_allow_html=True)
m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    if st.button("🏠 메인"):
        ss.page = 'main'
        ss.search_query = "" # 검색 초기화
        st.rerun()
# 요약도/설정 버튼은 필요시 기존 함수 연결
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# 검색창
search_input = st.text_input("🔍 문제점 검색", value=ss.search_query, 
                             placeholder="단어 입력", label_visibility="collapsed", key="main_search")

if search_input != ss.search_query:
    ss.search_query = search_input
    st.rerun()

# ════════════════════════════════════════
#  5. 화면 출력 (검색 / 메인 / 상세)
# ════════════════════════════════════════
if ss.search_query:
    found = False
    for cat, items in details.items():
        if cat == "__meta__": continue
        for sub, content in items.items():
            text, _ = parse_content(content)
            if ss.search_query in text or ss.search_query in sub:
                found = True
                with st.expander(f"✅ {clean_key(cat)} > {sub}", expanded=True):
                    render_card(content)
    if not found: st.info("검색 결과가 없습니다.")

elif ss.page == 'main':
    # 한 줄에 하나씩 배치 (롤백 완료)
    for cat in DB_KEYS:
        if st.button(clean_key(cat), use_container_width=True):
            ss.selected_main = cat
            ss.page = 'detail'
            st.rerun()

elif ss.page == 'detail':
    cat = ss.selected_main
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("◀ 뒤로가기"): 
        ss.page = 'main'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 헤더에 큰 폰트(render_content) 적용
    st.markdown(f"<div class='cat-header'>📍 {render_content(cat)}</div>", unsafe_allow_html=True)
    
    for sub, content in details[cat].items():
        with st.expander(f"🔎 {sub}", expanded=False): 
            render_card(content)
