import streamlit as st

# 1. 페이지 설정
st.set_page_config(page_title="설비 관리 시스템", layout="wide")

# 2. 반응형 CSS 수정
st.markdown("""
    <style>
    /* 기본 버튼 스타일 (모바일 우선) */
    div.stButton > button {
        width: 100%;
        height: 80px; /* 모바일에서 너무 크지 않게 조절 */
        font-size: 18px !important;
        font-weight: bold;
        border-radius: 15px;
        background: #ffffff;
        border: 1px solid #ddd;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }
    
    /* PC 환경 (너비가 700px 이상일 때) 버튼 높이 조절 */
    @media (min-width: 700px) {
        div.stButton > button {
            height: 120px;
            font-size: 22px !important;
        }
    }

    /* 상세 내용 카드 */
    .detail-card {
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 12px;
        border-left: 6px solid #4CAF50;
    }

    /* 상단 헤더 버튼 크기 최적화 */
    .header-btn div.stButton > button {
        height: 45px !important;
        font-size: 14px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 초기화 (내용 생략 - 기존과 동일)
if 'db' not in st.session_state:
    st.session_state.db = {
        "구동계통": ["안내륜/안정륜", "주행륜 및 타이어", "기타"],
        "공압계통": ["공압-1", "공압-2", "공압-3"],
        "제어계통": ["제어-1", "제어-2", "제어-3"],
        "기타분야": ["기타-1", "기타-2", "기타-3"]
    }
    if 'details' not in st.session_state:
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
        new_text = st.text_area("내용", value=st.session_state.details[t_main][t_sub], height=150)
        if st.button("저장"):
            st.session_state.details[t_main][t_sub] = new_text
            st.rerun()

# --- [상단 헤더] ---
h_col1, h_col2 = st.columns([5, 5]) # 모바일에서 버튼이 밀리지 않게 비율 조정
with h_col1:
    st.markdown("### ⚡ 설비 관리")
with h_col2:
    # 우측 상단에 버튼 나열
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="header-btn">', unsafe_allow_html=True)
        if st.button("🏠 메인"):
            st.session_state.page = 'main'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="header-btn">', unsafe_allow_html=True)
        if st.button("⚙️ 관리"):
            admin_dialog()
        st.markdown('</div>', unsafe_allow_html=True)

# --- [검색창] ---
search_query = st.text_input("🔍 문제점 검색 (예: 타이어)", placeholder="단어를 입력하세요")
st.divider()

# --- [메인 화면: 반응형 레이아웃] ---
if st.session_state.page == 'main':
    # 검색 결과 우선 표시
    if search_query:
        for cat, items in st.session_state.details.items():
            for sub, content in items.items():
                if search_query in content or search_query in sub:
                    with st.expander(f"✅ {cat} > {sub}", expanded=True):
                        st.markdown(f'<div class="detail-card">{content}</div>', unsafe_allow_html=True)
        st.divider()

    # 계통 선택 버튼
    # 중요: columns를 안 쓰거나 가변적으로 쓰면 모바일에서 자동 세로 정렬됩니다.
    cats = list(st.session_state.db.keys())
    for cat in cats:
        if st.button(cat, use_container_width=True):
            st.session_state.selected_main = cat
            st.session_state.page = 'detail'
            st.rerun()

# --- [상세 페이지] ---
elif st.session_state.page == 'detail':
    main_cat = st.session_state.selected_main
    st.subheader(f"📍 {main_cat}")
    for sub in st.session_state.db[main_cat]:
        with st.expander(f"🔎 {sub}", expanded=False):
            st.markdown(f'<div class="detail-card">{st.session_state.details[main_cat][sub]}</div>', unsafe_allow_html=True)