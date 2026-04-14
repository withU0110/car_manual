import streamlit as st
import os
import json
import base64
import requests
import html
import re
from io import BytesIO
from PIL import Image

# ── 페이지 설정 ──
st.set_page_config(page_title="설비 관리 시스템", layout="wide")

# ── CSS (다크 테마 #333333) ──
st.markdown("""
    <style>
    /* ── 전체 배경 및 기본 폰트 ── */
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #333333 !important;
        color: #E8E8E8 !important;
    }
    [data-testid="stHeader"] {
        background-color: #2A2A2A !important;
    }
    [data-testid="stSidebar"] {
        background-color: #2A2A2A !important;
    }
    /* 메인 컨텐츠 영역 */
    .block-container {
        padding-top: 2.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        background-color: #333333 !important;
    }

    /* ── 헤더 타이틀 ── */
    .header-title {
        font-size: 22px !important;
        font-weight: bold;
        color: #FFD966;
        text-align: center;
        margin-bottom: 10px;
        letter-spacing: 1px;
        text-shadow: 0 1px 3px rgba(0,0,0,0.5);
    }

    /* ── 메인 버튼 (계통 선택) ── */
    div.stButton > button {
        width: 100%;
        height: 68px;
        font-size: 17px !important;
        font-weight: bold;
        border-radius: 12px;
        background: #444444 !important;
        border: 1px solid #555555 !important;
        color: #E8E8E8 !important;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.4);
        margin-bottom: 8px;
        transition: background 0.2s, border 0.2s;
    }
    div.stButton > button:hover {
        background: #505050 !important;
        border: 1px solid #FFD966 !important;
        color: #FFD966 !important;
    }

    /* ── 메뉴 섹션 버튼 (메인/요약도/설정) ── */
    .menu-section div.stButton > button {
        border: 1.5px solid #FFD966 !important;
        color: #FFD966 !important;
        background: #3A3A3A !important;
        height: 52px !important;
        font-size: 15px !important;
        border-radius: 10px !important;
    }
    .menu-section div.stButton > button:hover {
        background: #FFD966 !important;
        color: #1E1E1E !important;
    }

    /* ── 뒤로가기 버튼 ── */
    .back-btn div.stButton > button {
        height: 36px !important;
        font-size: 14px !important;
        border: 1px solid #7CB9E8 !important;
        color: #7CB9E8 !important;
        border-radius: 8px !important;
        background: #3A3A3A !important;
        box-shadow: none !important;
        margin-bottom: 8px !important;
        width: auto !important;
        padding: 0 16px !important;
    }
    .back-btn div.stButton > button:hover {
        background: #7CB9E8 !important;
        color: #1E1E1E !important;
    }

    /* ── 상세 카드 ── */
    .detail-card-content {
        padding: 16px 18px;
        background-color: #3E3E3E;
        border-radius: 10px;
        border-left: 5px solid #FFD966;
        font-family: 'Nanum Gothic', 'Malgun Gothic', sans-serif;
        white-space: pre-wrap;
        word-wrap: break-word;
        word-break: keep-all;
        margin: 0;
        font-size: 15px;
        line-height: 1.85;
        color: #E8E8E8;
    }

    /* ── Expander ── */
    [data-testid="stExpander"] {
        background-color: #3A3A3A !important;
        border: 1px solid #4A4A4A !important;
        border-radius: 10px !important;
        margin-bottom: 6px;
    }
    [data-testid="stExpander"] summary {
        color: #E8E8E8 !important;
        font-weight: bold;
        font-size: 15px;
    }

    /* ── 텍스트 입력/검색창 ── */
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stSelectbox"] div[data-baseweb="select"] {
        background-color: #444444 !important;
        color: #E8E8E8 !important;
        border: 1px solid #555555 !important;
        border-radius: 8px !important;
    }
    [data-testid="stTextInput"] input::placeholder {
        color: #999999 !important;
    }
    [data-testid="stTextInput"] label,
    [data-testid="stTextArea"] label,
    [data-testid="stSelectbox"] label {
        color: #BBBBBB !important;
        font-size: 14px !important;
    }

    /* ── 탭 ── */
    [data-testid="stTabs"] [role="tab"] {
        color: #BBBBBB !important;
        font-size: 14px;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: #FFD966 !important;
        border-bottom: 2px solid #FFD966 !important;
    }

    /* ── Divider ── */
    hr {
        border-color: #4A4A4A !important;
    }

    /* ── st.info / st.error / st.success / st.caption ── */
    [data-testid="stNotification"] {
        border-radius: 8px !important;
    }
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #AAAAAA !important;
    }

    /* ── 카테고리 헤더 ── */
    .cat-header {
        font-size: 20px;
        font-weight: bold;
        color: #FFD966;
        margin: 6px 0 10px 0;
        padding-bottom: 4px;
        border-bottom: 1px solid #555555;
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

# ── 이미지 리사이즈 + 압축 (모바일 최적화) ──
def compress_image(img_file, max_px: int = 1200, quality: int = 85) -> tuple[bytes, str]:
    img = Image.open(img_file)
    try:
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > max_px:
        ratio = max_px / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    buf.seek(0)
    stem = os.path.splitext(img_file.name)[0]
    return buf.read(), f"{stem}.jpg"

# ── GitHub에 이미지 업로드하기 ──
def upload_image_to_github(img_file) -> str | None:
    img_bytes, filename = compress_image(img_file)
    encoded = base64.b64encode(img_bytes).decode("utf-8")
    img_api_url = (
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/images/{filename}"
    )
    check = requests.get(img_api_url, headers=HEADERS)
    sha   = check.json().get("sha") if check.status_code == 200 else None
    payload = {
        "message": f"Upload image: {filename}",
        "content": encoded,
    }
    if sha:
        payload["sha"] = sha
    res = requests.put(img_api_url, headers=HEADERS, json=payload)
    if res.status_code in (200, 201):
        return f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/images/{filename}"
    else:
        st.error(f"이미지 업로드 실패 ({filename}): {res.status_code} {res.text}")
        return None

# ── GitHub에서 summary.png raw URL 생성 ──
def get_summary_raw_url() -> str:
    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/summary.png"

# ── 서식 렌더링 함수 ──
# 지원 문법:
#   **텍스트**   → 굵게
#   *텍스트*     → 기울임
#   ***텍스트*** → 굵게+기울임
#   __텍스트__   → 밑줄
#   !!텍스트!!   → 빨간색 강조
#   ##텍스트##   → 크게 (22px)
#   ^^^텍스트^^^ → 매우 크게 (28px)
#   ~~텍스트~~   → 작게 (12px)
#   \n           → 줄바꿈
def render_content(text: str) -> str:
    s = html.escape(text)
    s = re.sub(r'\^\^\^(.+?)\^\^\^', r'<span style="font-size:28px;font-weight:bold;color:#FFD966;">\1</span>', s)
    s = re.sub(r'##(.+?)##',         r'<span style="font-size:22px;font-weight:bold;color:#FFD966;">\1</span>', s)
    s = re.sub(r'~~(.+?)~~',         r'<span style="font-size:12px;color:#AAAAAA;">\1</span>', s)
    s = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', s)
    s = re.sub(r'\*\*(.+?)\*\*',     r'<strong>\1</strong>', s)
    s = re.sub(r'\*(.+?)\*',         r'<em>\1</em>', s)
    s = re.sub(r'__(.+?)__',         r'<u>\1</u>', s)
    s = re.sub(r'!!(.+?)!!',         r'<span style="color:#FF6B6B;font-weight:bold;">\1</span>', s)
    s = s.replace('\n', '<br>')
    return s

# ── 키 이름에서 ##...## 마커 제거 (버튼 표시용) ──
def clean_key_name(key: str) -> str:
    """##텍스트## 형태의 마커를 제거하여 순수 텍스트만 반환"""
    return re.sub(r'##(.+?)##', r'\1', key).strip()

# ── content 값 파싱 헬퍼 ──
def parse_content(content) -> tuple[str, list[str]]:
    if isinstance(content, dict):
        return content.get("text", ""), content.get("images", [])
    return content, []

# ── 데이터 로드 ──
details = load_data_from_github()
DB_KEYS = list(details.keys())

if 'page' not in st.session_state:
    st.session_state.page = 'main'
if 'deleted_img_indices' not in st.session_state:
    st.session_state.deleted_img_indices = set()
if 'admin_last_key' not in st.session_state:
    st.session_state.admin_last_key = ""

# ── 비밀번호 검증 ──
DEFAULT_PW = "7895"

def get_stored_password() -> str:
    meta = details.get("__meta__", {})
    return meta.get("password", DEFAULT_PW)

def check_password(pw: str) -> bool:
    return pw == get_stored_password()

def save_password(new_pw: str) -> bool:
    if "__meta__" not in details:
        details["__meta__"] = {}
    details["__meta__"]["password"] = new_pw
    return save_data_to_github(details)

# ── 관리자 팝업 ──
@st.dialog("🔐 관리자 모드")
def admin_dialog():
    pw = st.text_input("비밀번호", type="password")
    if not check_password(pw):
        if pw:
            st.error("비밀번호가 틀렸습니다.")
        return

    tab_edit, tab_pw = st.tabs(["📝 내용 편집", "🔑 비밀번호 변경"])

    # ───────────────────────────────
    # 탭1: 내용 편집 + 이미지 관리
    # ───────────────────────────────
    with tab_edit:
        edit_keys = [k for k in DB_KEYS if k != "__meta__"]

        # selectbox에 표시할 라벨(##제거)과 실제 키 매핑
        key_labels  = [clean_key_name(k) for k in edit_keys]
        label_to_key = dict(zip(key_labels, edit_keys))

        selected_label = st.selectbox("계통", key_labels, key="admin_main_label")
        t_main = label_to_key[selected_label]
        t_sub  = st.selectbox("항목", list(details[t_main].keys()), key="admin_sub")

        # ── 계통/항목이 바뀌면 textarea key를 바꿔 내용 초기화 ──
        # [BUG FIX] key를 선택된 계통+항목 기반으로 동적 생성
        current_key = f"{t_main}::{t_sub}"
        if st.session_state.admin_last_key != current_key:
            st.session_state.deleted_img_indices = set()
            st.session_state.admin_last_key = current_key

        # 기존 데이터 파싱
        current_content = details[t_main][t_sub]
        current_text, current_images = parse_content(current_content)

        # ── 텍스트 수정 (key에 current_key 포함 → 항목 변경 시 위젯 재생성) ──
        textarea_key = f"admin_textarea__{current_key}"
        new_text = st.text_area(
            "내용 수정 (엔터로 줄바꿈 가능)",
            value=current_text,
            height=200,
            key=textarea_key
        )

        # ── 기존 이미지 목록 표시 및 삭제 ──
        st.markdown("**📎 현재 첨부 이미지**")
        if current_images:
            for idx, img_url in enumerate(current_images):
                is_deleted = idx in st.session_state.deleted_img_indices
                col_img, col_del = st.columns([5, 1])
                with col_img:
                    if is_deleted:
                        st.markdown(
                            f"<s style='color:#888888;font-size:12px'>{img_url.split('/')[-1]} (삭제 예정)</s>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.image(img_url, use_container_width=True)
                with col_del:
                    if is_deleted:
                        if st.button("↩️", key=f"restore_{idx}", help="삭제 취소"):
                            st.session_state.deleted_img_indices.discard(idx)
                    else:
                        if st.button("🗑️", key=f"del_{idx}", help="삭제 예약"):
                            st.session_state.deleted_img_indices.add(idx)
        else:
            st.caption("첨부된 이미지가 없습니다.")

        # ── 새 이미지 업로드 ──
        st.markdown("**➕ 이미지 추가 업로드**")
        uploaded_imgs = st.file_uploader(
            "이미지 선택 (png / jpg / jpeg)",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key=f"img_uploader__{current_key}"
        )

        # ── 저장 버튼 ──
        if st.button("💾 저장 (GitHub 반영)", key="btn_save_content"):
            kept_images = [
                url for idx, url in enumerate(current_images)
                if idx not in st.session_state.deleted_img_indices
            ]

            new_img_urls = []
            if uploaded_imgs:
                with st.spinner("이미지 업로드 중..."):
                    for img_file in uploaded_imgs:
                        url = upload_image_to_github(img_file)
                        if url:
                            new_img_urls.append(url)

            all_images = kept_images + new_img_urls

            if all_images:
                details[t_main][t_sub] = {"text": new_text, "images": all_images}
            else:
                details[t_main][t_sub] = new_text

            ok = save_data_to_github(details)
            if ok:
                st.session_state.deleted_img_indices = set()
                st.success("저장 완료! GitHub data.json이 업데이트됐습니다.")

    # ───────────────────────────────
    # 탭2: 비밀번호 변경
    # ───────────────────────────────
    with tab_pw:
        st.markdown("현재 비밀번호로 인증된 상태입니다.")
        new_pw1 = st.text_input("새 비밀번호", type="password", key="new_pw1")
        new_pw2 = st.text_input("새 비밀번호 확인", type="password", key="new_pw2")

        if st.button("🔒 비밀번호 변경", key="btn_change_pw"):
            if not new_pw1:
                st.error("새 비밀번호를 입력해 주세요.")
            elif new_pw1 != new_pw2:
                st.error("비밀번호가 일치하지 않습니다.")
            elif new_pw1 == get_stored_password():
                st.warning("현재 비밀번호와 동일합니다.")
            else:
                ok = save_password(new_pw1)
                if ok:
                    st.success("비밀번호가 변경되었습니다. 다음 로그인부터 적용됩니다.")

# ── 요약도 팝업 ──
@st.dialog("📋 전체 요약도")
def summary_dialog():
    raw_url = get_summary_raw_url()
    res = requests.get(raw_url)
    if res.status_code == 200:
        img_bytes = res.content
        st.image(img_bytes, use_container_width=True)
        st.download_button(
            label="⬇️ 이미지 다운로드",
            data=img_bytes,
            file_name="summary.png",
            mime="image/png",
            use_container_width=True
        )
    else:
        local_path = "summary.png"
        if os.path.exists(local_path):
            with open(local_path, "rb") as f:
                img_bytes = f.read()
            st.image(img_bytes, use_container_width=True)
            st.download_button(
                label="⬇️ 이미지 다운로드",
                data=img_bytes,
                file_name="summary.png",
                mime="image/png",
                use_container_width=True
            )
        else:
            st.error("summary.png 파일을 GitHub 또는 로컬에서 찾을 수 없습니다.")
            st.info("GitHub 저장소 루트에 summary.png 파일을 업로드해 주세요.")

# ── 항목 상세 카드 렌더링 ──
def render_item_card(content):
    text, images = parse_content(content)
    st.markdown(
        f'<div class="detail-card-content">{render_content(text)}</div>',
        unsafe_allow_html=True
    )
    if images:
        st.markdown("")
        for img_url in images:
            st.image(img_url, use_container_width=True)

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

# ── 검색어 있으면 전체 검색 ──
if search_query:
    found = False
    for cat, items in details.items():
        if cat == "__meta__":
            continue
        for sub, content in items.items():
            text, _ = parse_content(content)
            if search_query in text or search_query in sub:
                found = True
                with st.expander(f"✅ {clean_key_name(cat)} > {sub}", expanded=True):
                    render_item_card(content)
    if not found:
        st.info("검색 결과가 없습니다.")

elif st.session_state.page == 'main':
    for cat in DB_KEYS:
        if cat == "__meta__":
            continue
        # [BUG FIX] 버튼 라벨에서 ## 마커 제거
        display_name = clean_key_name(cat)
        if st.button(display_name, use_container_width=True):
            st.session_state.selected_main = cat
            st.session_state.page = 'detail'
            st.rerun()

elif st.session_state.page == 'detail':
    main_cat = st.session_state.selected_main
    display_cat = clean_key_name(main_cat)

    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("◀  뒤로가기", key="back_btn"):
        st.session_state.page = 'main'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"<div class='cat-header'>📍 {display_cat}</div>", unsafe_allow_html=True)

    for sub, content in details[main_cat].items():
        with st.expander(f"🔎 {sub}", expanded=False):
            render_item_card(content)
