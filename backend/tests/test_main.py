import pytest
from httpx import AsyncClient

# --- 1. System & Health Check (2개) ---

@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

# --- 2. Authentication & Users (7개) ---

@pytest.mark.asyncio
async def test_signup_success(client: AsyncClient):
    payload = {"email": "test@example.com", "password": "password123", "role": "USER"}
    response = await client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_signup_duplicate_email(client: AsyncClient):
    payload = {"email": "dup@example.com", "password": "password123", "role": "USER"}
    await client.post("/api/v1/auth/signup", json=payload)
    response = await client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_check_email_exists_logic(client: AsyncClient):
    """[신규] 이메일 중복 확인 테스트"""
    test_email = "unique_email_99@example.com"
    response = await client.get(f"/api/v1/users/check-email?email={test_email}")
    assert response.status_code == 200
    assert response.json()["exists"] is False

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post("/api/v1/auth/signup", json={"email": "login@example.com", "password": "password123"})
    payload = {"username": "login@example.com", "password": "password123"}
    response = await client.post("/api/v1/auth/login", data=payload)
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/signup", json={"email": "wrong@example.com", "password": "password123"})
    payload = {"username": "wrong@example.com", "password": "wrongpassword"}
    response = await client.post("/api/v1/auth/login", data=payload)
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_me_without_token(client: AsyncClient):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_change_password_success(client: AsyncClient):
    email = "pass_change@test.com"
    await client.post("/api/v1/auth/signup", json={"email": email, "password": "old_password"})
    login = await client.post("/api/v1/auth/login", data={"username": email, "password": "old_password"})
    token = login.json()["access_token"]
    
    payload = {"old_password": "old_password", "new_password": "new_password123"}
    res = await client.post("/api/v1/users/me/password", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

# --- 3. Categories & Admin Stats (5개) ---

@pytest.mark.asyncio
async def test_create_category_admin(client: AsyncClient):
    email = "admin_cat@test.com"
    await client.post("/api/v1/auth/signup", json={"email": email, "password": "password123", "role": "ADMIN"})
    login_res = await client.post("/api/v1/auth/login", data={"username": email, "password": "password123"})
    token = login_res.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.post("/api/v1/categories", json={"name": "Python"}, headers=headers)
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_admin_daily_stats_logic(client: AsyncClient):
    """[신규] 관리자 전용 일별 통계 테스트"""
    email = "admin_stats@test.com"
    await client.post("/api/v1/auth/signup", json={"email": email, "password": "password123", "role": "ADMIN"})
    login = await client.post("/api/v1/auth/login", data={"username": email, "password": "password123"})
    token = login.json()["access_token"]
    
    response = await client.get("/api/v1/admin/stats/daily", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "today" in response.json()

@pytest.mark.asyncio
async def test_create_category_user_fail(client: AsyncClient):
    email = "user_cat@test.com"
    await client.post("/api/v1/auth/signup", json={"email": email, "password": "password123", "role": "USER"})
    login_res = await client.post("/api/v1/auth/login", data={"username": email, "password": "password123"})
    token = login_res.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.post("/api/v1/categories", json={"name": "Hacking"}, headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_list_categories(client: AsyncClient):
    response = await client.get("/api/v1/categories")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_create_duplicate_category(client: AsyncClient):
    email = "admin_dup@test.com"
    await client.post("/api/v1/auth/signup", json={"email": email, "password": "password123", "role": "ADMIN"})
    login_res = await client.post("/api/v1/auth/login", data={"username": email, "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    await client.post("/api/v1/categories", json={"name": "Java"}, headers=headers)
    response = await client.post("/api/v1/categories", json={"name": "Java"}, headers=headers)
    assert response.status_code == 409

# --- 4. Courses & Search (7개) ---

@pytest.mark.asyncio
async def test_create_course(client: AsyncClient):
    email = "course_maker@test.com"
    await client.post("/api/v1/auth/signup", json={"email": email, "password": "password123", "role": "USER"})
    login_res = await client.post("/api/v1/auth/login", data={"username": email, "password": "password123"})
    token = login_res.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"title": "FastAPI Master", "description": "Good", "price": 10000}
    response = await client.post("/api/v1/courses", json=payload, headers=headers)
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_search_courses_query_logic(client: AsyncClient):
    """[신규] 강의 전용 검색 API 테스트"""
    response = await client.get("/api/v1/courses/search/query?keyword=FastAPI")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_filter_recent_courses_logic(client: AsyncClient):
    """[신규] 최신 강의 필터 테스트"""
    response = await client.get("/api/v1/courses/filter/recent?limit=5")
    assert response.status_code == 200
    assert len(response.json()) <= 5

@pytest.mark.asyncio
async def test_list_courses_pagination(client: AsyncClient):
    response = await client.get("/api/v1/courses?page=1&size=5")
    assert response.status_code == 200
    data = response.json()
    assert "content" in data

@pytest.mark.asyncio
async def test_get_course_detail(client: AsyncClient):
    email = "detail_maker@test.com"
    await client.post("/api/v1/auth/signup", json={"email": email, "password": "password123", "role": "USER"})
    login_res = await client.post("/api/v1/auth/login", data={"username": email, "password": "password123"})
    token = login_res.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    create_res = await client.post("/api/v1/courses", json={"title": "Detail Test"}, headers=headers)
    course_id = create_res.json()["id"]
    
    response = await client.get(f"/api/v1/courses/{course_id}")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_update_course_unauthorized(client: AsyncClient):
    email_a = "user_a@test.com"
    await client.post("/api/v1/auth/signup", json={"email": email_a, "password": "password123", "role": "USER"})
    token_a = (await client.post("/api/v1/auth/login", data={"username": email_a, "password": "password123"})).json()["access_token"]
    
    create_res = await client.post("/api/v1/courses", json={"title": "A Course"}, headers={"Authorization": f"Bearer {token_a}"})
    course_id = create_res.json()["id"]
    
    email_b = "user_b@test.com"
    await client.post("/api/v1/auth/signup", json={"email": email_b, "password": "password123", "role": "USER"})
    token_b = (await client.post("/api/v1/auth/login", data={"username": email_b, "password": "password123"})).json()["access_token"]
    
    response = await client.put(f"/api/v1/courses/{course_id}", json={"title": "Hacked"}, headers={"Authorization": f"Bearer {token_b}"})
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_delete_course_success(client: AsyncClient):
    email = "del_user@test.com"
    await client.post("/api/v1/auth/signup", json={"email": email, "password": "password123", "role": "USER"})
    token = (await client.post("/api/v1/auth/login", data={"username": email, "password": "password123"})).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    create_res = await client.post("/api/v1/courses", json={"title": "To Delete"}, headers=headers)
    course_id = create_res.json()["id"]
    
    response = await client.delete(f"/api/v1/courses/{course_id}", headers=headers)
    assert response.status_code == 204

# --- 5. Files (2개) ---

@pytest.mark.asyncio
async def test_file_upload_logic(client: AsyncClient):
    """[신규] 파일 업로드 테스트"""
    files = {"file": ("test.txt", b"hello world", "text/plain")}
    response = await client.post("/api/v1/files/upload", files=files)
    assert response.status_code == 201
    assert "url" in response.json()

@pytest.mark.asyncio
async def test_file_retrieve_logic(client: AsyncClient):
    """[신규] 파일 조회 테스트"""
    files = {"file": ("test_get.txt", b"get content", "text/plain")}
    upload = await client.post("/api/v1/files/upload", files=files)
    url = upload.json()["url"]
    
    response = await client.get(url)
    assert response.status_code == 200

# --- 6. Lectures, Enrollments & Reviews (6개) ---

@pytest.mark.asyncio
async def test_create_lecture(client: AsyncClient):
    email = "lec_user@test.com"
    await client.post("/api/v1/auth/signup", json={"email": email, "password": "password123", "role": "USER"})
    token = (await client.post("/api/v1/auth/login", data={"username": email, "password": "password123"})).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    c_res = await client.post("/api/v1/courses", json={"title": "Lec Course"}, headers=headers)
    cid = c_res.json()["id"]
    
    payload = {"title": "Intro", "video_url": "http://video.com", "order_index": 1}
    response = await client.post(f"/api/v1/courses/{cid}/lectures", json=payload, headers=headers)
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_list_lectures(client: AsyncClient):
    email = "lec_list_user@test.com"
    await client.post("/api/v1/auth/signup", json={"email": email, "password": "password123", "role": "USER"})
    token = (await client.post("/api/v1/auth/login", data={"username": email, "password": "password123"})).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    c_res = await client.post("/api/v1/courses", json={"title": "Lec List"}, headers=headers)
    cid = c_res.json()["id"]
    await client.post(f"/api/v1/courses/{cid}/lectures", json={"title": "Lecture 1", "video_url": "http://v.com"}, headers=headers)
    
    response = await client.get(f"/api/v1/courses/{cid}/lectures")
    assert response.status_code == 200
    assert len(response.json()) == 1

@pytest.mark.asyncio
async def test_enroll_course(client: AsyncClient):
    inst_email = "inst_enr@test.com"
    await client.post("/api/v1/auth/signup", json={"email": inst_email, "password": "password123", "role": "USER"})
    inst_token = (await client.post("/api/v1/auth/login", data={"username": inst_email, "password": "password123"})).json()["access_token"]
    c_res = await client.post("/api/v1/courses", json={"title": "Enroll Me"}, headers={"Authorization": f"Bearer {inst_token}"})
    cid = c_res.json()["id"]
    
    stu_email = "student@test.com"
    await client.post("/api/v1/auth/signup", json={"email": stu_email, "password": "password123", "role": "USER"})
    stu_token = (await client.post("/api/v1/auth/login", data={"username": stu_email, "password": "password123"})).json()["access_token"]
    
    response = await client.post(f"/api/v1/courses/{cid}/enroll", headers={"Authorization": f"Bearer {stu_token}"})
    assert response.status_code == 201
    assert response.json()["status"] == "ACTIVE"

@pytest.mark.asyncio
async def test_enroll_duplicate_fail(client: AsyncClient):
    inst_email = "inst_dup@test.com"
    await client.post("/api/v1/auth/signup", json={"email": inst_email, "password": "password123", "role": "USER"})
    inst_token = (await client.post("/api/v1/auth/login", data={"username": inst_email, "password": "password123"})).json()["access_token"]
    c_res = await client.post("/api/v1/courses", json={"title": "Dup Test"}, headers={"Authorization": f"Bearer {inst_token}"})
    cid = c_res.json()["id"]
    
    stu_email = "stu_dup@test.com"
    await client.post("/api/v1/auth/signup", json={"email": stu_email, "password": "password123", "role": "USER"})
    stu_token = (await client.post("/api/v1/auth/login", data={"username": stu_email, "password": "password123"})).json()["access_token"]
    headers = {"Authorization": f"Bearer {stu_token}"}
    
    await client.post(f"/api/v1/courses/{cid}/enroll", headers=headers)
    response = await client.post(f"/api/v1/courses/{cid}/enroll", headers=headers)
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_get_my_enrollments(client: AsyncClient):
    email = "my_enr@test.com"
    await client.post("/api/v1/auth/signup", json={"email": email, "password": "password123", "role": "USER"})
    token = (await client.post("/api/v1/auth/login", data={"username": email, "password": "password123"})).json()["access_token"]
    
    response = await client.get("/api/v1/enrollments/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_create_review(client: AsyncClient):
    inst_email = "rev_inst@test.com"
    await client.post("/api/v1/auth/signup", json={"email": inst_email, "password": "password123", "role": "USER"})
    inst_token = (await client.post("/api/v1/auth/login", data={"username": inst_email, "password": "password123"})).json()["access_token"]
    c_res = await client.post("/api/v1/courses", json={"title": "Review Class"}, headers={"Authorization": f"Bearer {inst_token}"})
    cid = c_res.json()["id"]
    
    stu_email = "reviewer@test.com"
    await client.post("/api/v1/auth/signup", json={"email": stu_email, "password": "password123", "role": "USER"})
    stu_token = (await client.post("/api/v1/auth/login", data={"username": stu_email, "password": "password123"})).json()["access_token"]
    headers = {"Authorization": f"Bearer {stu_token}"}
    
    await client.post(f"/api/v1/courses/{cid}/enroll", headers=headers)
    
    payload = {"rating": 5, "comment": "Great course!"}
    response = await client.post(f"/api/v1/courses/{cid}/reviews", json=payload, headers=headers)
    assert response.status_code == 201