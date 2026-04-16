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

/* ── 관련 업무 매뉴얼 섹션 스타일 ── */
.manual-box {
    border: 2px solid #555;
    border-radius: 12px;
    padding: 25px;
    background-color: #2D2D2D;
    margin-top: 15px;
    text-align: center;
}
.manual-title {
    font-size: 28px;
    font-weight: bold;
    color: #FFD966;
    margin-bottom: 20px;
    display: block;
}

/* ── 공통 Streamlit 버튼 ── */
div.stButton>button{width:100%;font-weight:bold;border-radius:8px;background:#444!important;
  border:1px solid #555!important;color:#E8E8E8!important;transition:.2s}
div.stButton>button:hover{background:#505050!important;border-color:#FFD966!important;}

/* ── 다운로드 버튼 전용 스타일 (매뉴얼 섹션 내) ── */
div.stDownloadButton>button {
    background: #3A3A3A !important;
    border: 1px solid #7CB9E8 !important;
    color: #7CB9E8 !important;
    height: 55px !important;
    font-size: 18px !important;
}
div.stDownloadButton>button:hover {
    background: #7CB9E8 !important;
    color: #1E1E1E !important;
}

/* ── 뒤로가기 버튼 ── */
.back-btn div.stButton>button {
  height:45px!important; border:1px solid #7CB9E8!important;
  border-radius:8px!important; background:#3A3A3A!important;
  box-shadow:none!important; margin-bottom:8px!important; width:auto!important; padding:0 20px!important;
}
.back-btn div.stButton>button p, .back-btn div.stButton>button span {
  font-size:20px!important; color:#7CB9E8!important;
}
.back-btn div.stButton>button:hover {background:#7CB9E8!important;}
.back-btn div.stButton>button:hover p, .back-btn div.stButton>button:hover span {
  color:#1E1E1E!important;
}

/* ── 상세 내용 카드 ── */
.detail-card-content{padding:16px 18px;background:#3E3E3E;border-radius:10px;
  border-left:5px solid #FFD966;font-family:'Nanum Gothic','Malgun Gothic',sans-serif;
  white-space:pre-wrap;word-break:keep-all;font-size:20px;line-height:1.85;color:#E8E8E8}

/* ── Expander ── */
[data-testid="stExpander"]{background:#3A3A3A!important;border:1px solid #4A4A4A!important;
  border-radius:10px!important;margin-bottom:6px}
[data-testid="stExpander"] summary{color:#E8E8E8!important;font-weight:bold;font-size:40px!important;padding:15px!important}

/* ── 상세 화면 카테고리 제목 ── */
.cat-header{font-size:40px;font-weight:bold;color:#FFD966;margin:6px 0 15px;
  padding-bottom:8px;border-bottom:1px solid #555}

/* ── 메뉴 버튼 그리드 ── */
.html-menu-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px;}
.html-menu-grid form{margin:0;padding:0;}
.html-menu-btn{
  width:100%;height:65px;border:1.5px solid #FFD966;background:#3A3A3A;
  color:#FFD966;font-size:clamp(16px,3.5vw,34px);font-weight:bold;border-radius:10px;cursor:pointer;
  transition:.2s;white-space:nowrap;
}
.html-menu-btn:hover{background:#FFD966;color:#1E1E1E;}

/* ── 카테고리 그리드 ── */
.html-cat-grid{display:grid;grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));gap:10px;margin-top:10px;}
.html-cat-grid form{margin:0;padding:0;}
.html-cat-btn{
  width:100%;aspect-ratio:2/1;min-height:100px;border:none;background:#444;
  color:#E8E8E8;font-size:clamp(18px,4vw,40px);font-weight:bold;border-radius:12px;cursor:pointer;
  box-shadow:2px 2px 8px rgba(0,0,0,.4);transition:.2s;
}
.html-cat-btn:hover{background:#505050;color:#FFD966;}
</style>""", unsafe_allow_html=True)

# ════════════════════════════════════════
#  GitHub 연동
# ════════════════════════════════════════
GITHUB_TOKEN     = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO      = st.secrets["GITHUB_REPO"]
GITHUB_FILE_PATH = st.secrets["GITHUB_FILE_PATH"]
API_URL  = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main"
HEADERS  = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

@st.cache_data(ttl=60)
def load_data():
    res = requests.get(API_URL, headers=HEADERS)
    if res.status_code == 200:
        return json.loads(base64.b64decode(res.json()["content"]).decode())
    return {}

def save_data(data: dict) -> bool:
    res = requests.get(API_URL, headers=HEADERS)
    if res.status_code != 200: return False
    payload = {
        "message": "Update data.json",
        "content": base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode()).decode(),
        "sha": res.json()["sha"]
    }
    put = requests.put(API_URL, headers=HEADERS, json=payload)
    return put.status_code in (200, 201)

# ════════════════════════════════════════
#  헬퍼 함수
# ════════════════════════════════════════
FORMATS = [
    (r'(?m)^### (.+)$', r'<span style="font-size:26px !important;font-weight:bold;color:#FFD966">\1</span>'),
    (r'(?m)^## (.+)$',  r'<span style="font-size:30px !important;font-weight:bold;color:#FFD966">\1</span>'),
    (r'(?m)^# (.+)$',   r'<span style="font-size:34px !important;font-weight:bold;color:#FFD966">\1</span>'),
    (r'!!(.+?)!!',      r'<span style="color:#FF6B6B !important;font-weight:bold">\1</span>'),
]

def render_content(text: str) -> str:
    s = html.escape(text)
    for pat, rep in FORMATS: s = re.sub(pat, rep, s)
    return s.replace('\n', '<br>')

def clean_key(key: str) -> str:
    s = re.sub(r'\^\^\^(.+?)\^\^\^|##(.+?)##|^#+\s*', r'\1\2', key)
    return s.strip()

def parse_content(content) -> tuple[str, list]:
    if isinstance(content, dict): return content.get("text", ""), content.get("images", [])
    return content, []

def render_card(content):
    text, images = parse_content(content)
    st.markdown(f'<div class="detail-card-content">{render_content(text)}</div>', unsafe_allow_html=True)
    for url in images: st.image(url, use_container_width=True)

# ════════════════════════════════════════
#  메인 로직
# ════════════════════════════════════════
details = load_data()
DB_KEYS = list(details.keys())

ss = st.session_state
if "page" not in ss: ss.page = 'main'
if "search_query" not in ss: ss.search_query = ""

# 상단 제목 및 메뉴
st.markdown("<p class='header-title'>철도장비 스마트 관리체계</p>", unsafe_allow_html=True)
st.markdown("""
<div class="html-menu-grid">
  <form action="" method="get"><input type="hidden" name="nav" value="main"><button class="html-menu-btn" type="submit">🏠 메인</button></form>
  <form action="" method="get"><input type="hidden" name="nav" value="summary"><button class="html-menu-btn" type="submit">📋 요약도</button></form>
  <form action="" method="get"><input type="hidden" name="nav" value="admin"><button class="html-menu-btn" type="submit">⚙️ 설정</button></form>
</div>
""", unsafe_allow_html=True)

st.divider()

# 검색창
query = st.text_input("🔍 문제점 검색", placeholder="단어 입력", label_visibility="collapsed", key="search_query")

if query:
    found = False
    for cat, items in details.items():
        if cat == "__meta__": continue
        for sub, content in items.items():
            text, _ = parse_content(content)
            if query in text or query in sub:
                found = True
                with st.expander(f"✅ {clean_key(cat)} > {sub}", expanded=True): render_card(content)
    if not found: st.info("검색 결과가 없습니다.")

elif ss.page == 'main':
    # 카테고리 그리드
    cat_keys = [k for k in DB_KEYS if k != "__meta__"]
    btns_html = "".join(f'<form action="" method="get"><input type="hidden" name="nav" value="cat:{k}"><button class="html-cat-btn" type="submit">{clean_key(k)}</button></form>' for k in cat_keys)
    st.markdown(f'<div class="html-cat-grid">{btns_html}</div>', unsafe_allow_html=True)

    # ── 추가된 섹션: 관련 업무 매뉴얼 ──
    st.divider()
    st.markdown('<div class="manual-box">', unsafe_allow_html=True)
    st.markdown('<span class="manual-title">📚 관련 업무 매뉴얼</span>', unsafe_allow_html=True)
    
    # 다운로드할 파일 정보 (버튼이름: 실제파일명)
    # 깃허브 저장소의 /manuals/ 폴더 안에 파일을 넣는다고 가정합니다.
    manual_files = {
        "📘 유지보수 매뉴얼": "maintenance_manual.pdf",
        "📙 비상시 조치방법": "emergency_manual.pdf",
        "📗 운전원 일상점검": "daily_inspection.pdf"
    }
    
    m_cols = st.columns(len(manual_files))
    for idx, (label, filename) in enumerate(manual_files.items()):
        with m_cols[idx]:
            file_url = f"{RAW_BASE}/manuals/{filename}"
            try:
                # 파일 데이터를 가져와서 버튼에 연결
                res = requests.get(file_url)
                if res.status_code == 200:
                    st.download_button(label=label, data=res.content, file_name=filename, key=f"btn_dl_{idx}")
                else:
                    st.button(f"❌ {filename} 없음", disabled=True, key=f"err_{idx}")
            except:
                st.button("⚠️ 연결 오류", disabled=True, key=f"err_conn_{idx}")
                
    st.markdown('</div>', unsafe_allow_html=True)

elif ss.page == 'detail':
    cat = ss.selected_main
    if st.button("◀  뒤로가기"): ss.page = 'main'; st.rerun()
    st.markdown(f"<div class='cat-header'>📍 {clean_key(cat)}</div>", unsafe_allow_html=True)
    for sub, content in details[cat].items():
        with st.expander(f"🔎 {sub}", expanded=False): render_card(content)

# 쿼리 파라미터 처리 (페이지 전환용)
qp = st.query_params
if "nav" in qp:
    nav = qp["nav"]
    if nav == "main": ss.page = "main"
    elif nav.startswith("cat:"):
        ss.selected_main = nav[4:]; ss.page = "detail"
    st.query_params.clear()
    st.rerun()
