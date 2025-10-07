from app.services.auth import register_user, authenticate_user, login_user
from app.services.user import (
    get_users, get_user_by_id, get_user_by_username, 
    update_user, verify_user, deactivate_user,
    get_users_by_role, get_unverified_users, delete_user
)
from app.services.journal import (
    create_faculty, get_faculties, get_faculty_by_id,
    create_group, get_groups, get_group_by_id,
    create_subject, get_subjects, get_subject_by_id,
    create_subject_group, get_subject_groups, get_subject_group_by_id,
    create_grade, get_grades, update_grade,
    create_attendance, get_attendance, update_attendance,
    get_journal_view, assign_subject_to_teacher, remove_subject_from_teacher,
    get_teacher_subjects
)
