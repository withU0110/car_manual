import streamlit as st

# 1. 페이지 설정
st.set_page_config(page_title="설비 관리 시스템", layout="wide")

# 2. 고도화된 반응형 CSS
st.markdown("""
    <style>
    /* 상단 헤더 컨테이너: 한 줄 고정 */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        margin-bottom: 20px;
    }
    .header-title {
        font-size: 20px;
        font-weight: bold;
        color: #333;
    }
    .header-buttons {
        display: flex;
        gap: 10px;
    }

    /* 버튼 기본 공통 스타일 */
    div.stButton > button {
        width: 100%;
        font-weight: bold;
        border-radius: 12px;
        background: #ffffff;
        border: 1px solid #ddd;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }

    /* 메인 큰 버튼 스타일 */
    .main-btn div.stButton > button {
        height: 100px;
        font-size: 20px !important;
        margin-bottom: 10px;
    }

    /* 상단 메뉴 전용 작은 버튼 스타일 */
    .menu-btn div.stButton > button {
        height: 40px !important;
        padding: 0 15px !important;
        font-size: 14px !important;
        width: auto !important; /* 글자 크기에 맞게 조절 */
    }

    /* 상세 내용 카드 */
    .detail-card {
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
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

# --- [관리자 팝업] ---
@st.dialog("🔐 관리자 모드")
def admin_dialog():
    pw = st.text_input("비밀번호", type="password")
    if pw == "7895":
        t_main = st.selectbox("계통", list(st.session_state.db.keys()))
        t_sub = st.selectbox("항목", st.session_state.db[t_main])
        new_text = st.text_area("내용 수정", value=st.session_state.details[t_main][t_sub], height=150)
        if st.button("내용 저장"):
            st.session_state.details[t_main][t_sub] = new_text
            st.rerun()

# --- [상단 헤더 커스텀 배치] ---
# 가로로 나열하기 위해 columns 비율을 매우 세밀하게 조정합니다.
col_t, col_b1, col_b2 = st.columns([6, 2.5, 1.5])

with col_t:
    st.markdown("<h3 style='margin:0;'>⚡ 설비 관리</h3>", unsafe_allow_html=True)

with col_b1:
    st.markdown('<div class="menu-btn">', unsafe_allow_html=True)
    if st.button("🏠 메인"):
        st.session_state.page = 'main'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_b2:
    st.markdown('<div class="menu-btn">', unsafe_allow_html=True)
    if st.button("⚙️"):  # 텍스트 제거하고 이모티콘만 남김
        admin_dialog()
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- [검색 및 메인/상세 로직] ---
search_query = st.text_input("🔍 검색", placeholder="단어를 입력하세요", label_visibility="collapsed")

if st.session_state.page == 'main':
    if search_query:
        for cat, items in st.session_state.details.items():
            for sub, content in items.items():
                if search_query in content or search_query in sub:
                    with st.expander(f"✅ {cat} > {sub}", expanded=True):
                        st.markdown(f'<div class="detail-card">{content}</div>', unsafe_allow_html=True)
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
            st.markdown(f'<div class="detail-card">{st.session_state.details[main_cat][sub]}</div>', unsafe_allow_html=True)
