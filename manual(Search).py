import streamlit as st
import os

# 1. 페이지 설정
st.set_page_config(page_title="설비 관리 시스템", layout="wide")

# 2. CSS 최적화 (모든 버튼을 큼직한 세로 나열 스타일로 통일)
st.markdown("""
    <style>
    /* 상단 타이틀 스타일 */
    .header-title { 
        font-size: 24px !important; 
        font-weight: bold; 
        color: #1E1E1E;
        text-align: center;
        margin-bottom: 20px;
    }
    
    /* 모든 버튼 공통 디자인 (구동/공압 버튼 스타일과 통일) */
    div.stButton > button {
        width: 100%;
        height: 80px; /* 모바일 터치 최적화 높이 */
        font-size: 18px !important;
        font-weight: bold;
        border-radius: 15px;
        background: #ffffff;
        border: 1px solid #ddd;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 12px;
        transition: 0.2s;
    }
    
    /* 메뉴용 버튼 색상 살짝 다르게 (선택 사항) */
    .menu-section div.stButton > button {
        border-color: #2E7D32;
        color: #2E7D32;
        height: 60px; /* 메뉴 버튼은 살짝 낮게 */
    }

    /* 줄바꿈(\n) 완벽 지원 카드 */
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
        if st.button("내용 저장"):
            st.session_state.details[t_main][t_sub] = new_text
            st.rerun()

# --- [전체 요약 사진 팝업] ---
@st.dialog("📋 전체 요약도")
def summary_dialog():
    image_path = "summary.png"
    if os.path.exists(image_path):
        st.image(image_path, use_container_width=True)
    else:
        st.error(f"'{image_path}' 파일을 찾을 수 없습니다.")
        st.info("GitHub에 summary.png 파일이 있는지 확인해 주세요.")

# --- [화면 구성] ---

# 1. 최상단 타이틀
st.markdown("<p class='header-title'>⚡ 설비 유지보수 시스템</p>", unsafe_allow_html=True)

# 2. 상단 메뉴 버튼 (한 줄씩 큼직하게 배치)
st.markdown('<div class="menu-section">', unsafe_allow_html=True)
col_menu1, col_menu2, col_menu3 = st.columns(3) # 모바일에서 3분할이 작으면 그냥 세로로 나열됩니다.

with col_menu1:
    if st.button("📋 요약도"):
        summary_dialog()
with col_menu2:
    if st.button("🏠 메인"):
        st.session_state.page = 'main'
        st.rerun()
with col_menu3:
    if st.button("⚙️ 설정"):
        admin_dialog()
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# 3. 검색창
search_query = st.text_input("🔍 문제점 검색", placeholder="단어 입력", label_visibility="collapsed")

# 4. 메인/상세 로직
if st.session_state.page == 'main':
    if search_query:
        for cat, items in st.session_state.details.items():
            for sub, content in items.items():
                if search_query in content or search_query in sub:
                    with st.expander(f"✅ {cat} > {sub}", expanded=True):
                        st.markdown(f'<pre class="detail-card-content">{content}</pre>', unsafe_allow_html=True)
        st.divider()

    # 4대 계통 버튼 (한 줄씩 큼직하게)
    for cat in st.session_state.db.keys():
        if st.button(cat, use_container_width=True):
            st.session_state.selected_main = cat
            st.session_state.page = 'detail'
            st.rerun()

elif st.session_state.page == 'detail':
    main_cat = st.session_state.selected_main
    st.subheader(f"📍 {main_cat}")
    for sub in st.session_state.db[main_cat]:
        with st.expander(f"🔎 {sub}", expanded=False):
            st.markdown(f'<pre class="detail-card-content">{st.session_state.details[main_cat][sub]}</pre>', unsafe_allow_html=True)
