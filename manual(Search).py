import streamlit as st
import os, json, base64, html, re, requests
from io import BytesIO

# ════════════════════════════════════════
#  설정 및 초기화
# ════════════════════════════════════════
st.set_page_config(page_title="철도장비 스마트 관리체계", layout="wide")

# 관리자 비밀번호 설정
ADMIN_PASSWORD = "1234" 

# CSS 스타일 적용
st.markdown("""<style>
.stApp,[data-testid="stAppViewContainer"]{background:#333;color:#E8E8E8}
[data-testid="stHeader"],[data-testid="stSidebar"]{background:#2A2A2A}
.block-container{padding:2rem 1rem 1rem !important;background:#333}

/* 제목 */
.header-title{
  font-weight:bold;color:#FFD966;text-align:center;
  margin-top:9px;margin-bottom:20px;letter-spacing:2px;
  text-shadow:0 2px 5px rgba(0,0,0,.6);
  font-size:clamp(20px, 5vw, 45px)!important;
}

/* 관련 업무 매뉴얼 섹션 */
.manual-box {
    border: 2px solid #555;
    border-radius: 12px;
    padding: 25px;
    background-color: #2D2D2D;
    margin-top: 15px;
    text-align: center;
}
.manual-title {
    font-size: 28px;
    font-weight: bold;
    color: #FFD966;
    margin-bottom: 20px;
    display: block;
}

/* 상세 내용 카드 */
.detail-card-content{padding:16px 18px;background:#3E3E3E;border-radius:10px;
  border-left:5px solid #FFD966;font-family:'Nanum Gothic','Malgun Gothic',sans-serif;
  white-space:pre-wrap;word-break:keep-all;font-size:20px;line-height:1.85;color:#E8E8E8}

/* Expander 크기 조정 */
[data-testid="stExpander"]{background:#3A3A3A!important;border:1px solid #4A4A4A!important;border-radius:10px!important;margin-bottom:6px}
[data-testid="stExpander"] summary{color:#E8E8E8!important;font-weight:bold;font-size:22px!important;padding:10px!important}

/* 상세 화면 카테고리 제목 */
.cat-header{font-size:32px;font-weight:bold;color:#FFD966;margin:6px 0 15px;padding-bottom:8px;border-bottom:1px solid #555}
</style>""", unsafe_allow_html=True)

# Session State 초기화
if "page" not in st.session_state: st.session_state.page = 'main'
if "selected_main" not in st.session_state: st.session_state.selected_main = None
if "is_admin" not in st.session_state: st.session_state.is_admin = False

# ════════════════════════════════════════
#  GitHub 연동 함수
# ════════════════════════════════════════
GITHUB_TOKEN     = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO      = st.secrets["GITHUB_REPO"]
GITHUB_FILE_PATH = st.secrets["GITHUB_FILE_PATH"]
API_URL  = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main"
HEADERS  = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

@st.cache_data(ttl=10)
def load_data():
    try:
        res = requests.get(API_URL, headers=HEADERS)
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()["content"]).decode('utf-8'))
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
    return {}

def save_data(data: dict) -> bool:
    res = requests.get(API_URL, headers=HEADERS)
    if res.status_code != 200: return False
    payload = {
        "message": "Update data.json via Streamlit Admin",
        "content": base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')).decode('utf-8'),
        "sha": res.json()["sha"]
    }
    put = requests.put(API_URL, headers=HEADERS, json=payload)
    if put.status_code in (200, 201):
        st.cache_data.clear() # 캐시 초기화하여 즉시 반영
        return True
    return False

# ════════════════════════════════════════
#  텍스트 포맷 및 헬퍼 함수
# ════════════════════════════════════════
FORMATS = [
    (r'(?m)^### (.+)$', r'<span style="font-size:22px !important;font-weight:bold;color:#FFD966">\1</span>'),
    (r'(?m)^## (.+)$',  r'<span style="font-size:24px !important;font-weight:bold;color:#FFD966">\1</span>'),
    (r'(?m)^# (.+)$',   r'<span style="font-size:26px !important;font-weight:bold;color:#FFD966">\1</span>'),
    (r'!!(.+?)!!',      r'<span style="color:#FF6B6B !important;font-weight:bold">\1</span>'),
]

