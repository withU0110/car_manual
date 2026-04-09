import streamlit as st
import os
import base64

# 1. 페이지 설정
st.set_page_config(page_title="설비 관리 시스템", layout="wide")

# 2. 디자인 개선 (입체형 버튼 및 상단 정렬)
st.markdown("""
    <style>
    /* 메인 4분할 버튼 스타일 */
    div.stButton > button {
        width: 100%;
        height: 120px;
        font-size: 22px !important;
        font-weight: bold;
        border-radius: 20px;
        background: #ffffff;
        border: 1px solid #ddd;
        box-shadow: 4px 4px 10px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }
    /* 상세 내용 카드 스타일 */
    .detail-card {
        padding: 20px;
        background-color: #f8f9fa;
        border-radius: 12px;
        border-left: 6px solid #4CAF50;
        font-size: 18px;
        line-height: 1.6;
    }
    /* 상단 버튼 전용 스타일 (작게) */
    .header-btn div.stButton > button {
        height: 50px !important;
        font-size: 16px !important;
        margin-bottom: 0px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 및 상태 관리 초기화
if 'db' not in st.session_state:
    st.session_state.db = {
        "구동계통": ["안내륜/안정륜", "주행륜 및 타이어", "기타"],
        "공압계통": ["공압-1", "공압-2", "공압-3"],
        "제어계통": ["제어-1", "제어-2", "제어-3"],
        "기타분야": ["기타-1", "기타-2", "기타-3"]
    }
    # 초기 상세 내용 (관리자가 수정할 데이터)
    st.session_state.details = {k: {sub: f"{sub} 항목의 상세 점검 내용이 아직 입력되지 않았습니다." for sub in v} for k, v in st.session_state.db.items()}

if 'page' not in st.session_state:
    st.session_state.page = 'main'
if 'selected_main' not in st.session_state:
    st.session_state.selected_main = None

# --- [관리자 팝업 다이얼로그] ---
@st.dialog("🔐 관리자 데이터 수정")
def admin_dialog():
    st.write("내용을 수정한 후 저장 버튼을 눌러주세요.")
    password = st.text_input("관리자 비밀번호", type="password")
    
    if password == "7895":
        target_main = st.selectbox("수정할 계통", list(st.session_state.db.keys()))
        target_sub = st.selectbox("수정할 세부 항목", st.session_state.db[target_main])
        new_content = st.text_area("내용 입력", value=st.session_state.details[target_main][target_sub], height=250)
        
        if st.button("내용 업데이트 및 저장"):
            st.session_state.details[target_main][target_sub] = new_content
            st.toast("✅ 데이터가 성공적으로 저장되었습니다.")
            st.rerun()
    elif password != "":
        st.error("비밀번호가 틀렸습니다.")

# --- [상단 헤더 영역: 제목 및 버튼 이동] ---
header_col1, header_col2, header_col3 = st.columns([6, 2, 2])

with header_col1:
    st.subheader("⚡ 설비 유지보수 시스템")

with header_col2:
    st.markdown('<div class="header-btn">', unsafe_allow_html=True)
    if st.button("🏠 메인으로"):
        st.session_state.page = 'main'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with header_col3:
    st.markdown('<div class="header-btn">', unsafe_allow_html=True)
    if st.button("⚙️ 관리자"):
        admin_dialog()
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- [화면 전환 로직] ---

# 1. 메인 화면 (4분할)
if st.session_state.page == 'main':
    col1, col2 = st.columns(2)
    categories = list(st.session_state.db.keys())

    with col1:
        if st.button(f"⚙️ {categories[0]}", key="m1"):
            st.session_state.selected_main = categories[0]
            st.session_state.page = 'detail'
            st.rerun()
        if st.button(f"🕹️ {categories[2]}", key="m3"):
            st.session_state.selected_main = categories[2]
            st.session_state.page = 'detail'
            st.rerun()

    with col2:
        if st.button(f"💨 {categories[1]}", key="m2"):
            st.session_state.selected_main = categories[1]
            st.session_state.page = 'detail'
            st.rerun()
        if st.button(f"📁 {categories[3]}", key="m4"):
            st.session_state.selected_main = categories[3]
            st.session_state.page = 'detail'
            st.rerun()

# 2. 상세 페이지 (토글 목록)
elif st.session_state.page == 'detail':
    main_cat = st.session_state.selected_main
    st.title(f"🔍 {main_cat} 상세 내역")
    
    # 해당 계통의 세부 항목 3가지를 토글로 표시
    for sub_item in st.session_state.db[main_cat]:
        with st.expander(f"📍 {sub_item}", expanded=False):
            content = st.session_state.details[main_cat][sub_item]
            st.markdown(f'<div class="detail-card">{content}</div>', unsafe_allow_html=True)