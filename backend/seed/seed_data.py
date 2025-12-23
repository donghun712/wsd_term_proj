# backend/seed/seed_data.py
import asyncio
import random
import sys
import os

from faker import Faker
from sqlalchemy import select, text

# 프로젝트 루트(/app) 기준 import 되도록 path 보정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import engine, Base, async_session_maker
from src import models, security

fake = Faker("ko_KR")


async def seed_data() -> None:
    print("🌱 시드 데이터 생성을 시작합니다...")

    # 안전장치: 테이블 없으면 생성
    print("🛠️ 테이블 생성 중...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 테이블 생성 완료!")

    async with async_session_maker() as db:
        try:
            # ---------------------------
            # 1) 관리자 계정 생성
            # ---------------------------
            admin_email = "admin@example.com"
            res = await db.execute(select(models.User).where(models.User.email == admin_email))
            if not res.scalars().first():
                admin = models.User(
                    email=admin_email,
                    hashed_password=security.get_password_hash("admin_password_123!"),
                    role=models.UserRole.ADMIN,
                    provider="LOCAL",
                )
                db.add(admin)
                await db.commit()
                print("✅ 관리자 계정 생성 완료")
            else:
                print("ℹ️ 관리자 계정은 이미 존재합니다.")

            # ---------------------------
            # 2) 일반 유저 생성 (30명)
            # ---------------------------
            created_users = 0
            for i in range(30):
                email = f"user{i+1}@example.com"
                res = await db.execute(select(models.User).where(models.User.email == email))
                if res.scalars().first():
                    continue

                user = models.User(
                    email=email,
                    hashed_password=security.get_password_hash("password123"),
                    role=models.UserRole.USER,
                    provider="LOCAL",
                )
                db.add(user)
                created_users += 1

            if created_users:
                await db.commit()
                print(f"✅ 일반 유저 {created_users}명 생성 완료")
            else:
                print("ℹ️ 일반 유저는 이미 존재합니다.")

            # ✅ 가장 중요한 방어: ORM enum 비교 대신 SQL로 role='USER' 강제
            rows = (await db.execute(text("SELECT id FROM users WHERE role='USER'"))).fetchall()
            user_ids = [r[0] for r in rows]
            print(f"🔎 USER 역할 유저 수: {len(user_ids)}")

            # ---------------------------
            # 3) 카테고리 생성
            # ---------------------------
            categories = ["프로그래밍", "디자인", "마케팅", "비즈니스", "외국어"]
            created_cat = 0
            for name in categories:
                res = await db.execute(select(models.Category).where(models.Category.name == name))
                if not res.scalars().first():
                    db.add(models.Category(name=name))
                    created_cat += 1
            await db.commit()
            print(f"✅ 카테고리 생성/확인 완료 (신규 {created_cat}개)")

            cat_rows = (await db.execute(text("SELECT id FROM categories"))).fetchall()
            cat_ids = [r[0] for r in cat_rows]
            print(f"🔎 카테고리 수: {len(cat_ids)}")

            if not user_ids or not cat_ids:
                print("⚠️ 유저 또는 카테고리가 없어 강의 생성을 중단합니다.")
                return

            # ---------------------------
            # 4) 강의 생성 (20개)
            # ---------------------------
            new_courses = []
            for _ in range(20):
                inst_id = random.choice(user_ids)
                cat_id = random.choice(cat_ids)
                new_courses.append(
                    models.Course(
                        title=fake.catch_phrase(),
                        description=fake.text(),
                        price=random.randint(0, 10) * 10000,
                        level=random.choice(["BEGINNER", "INTERMEDIATE", "ADVANCED"]),
                        instructor_id=inst_id,
                        category_id=cat_id,
                        is_public=True,
                        thumbnail_url=None,
                    )
                )

            db.add_all(new_courses)
            await db.commit()
            print("✅ 강의 20개 생성 완료")

            course_rows = (await db.execute(text("SELECT id FROM courses"))).fetchall()
            course_ids = [r[0] for r in course_rows]
            print(f"🔎 강의 수: {len(course_ids)}")

            # ---------------------------
            # 5) 강의 회차 생성 (각 강의당 3개)
            # ---------------------------
            new_lectures = []
            for cid in course_ids:
                for i in range(3):
                    new_lectures.append(
                        models.Lecture(
                            title=f"강의 {cid} - {i+1}강",
                            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                            order_index=i + 1,
                            course_id=cid,
                        )
                    )
            db.add_all(new_lectures)
            await db.commit()
            print("✅ 강의 회차 생성 완료")

            # ---------------------------
            # 6) 수강 신청 & 리뷰 생성
            # ---------------------------
            enrollment_pairs = set()
            new_enrollments = []
            new_reviews = []

            attempts = 0
            while len(new_enrollments) < 150 and attempts < 1000:
                attempts += 1
                uid = random.choice(user_ids)
                cid = random.choice(course_ids)
                pair = (uid, cid)
                if pair in enrollment_pairs:
                    continue
                enrollment_pairs.add(pair)

                new_enrollments.append(
                    models.Enrollment(user_id=uid, course_id=cid, status="ACTIVE")
                )

                if random.random() < 0.7:
                    new_reviews.append(
                        models.Review(
                            user_id=uid,
                            course_id=cid,
                            rating=random.randint(1, 5),
                            comment=fake.sentence(),
                        )
                    )

            db.add_all(new_enrollments)
            await db.commit()
            print(f"✅ 수강 신청 {len(new_enrollments)}개 생성 완료")

            db.add_all(new_reviews)
            await db.commit()
            print(f"✅ 리뷰 {len(new_reviews)}개 생성 완료")

            print("🌳 시드 데이터 생성 완료! (200+ 목표)")

        except Exception as e:
            print(f"❌ 데이터 생성 중 오류 발생: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_data())