def render_content(text: str) -> str:
    s = html.escape(text)
    for pat, rep in FORMATS: s = re.sub(pat, rep, s)
    return s.replace('\n', '<br>')

def clean_key(key: str) -> str:
    return re.sub(r'\^\^\^(.+?)\^\^\^|##(.+?)##|^#+\s*', r'\1\2', key).strip()

def parse_content(content) -> tuple[str, list]:
    if isinstance(content, dict): 
        return content.get("text", ""), content.get("images", [])
    return str(content), []

def render_card(content):
    text, images = parse_content(content)
    st.markdown(f'<div class="detail-card-content">{render_content(text)}</div>', unsafe_allow_html=True)
    for url in images: 
        if url.strip(): st.image(url.strip(), use_container_width=True)

# ════════════════════════════════════════
#  상단 네비게이션 헤더
# ════════════════════════════════════════
st.markdown("<p class='header-title'>철도장비 스마트 관리체계</p>", unsafe_allow_html=True)

# Streamlit 표준 버튼을 활용한 안정적인 메뉴 구성
menu_cols = st.columns(3)
with menu_cols[0]:
    if st.button("🏠 메인 화면", use_container_width=True):
        st.session_state.page = 'main'
        st.session_state.selected_main = None
        st.rerun()
with menu_cols[1]:
    if st.button("📋 요약도 보기", use_container_width=True):
        st.session_state.page = 'summary'
        st.rerun()
with menu_cols[2]:
    if st.button("⚙️ 설정 (관리자)", use_container_width=True):
        st.session_state.page = 'admin_auth'
        st.rerun()

st.divider()

# 데이터 불러오기
details = load_data()
DB_KEYS = [k for k in details.keys() if k != "__meta__"]

# ════════════════════════════════════════
#  [모달 창] 비밀번호 인증 팝업 기능
# ════════════════════════════════════════
@st.dialog("🔒 관리자 인증")
def auth_dialog():
    st.write("시스템 설정을 변경하려면 비밀번호를 입력하세요.")
    pwd = st.text_input("비밀번호 입력", type="password")
    if st.button("확인", use_container_width=True):
        if pwd == ADMIN_PASSWORD:
            st.session_state.is_admin = True
            st.session_state.page = 'admin'
            st.rerun()
        else:
            st.error("비밀번호가 일치하지 않습니다.")

if st.session_state.page == 'admin_auth':
    if st.session_state.is_admin:
        st.session_state.page = 'admin'
        st.rerun()
    else:
        auth_dialog()
        st.session_state.page = 'main'

# ════════════════════════════════════════
#  공통 검색창 (메인 및 상세 페이지에서 작동)
# ════════════════════════════════════════
query = st.text_input("🔍 문제점 및 고장 내용 검색", placeholder="검색어를 입력하세요 (예: 누설, PLC, 타이머)", label_visibility="collapsed")

if query:
    st.markdown(f"### 🔎 '{query}' 검색 결과")
    found = False
    for cat, items in details.items():
        if cat == "__meta__": continue
        for sub, content in items.items():
            text, _ = parse_content(content)
            if query in text or query in sub or query in cat:
                found = True
                with st.expander(f"✅ {clean_key(cat)} > {sub}", expanded=True): 
                    render_card(content)
    if not found: 
        st.info("검색 결과가 없습니다.")

