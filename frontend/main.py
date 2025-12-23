import streamlit as st
import requests
import pandas as pd
import streamlit.components.v1 as components

# ==========================================
# 1. 페이지 및 기본 설정
# ==========================================
st.set_page_config(page_title="LMS Student System", layout="wide", page_icon="🎓")

# ⚠️ 백엔드 API 주소 (데이터 처리용 - 8000번 포트)
BASE_URL = "http://localhost:8000/api/v1"

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
        res = requests.post(f"{BASE_URL}/auth/login", data={"username": email, "password": password})
        if res.status_code == 200:
            data = res.json()
            token = data.get('access_token')
            if token:
                return fetch_user_info(token)
        return False
    except Exception:
        return False

# --- 소셜 로그인 처리 (구글 ID 토큰 -> 백엔드 전송) ---
def process_social_login(id_token):
    try:
        with st.spinner("구글 인증 정보를 서버로 전송 중..."):
            # 8000번 백엔드로 토큰 전송
            res = requests.post(f"{BASE_URL}/auth/google", json={"token": id_token})
            
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
        me_res = requests.get(f"{BASE_URL}/users/me", headers={"Authorization": f"Bearer {token}"})
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
# 사이드바 (로그인 처리)
# ------------------------------------------
with st.sidebar:
    st.header("로그인")
    
    if not st.session_state.access_token:
        # --- A. 일반 로그인 ---
        with st.expander("🔑 이메일 로그인", expanded=False):
            login_type = st.radio("계정 유형", ["학생 (User)", "관리자 (Admin)"])
            
            if login_type == "관리자 (Admin)":
                default_email = "admin@example.com"
                default_pw = "admin_password_123!" 
            else:
                default_email = "user1@example.com"
                default_pw = "password123"

            with st.form("login_form"):
                email = st.text_input("이메일", value=default_email)
                password = st.text_input("비밀번호", type="password", value=default_pw)
                submitted = st.form_submit_button("로그인", type="primary")
                
                if submitted:
                    if login(email, password):
                        st.rerun()
                    else:
                        st.error("로그인 실패: 정보를 확인하세요.")

        st.markdown("---")
        
        # --- B. 구글 로그인 (Iframe 연동: 8888번 포트) ---
        st.subheader("🔵 구글 로그인")
        
        try:
            # ✅ [핵심 수정] 8888번 포트의 login.html을 불러옵니다.
            # 높이를 350으로 넉넉하게 잡아서 토큰 박스가 나와도 잘리게 않게 했습니다.
            components.iframe("http://localhost:8000/static/login.html", height=350, scrolling=True)
        except Exception:
            st.error("⚠️ 로컬 로그인 서버(8000) 연결 실패")
        
        with st.form("google_token_form"):
            google_token_input = st.text_input("토큰 붙여넣기 (Ctrl+V)", placeholder="eyJhbGciOiJSUzI1...")
            submit_token = st.form_submit_button("토큰 전송 (최종 로그인)", type="primary")
            
            if submit_token:
                if google_token_input:
                    process_social_login(google_token_input)
                else:
                    st.warning("토큰을 입력해주세요.")

    else:
        # --- 로그인 완료 상태 ---
        st.info(f"접속 중: {st.session_state.user_email}")
        role_label = "👑 관리자" if st.session_state.user_role == "ADMIN" else "🎓 학생"
        st.success(f"권한: {role_label}")
        
        if st.button("로그아웃", type="secondary"):
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
        
        # 1. 통계
        with tab1:
            if st.button("통계 새로고침"):
                try:
                    res = requests.get(f"{BASE_URL}/admin/stats", headers=get_headers())
                    if res.status_code == 200:
                        stats = res.json()
                        c1, c2, c3 = st.columns(3)
                        c1.metric("총 유저", stats.get('total_users', 0))
                        c1.metric("총 강의", stats.get('total_courses', 0))
                        c1.metric("총 리뷰", stats.get('total_reviews', 0))
                    else:
                        st.error("데이터를 불러올 수 없습니다.")
                except:
                    st.error("서버 연결 실패")

        # 2. 강의 목록
        with tab2:
            try:
                res = requests.get(f"{BASE_URL}/courses", params={"page": 1, "size": 100})
                if res.status_code == 200:
                    content = res.json().get('content', [])
                    if content:
                        df = pd.DataFrame(content)
                        cols = [c for c in ['id', 'title', 'instructor_id', 'price'] if c in df.columns]
                        st.dataframe(df[cols], use_container_width=True)
                    else:
                        st.info("등록된 강의가 없습니다.")
            except:
                st.error("강의 목록 로딩 실패")

        # 3. 강의 개설
        with tab3:
            with st.form("new_course"):
                title = st.text_input("강의 제목")
                desc = st.text_area("설명")
                price = st.number_input("가격", step=1000, min_value=0)
                if st.form_submit_button("강의 생성"):
                    payload = {"title": title, "description": desc, "price": price, "level": "BEGINNER", "category_id": 1}
                    try:
                        res = requests.post(f"{BASE_URL}/courses", json=payload, headers=get_headers())
                        if res.status_code == 201: st.success("강의가 생성되었습니다!")
                        else: st.error(f"실패: {res.text}")
                    except:
                        st.error("서버 오류")

        # 4. 커리큘럼
        with tab4:
            c_id = st.number_input("영상 추가할 강의 ID", min_value=1)
            l_title = st.text_input("영상 제목")
            l_url = st.text_input("YouTube URL")
            if st.button("영상 추가"):
                payload = {"title": l_title, "video_url": l_url, "order_index": 1}
                try:
                    res = requests.post(f"{BASE_URL}/courses/{c_id}/lectures", json=payload, headers=get_headers())
                    if res.status_code == 201: st.success("영상이 추가되었습니다.")
                    else: st.error(f"실패: {res.text}")
                except:
                    st.error("서버 오류")

    # [B] 학생 화면
    else:
        tab1, tab2, tab3 = st.tabs(["🏠 수강 신청 센터", "📺 나의 강의실", "👤 내 정보"])

        # [Tab 1] 수강 신청
        with tab1:
            st.subheader("탐색 & 신청")
            try:
                res = requests.get(f"{BASE_URL}/courses", params={"page": 1, "size": 50})
                if res.status_code == 200:
                    courses = res.json().get('content', [])
                    if courses:
                        for c in courses:
                            with st.expander(f"[{c.get('level','?')}] {c['title']} - {c['price']}원"):
                                st.write(c.get('description', '설명 없음'))
                                if st.button("신청하기", key=f"btn_{c['id']}"):
                                    enroll_res = requests.post(f"{BASE_URL}/courses/{c['id']}/enroll", headers=get_headers())
                                    if enroll_res.status_code == 201: st.success("신청 완료!")
                                    elif enroll_res.status_code == 409: st.warning("이미 신청한 강의입니다.")
                                    else: st.error("신청 실패")
                    else:
                        st.info("등록된 강의가 없습니다.")
                else:
                    st.error("강의 목록을 불러오지 못했습니다.")
            except:
                st.error("서버 연결 실패")

        # [Tab 2] 나의 강의실
        with tab2:
            st.subheader("내 학습 공간")
            try:
                my_res = requests.get(f"{BASE_URL}/enrollments/me", headers=get_headers())
                if my_res.status_code == 200:
                    my_courses = my_res.json()
                    if my_courses and len(my_courses) > 0:
                        course_options = {c['title']: c['id'] for c in my_courses}
                        selected_name = st.selectbox("학습할 강의 선택", list(course_options.keys()))
                        c_id = course_options[selected_name]
                        
                        st.divider()
                        col_vid, col_rev = st.columns([2, 1])
                        
                        # 영상 목록
                        with col_vid:
                            st.markdown(f"### 🎬 {selected_name}")
                            l_res = requests.get(f"{BASE_URL}/courses/{c_id}/lectures", headers=get_headers())
                            if l_res.status_code == 200:
                                lectures = l_res.json()
                                if lectures:
                                    for l in lectures:
                                        with st.expander(f"{l['order_index']}강: {l['title']}"):
                                            st.video(l['video_url'])
                                else:
                                    st.info("등록된 영상이 없습니다.")
                        
                        # 리뷰 작성
                        with col_rev:
                            st.markdown("### ⭐ 리뷰")
                            with st.form(f"rev_{c_id}"):
                                rating = st.slider("별점", 1, 5, 5)
                                comment = st.text_area("수강평")
                                if st.form_submit_button("등록"):
                                    rv = requests.post(f"{BASE_URL}/courses/{c_id}/reviews", json={"rating": rating, "comment": comment}, headers=get_headers())
                                    if rv.status_code == 201: st.success("등록됨!")
                                    else: st.error("실패")
                    else:
                        st.info("신청한 강의가 없습니다. '수강 신청 센터'를 이용해보세요!")
            except:
                st.error("내 강의실 로딩 실패")

        # [Tab 3] 내 정보
        with tab3:
            st.subheader("내 정보")
            try:
                me = requests.get(f"{BASE_URL}/users/me", headers=get_headers())
                if me.status_code == 200:
                    st.json(me.json())
            except:
                st.error("정보 로딩 실패")

else:
    # 로그인 전 메인 화면
    st.markdown("## 👋 LMS 시스템에 오신 것을 환영합니다!")
    st.info("왼쪽 사이드바에서 **로그인**해주세요.")