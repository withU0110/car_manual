import streamlit as st

# 1. 페이지 설정
st.set_page_config(page_title="설비 관리 시스템", layout="wide")

# 2. 반응형 CSS 최적화
st.markdown("""
    <style>
    /* 기본 버튼 스타일 */
    div.stButton > button {
        width: 100%;
        font-weight: bold;
        border-radius: 15px;
        background: #ffffff;
        border: 1px solid #ddd;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
    }

    /* 메인 4대 계통 버튼 (반응형 높이) */
    .main-btn div.stButton > button {
        height: 80px;
        font-size: 18px !important;
        margin-bottom: 10px;
    }
    @media (min-width: 700px) {
        .main-btn div.stButton > button {
            height: 120px;
            font-size: 22px !important;
        }
    }

    /* 상단 헤더 버튼 (반응형 정렬) */
    .header-btn div.stButton > button {
        height: 45px !important;
        font-size: 14px !important;
        border-color: #2E7D32;
        color: #2E7D32;
    }

    /* 상세 내용 카드 */
    .detail-card {
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 12px;
        border-left: 6px solid #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 초기화 (기존과 동일)
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
        new_text = st.text_area("내용", value=st.session_state.details[t_main][t_sub], height=150)
        if st.button("저장"):
            st.session_state.details[t_main][t_sub] = new_text
            st.rerun()

# --- [반응형 상단 헤더 구성] ---
# 제목은 항상 크게 표시
st.markdown("## ⚡ 설비 유지보수 시스템")

# 버튼 전용 컬럼: 모바일에서는 자동으로 아래로 떨어지게 설정
h_col1, h_col2 = st.columns([1, 1]) 
with h_col1:
    st.markdown('<div class="header-btn">', unsafe_allow_html=True)
    if st.button("🏠 메인으로"):
        st.session_state.page = 'main'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
with h_col2:
    st.markdown('<div class="header-btn">', unsafe_allow_html=True)
    if st.button("⚙️ 관리자"):
        admin_dialog()
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- [검색창] ---
search_query = st.text_input("🔍 문제점 검색", placeholder="단어를 입력하세요")

# --- [화면 레이아웃] ---
if st.session_state.page == 'main':
    # 검색 결과
    if search_query:
        for cat, items in st.session_state.details.items():
            for sub, content in items.items():
                if search_query in content or search_query in sub:
                    with st.expander(f"✅ {cat} > {sub}", expanded=True):
                        st.markdown(f'<div class="detail-card">{content}</div>', unsafe_allow_html=True)
        st.divider()

    # 메인 4대 계통 (모바일에서 1열로 쌓이도록 columns 제거)
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