# ════════════════════════════════════════
#  메인 화면 (카테고리 선택 및 매뉴얼 다운로드)
# ════════════════════════════════════════
elif st.session_state.page == 'main':
    st.markdown("### 🗂️ 계통별 고장 조치 매뉴얼")
    
    # 카테고리 버튼 그리드 배치
    cat_cols = st.columns(len(DB_KEYS))
    for idx, cat_key in enumerate(DB_KEYS):
        with cat_cols[idx]:
            if st.button(clean_key(cat_key), key=f"cat_{idx}", use_container_width=True, height=100):
                st.session_state.selected_main = cat_key
                st.session_state.page = 'detail'
                st.rerun()

    # 관련 업무 매뉴얼 섹션
    st.markdown('<div class="manual-box">', unsafe_allow_html=True)
    st.markdown('<span class="manual-title">📚 관련 업무 매뉴얼 다운로드</span>', unsafe_allow_html=True)
    
    manual_files = {
        "📘 유지보수 매뉴얼": "maintenance_manual.pdf",
        "📙 비상시 조치방법": "emergency_manual.pdf",
        "📗 운전원 일상점검": "daily_inspection.pdf"
    }
    
    m_cols = st.columns(len(manual_files))
    for idx, (label, filename) in enumerate(manual_files.items()):
        with m_cols[idx]:
            file_url = f"{RAW_BASE}/manuals/{filename}"
            try:
                res = requests.get(file_url, timeout=3)
                if res.status_code == 200:
                    st.download_button(label=label, data=res.content, file_name=filename, key=f"btn_dl_{idx}", use_container_width=True)
                else:
                    st.button(f"❌ {filename} 없음", disabled=True, key=f"err_{idx}", use_container_width=True)
            except:
                st.button("⚠️ 연결 오류", disabled=True, key=f"err_conn_{idx}", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════
#  상세 화면 (선택된 카테고리의 고장 내용 표시)
# ════════════════════════════════════════
elif st.session_state.page == 'detail':
    cat = st.session_state.selected_main
    if cat and cat in details:
        if st.button("◀ 뒤로가기", key="back_to_main"):
            st.session_state.page = 'main'
            st.session_state.selected_main = None
            st.rerun()
            
        st.markdown(f"<div class='cat-header'>📍 {clean_key(cat)} 상세 리스트</div>", unsafe_allow_html=True)
        
        for sub, content in details[cat].items():
            with st.expander(f"🔎 {sub}", expanded=False): 
                render_card(content)
    else:
        st.session_state.page = 'main'
        st.rerun()

# ════════════════════════════════════════
#  요약도 보기 화면
# ════════════════════════════════════════
elif st.session_state.page == 'summary':
    st.markdown("### 📋 장비 계통 요약도")
    st.info("요약도 이미지 또는 도면 정보가 들어갈 자리입니다.")
    # 필요시 여기에 RAW_BASE 환경의 요약도 이미지 배치 가능
    if st.button("◀ 메인으로 돌아가기"):
        st.session_state.page = 'main'
        st.rerun()

# ════════════════════════════════════════
#  ⚙️ 설정 메뉴 (관리자 전용 CRUD 완전 구현)
# ════════════════════════════════════════
elif st.session_state.page == 'admin' and st.session_state.is_admin:
    st.markdown("## ⚙️ 데이터베이스 관리자 설정")
    
    if st.button("🔒 로그아웃 (관리자 모드 종료)"):
        st.session_state.is_admin = False
        st.session_state.page = 'main'
        st.rerun()
        
    tab1, tab2, tab3 = st.tabs(["📝 항목 수정 및 삭제", "➕ 새 항목 추가", "📂 대분류(계통) 관리"])
    
    # ----------------------------------------------------
    # Tab 1: 기존 내용 수정 및 삭제
    # ----------------------------------------------------
    with tab1:
        st.markdown("### 🔍 기존 고장 매뉴얼 수정/삭제")
        edit_cat = st.selectbox("대분류(계통) 선택", DB_KEYS, key="edit_cat")
        
        if edit_cat:
            sub_keys = list(details[edit_cat].keys())
            if sub_keys:
                edit_sub = st.selectbox("소분류(장비/증상) 선택", sub_keys, key="edit_sub")
                
                # 기존 데이터 분해
                current_content = details[edit_cat][edit_sub]
                curr_text, curr_imgs = parse_content(current_content)
                curr_img_str = ", ".join(curr_imgs) if curr_imgs else ""
                
                # 입력 폼
                mod_text = st.text_area("매뉴얼 내용 (Markdown 포맷 활용 가능)", value=curr_text, height=200)
                mod_imgs = st.text_input("이미지 URL (쉼표로 여러 개 구분)", value=curr_img_str)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 변경사항 저장", use_container_width=True, type="primary"):
                        img_list = [img.strip() for img in mod_imgs.split(",") if img.strip()]
                        details[edit_cat][edit_sub] = {"text": mod_text, "images": img_list}
                        
                        if save_data(details):
                            st.success(f"✅ {edit_sub} 항목이 성공적으로 업데이트되어 GitHub에 저장되었습니다.")
                        else:
                            st.error("❌ GitHub 저장에 실패했습니다. 토큰 및 권한 설정을 확인하세요.")
                with col2:
                    if st.button("🗑️ 해당 소분류 삭제", use_container_width=True):
                        del details[edit_cat][edit_sub]
                        if save_data(details):
                            st.success(f"🗑️ {edit_sub} 항목이 완전히 삭제되었습니다.")
                            st.rerun()
            else:
                st.warning("이 카테고리에는 하위 소분류 항목이 없습니다.")

    # ----------------------------------------------------
    # Tab 2: 새 항목 추가 (소분류 추가)
    # ----------------------------------------------------
    with tab2:
        st.markdown("### ➕ 새로운 고장 조치 정보 추가")
        add_cat = st.selectbox("추가할 대상 대분류 선택", DB_KEYS, key="add_cat")
        new_sub = st.text_input("새 소분류 명칭 (예: 압력 벨브 오작동)")
        new_text = st.text_area("고장 내용 및 조치 방법 명세", height=150, placeholder="##1. 증상 내용\n · 확인사항:\n · 조치방법:")
        new_imgs = st.text_input("첨부 이미지 URL (선택 사항)", placeholder="https://example.com/image.jpg")
        
        if st.button("➕ 신규 데이터 추가", type="primary"):
            if not new_sub or not new_text:
                st.error("소분류 명칭과 내용을 모두 입력해주세요.")
            elif new_sub in details[add_cat]:
                st.error("이미 존재하는 소분류 명칭입니다. '수정' 탭을 이용하세요.")
            else:
                img_list = [img.strip() for img in new_imgs.split(",") if img.strip()]
                details[add_cat][new_sub] = {"text": new_text, "images": img_list}
                
                if save_data(details):
                    st.success(f"🎉 [{new_sub}] 항목이 {add_cat} 계통에 추가되어 반영되었습니다.")
                    st.rerun()

    # ----------------------------------------------------
    # Tab 3: 대분류(계통) 생성 및 제거
    # ----------------------------------------------------
    with tab3:
        st.markdown("### 📂 대분류(계통) 추가 및 삭제")
        new_main_cat = st.text_input("새로운 대분류(계통) 이름 입력 (예: 유압계통 ⚙️)")
        
        if st.button("📂 신규 대분류 생성"):
            if new_main_cat.strip() and new_main_cat not in details:
                details[new_main_cat.strip()] = {}
                if save_data(details):
                    st.success(f"📂 {new_main_cat} 카테고리가 생성되었습니다.")
                    st.rerun()
            else:
                st.error("올바른 이름을 입력하거나 중복 여부를 확인하세요.")
                
        st.divider()
        st.markdown("### ⚠️ 위험 구역: 대분류 삭제")
        del_cat = st.selectbox("🚨 삭제할 대분류 선택 (하위 모든 데이터가 함께 삭제됩니다)", DB_KEYS, key="del_cat")
        if st.button("🚨 대분류 완전 삭제", type="secondary"):
            if del_cat in details:
                del details[del_cat]
                if save_data(details):
                    st.success(f"🔥 {del_cat} 및 그 하위 데이터가 모두 삭제되었습니다.")
                    st.rerun()
