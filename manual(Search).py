import streamlit as st
import os

# 1. 페이지 설정
st.set_page_config(page_title="설비 관리 시스템", layout="wide")

# 2. CSS 수정 (줄바꿈 완벽 지원 및 팝업 스타일)
st.markdown("""
    <style>
    /* 기본 공통 스타일 */
    .header-title { font-size: 22px; font-weight: bold; margin: 0; }
    div.stButton > button { width: 100%; font-weight: bold; border-radius: 12px; }
    
    /* 상단 메뉴 작은 버튼 */
    .menu-btn div.stButton > button {
        height: 38px !important; padding: 0 12px !important;
        font-size: 14px !important; width: auto !important;
    }
    
    /* 메인 큰 버튼 */
    .main-btn div.stButton > button {
        height: 100px; font-size: 20px !important; margin-bottom: 10px;
        background: #ffffff; border: 1px solid #ddd;
    }

    /* ⭐ 핵심: 줄바꿈 완벽 지원 스타일 */
    .detail-card-content {
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        /* <pre> 태그 스타일 정의 */
        font-family: inherit; /* 기본 폰트 사용 */
        white-space: pre-wrap; /* 줄바꿈 문자('\n') 인식 및 자동 줄바꿈 */
        word-wrap: break-word; /* 긴 단어 줄바꿈 */
        margin: 0; /* 기본 마진 제거 */
    }

    /* 팝업 이미지 스타일 */
    .summary-image {
        width: 100%;
        max-width: 600px;
        height: auto;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 초기화 (기존 동일)
if 'db' not in st.session_state:
    st.session_state.db = {
        "구동계통": ["안내륜/안정륜", "주행륜 및 타이어", "기타"],
        "공압계통": ["공압-1", "공압-2", "공압-3"],
        "제어계통": ["제어-1", "제어-2", "제어-3"],
        "기타분야": ["기타-1", "기타-2", "기타-3"]
    }
    st.session_state.details = {k: {sub: f"{sub}의 점검 내용입니다." for sub in v} for k, v in st.session_state.db.items()}
if 'page' not in st.session_state:
    st.session_state.page = 'main'

# --- [관리자 팝업] --- (기본 기능 유지)
@st.dialog("🔐 관리자 모드")
def admin_dialog():
    pw = st.text_input("비밀번호", type="password")
    if pw == "7895":
        t_main = st.selectbox("계통", list(st.session_state.db.keys()))
        t_sub = st.selectbox("항목", st.session_state.db[t_main])
        # st.text_area는 Enter 입력을 지원합니다.
        new_text = st.text_area("내용 수정 (Enter로 줄바꿈 가능)", 
                                value=st.session_state.details[t_main][t_sub], 
                                height=200)
        if st.button("내용 저장"):
            st.session_state.details[t_main][t_sub] = new_text
            st.rerun()

# --- [전체 요약 사진 팝업] ---
@st.dialog("📋 전체 요약 사진")
def summary_dialog():
    # 💡 배포할 사진 파일명(예: summary.png)을 여기에 맞춰 수정하세요.
    image_path = "summary.png" 
    
    if os.path.exists(image_path):
        st.image(image_path, caption="설비 전체 요약도", use_column_width=True)
    else:
        st.warning(f"'{image_path}' 파일을 찾을 수 없습니다. (서버 업로드 필요)")
        st.write("깃허브 저장소에 파이썬 파일과 같은 폴더에 사진을 올려두어야 합니다.")

# --- [상단 헤더: 제목 및 버튼 이동] ---
t_col, b_col1, b_col2, b_col3 = st.columns([5, 2, 2, 1])

with t_col:
    st.markdown("<p class='header-title'>⚡ 설비 유지보수 시스템</p>", unsafe_allow_html=True)

with b_col1:
    st.markdown('<div class="menu-btn">', unsafe_allow_html=True)
    if st.button("📋 요약"):
        summary_dialog()
    st.markdown('</div>', unsafe_allow_html=True)

with b_col2:
    st.markdown('<div class="menu-btn">', unsafe_allow_html=True)
    if st.button("🏠 메인"):
        st.session_state.page = 'main'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with b_col3:
    st.markdown('<div class="menu-btn">', unsafe_allow_html=True)
    if st.button("⚙️"):
        admin_dialog()
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- [검색창] ---
search_query = st.text_input("🔍 검색", placeholder="단어를 입력하세요", label_visibility="collapsed")

# --- [메인/상세 로직] ---
if st.session_state.page == 'main':
    if search_query:
        for cat, items in st.session_state.details.items():
            for sub, content in items.items():
                if search_query in content or search_query in sub:
                    with st.expander(f"✅ {cat} > {sub}", expanded=True):
                        # ⭐ 줄바꿈 적용 출력: <pre> 태그 사용
                        st.markdown(f'<pre class="detail-card-content">{content}</pre>', unsafe_allow_html=True)
        st.divider()

    st.markdown('<div class="main-btn">', unsafe_allow_html=True)
    for cat in st.session_state.db.keys():
        if st.button(cat, use_container_width=True):
            st.session_state.selected_main = cat
            st.session_state.page = 'detail'
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == 'detail':
    main_cat = st.session_state.selected_main
    st.subheader(f"📍 {main_cat}")
    for sub in st.session_state.db[main_cat]:
        with st.expander(f"🔎 {sub}", expanded=False):
            # ⭐ 줄바꿈 적용 출력: <pre> 태그 사용
            st.markdown(f'<pre class="detail-card-content">{st.session_state.details[main_cat][sub]}</pre>', unsafe_allow_html=True)
