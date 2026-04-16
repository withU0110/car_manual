import streamlit as st
import os, json, base64, html, re, requests
from io import BytesIO
from PIL import Image, ImageOps

# ════════════════════════════════════════
#  설정
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
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}

/* ── 매뉴얼 섹션 타이틀 ── */
.manual-section-title {
    font-size: 28px;
    font-weight: bold;
    color: #FFD966;
    margin: 30px 0 15px 0;
    text-align: left;
}

/* ── 매뉴얼 전용 버튼 스타일 (상단 메뉴와 통일) ── */
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
    background: #FFD966 !important;
    color: #1E1E1E !important;
}

/* ── 기존 UI 스타일 유지 ── */
div.stButton>button{width:100%;font-weight:bold;border-radius:8px;background:#444;
  border:1px solid #555;color:#E8E8E8;transition:.2s}
div.stButton>button:hover{background:#505050;border-color:#FFD966}

.html-menu-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px;}
.html-menu-btn{
  width:100%;height:65px;border:1.5px solid #FFD966;background:#3A3A3A;
  color:#FFD966;font-size:clamp(16px,3.5vw,34px);font-weight:bold;border-radius:10px;cursor:pointer;
}
.html-menu-btn:hover{background:#FFD966;color:#1E1E1E;}

.html-cat-grid{display:grid;grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));gap:10px;margin-top:10px;}
.html-cat-btn{
  width:100%;aspect-ratio:2/1;min-height:100px;border:none;background:#444;
  color:#E8E8E8;font-size:clamp(18px,4vw,40px);font-weight:bold;border-radius:12px;cursor:pointer;
  box-shadow:2px 2px 8px rgba(0,0,0,.4);
}
.html-cat-btn:hover{background:#505050;color:#FFD966;}
</style>""", unsafe_allow_html=True)

# ════════════════════════════════════════
#  GitHub 연동
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
#  팝업 다이얼로그 함수
# ════════════════════════════════════════
@st.dialog("📖 매뉴얼 상세보기", width="large")
def open_manual(title, filename):
    file_url = f"{RAW_BASE}/manuals/{filename}"
    st.write(f"### {title}")
    
    # PDF인 경우 iframe으로 표시
    if filename.lower().endswith('.pdf'):
        pdf_display = f'<iframe src="{file_url}" width="100%" height="800px" style="border:none; border-radius:10px;"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.info("미리보기를 지원하지 않는 파일 형식입니다. 아래 버튼으로 다운로드하세요.")
        res = requests.get(file_url)
        st.download_button("💾 파일 다운로드", data=res.content, file_name=filename)

# ════════════════════════════════════════
#  메인 화면 구성
# ════════════════════════════════════════
details = load_data()
DB_KEYS = list(details.keys())
ss = st.session_state
if "page" not in ss: ss.page = 'main'

# 제목 및 상단 메뉴
st.markdown("<p class='header-title'>철도장비 스마트 관리체계</p>", unsafe_allow_html=True)
st.markdown("""
<div class="html-menu-grid">
  <form action="" method="get"><input type="hidden" name="nav" value="main"><button class="html-menu-btn" type="submit">🏠 메인</button></form>
  <form action="" method="get"><input type="hidden" name="nav" value="summary"><button class="html-menu-btn" type="submit">📋 요약도</button></form>
  <form action="" method="get"><input type="hidden" name="nav" value="admin"><button class="html-menu-btn" type="submit">⚙️ 설정</button></form>
</div>
""", unsafe_allow_html=True)

st.divider()

# 검색 기능
query = st.text_input("🔍 문제점 검색", placeholder="단어 입력", label_visibility="collapsed", key="search_query")

if query:
    # 검색 결과 렌더링 (기존 로직 유지)
    found = False
    for cat, items in details.items():
        if cat == "__meta__": continue
        for sub, content in items.items():
            if query in sub or (isinstance(content, dict) and query in content.get("text", "")):
                found = True
                with st.expander(f"✅ {cat} > {sub}", expanded=True):
                    text = content.get("text", "") if isinstance(content, dict) else content
                    st.write(text)
    if not found: st.info("검색 결과가 없습니다.")

elif ss.page == 'main':
    # ── 1. 기존 4분할 카테고리 그리드 ──
    cat_keys = [k for k in DB_KEYS if k != "__meta__"]
    btns_html = "".join(f'<form action="" method="get"><input type="hidden" name="nav" value="cat:{k}"><button class="html-cat-btn" type="submit">{k}</button></form>' for k in cat_keys)
    st.markdown(f'<div class="html-cat-grid">{btns_html}</div>', unsafe_allow_html=True)

    # ── 2. 관련 업무 매뉴얼 섹션 (요청사항 반영) ──
    st.markdown('<p class="manual-section-title">📂 관련 업무 매뉴얼</p>', unsafe_allow_html=True)
        
    manuals = [
        {"title": "모터카 운전원 일상점검", "file": "daily_inspection.pdf"},
        {"title": "비상시 조치방법", "file": "emergency_manual.pdf"},
        {"title": "모터카 유지보수 매뉴얼", "file": "maintenance_manual.pdf"},
      #{"title": "비상시 대응 절차", "file": "emergency_step.pdf"} 
    ]

    # 한 줄에 2개씩 배치
    for i in range(0, len(manuals), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(manuals):
                m = manuals[i + j]
                # CSS 클래스 적용을 위해 st.markdown 대신 st.button 사용 후 스타일 강제 적용
                if cols[j].button(f"📚 {m['title']}", key=f"m_{i+j}", help="클릭 시 매뉴얼 팝업", use_container_width=True):
                    open_manual(m['title'], m['file'])
                # 버튼 스타일 강제 주입
                st.markdown(f"""<style>div[data-testid="stColumn"]:nth-of-type({j+1}) button[key="m_{i+j}"] {{ border: 1.5px solid #FFD966 !important; color: #FFD966 !important; background: #3A3A3A !important; height: 60px !important; font-size: 20px !important; font-weight: bold !important; border-radius: 10px !important; }}</style>""", unsafe_allow_html=True)

elif ss.page == 'detail':
    # 상세 페이지 (기존 로직 유지)
    cat = ss.get("selected_main")
    if st.button("◀ 뒤로가기"): 
        ss.page = 'main'
        st.rerun()
    st.subheader(f"📍 {cat}")
    # ... 상세 내용 루프 ...

# 쿼리 파라미터 처리
qp = st.query_params
if "nav" in qp:
    nav = qp["nav"]
    if nav == "main": ss.page = "main"
    elif nav.startswith("cat:"):
        ss.selected_main = nav[4:]; ss.page = "detail"
    st.query_params.clear()
    st.rerun()
