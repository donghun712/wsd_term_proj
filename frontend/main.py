import streamlit as st
import requests
import pandas as pd
import streamlit.components.v1 as components
import os

# ==========================================
# 1. 페이지 및 환경 설정
# ==========================================
st.set_page_config(page_title="LMS Student System", layout="wide", page_icon="🎓")

# [환경변수 로드] 
# 깃허브에 올릴 때는 로컬/서버 환경이 다를 수 있으므로 환경변수로 분리합니다.

# 1. API_URL: 스트림릿(서버)이 백엔드(서버)와 통신하는 주소
# 도커 내부 통신이므로 기본값은 'http://backend:8000/api/v1' 입니다.
API_URL = os.getenv("API_URL", "http://backend:8000/api/v1")

# 2. LOGIN_PAGE_URL: 사용자의 '브라우저'가 접속해야 하는 로그인 페이지 주소
# 로컬 테스트용 기본값은 'http://localhost:8000...' 입니다.
LOGIN_PAGE_URL = os.getenv("LOGIN_PAGE_URL", "http://localhost:8000/static/login.html")

# --- 세션 상태 초기화 ---
if 'access_token' not in st.session_state: st.session_state.access_token = None
if 'user_role' not in st.session_state: st.session_state.user_role = None
if 'user_email' not in st.session_state: st.session_state.user_email = None

def get_headers():
    return {"Authorization": f"Bearer {st.session_state.access_token}"}

# ==========================================
# 2. 인증 로직 함수
# ==========================================

# --- 일반 로그인 (이메일/비번) ---
def login(email, password):
    try:
        # 백엔드와 통신하므로 API_URL 사용
        res = requests.post(f"{API_URL}/auth/login", data={"username": email, "password": password})
        if res.status_code == 200:
            data = res.json()
            token = data.get('access_token')
            if token:
                return fetch_user_info(token)
        return False
    except Exception:
        return False

# --- 회원가입 (닉네임 제거 버전) ---
def register(email, password):
    try:
        # 백엔드 스키마에 맞춰 role='USER' 고정 전송
        res = requests.post(f"{API_URL}/auth/signup", json={
            "email": email,
            "password": password,
            "role": "USER"
        })
        return res
    except Exception as e:
        st.error(f"서버 오류: {e}")
        return None

# --- 소셜 로그인 처리 ---
def process_social_login(id_token):
    try:
        with st.spinner("구글 인증 정보를 서버로 전송 중..."):
            res = requests.post(f"{API_URL}/auth/google", json={"token": id_token})
            
            if res.status_code == 200:
                data = res.json()
                token = data.get('access_token')
                if token and fetch_user_info(token):
                    st.success(f"구글 로그인 성공! ({st.session_state.user_email})")
                    st.rerun()
                else:
                    st.error("사용자 정보를 불러오는 데 실패했습니다.")
            else:
                st.error(f"백엔드 검증 실패: {res.text}")
    except Exception as e:
        st.error(f"서버 연결 오류: {e}")

# --- 공통: 사용자 정보 가져오기 ---
def fetch_user_info(token):
    try:
        me_res = requests.get(f"{API_URL}/users/me", headers={"Authorization": f"Bearer {token}"})
        if me_res.status_code == 200:
            user_info = me_res.json()
            st.session_state.access_token = token
            st.session_state.user_email = user_info.get('email')
            st.session_state.user_role = user_info.get('role')
            return True
        return False
    except:
        return False

# ==========================================
# 3. UI 구성
# ==========================================
st.title("🎓 Term Project LMS")

# ------------------------------------------
# 사이드바 (로그인/회원가입 처리)
# ------------------------------------------
with st.sidebar:
    st.header("계정 관리")
    
    if not st.session_state.access_token:
        tab_login, tab_signup = st.tabs(["로그인", "회원가입"])

        # [Tab 1] 로그인
        with tab_login:
            # A. 일반 로그인
            with st.expander("🔑 이메일 로그인", expanded=True):
                with st.form("login_form"):
                    email = st.text_input("이메일", value="user1@example.com")
                    password = st.text_input("비밀번호", type="password", value="password123")
                    if st.form_submit_button("로그인", type="primary"):
                        if login(email, password):
                            st.rerun()
                        else:
                            st.error("로그인 실패")

            st.markdown("---")
            
            # B. 구글 로그인
            st.subheader("🔵 구글 로그인")
            try:
                # 브라우저에서 접속하는 주소이므로 LOGIN_PAGE_URL 사용
                components.iframe(LOGIN_PAGE_URL, height=350, scrolling=True)
            except Exception:
                st.error("⚠️ 로그인 페이지 로딩 실패")
            
            with st.form("google_token_form"):
                google_token_input = st.text_input("토큰 붙여넣기 (Ctrl+V)")
                if st.form_submit_button("토큰 전송"):
                    if google_token_input:
                        process_social_login(google_token_input)
                    else:
                        st.warning("토큰을 입력해주세요.")

        # [Tab 2] 회원가입
        with tab_signup:
            with st.form("signup_form"):
                new_email = st.text_input("이메일")
                new_pw = st.text_input("비밀번호", type="password")
                
                if st.form_submit_button("가입하기"):
                    if new_email and new_pw:
                        res = register(new_email, new_pw)
                        if res and res.status_code in [200, 201]:
                            st.success("가입 성공! 로그인 탭에서 로그인하세요.")
                        elif res and res.status_code == 400:
                            st.error("이미 존재하는 이메일입니다.")
                        else:
                            st.error(f"가입 실패 (Code: {res.status_code if res else 'None'})")
                    else:
                        st.warning("이메일과 비밀번호를 입력하세요.")

    else:
        # --- 로그인 완료 상태 ---
        st.info(f"접속: {st.session_state.user_email}")
        role_label = "👑 관리자" if st.session_state.user_role == "ADMIN" else "🎓 학생"
        st.success(f"권한: {role_label}")
        
        if st.button("로그아웃"):
            st.session_state.access_token = None
            st.session_state.user_role = None
            st.session_state.user_email = None
            st.rerun()

