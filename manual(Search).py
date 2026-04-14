import streamlit as st
import os, json, base64, html, re, requests
from io import BytesIO
from PIL import Image, ImageOps

# ════════════════════════════════════════
#  설정
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

/* 메뉴 섹션 버튼 (상단 3개) */
.menu-section div.stButton>button{border:1.5px solid #FFD966!important;color:#FFD966!important;
  background:#3A3A3A!important;height:52px!important;font-size:15px!important;border-radius:10px!important}
.menu-section div.stButton>button:hover{background:#FFD966!important;color:#1E1E1E!important}

/* 뒤로가기 버튼 */
.back-btn div.stButton>button{height:36px!important;font-size:14px!important;
  border:1px solid #7CB9E8!important;color:#7CB9E8!important;border-radius:8px!important;
  background:#3A3A3A!important;box-shadow:none!important;margin-bottom:8px!important;
  width:auto!important;padding:0 16px!important}
.back-btn div.stButton>button:hover{background:#7CB9E8!important;color:#1E1E1E!important}

/* 상세 카드 */
.detail-card-content{padding:16px 18px;background:#3E3E3E;border-radius:10px;
  border-left:5px solid #FFD966;font-family:'Nanum Gothic','Malgun Gothic',sans-serif;
  white-space:pre-wrap;word-break:keep-all;font-size:15px;line-height:1.85;color:#E8E8E8}

/* Expander 배경색 고정 */
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
    font-size:15px;
}

/* 입력 필드 스타일 */
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] div[data-baseweb="select"]{background:#444!important;
  color:#E8E8E8!important;border:1px solid #555!important;border-radius:8px!important}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{color:#FFD966!important;border-bottom:2px solid #FFD966!important}
.cat-header{font-size:20px;font-weight:bold;color:#FFD966;margin:6px 0 10px;
  padding-bottom:4px;border-bottom:1px solid #555}
</style>""", unsafe_allow_html=True)

# ════════════════════════════════════════
#  GitHub 연동 및 헬퍼 함수
# ════════════════════════════════════════
# ( load_data, save_data, upload_image 함수 로직 유지 )

FORMATS = [
    (r'\^\^\^(.+?)\^\^\^', r'<span style="font-size:28px;font-weight:bold;color:#FFD966">\1</span>'),
    (r'##(.+?)##',          r'<span style="font-size:22px;font-weight:bold;color:#FFD966">\1</span>'),
    (r'~~(.+?)~~',          r'<span style="font-size:12px;color:#AAA">\1</span>'),
    (r'\*\*\*(.+?)\*\*\*',  r'<strong><em>\1</em></strong>'),
    (r'\*\*(.+?)\*\*',      r'<strong>\1</strong>'),
    (r'\*(.+?)\*',          r'<em>\1</em>'),
    (r'__(.+?)__',          r'<u>\1</u>'),
    (r'!!(.+?)!!',          r'<span style="color:#FF6B6B;font-weight:bold">\1</span>'),
]

def render_content(text: str) -> str:
    s = html.escape(text)
    for pat, rep in FORMATS: s = re.sub(pat, rep, s)
    return s.replace('\n', '<br>')

def clean_key(key: str) -> str:
    # 버튼 텍스트에서 특수 기호 제거
    return re.sub(r'\^\^\^|##', '', key).strip()

def parse_content(content) -> tuple[str, list]:
    if isinstance(content, dict):
        return content.get("text", ""), content.get("images", [])
    return content, []

def render_card(content):
    text, images = parse_content(content)
    st.markdown(f'<div class="detail-card-content">{render_content(text)}</div>', unsafe_allow_html=True)
    for url in images: st.image(url, use_container_width=True)

# ════════════════════════════════════════
#  데이터 & 세션 초기화
# ════════════════════════════════════════
details = load_data()
DB_KEYS = [k for k in list(details.keys()) if k != "__meta__"]

if "page" not in st.session_state: st.session_state.page = "main"
if "search_query" not in st.session_state: st.session_state.search_query = ""

# ════════════════════════════════════════
#  화면 렌더링
# ════════════════════════════════════════
st.markdown("<p class='header-title'>⚡ 설비 유지보수 시스템</p>", unsafe_allow_html=True)

# 상단 메뉴 섹션
st.markdown('<div class="menu-section">', unsafe_allow_html=True)
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    if st.button("🏠 메인"):
        st.session_state.page = 'main'
        st.session_state.search_query = "" # 검색어 초기화
        st.rerun()
# (📋 요약도, ⚙️ 설정 버튼 생략 - 기존 다이얼로그 함수 연결 필요)
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# 검색창
query = st.text_input("🔍 문제점 검색", value=st.session_state.search_query, 
                      placeholder="단어 입력", label_visibility="collapsed", key="search_input")

if query != st.session_state.search_query:
    st.session_state.search_query = query
    st.rerun()

if st.session_state.search_query:
    found = False
    for cat, items in details.items():
        if cat == "__meta__": continue
        for sub, content in items.items():
            text, _ = parse_content(content)
            if st.session_state.search_query in text or st.session_state.search_query in sub:
                found = True
                with st.expander(f"✅ {clean_key(cat)} > {sub}", expanded=True):
                    render_card(content)
    if not found: st.info("검색 결과가 없습니다.")

elif st.session_state.page == 'main':
    # 롤백: 한 줄에 버튼 하나씩 출력
    for cat in DB_KEYS:
        if st.button(clean_key(cat), use_container_width=True):
            st.session_state.selected_main = cat
            st.session_state.page = 'detail'
            st.rerun()

elif st.session_state.page == 'detail':
    cat = st.session_state.selected_main
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("◀  뒤로가기"): 
        st.session_state.page = 'main'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 카테고리 제목 (^^^ 포맷팅 적용)
    st.markdown(f"<div class='cat-header'>📍 {render_content(cat)}</div>", unsafe_allow_html=True)
    for sub, content in details[cat].items():
        with st.expander(f"🔎 {sub}", expanded=False): 
            render_card(content)
