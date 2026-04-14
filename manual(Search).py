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
.block-container{padding:4rem 1rem 1rem !important;background:#333}

/* 상단 메인 제목 폰트 사이즈 (45px) */
.header-title{font-size:45px!important;font-weight:bold;color:#FFD966;text-align:center;
  margin-top:10px;margin-bottom:20px;letter-spacing:2px;text-shadow:0 2px 5px rgba(0,0,0,.6)}

/* 공통 버튼 디자인 (다이얼로그 내 작은 버튼들 붕괴 방지) */
div.stButton>button{width:100%;font-weight:bold;border-radius:8px;background:#444!important;
  border:1px solid #555!important;color:#E8E8E8!important;transition:.2s}
div.stButton>button:hover{background:#505050!important;border-color:#FFD966!important;}

/* 1. 하단 계통(메인 카테고리) 버튼 - 폰트 강제 적용(p, span) */
.category-section div.stButton>button {
  height:80px; border-radius:12px; box-shadow:2px 2px 8px rgba(0,0,0,.4); margin-bottom:8px;
}
.category-section div.stButton>button p, .category-section div.stButton>button span {
  font-size:40px!important; font-weight:bold!important; color:#E8E8E8!important;
}
.category-section div.stButton>button:hover p, .category-section div.stButton>button:hover span {
  color:#FFD966!important;
}

/* 2. 상단 메뉴(메인/요약도/설정) 버튼 - 폰트 강제 적용(p, span) */
.menu-section div.stButton>button {
  border:1.5px solid #FFD966!important; background:#3A3A3A!important;
  height:70px!important; border-radius:10px!important;
}
.menu-section div.stButton>button p, .menu-section div.stButton>button span {
  font-size:40px!important; color:#FFD966!important;
}
.menu-section div.stButton>button:hover {background:#FFD966!important;}
.menu-section div.stButton>button:hover p, .menu-section div.stButton>button:hover span {
  color:#1E1E1E!important;
}

/* 3. 뒤로가기 버튼 유지 */
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

/* 상세 내용 카드 내용 폰트 크기 */
.detail-card-content{padding:16px 18px;background:#3E3E3E;border-radius:10px;
  border-left:5px solid #FFD966;font-family:'Nanum Gothic','Malgun Gothic',sans-serif;
  white-space:pre-wrap;word-break:keep-all;font-size:20px;line-height:1.85;color:#E8E8E8}

/* 세부 항목(안내륜/안정륜) 제목 크기 (40px) */
[data-testid="stExpander"]{background:#3A3A3A!important;border:1px solid #4A4A4A!important;
  border-radius:10px!important;margin-bottom:6px}
[data-testid="stExpander"] summary{color:#E8E8E8!important;font-weight:bold;font-size:40px!important; padding:15px!}
[data-testid="stExpander"] summary:hover,
[data-testid="stExpander"] summary:focus,
[data-testid="stExpander"] summary:active {
  color:#E8E8E8 !important; outline:none !important; border:none !important; background:transparent !important;
}
[data-testid="stExpander"] summary:hover p,
[data-testid="stExpander"] summary:focus p,
[data-testid="stExpander"] summary:active p { color:#E8E8E8 !important; }

/* 기타 UI 설정 */
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] div[data-baseweb="select"]{background:#444!important;
  color:#E8E8E8!important;border:1px solid #555!important;border-radius:8px!important;font-size:20px!important}
[data-testid="stTextInput"] input::placeholder{color:#999!important}
[data-testid="stTextInput"] label,[data-testid="stTextArea"] label,
[data-testid="stSelectbox"] label{color:#BBB!important;font-size:18px!important}
[data-testid="stTabs"] [role="tab"]{color:#BBB!important;font-size:18px}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{color:#FFD966!important;border-bottom:2px solid #FFD966!important}
hr{border-color:#4A4A4A!important}
[data-testid="stNotification"]{border-radius:8px!important}
.stCaption,[data-testid="stCaptionContainer"]{color:#AAA!important}

/* 상세 화면 상단 카테고리 제목 (40px) */
.cat-header{font-size:40px;font-weight:bold;color:#FFD966;margin:6px 0 15px;
  padding-bottom:8px;border-bottom:1px solid #555}
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
    st.error(f"data.json 불러오기 실패: {res.status_code}")
    return {}

def save_data(data: dict) -> bool:
    res = requests.get(API_URL, headers=HEADERS)
    if res.status_code != 200:
        st.error("저장 실패: SHA를 가져올 수 없습니다."); return False
    payload = {
        "message": "Update data.json via Streamlit app",
        "content": base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode()).decode(),
        "sha": res.json()["sha"]
    }
    put = requests.put(API_URL, headers=HEADERS, json=payload)
    if put.status_code in (200, 201):
        st.cache_data.clear(); return True
    st.error(f"저장 실패: {put.status_code} {put.text}"); return False

def compress_image(img_file, max_px=1200, quality=85) -> tuple[bytes, str]:
    img = Image.open(img_file)
    try: img = ImageOps.exif_transpose(img)
    except Exception: pass
    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > max_px:
        r = max_px / max(w, h)
        img = img.resize((int(w*r), int(h*r)), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue(), f"{os.path.splitext(img_file.name)[0]}.jpg"

def upload_image(img_file) -> str | None:
    data, filename = compress_image(img_file)
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/images/{filename}"
    chk = requests.get(url, headers=HEADERS)
    payload = {"message": f"Upload image: {filename}",
               "content": base64.b64encode(data).decode()}
    if chk.status_code == 200: payload["sha"] = chk.json()["sha"]
    res = requests.put(url, headers=HEADERS, json=payload)
    if res.status_code in (200, 201): return f"{RAW_BASE}/images/{filename}"
    st.error(f"이미지 업로드 실패 ({filename}): {res.status_code}"); return None

# ════════════════════════════════════════
#  헬퍼 함수 & 콜백 함수
# ════════════════════════════════════════
FORMATS = [
    (r'(?m)^### (.+)$', r'<span style="font-size:26px !important;font-weight:bold;color:#FFD966">\1</span>'),
    (r'(?m)^## (.+)$',  r'<span style="font-size:30px !important;font-weight:bold;color:#FFD966">\1</span>'),
    (r'(?m)^# (.+)$',   r'<span style="font-size:34px !important;font-weight:bold;color:#FFD966">\1</span>'),
    (r'\^\^\^(.+?)\^\^\^', r'<span style="font-size:34px !important;font-weight:bold;color:#FFD966">\1</span>'),
    (r'##(.+?)##',          r'<span style="font-size:28px !important;font-weight:bold;color:#FFD9