# ------------------------------------------
# 메인 화면 (권한별 분기)
# ------------------------------------------
if st.session_state.access_token:
    
    # [A] 관리자 화면
    if st.session_state.user_role == "ADMIN":
        st.subheader("👑 관리자 대시보드")
        tab1, tab2, tab3, tab4 = st.tabs(["📊 통계", "📚 강의 관리", "✍️ 강의 개설", "🎬 커리큘럼"])
        
        with tab1:
            if st.button("통계 새로고침"):
                try:
                    res = requests.get(f"{API_URL}/admin/stats", headers=get_headers())
                    if res.status_code == 200:
                        stats = res.json()
                        c1, c2, c3 = st.columns(3)
                        c1.metric("총 유저", stats.get('total_users', 0))
                        c1.metric("총 강의", stats.get('total_courses', 0))
                        c1.metric("총 리뷰", stats.get('total_reviews', 0))
                except: st.error("연결 실패")

        with tab2:
            try:
                res = requests.get(f"{API_URL}/courses", params={"page": 1, "size": 100})
                if res.status_code == 200:
                    content = res.json().get('content', [])
                    if content:
                        df = pd.DataFrame(content)
                        # 존재하는 컬럼만 선택하여 에러 방지
                        cols = [c for c in ['id', 'title', 'instructor_id', 'price'] if c in df.columns]
                        st.dataframe(df[cols], use_container_width=True)
                    else: st.info("강의 없음")
            except: st.error("로딩 실패")

        with tab3:
            with st.form("new_course"):
                title = st.text_input("제목")
                desc = st.text_area("설명")
                price = st.number_input("가격", step=1000)
                if st.form_submit_button("생성"):
                    try:
                        res = requests.post(f"{API_URL}/courses", json={"title": title, "description": desc, "price": price, "level": "BEGINNER", "category_id": 1}, headers=get_headers())
                        if res.status_code == 201: st.success("생성 완료")
                        else: st.error("실패")
                    except: st.error("오류")

        with tab4:
            c_id = st.number_input("강의 ID", min_value=1)
            l_title = st.text_input("영상 제목")
            l_url = st.text_input("URL")
            if st.button("추가"):
                try:
                    res = requests.post(f"{API_URL}/courses/{c_id}/lectures", json={"title": l_title, "video_url": l_url, "order_index": 1}, headers=get_headers())
                    if res.status_code == 201: st.success("추가됨")
                    else: st.error("실패")
                except: st.error("오류")

    # [B] 학생 화면
    else:
        tab1, tab2, tab3 = st.tabs(["🏠 수강 신청", "📺 내 강의실", "👤 내 정보"])

        with tab1:
            try:
                res = requests.get(f"{API_URL}/courses", params={"page": 1, "size": 50})
                if res.status_code == 200:
                    for c in res.json().get('content', []):
                        with st.expander(f"[{c.get('level','?')}] {c['title']} - {c['price']}원"):
                            st.write(c.get('description'))
                            if st.button("신청", key=f"btn_{c['id']}"):
                                r = requests.post(f"{API_URL}/courses/{c['id']}/enroll", headers=get_headers())
                                if r.status_code == 201: st.success("완료")
                                elif r.status_code == 409: st.warning("이미 신청함")
                                else: st.error("실패")
                else: st.error("로딩 실패")
            except: st.error("연결 실패")

        with tab2:
            try:
                res = requests.get(f"{API_URL}/enrollments/me", headers=get_headers())
                if res.status_code == 200:
                    courses = res.json()
                    if courses:
                        opts = {c['title']: c['id'] for c in courses}
                        sel = st.selectbox("강의 선택", list(opts.keys()))
                        cid = opts[sel]
                        
                        st.divider()
                        cv, cr = st.columns([2, 1])
                        with cv:
                            st.markdown(f"### 🎬 {sel}")
                            l_res = requests.get(f"{API_URL}/courses/{cid}/lectures", headers=get_headers())
                            if l_res.status_code == 200:
                                for l in l_res.json():
                                    with st.expander(f"{l['title']}"):
                                        st.video(l['video_url'])
                            else: st.info("영상 없음")
                        
                        with cr:
                            st.markdown("### ⭐ 리뷰")
                            with st.form(f"rev_{cid}"):
                                star = st.slider("별점", 1, 5, 5)
                                cmt = st.text_area("내용")
                                if st.form_submit_button("등록"):
                                    rv = requests.post(f"{API_URL}/courses/{cid}/reviews", json={"rating": star, "comment": cmt}, headers=get_headers())
                                    if rv.status_code == 201: st.success("완료")
                                    else: st.error("실패")
                    else: st.info("수강 중인 강의가 없습니다.")
            except: st.error("오류")

        with tab3:
            try:
                me = requests.get(f"{API_URL}/users/me", headers=get_headers())
                if me.status_code == 200: st.json(me.json())
            except: st.error("정보 로딩 실패")

else:
    st.markdown("## 👋 LMS 시스템에 오신 것을 환영합니다!")
    st.info("왼쪽 사이드바에서 **로그인** 또는 **회원가입**을 해주세요.")