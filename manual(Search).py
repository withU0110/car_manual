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

/* ── 제목: 항상 한 줄, 화면 너비에 맞게 폰트 자동 축소 ── */
.header-title{
  font-weight:bold;color:#FFD966;text-align:center;
  margin-top:10px;margin-bottom:20px;letter-spacing:2px;
  text-shadow:0 2px 5px rgba(0,0,0,.6);
  font-size:clamp(20px, 5vw, 45px)!important;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}

/* ── 공통 Streamlit 버튼 (다이얼로그 내부용) ── */
div.stButton>button{width:100%;font-weight:bold;border-radius:8px;background:#444!important;
  border:1px solid #555!important;color:#E8E8E8!important;transition:.2s}
div.stButton>button:hover{background:#505050!important;border-color:#FFD966!important;}

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
[data-testid="stExpander"] summary:hover,
[data-testid="stExpander"] summary:focus,
[data-testid="stExpander"] summary:active {
  color:#E8E8E8!important;outline:none!important;border:none!important;background:transparent!important;
}
[data-testid="stExpander"] summary:hover p,
[data-testid="stExpander"] summary:focus p,
[data-testid="stExpander"] summary:active p { color:#E8E8E8!important; }

/* ── 기타 UI ── */
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

/* ── 상세 화면 카테고리 제목 ── */
.cat-header{font-size:40px;font-weight:bold;color:#FFD966;margin:6px 0 15px;
  padding-bottom:8px;border-bottom:1px solid #555}

/* ════════════════════════════════════════
   순수 HTML 메뉴 버튼 그리드 (3열, 항상 한 줄)
   ════════════════════════════════════════ */
.html-menu-grid{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:10px;
  margin-bottom:14px;
}
.html-menu-grid form{margin:0;padding:0;}
.html-menu-btn{
  width:100%;height:65px;
  border:1.5px solid #FFD966;background:#3A3A3A;
  color:#FFD966;font-size:clamp(16px,3.5vw,34px);
  font-weight:bold;border-radius:10px;cursor:pointer;
  transition:.2s;white-space:nowrap;
}
.html-menu-btn:hover{background:#FFD966;color:#1E1E1E;}

/* ════════════════════════════════════════
   순수 HTML 카테고리 4분할 그리드 (십자가)
   ════════════════════════════════════════ */
.html-cat-grid{
  display:grid;
  grid-template-columns:repeat(2,1fr);
  grid-template-rows:repeat(2,1fr);
  gap:10px;
  margin-top:10px;
}
.html-cat-grid form{margin:0;padding:0;}
.html-cat-btn{
  width:100%;
  aspect-ratio:2/1;
  min-height:100px;
  border:none;background:#444;
  color:#E8E8E8;font-size:clamp(18px,4vw,40px);
  font-weight:bold;border-radius:12px;cursor:pointer;
  box-shadow:2px 2px 8px rgba(0,0,0,.4);
  transition:.2s;
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
    (r'##(.+?)##',          r'<span style="font-size:28px !important;font-weight:bold;color:#FFD966">\1</span>'),
    (r'~~(.+?)~~',          r'<span style="font-size:16px !important;color:#AAA">\1</span>'),
    (r'\*\*\*(.+?)\*\*\*',  r'<strong><em>\1</em></strong>'),
    (r'\*\*(.+?)\*\*',      r'<strong>\1</strong>'),
    (r'\*(.+?)\*',          r'<em>\1</em>'),
    (r'__(.+?)__',          r'<u>\1</u>'),
    (r'!!(.+?)!!',          r'<span style="color:#FF6B6B !important;font-weight:bold">\1</span>'),
]

def render_content(text: str) -> str:
    s = html.escape(text)
    for pat, rep in FORMATS: s = re.sub(pat, rep, s)
    return s.replace('\n', '<br>')

def clean_key(key: str) -> str:
    s = re.sub(r'\^\^\^(.+?)\^\^\^', r'\1', key)
    s = re.sub(r'##(.+?)##', r'\1', s)
    s = re.sub(r'^#+\s*', '', s)
    return s.strip()

def parse_content(content) -> tuple[str, list]:
    if isinstance(content, dict):
        return content.get("text", ""), content.get("images", [])
    return content, []

def render_card(content):
    text, images = parse_content(content)
    st.markdown(f'<div class="detail-card-content">{render_content(text)}</div>',
                unsafe_allow_html=True)
    for url in images: st.image(url, use_container_width=True)

def go_to_main():
    st.session_state.page = 'main'
    st.session_state.search_query = ""

# ════════════════════════════════════════
#  데이터 & 세션 초기화
# ════════════════════════════════════════
details = load_data()
DB_KEYS = list(details.keys())

ss = st.session_state
for k, v in [("page","main"), ("deleted_img_indices",set()), ("admin_last_key",""), ("search_query", "")]:
    if k not in ss: ss[k] = v

# ════════════════════════════════════════
#  비밀번호
# ════════════════════════════════════════
DEFAULT_PW = "7895"

def get_pw() -> str:
    return details.get("__meta__", {}).get("password", DEFAULT_PW)

def save_pw(new_pw: str) -> bool:
    details.setdefault("__meta__", {})["password"] = new_pw
    return save_data(details)

# ════════════════════════════════════════
#  다이얼로그
# ════════════════════════════════════════
@st.dialog("🔐 관리자 모드")
def admin_dialog():
    pw = st.text_input("비밀번호", type="password")
    if pw and pw != get_pw(): st.error("비밀번호가 틀렸습니다."); return
    if not pw: return

    tab_edit, tab_pw = st.tabs(["📝 내용 편집", "🔑 비밀번호 변경"])

    with tab_edit:
        edit_keys   = [k for k in DB_KEYS if k != "__meta__"]
        label_map   = {clean_key(k): k for k in edit_keys}
        t_main      = label_map[st.selectbox("계통", list(label_map), key="admin_main")]
        t_sub       = st.selectbox("항목", list(details[t_main]), key="admin_sub")
        cur_key     = f"{t_main}::{t_sub}"

        if ss.admin_last_key != cur_key:
            ss.deleted_img_indices = set()
            ss.admin_last_key = cur_key

        cur_text, cur_imgs = parse_content(details[t_main][t_sub])
        new_text = st.text_area("내용 수정", value=cur_text, height=200,
                                key=f"ta__{cur_key}")

        st.markdown("**📎 현재 첨부 이미지**")
        for idx, url in enumerate(cur_imgs):
            deleted = idx in ss.deleted_img_indices
            c1, c2 = st.columns([5, 1])
            with c1:
                if deleted: st.markdown(f"<s style='color:#888;font-size:12px'>{url.split('/')[-1]} (삭제 예정)</s>", unsafe_allow_html=True)
                else: st.image(url, use_container_width=True)
            with c2:
                if deleted:
                    if st.button("↩️", key=f"restore_{idx}"): ss.deleted_img_indices.discard(idx)
                else:
                    if st.button("🗑️", key=f"del_{idx}"): ss.deleted_img_indices.add(idx)
        if not cur_imgs: st.caption("첨부된 이미지가 없습니다.")

        st.markdown("**➕ 이미지 추가 업로드**")
        new_imgs = st.file_uploader("이미지 선택 (png/jpg/jpeg)", type=["png","jpg","jpeg"],
                                    accept_multiple_files=True, key=f"uploader__{cur_key}")

        if st.button("💾 저장 (GitHub 반영)", key="btn_save"):
            kept = [u for i, u in enumerate(cur_imgs) if i not in ss.deleted_img_indices]
            uploaded = []
            if new_imgs:
                with st.spinner("이미지 업로드 중..."):
                    uploaded = [u for f in new_imgs if (u := upload_image(f))]
            all_imgs = kept + uploaded
            details[t_main][t_sub] = {"text": new_text, "images": all_imgs} if all_imgs else new_text
            if save_data(details):
                ss.deleted_img_indices = set()
                st.success("저장 완료!")

    with tab_pw:
        st.markdown("현재 비밀번호로 인증된 상태입니다.")
        p1 = st.text_input("새 비밀번호", type="password", key="new_pw1")
        p2 = st.text_input("새 비밀번호 확인", type="password", key="new_pw2")
        if st.button("🔒 비밀번호 변경", key="btn_change_pw"):
            if not p1:              st.error("새 비밀번호를 입력해 주세요.")
            elif p1 != p2:          st.error("비밀번호가 일치하지 않습니다.")
            elif p1 == get_pw():    st.warning("현재 비밀번호와 동일합니다.")
            elif save_pw(p1):       st.success("변경 완료. 다음 로그인부터 적용됩니다.")

@st.dialog("📋 전체 요약도")
def summary_dialog():
    res = requests.get(f"{RAW_BASE}/summary.png")
    if res.status_code == 200:
        img_bytes = res.content
    elif os.path.exists("summary.png"):
        img_bytes = open("summary.png", "rb").read()
    else:
        st.error("summary.png를 찾을 수 없습니다.")
        st.info("GitHub 저장소 루트에 summary.png를 업로드해 주세요."); return
    st.image(img_bytes, use_container_width=True)
    st.download_button("⬇️ 이미지 다운로드", img_bytes, "summary.png", "image/png",
                       use_container_width=True)

# ════════════════════════════════════════
#  화면 렌더링
# ════════════════════════════════════════

# ── query_params로 HTML 버튼 클릭 처리 ──
qp = st.query_params
if "nav" in qp:
    nav = qp["nav"]
    if nav == "main":
        ss.page = "main"; ss.search_query = ""
    elif nav == "summary":
        st.query_params.clear(); summary_dialog()
    elif nav == "admin":
        st.query_params.clear(); admin_dialog()
    elif nav.startswith("cat:"):
        cat_key = nav[4:]
        if cat_key in details:
            ss.selected_main = cat_key; ss.page = "detail"
    st.query_params.clear()

# ── 제목 ──
st.markdown("<p class='header-title'>⚡ 설비 유지보수 시스템</p>", unsafe_allow_html=True)

# ── 상단 메뉴: HTML 3열 그리드 (항상 한 줄) ──
st.markdown("""
<div class="html-menu-grid">
  <form action="" method="get">
    <input type="hidden" name="nav" value="main">
    <button class="html-menu-btn" type="submit">🏠 메인</button>
  </form>
  <form action="" method="get">
    <input type="hidden" name="nav" value="summary">
    <button class="html-menu-btn" type="submit">📋 요약도</button>
  </form>
  <form action="" method="get">
    <input type="hidden" name="nav" value="admin">
    <button class="html-menu-btn" type="submit">⚙️ 설정</button>
  </form>
</div>
""", unsafe_allow_html=True)

st.divider()

query = st.text_input("🔍 문제점 검색", placeholder="단어 입력", label_visibility="collapsed", key="search_query")

if query:
    found = False
    for cat, items in details.items():
        if cat == "__meta__": continue
        for sub, content in items.items():
            text, _ = parse_content(content)
            if query in text or query in sub:
                found = True
                with st.expander(f"✅ {clean_key(cat)} > {sub}", expanded=True):
                    render_card(content)
    if not found: st.info("검색 결과가 없습니다.")

elif ss.page == 'main':
    # ── 카테고리 4분할 HTML 그리드 ──
    cat_keys = [k for k in DB_KEYS if k != "__meta__"]
    btns_html = "".join(
        f'<form action="" method="get">'
        f'<input type="hidden" name="nav" value="cat:{k}">'
        f'<button class="html-cat-btn" type="submit">{clean_key(k)}</button>'
        f'</form>'
        for k in cat_keys
    )
    st.markdown(f'<div class="html-cat-grid">{btns_html}</div>', unsafe_allow_html=True)

elif ss.page == 'detail':
    cat = ss.selected_main
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("◀  뒤로가기", key="back_btn", on_click=go_to_main): pass
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"<div class='cat-header'>📍 {clean_key(cat)}</div>", unsafe_allow_html=True)
    for sub, content in details[cat].items():
        with st.expander(f"🔎 {sub}", expanded=False): render_card(content)
