import json
import logging
from datetime import date, datetime, timedelta, timezone

from app.database import AsyncSessionLocal, init_db
from app.models.github import GitHubStats
from app.models.leetcode import LeetCodeStats
from app.models.performance import PerformanceScore
from app.models.profiles import StaffProfile, StudentProfile
from app.models.user import Department, Role, User
from app.utils.security import hash_password, hash_password_fast
from sqlalchemy import func, select

logger = logging.getLogger(__name__)


async def seed_db():
    logger.info("Running database migrations and seeds...")

    # 1. Create all tables
    await init_db()

    # 2. Quick check — if data already seeded, skip entirely for fast startup
    async with AsyncSessionLocal() as db:
        user_count_result = await db.execute(select(func.count(User.id)))
        user_count = user_count_result.scalar() or 0
        if user_count >= 120:
            logger.info(f"Database already has {user_count} users — skipping seed (fast startup).")
            return
        logger.info(f"Database has {user_count} users — seeding required.")

    # 3. Seed Data
    async with AsyncSessionLocal() as db:
        # Seed Roles
        roles = ["admin", "staff", "student"]
        for role_name in roles:
            result = await db.execute(select(Role).where(Role.name == role_name))
            if not result.scalar_one_or_none():
                db.add(Role(name=role_name))

        # Seed Departments
        departments = [
            ("CSE", "Computer Science & Engineering"),
            ("IT", "Information Technology"),
            ("AIDS", "AI & Data Science"),
            ("ECE", "Electronics & Communication"),
            ("EEE", "Electrical & Electronics"),
            ("MECH", "Mechanical Engineering"),
        ]
        for code, name in departments:
            result = await db.execute(select(Department).where(Department.code == code))
            if not result.scalar_one_or_none():
                db.add(Department(code=code, name=name))

        await db.commit()

        # Load roles and departments in memory to avoid repetitive queries
        admin_role = (await db.execute(select(Role).where(Role.name == "admin"))).scalar_one()
        staff_role = (await db.execute(select(Role).where(Role.name == "staff"))).scalar_one()
        student_role = (await db.execute(select(Role).where(Role.name == "student"))).scalar_one()

        depts_result = await db.execute(select(Department))
        dept_map = {d.code: d for d in depts_result.scalars().all()}
        cse_dept = dept_map["CSE"]

        # Bulk load existing users, student profiles, and staff profiles in memory
        existing_users_result = await db.execute(select(User.email))
        existing_emails = {row[0].lower() for row in existing_users_result.fetchall()}

        existing_students_result = await db.execute(select(StudentProfile.reg_no))
        existing_regs = {row[0].upper() for row in existing_students_result.fetchall()}

        existing_staff_result = await db.execute(select(StaffProfile.employee_id))
        existing_emps = {row[0].upper() for row in existing_staff_result.fetchall()}

        # Pre-compute hashes for shared passwords (massive speedup: hash once, use many times)
        _admin_hash = hash_password("admin123")
        _student_hash = hash_password_fast("Student@123")
        _staff_hash = hash_password_fast("Staff@123")

        # Seed Admins (3 Access Accounts) — use full-strength hash for admins
        admins_data = [
            ("admin1@vsb.edu.in", "Main Admin"),
            ("admin2@vsb.edu.in", "Technical Admin"),
            ("admin3@vsb.edu.in", "Database Admin")
        ]
        for email, name in admins_data:
            # Query the user model to see if the admin already exists
            user_q = await db.execute(select(User).where(User.email == email))
            existing_user = user_q.scalar_one_or_none()
            if existing_user:
                # Only update role/name/status, NOT password (admin may have changed it)
                existing_user.role_id = admin_role.id
                existing_user.full_name = name
                existing_user.is_active = True
                existing_user.is_verified = True
            else:
                db.add(User(
                    email=email,
                    password_hash=_admin_hash,
                    full_name=name,
                    role_id=admin_role.id,
                    department_id=cse_dept.id,
                    is_active=True,
                    is_verified=True
                ))
                existing_emails.add(email.lower())

        # Seed 100 Students — using fast hash (pre-computed once)
        for i in range(1, 101):
            email = f"student{i}@vsb.edu.in"
            depts = ["CSE", "IT", "AIDS", "ECE", "EEE", "MECH"]
            dept_code = depts[i % len(depts)]
            reg_no = f"23{dept_code}{i:03d}"

            # Skip if already exists in in-memory sets
            if reg_no.upper() in existing_regs:
                continue
            if email.lower() in existing_emails:
                continue

            total_lc = 50 + (i * 3) % 450
            easy_lc = int(total_lc * 0.5)
            med_lc = int(total_lc * 0.35)
            hard_lc = total_lc - easy_lc - med_lc

            commits_gh = 100 + (i * 17) % 1500
            repos_gh = 2 + (i * 3) % 12
            prs_gh = 5 + (i * 7) % 40

            dept_obj = dept_map.get(dept_code, cse_dept)

            try:
                student_user = User(
                    email=email,
                    password_hash=_student_hash,
                    full_name=f"Student {i}",
                    role_id=student_role.id,
                    department_id=dept_obj.id,
                    is_active=True,
                    is_verified=True,
                    phone=f"9876543{i:03d}"
                )
                db.add(student_user)
                await db.flush()

                db.add(StudentProfile(
                    user_id=student_user.id,
                    reg_no=reg_no,
                    year=1 + (i % 4),
                    section=chr(65 + (i % 3)),
                    leetcode_username=f"lc_student{i}",
                    github_username=f"gh_student{i}"
                ))

                db.add(LeetCodeStats(
                    user_id=student_user.id,
                    total_solved=total_lc,
                    easy_solved=easy_lc,
                    medium_solved=med_lc,
                    hard_solved=hard_lc,
                    contest_rating=1200.0 + (i * 11) % 1000,
                    contests_attended=(i * 3) % 25,
                    current_streak=(i * 7) % 30,
                    longest_streak=30 + (i * 2) % 60,
                    submission_calendar=json.dumps({
                        str(int(datetime.combine(date.today() - timedelta(days=d), datetime.min.time()).replace(tzinfo=timezone.utc).timestamp())): (1 + (d + i) % 5)
                        for d in range(15)
                    }),
                    last_synced=datetime.now(tz=timezone.utc)
                ))

                db.add(GitHubStats(
                    user_id=student_user.id,
                    public_repos=repos_gh,
                    total_commits=commits_gh,
                    pull_requests=prs_gh,
                    contribution_streak=(i * 4) % 20,
                    longest_contribution_streak=20 + (i * 3) % 40,
                    contribution_calendar=json.dumps({
                        (date.today() - timedelta(days=d)).isoformat(): (1 + (d + i) % 8)
                        for d in range(15)
                    }),
                    last_synced=datetime.now(tz=timezone.utc)
                ))

                lc_score = min(total_lc * 0.15, 60.0)
                gh_score = min(commits_gh * 0.05, 40.0)
                tot_score = lc_score + gh_score
                placement_score = tot_score * 0.95
                db.add(PerformanceScore(
                    user_id=student_user.id,
                    leetcode_score=lc_score,
                    github_score=gh_score,
                    total_score=tot_score,
                    placement_score=placement_score,
                    classification="Excellent" if tot_score > 75 else "Good" if tot_score > 55 else "Needs Improvement",
                    placement_classification="Excellent" if placement_score > 75 else "Good" if placement_score > 55 else "Needs Improvement",
                    calculated_at=datetime.now(tz=timezone.utc)
                ))
            except Exception as e:
                logger.warning(f"Failed to seed student {i}: {e}")
                continue

        # Seed 20 Staff — using fast hash (pre-computed once)
        designations = ["Assistant Professor", "Associate Professor", "Professor", "HOD"]
        for i in range(1, 21):
            email = f"staff{i}@vsb.edu.in"
            emp_id = f"VSB-STAFF-{i:03d}"

            # Skip if already exists in in-memory sets
            if emp_id.upper() in existing_emps:
                continue
            if email.lower() in existing_emails:
                continue

            depts = ["CSE", "IT", "AIDS", "ECE", "MECH"]
            dept_code = depts[i % len(depts)]
            dept_obj = dept_map.get(dept_code, cse_dept)

            try:
                staff_user = User(
                    email=email,
                    password_hash=_staff_hash,
                    full_name=f"Professor {i}",
                    role_id=staff_role.id,
                    department_id=dept_obj.id,
                    is_active=True,
                    is_verified=True,
                    phone=f"9944123{i:03d}"
                )
                db.add(staff_user)
                await db.flush()

                db.add(StaffProfile(
                    user_id=staff_user.id,
                    employee_id=emp_id,
                    designation=designations[i % len(designations)],
                    leetcode_username=f"lc_staff{i}",
                    github_username=f"gh_staff{i}"
                ))

                total_lc = 30 + (i * 5) % 150
                db.add(LeetCodeStats(
                    user_id=staff_user.id,
                    total_solved=total_lc,
                    easy_solved=int(total_lc * 0.6),
                    medium_solved=int(total_lc * 0.3),
                    hard_solved=total_lc - int(total_lc * 0.6) - int(total_lc * 0.3),
                    current_streak=i % 10,
                    last_synced=datetime.now(tz=timezone.utc)
                ))

                db.add(GitHubStats(
                    user_id=staff_user.id,
                    total_commits=150 + (i * 23) % 400,
                    public_repos=2 + i % 5,
                    last_synced=datetime.now(tz=timezone.utc)
                ))

                db.add(PerformanceScore(
                    user_id=staff_user.id,
                    total_score=50.0 + (i * 2.3) % 40.0,
                    classification="Good",
                    calculated_at=datetime.now(tz=timezone.utc)
                ))
            except Exception as e:
                logger.warning(f"Failed to seed staff {i}: {e}")
                continue

        await db.commit()
    logger.info("Database seeding complete!")
