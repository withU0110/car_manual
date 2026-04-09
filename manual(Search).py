import streamlit as st
import os

# 1. 페이지 설정
st.set_page_config(page_title="설비 관리 시스템", layout="wide")

# 2. CSS 최적화 (버튼 한 줄 정렬 강제 및 줄바꿈 지원)
st.markdown("""
    <style>
    /* 상단 타이틀 크기 축소하여 공간 확보 */
    .header-title { 
        font-size: 18px !important; 
        font-weight: bold; 
        margin: 0; 
        white-space: nowrap; 
    }
    
    /* 버튼 공통 디자인 */
    div.stButton > button { width: 100%; font-weight: bold; border-radius: 10px; }
    
    /* 상단 메뉴 버튼: 너비 최소화 */
    .menu-btn div.stButton > button {
        height: 35px !important; 
        padding: 0 5px !important;
        font-size: 13px !important;
    }
    
    /* 메인 큰 버튼 */
    .main-btn div.stButton > button {
        height: 100px; font-size: 20px !important; margin-bottom: 10px;
        background: #ffffff; border: 1px solid #ddd;
    }

    /* 줄바꿈(\n) 완벽 지원 */
    .detail-card-content {
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        font-family: inherit;
        white-space: pre-wrap; 
        word-wrap: break-word;
        margin: 0;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 초기화
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
        new_text = st.text_area("내용 수정", value=st.session_state.details[t_main][t_sub], height=200)
        if st.button("저장"):
            st.session_state.details[t_main][t_sub] = new_text
            st.rerun()

# --- [전체 요약 사진 팝업] ---
@st.dialog("📋 전체 요약도")
def summary_dialog():
    image_path = "summary.png" # 확장자 png로 수정됨
    if os.path.exists(image_path):
        st.image(image_path, use_container_width=True)
    else:
        st.error(f"'{image_path}' 파일을 찾을 수 없습니다.")
        st.info("GitHub 저장소에 summary.png 파일이 있는지 확인해 주세요.")

# --- [상단 헤더: 4컬럼 배치 최적화] ---
# 비율을 [4, 2, 2, 1.2]로 조정하여 제목 공간은 줄이고 버튼 공간을 늘렸습니다.
t_col, b_col1, b_col2, b_col3 = st.columns([4, 2, 2, 1.2])

with t_col:
    st.markdown("<p class='header-title'>⚡ 설비관리</p>", unsafe_allow_html=True)

with b_col1:
    st.markdown('<div class="menu-btn">', unsafe_allow_html=True)
    if st.button("📋요약"):
        summary_dialog()
    st.markdown('</div>', unsafe_allow_html=True)

with b_col2:
    st.markdown('<div class="menu-btn">', unsafe_allow_html=True)
    if st.button("🏠메인"):
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
search_query = st.text_input("🔍 검색", placeholder="단어 입력", label_visibility="collapsed")

# --- [메인/상세 로직] ---
if st.session_state.page == 'main':
    if search_query:
        for cat, items in st.session_state.details.items():
            for sub, content in items.items():
                if search_query in content or search_query in sub:
                    with st.expander(f"✅ {cat} > {sub}", expanded=True):
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
            st.markdown(f'<pre class="detail-card-content">{st.session_state.details[main_cat][sub]}</pre>', unsafe_allow_html=True)
