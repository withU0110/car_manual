import streamlit as st
import os, json, base64, html, re, requests
from io import BytesIO

# ════════════════════════════════════════
#  설정 및 스타일
# ════════════════════════════════════════
st.set_page_config(page_title="철도장비 스마트 관리체계", layout="wide")

st.markdown("""<style>
.stApp,[data-testid="stAppViewContainer"]{background:#333;color:#E8E8E8}
[data-testid="stHeader"],[data-testid="stSidebar"]{background:#2A2A2A}
.block-container{padding:4rem 1rem 1rem !important;background:#333}

/* ── 제목 ── */
.header-title{
  font-weight:bold;color:#FFD966;text-align:center;
  margin-top:9px;margin-bottom:20px;letter-spacing:2px;
  text-shadow:0 2px 5px rgba(0,0,0,.6);
  font-size:clamp(20px, 5vw, 45px)!important;
}

/* ── 관련 업무 매뉴얼 타이틀 ── */
.manual-section-title {
    font-size: 28px;
    font-weight: bold;
    color: #FFD966;
    margin: 30px 0 15px 0;
}

/* ── 메뉴 및 매뉴얼 버튼 스타일 (반전 제거 버전) ── */
/* 상단 메인 메뉴용 스타일 */
.html-menu-btn {
  width:100%; height:65px; border:1.5px solid #FFD966; background:#3A3A3A;
  color:#FFD966; font-size:clamp(16px,3.5vw,28px); font-weight:bold; border-radius:10px; cursor:pointer;
  transition:.2s;
}
.html-menu-btn:hover { background:#FFD966; color:#1E1E1E; }

/* 매뉴얼 버튼용 전용 스타일 (색상 반전 없음) */
div.stButton > button.manual-btn-style {
    width: 100%;
    height: 60px !important;
    border: 1.5px solid #FFD966 !important;
    background: #3A3A3A !important;
    color: #FFD966 !important;
    font-size: 20px !important;
    font-weight: bold !important;
    border-radius: 10px !important;
    transition: 0.2s;
}
div.stButton > button.manual-btn-style:hover {
    border-color: #FFF !important; /* 호버 시 테두리만 밝게 */
    background: #3A3A3A !important; /* 배경색 유지 */
    color: #FFD966 !important;    /* 글자색 유지 */
}

/* ── 카테고리 그리드 ── */
.html-cat-grid{display:grid;grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));gap:10px;margin-top:10px;}
.html-cat-btn{
  width:100%;aspect-ratio:2/1;min-height:100px;border:none;background:#444;
  color:#E8E8E8;font-size:clamp(18px,4vw,32px);font-weight:bold;border-radius:12px;cursor:pointer;
}
.html-cat-btn:hover{background:#505050;color:#FFD966;}

/* 팝업 내 버튼 스타일 */
.popup-link {
    display: inline-block;
    padding: 10px 20px;
    background-color: #FFD966;
    color: #1E1E1E;
    text-decoration: none;
    font-weight: bold;
    border-radius: 5px;
    margin-bottom: 15px;
}
</style>""", unsafe_allow_html=True)

# ════════════════════════════════════════
#  GitHub 연동 및 데이터 로드
# ════════════════════════════════════════
GITHUB_TOKEN     = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO      = st.secrets["GITHUB_REPO"]
GITHUB_FILE_PATH = st.secrets["GITHUB_FILE_PATH"]
RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main"
API_URL  = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
HEADERS  = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

@st.cache_data(ttl=60)
def load_data():
    res = requests.get(API_URL, headers=HEADERS)
    if res.status_code == 200:
        return json.loads(base64.b64decode(res.json()["content"]).decode())
    return {}

# ════════════════════════════════════════
#  팝업 다이얼로그 (모바일 호환성 강화)
# ════════════════════════════════════════
@st.dialog("📄 매뉴얼 확인", width="large")
def open_manual(title, filename):
    file_url = f"{RAW_BASE}/manuals/{filename}"
    st.markdown(f"### {title}")
    st.write("모바일 및 일부 브라우저에서는 아래 버튼을 이용해 확인해 주세요.")
    
    col1, col2 = st.columns(2)
    with col1:
        # 1. 새창에서 보기 (모바일은 이 방식이 가장 안정적임)
        st.markdown(f'<a href="{file_url}" target="_blank" class="popup-link">🔗 새창에서 보기 (뷰어)</a>', unsafe_allow_html=True)
    with col2:
        # 2. 파일 직접 다운로드
        try:
            file_res = requests.get(file_url)
            st.download_button("💾 파일 직접 다운로드", data=file_res.content, file_name=filename)
        except:
            st.error("파일을 불러올 수 없습니다.")

    st.divider()
    
    # 데스크탑 사용자를 위한 미리보기 (모바일에서는 안 보일 수 있음)
    if filename.lower().endswith('.pdf'):
        pdf_display = f'<iframe src="{file_url}" width="100%" height="600px" style="border:1px solid #555;"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

