import streamlit as st
import os
import json
import base64
import requests
import html
from io import BytesIO
from PIL import Image

# ── 페이지 설정 ──
st.set_page_config(page_title="설비 관리 시스템", layout="wide")

# ── CSS ──
st.markdown("""
    <style>
    .block-container {
        padding-top: 4rem !important;
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
        white-space: pre-wrap;
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

# ── 이미지 리사이즈 + 압축 (모바일 최적화) ──
def compress_image(img_file, max_px: int = 1200, quality: int = 85) -> tuple[bytes, str]:
    """
    업로드된 이미지를 리사이즈·압축하여 bytes로 반환합니다.
    - max_px  : 가로/세로 중 긴 변의 최대 픽셀 (기본 1200px ≈ 150dpi @ 8인치)
    - quality : JPEG 압축 품질 0~95 (기본 85)
    반환값: (압축된 bytes, 저장 파일명(확장자 .jpg로 통일))
    """
    img = Image.open(img_file)

    # EXIF 회전 보정
    try:
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    # RGBA / P 모드 → RGB 변환 (JPEG 저장 위해 필요)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # 긴 변 기준 리사이즈
    w, h = img.size
    if max(w, h) > max_px:
        ratio = max_px / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

    # JPEG로 압축
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    buf.seek(0)

    # 파일명 확장자를 .jpg로 통일
    stem = os.path.splitext(img_file.name)[0]
    return buf.read(), f"{stem}.jpg"

# ── GitHub에 이미지 업로드하기 ──
def upload_image_to_github(img_file) -> str | None:
    """
    이미지를 압축 후 GitHub /images/ 폴더에 업로드하고 raw URL을 반환합니다.
    동일 파일명이 존재하면 SHA를 가져와 덮어씁니다.
    반환값: raw URL 문자열 또는 None (실패 시)
    """
    img_bytes, filename = compress_image(img_file)
    encoded = base64.b64encode(img_bytes).decode("utf-8")

    img_api_url = (
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/images/{filename}"
    )

    # 기존 파일 SHA 확인 (덮어쓰기용)
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
        raw_url = (
            f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/images/{filename}"
        )
        return raw_url
    else:
        st.error(f"이미지 업로드 실패 ({filename}): {res.status_code} {res.text}")
        return None

# ── GitHub에서 summary.png raw URL 생성 ──
def get_summary_raw_url() -> str:
    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/summary.png"

# ── 줄바꿈 안전 렌더링 함수 ──
def render_content(text: str) -> str:
    escaped = html.escape(text)
    return escaped.replace("\n", "<br>")

# ── content 값 파싱 헬퍼 ──
# data.json 항목은 기존(문자열) 또는 신규(dict: {text, images}) 두 가지 형태를 모두 지원
def parse_content(content) -> tuple[str, list[str]]:
    """content → (text: str, images: list[str]) 반환"""
    if isinstance(content, dict):
        return content.get("text", ""), content.get("images", [])
    return content, []  # 기존 문자열 구조 하위 호환

# ── 데이터 로드 ──
details = load_data_from_github()
DB_KEYS = list(details.keys())

if 'page' not in st.session_state:
    st.session_state.page = 'main'
# 이미지 삭제 상태를 다이얼로그 재렌더링 간에 유지
if 'deleted_img_indices' not in st.session_state:
    st.session_state.deleted_img_indices = set()
# 현재 관리자가 보고 있는 계통/항목 추적 (삭제 상태 초기화용)
if 'admin_last_key' not in st.session_state:
    st.session_state.admin_last_key = ""

# ── 비밀번호 검증 (data.json의 __meta__.password 또는 기본값) ──
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

    # ── 탭: 내용편집 / 비밀번호변경 ──
    tab_edit, tab_pw = st.tabs(["📝 내용 편집", "🔑 비밀번호 변경"])

    # ───────────────────────────────
    # 탭1: 내용 편집 + 이미지 관리
    # ───────────────────────────────
    with tab_edit:
        # __meta__ 키는 편집 대상에서 제외
        edit_keys = [k for k in DB_KEYS if k != "__meta__"]
        t_main = st.selectbox("계통", edit_keys, key="admin_main")
        t_sub  = st.selectbox("항목", list(details[t_main].keys()), key="admin_sub")

        # 계통/항목이 바뀌면 삭제 상태 초기화
        current_key = f"{t_main}::{t_sub}"
        if st.session_state.admin_last_key != current_key:
            st.session_state.deleted_img_indices = set()
            st.session_state.admin_last_key = current_key

        # 기존 데이터 파싱
        current_content = details[t_main][t_sub]
        current_text, current_images = parse_content(current_content)

        # ── 텍스트 수정 ──
        new_text = st.text_area(
            "내용 수정 (엔터로 줄바꿈 가능)",
            value=current_text,
            height=200,
            key="admin_textarea"
        )

        # ── 기존 이미지 목록 표시 및 삭제 ──
        # rerun 없이 session_state로 삭제 상태 관리
        st.markdown("**📎 현재 첨부 이미지**")
        if current_images:
            for idx, img_url in enumerate(current_images):
                is_deleted = idx in st.session_state.deleted_img_indices
                col_img, col_del = st.columns([5, 1])
                with col_img:
                    if is_deleted:
                        st.markdown(
                            f"<s style='color:gray;font-size:12px'>{img_url.split('/')[-1]} (삭제 예정)</s>",
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
            key="img_uploader"
        )

        # ── 저장 버튼 ──
        if st.button("💾 저장 (GitHub 반영)", key="btn_save_content"):
            # 삭제 표시되지 않은 기존 이미지만 유지
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
                # 저장 완료 후 삭제 상태 초기화
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
    # GitHub raw URL 로 이미지 로드
    raw_url = get_summary_raw_url()
    res = requests.get(raw_url)

    if res.status_code == 200:
        img_bytes = res.content
        st.image(img_bytes, use_container_width=True)

        # ── 다운로드 버튼 ──
        st.download_button(
            label="⬇️ 이미지 다운로드",
            data=img_bytes,
            file_name="summary.png",
            mime="image/png",
            use_container_width=True
        )
    else:
        # fallback: 로컬 파일
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
    # 텍스트
    st.markdown(
        f'<div class="detail-card-content">{render_content(text)}</div>',
        unsafe_allow_html=True
    )
    # 첨부 이미지
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

# ── 메인 / 상세 로직 ──
if st.session_state.page == 'main':
    if search_query:
        found = False
        for cat, items in details.items():
            for sub, content in items.items():
                text, _ = parse_content(content)
                if search_query in text or search_query in sub:
                    found = True
                    with st.expander(f"✅ {cat} > {sub}", expanded=True):
                        render_item_card(content)
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
            render_item_card(content)
