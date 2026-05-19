import streamlit as st
import os, json, base64, html, re, requests
from io import BytesIO

# ════════════════════════════════════════
#  설정 및 초기화
# ════════════════════════════════════════
st.set_page_config(page_title="철도장비 스마트 관리체계", layout="wide")

# 관리자 비밀번호 설정
ADMIN_PASSWORD = "1234" 

# CSS 스타일 적용 (에러 방지 및 디자인 커스텀)
st.markdown("""<style>
.stApp,[data-testid="stAppViewContainer"]{background:#333;color:#E8E8E8}
[data-testid="stHeader"],[data-testid="stSidebar"]{background:#2A2A2A}
.block-container{padding:2rem 1rem 1rem !important;background:#333}

/* 제목 스타일 */
.header-title{
  font-weight:bold;color:#FFD966;text-align:center;
  margin-top:9px;margin-bottom:20px;letter-spacing:2px;
  text-shadow:0 2px 5px rgba(0,0,0,.6);
  font-size:clamp(20px, 5vw, 45px)!important;
}

/* 메인 화면 카테고리 버튼 커스텀 (TypeError height 인자 에러 완벽 해결) */
div[data-testid="stColumn"] div.stButton>button {
    height: 100px !important;
    font-size: 22px !important;
    font-weight: bold !important;
    border: 2px solid #FFD966 !important;
    color: #FFD966 !important;
    background-color: #2D2D2D !important;
    border-radius: 12px !important;
    transition: all 0.3s ease;
}
div[data-testid="stColumn"] div.stButton>button:hover {
    background-color: #FFD966 !important;
    color: #333 !important;
    box-shadow: 0 4px 15px rgba(255, 217, 102, 0.4);
}

/* 관련 업무 매뉴얼 섹션 */
.manual-box {
    border: 2px solid #555;
    border-radius: 12px;
    padding: 25px;
    background-color: #2D2D2D;
    margin-top: 25px;
    text-align: center;
}
.manual-title {
    font-size: 26px;
    font-weight: bold;
    color: #FFD966;
    margin-bottom: 20px;
    display: block;
}

/* 상세 내용 카드 */
.detail-card-content{padding:16px 18px;background:#3E3E3E;border-radius:10px;
  border-left:5px solid #FFD966;font-family:'Nanum Gothic','Malgun Gothic',sans-serif;
  white-space:pre-wrap;word-break:keep-all;font-size:20px;line-height:1.85;color:#E8E8E8}

/* Expander 스타일 조정 */
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
#  GitHub 연동 함수 (Secrets 연동)
# ════════════════════════════════════════
try:
    GITHUB_TOKEN     = st.secrets["GITHUB_TOKEN"]
    GITHUB_REPO      = st.secrets["GITHUB_REPO"]
    GITHUB_FILE_PATH = st.secrets["GITHUB_FILE_PATH"]
except KeyError as e:
    st.error(f"Streamlit Secrets 설정이 누락되었습니다: {e}")
    st.stop()

API_URL  = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main"
HEADERS  = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

@st.cache_data(ttl=5)
def load_data():
    try:
        res = requests.get(API_URL, headers=HEADERS)
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()["content"]).decode('utf-8'))
    except Exception as e:
        st.error(f"GitHub 데이터 로드 실패: {e}")
    return {}

def save_data(data: dict) -> bool:
    try:
        res = requests.get(API_URL, headers=HEADERS)
        if res.status_code != 200: return False
        payload = {
            "message": "Update data.json via Streamlit Admin",
            "content": base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')).decode('utf-8'),
            "sha": res.json()["sha"]
        }
        put = requests.put(API_URL, headers=HEADERS, json=payload)
        if put.status_code in (200, 201):
            st.cache_data.clear() # 수정 사항 즉시 반영을 위한 캐시 초기화
            return True
    except Exception as e:
        st.error(f"GitHub 저장 중 오류 발생: {e}")
    return False

# ════════════════════════════════════════
#  텍스트 포맷 및 데이터 파싱 함수
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
    if not key: return ""
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

menu_cols = st.columns(3)
with menu_cols[0]:
    if st.button("🏠 메인 화면", use_container_width=True, key="nav_main"):
        st.session_state.page = 'main'
        st.session_state.selected_main = None
        st.rerun()
with menu_cols[1]:
    if st.button("📋 요약도 보기", use_container_width=True, key="nav_summary"):
        st.session_state.page = 'summary'
        st.rerun()
with menu_cols[2]:
    if st.button("⚙️ 설정 (관리자)", use_container_width=True, key="nav_admin"):
        st.session_state.page = 'admin_auth'
        st.rerun()

st.divider()

# JSON 데이터 실시간 로드 및 키 정의
details = load_data()
DB_KEYS = [k for k in details.keys() if k != "__meta__"]

# ════════════════════════════════════════
#  [설정 기능] 팝업 비밀번호 인증 함수
# ════════════════════════════════════════
@st.dialog("🔒 관리자 인증")
def auth_dialog():
    st.write("시스템 설정을 변경하려면 비밀번호를 입력하세요.")
    pwd = st.text_input("비밀번호 입력", type="password", key="admin_pwd_input")
    if st.button("확인", use_container_width=True, key="admin_pwd_submit"):
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
#  공통 실시간 검색창
# ════════════════════════════════════════
query = st.text_input("🔍 문제점 및 고장 내용 검색", placeholder="검색어를 입력하세요 (예: 누설, PLC, 타이머)", label_visibility="collapsed")

if query:
    st.markdown(f"### 🔎 '{query}' 검색 결과")
    found = False
    for cat, items in details.items():
        if cat == "__meta__": continue
        for sub, content in items.items():
            text, _ = parse_content(content)
            if query.lower() in text.lower() or query.lower() in sub.lower() or query.lower() in cat.lower():
                found = True
                with st.expander(f"✅ {clean_key(cat)} > {sub}", expanded=True): 
                    render_card(content)
    if not found: 
        st.info("검색 결과가 없습니다.")

# ════════════════════════════════════════
#  1. 메인 화면 (계통 클릭 시 고장내용 확인 연동)
# ════════════════════════════════════════
elif st.session_state.page == 'main':
    st.markdown("### 🗂️ 계통별 고장 조치 매뉴얼")
    
    # 동적 컬럼 생성을 통한 계통 버튼 배치
    if DB_KEYS:
        cat_cols = st.columns(len(DB_KEYS))
        for idx, cat_key in enumerate(DB_KEYS):
            with cat_cols[idx]:
                if st.button(clean_key(cat_key), key=f"cat_{idx}", use_container_width=True):
                    st.session_state.selected_main = cat_key
                    st.session_state.page = 'detail'
                    st.rerun()
    else:
        st.warning("등록된 계통 데이터가 없습니다. 설정 메뉴에서 대분류를 생성해 주세요.")

    # 관련 업무 매뉴얼 다운로드 구역
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
#  2. 상세 고장 내용 리스트 화면
# ════════════════════════════════════════
elif st.session_state.page == 'detail':
    cat = st.session_state.selected_main
    if cat and cat in details:
        if st.button("◀ 뒤로가기", key="back_to_main"):
            st.session_state.page = 'main'
            st.session_state.selected_main = None
            st.rerun()
            
        st.markdown(f"<div class='cat-header'>📍 {clean_key(cat)} 상세 리스트</div>", unsafe_allow_html=True)
        
        if details[cat]:
            for sub, content in details[cat].items():
                with st.expander(f"🔎 {sub}", expanded=False): 
                    render_card(content)
        else:
            st.info("이 계통에 등록된 고장 조치 정보가 없습니다.")
    else:
        st.session_state.page = 'main'
        st.rerun()

# ════════════════════════════════════════
#  3. 요약도 보기 화면
# ════════════════════════════════════════
elif st.session_state.page == 'summary':
    st.markdown("### 📋 장비 계통 요약도")
    st.info("요약도 이미지 또는 도면 정보 공간입니다.")
    if st.button("◀ 메인으로 돌아가기", key="summary_back"):
        st.session_state.page = 'main'
        st.rerun()

# ════════════════════════════════════════
#  4. 설정 메뉴 (비밀번호 후 작성/수정/삭제 기능 및 GitHub 동기화)
# ════════════════════════════════════════
elif st.session_state.page == 'admin' and st.session_state.is_admin:
    st.markdown("## ⚙️ 데이터베이스 관리자 설정")
    
    if st.button("🔒 로그아웃 (관리자 모드 종료)", type="secondary"):
        st.session_state.is_admin = False
        st.session_state.page = 'main'
        st.rerun()
        
    tab1, tab2, tab3 = st.tabs(["📝 항목 수정 및 삭제", "➕ 새 항목 추가", "📂 대분류(계통) 관리"])
    
    # ----------------------------------------------------
    # Tab 1: 내용 수정 및 삭제 (U/D)
    # ----------------------------------------------------
    with tab1:
        st.markdown("### 🔍 기존 고장 매뉴얼 수정/삭제")
        if DB_KEYS:
            edit_cat = st.selectbox("대분류(계통) 선택", DB_KEYS, key="edit_cat_select")
            
            if edit_cat:
                sub_keys = list(details[edit_cat].keys())
                if sub_keys:
                    edit_sub = st.selectbox("소분류(장비/증상) 선택", sub_keys, key="edit_sub_select")
                    
                    # 데이터 분해 후 화면 배치
                    current_content = details[edit_cat][edit_sub]
                    curr_text, curr_imgs = parse_content(current_content)
                    curr_img_str = ", ".join(curr_imgs) if curr_imgs else ""
                    
                    mod_text = st.text_area("매뉴얼 내용 (Markdown 포맷 가능)", value=curr_text, height=200, key="mod_text_input")
                    mod_imgs = st.text_input("이미지 URL (쉼표 `,` 로 구분)", value=curr_img_str, key="mod_imgs_input")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 변경사항 저장", use_container_width=True, type="primary", key="save_edit_btn"):
                            img_list = [img.strip() for img in mod_imgs.split(",") if img.strip()]
                            details[edit_cat][edit_sub] = {"text": mod_text, "images": img_list}
                            
                            if save_data(details):
                                st.success(f"✅ {edit_sub} 수정본이 GitHub에 정상 저장되었습니다.")
                                st.rerun()
                            else:
                                st.error("❌ GitHub 저장 실패. Secrets 권한을 확인하세요.")
                    with col2:
                        if st.button("🗑️ 해당 소분류 삭제", use_container_width=True, key="del_sub_btn"):
                            del details[edit_cat][edit_sub]
                            if save_data(details):
                                st.success(f"🗑️ {edit_sub} 항목이 완전히 삭제되었습니다.")
                                st.rerun()
                else:
                    st.warning("이 계통 산하에 등록된 하위 소분류 항목이 없습니다.")
        else:
            st.info("데이터베이스가 비어 있습니다.")

    # ----------------------------------------------------
    # Tab 2: 새 항목 작성 및 추가 (C)
    # ----------------------------------------------------
    with tab2:
        st.markdown("### ➕ 새로운 고장 조치 정보 추가")
        if DB_KEYS:
            add_cat = st.selectbox("추가할 대상 대분류 선택", DB_KEYS, key="add_cat_select")
            new_sub = st.text_input("새 소분류 명칭 (예: 제동공기압 누설)", key="new_sub_input")
            new_text = st.text_area("고장 내용 및 조치 방법 명세", height=150, placeholder="##1. 증상 명칭\n · 확인사항:\n · 조치방법:", key="new_text_input")
            new_imgs = st.text_input("첨부 이미지 URL (선택 사항, 다중 등록 시 쉼표로 구분)", placeholder="https://raw.githubusercontent.com/.../images/photo.jpg", key="new_imgs_input")
            
            if st.button("➕ 신규 데이터 작성 완료", type="primary", key="add_new_data_btn"):
                if not new_sub or not new_text:
                    st.error("소분류 명칭과 본문 내용을 모두 입력해주세요.")
                elif new_sub in details[add_cat]:
                    st.error("이미 존재하는 명칭입니다. 변경은 '수정' 탭을 이용하세요.")
                else:
                    img_list = [img.strip() for img in new_imgs.split(",") if img.strip()]
                    details[add_cat][new_sub] = {"text": new_text, "images": img_list}
                    
                    if save_data(details):
                        st.success(f"🎉 [{new_sub}] 정보가 {add_cat} 계통에 신규 등록되었습니다.")
                        st.rerun()
        else:
            st.warning("대분류(계통)가 먼저 존재해야 소분류 작성이 가능합니다. 세 번째 탭을 이용해 주세요.")

    # ----------------------------------------------------
    # Tab 3: 대분류(계통) 직접 추가/삭제
    # ----------------------------------------------------
    with tab3:
        st.markdown("### 📂 대분류(계통) 추가")
        new_main_cat = st.text_input("새로운 대분류 이름 입력 (예: 구동계통🛞)", key="new_main_cat_input")
        
        if st.button("📂 신규 대분류 생성", key="create_main_cat_btn"):
            if new_main_cat.strip() and new_main_cat not in details:
                details[new_main_cat.strip()] = {}
                if save_data(details):
                    st.success(f"📂 {new_main_cat} 카테고리가 데이터베이스에 추가되었습니다.")
                    st.rerun()
            else:
                st.error("이름을 다시 확인해 주시거나 중복된 이름인지 확인하십시오.")
                
        st.divider()
        st.markdown("### ⚠️ 위험 Zone: 대분류 삭제")
        if DB_KEYS:
            del_cat = st.selectbox("🚨 삭제할 대분류 선택 (하위 모든 데이터가 소실됩니다)", DB_KEYS, key="del_cat_select")
            if st.button("🚨 대분류 완전 삭제", type="secondary", key="del_main_cat_btn"):
                if del_cat in details:
                    del details[del_cat]
                    if save_data(details):
                        st.success(f"🔥 {del_cat} 및 하위 고장 정보가 완전히 삭제되었습니다.")
                        st.rerun()
        else:
            st.info("삭제할 대분류가 없습니다.")