# ════════════════════════════════════════
#  메인 페이지 레이아웃
# ════════════════════════════════════════
details = load_data()
DB_KEYS = list(details.keys())
ss = st.session_state
if "page" not in ss: ss.page = 'main'

# 상단 제목 및 공통 메뉴
st.markdown("<p class='header-title'>철도장비 스마트 관리체계</p>", unsafe_allow_html=True)
st.markdown(f"""
<div class="html-menu-grid">
  <form action="" method="get"><input type="hidden" name="nav" value="main"><button class="html-menu-btn" type="submit">🏠 메인</button></form>
  <form action="" method="get"><input type="hidden" name="nav" value="summary"><button class="html-menu-btn" type="submit">📋 요약도</button></form>
  <form action="" method="get"><input type="hidden" name="nav" value="admin"><button class="html-menu-btn" type="submit">⚙️ 설정</button></form>
</div>
""", unsafe_allow_html=True)

st.divider()

if ss.page == 'main':
    # 검색창
    query = st.text_input("🔍 문제점 검색", placeholder="단어 입력", label_visibility="collapsed")
    
    if query:
        # 검색 결과 렌더링 (기본 검색 로직)
        found = False
        for cat, items in details.items():
            if cat == "__meta__": continue
            for sub, content in items.items():
                if query in sub:
                    found = True
                    with st.expander(f"✅ {cat} > {sub}", expanded=True):
                        st.write(content)
        if not found: st.info("검색 결과가 없습니다.")
    else:
        # 1. 4분할 카테고리 그리드
        cat_keys = [k for k in DB_KEYS if k != "__meta__"]
        btns_html = "".join(f'<form action="" method="get"><input type="hidden" name="nav" value="cat:{k}"><button class="html-cat-btn" type="submit">{k}</button></form>' for k in cat_keys)
        st.markdown(f'<div class="html-cat-grid">{btns_html}</div>', unsafe_allow_html=True)

        # 2. 관련 업무 매뉴얼 (구분선 + 2열 구성 + 반전 제거)
        st.divider()
        st.markdown('<p class="manual-section-title">📂 관련 업무 매뉴얼</p>', unsafe_allow_html=True)
        
        # 파일 리스트 (필요에 따라 수정)
        manual_list = [
            {"title": "유지보수 매뉴얼", "file": "maintenance_manual.pdf"},
            {"title": "비상시 조치방법", "file": "emergency_manual.pdf"},
            {"title": "운전원 일상점검", "file": "daily_inspection.pdf"},
            {"title": "안전 수칙 가이드", "file": "safety_guide.pdf"}
        ]

        for i in range(0, len(manual_list), 2):
            m_cols = st.columns(2)
            for j in range(2):
                if i + j < len(manual_list):
                    item = manual_list[i + j]
                    # 스타일 클래스를 적용한 버튼 생성
                    if m_cols[j].button(f"📖 {item['title']}", key=f"man_{i+j}", use_container_width=True):
                        open_manual(item['title'], item['file'])
                    
                    # 수동 스타일 주입 (반전 효과 제거 및 테두리 설정)
                    st.markdown(f"""
                        <style>
                        div[data-testid="stColumn"]:nth-of-type({j+1}) button[key="man_{i+j}"] {{
                            border: 1.5px solid #FFD966 !important;
                            color: #FFD966 !important;
                            background: #3A3A3A !important;
                            height: 60px !important;
                            font-size: 18px !important;
                            font-weight: bold !important;
                        }}
                        div[data-testid="stColumn"]:nth-of-type({j+1}) button[key="man_{i+j}"]:hover {{
                            border-color: #FFF !important;
                            background: #3A3A3A !important;
                            color: #FFD966 !important;
                        }}
                        </style>
                    """, unsafe_allow_html=True)

# 페이지 전환 로직
qp = st.query_params
if "nav" in qp:
    nav = qp["nav"]
    if nav == "main": ss.page = "main"
    elif nav.startswith("cat:"):
        ss.selected_main = nav[4:]; ss.page = "detail"
    st.query_params.clear()
    st.rerun()
