from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Dict, Optional, Any
from datetime import date

from app.models import (
    Faculty, Group, Subject, SubjectGroup, 
    Grade, Attendance, User, UserRole
)
from app.models.users import teacher_subject

from app.schemas import (
    FacultyCreate, GroupCreate, SubjectCreate, 
    SubjectGroupCreate, GradeCreate, GradeUpdate, 
    AttendanceCreate, AttendanceUpdate, JournalView
)

# Faculty services
def create_faculty(db: Session, faculty: FacultyCreate) -> Faculty:
    """
    Create a new faculty
    """
    # Check if faculty with the same name already exists
    existing_faculty = db.query(Faculty).filter(Faculty.name == faculty.name).first()
    if existing_faculty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Faculty with name '{faculty.name}' already exists"
        )
    
    # Create the faculty
    db_faculty = Faculty(name=faculty.name)
    
    db.add(db_faculty)
    db.commit()
    db.refresh(db_faculty)
    
    return db_faculty

def get_faculties(db: Session, skip: int = 0, limit: int = 100) -> List[Faculty]:
    """
    Get a list of faculties
    """
    return db.query(Faculty).offset(skip).limit(limit).all()

def get_faculty_by_id(db: Session, faculty_id: int) -> Faculty:
    """
    Get a faculty by its ID
    """
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Faculty with ID {faculty_id} not found"
        )
    return faculty

# Group services
def create_group(db: Session, group: GroupCreate) -> Group:
    """
    Create a new group
    """
    # Check if the faculty exists
    faculty = get_faculty_by_id(db, group.faculty_id)
    
    # Check if group with the same name already exists in the faculty
    existing_group = db.query(Group).filter(
        Group.name == group.name, 
        Group.faculty_id == group.faculty_id
    ).first()
    
    if existing_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Group with name '{group.name}' already exists in faculty '{faculty.name}'"
        )
    
    # Create the group
    db_group = Group(name=group.name, faculty_id=group.faculty_id)
    
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    return db_group

def get_groups(db: Session, faculty_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Group]:
    """
    Get a list of groups, optionally filtered by faculty
    """
    query = db.query(Group)
    
    if faculty_id:
        query = query.filter(Group.faculty_id == faculty_id)
    
    return query.offset(skip).limit(limit).all()

def get_group_by_id(db: Session, group_id: int) -> Group:
    """
    Get a group by its ID
    """
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group with ID {group_id} not found"
        )
    return group

# Subject services
def create_subject(db: Session, subject: SubjectCreate) -> Subject:
    """
    Create a new subject
    """
    # Check if the faculty exists
    faculty = get_faculty_by_id(db, subject.faculty_id)
    
    # Check if subject with the same name already exists in the faculty
    existing_subject = db.query(Subject).filter(
        Subject.name == subject.name, 
        Subject.faculty_id == subject.faculty_id
    ).first()
    
    if existing_subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subject with name '{subject.name}' already exists in faculty '{faculty.name}'"
        )
    
    # Create the subject
    db_subject = Subject(
        name=subject.name, 
        description=subject.description, 
        faculty_id=subject.faculty_id
    )
    
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    
    return db_subject

def get_subjects(db: Session, faculty_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Subject]:
    """
    Get a list of subjects, optionally filtered by faculty
    """
    query = db.query(Subject)
    
    if faculty_id:
        query = query.filter(Subject.faculty_id == faculty_id)
    
    return query.offset(skip).limit(limit).all()

def get_subject_by_id(db: Session, subject_id: int) -> Subject:
    """
    Get a subject by its ID
    """
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found"
        )
    return subject

# SubjectGroup services
def create_subject_group(db: Session, subject_group: SubjectGroupCreate) -> SubjectGroup:
    """
    Create a new subject-group relationship
    """
    # Check if the subject exists
    subject = get_subject_by_id(db, subject_group.subject_id)
    
    # Check if the group exists
    group = get_group_by_id(db, subject_group.group_id)
    
    # Check if the relationship already exists
    existing_subject_group = db.query(SubjectGroup).filter(
        SubjectGroup.subject_id == subject_group.subject_id,
        SubjectGroup.group_id == subject_group.group_id
    ).first()
    
    if existing_subject_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Relationship between subject '{subject.name}' and group '{group.name}' already exists"
        )
    
    # Create the subject-group relationship
    db_subject_group = SubjectGroup(
        subject_id=subject_group.subject_id,
        group_id=subject_group.group_id
    )
    
    db.add(db_subject_group)
    db.commit()
    db.refresh(db_subject_group)
    
    return db_subject_group

def get_subject_groups(
    db: Session, 
    subject_id: Optional[int] = None, 
    group_id: Optional[int] = None, 
    skip: int = 0, 
    limit: int = 100
) -> List[SubjectGroup]:
    """
    Get a list of subject-group relationships, optionally filtered by subject or group
    """
    query = db.query(SubjectGroup)
    
    if subject_id:
        query = query.filter(SubjectGroup.subject_id == subject_id)
    
    if group_id:
        query = query.filter(SubjectGroup.group_id == group_id)
    
    return query.offset(skip).limit(limit).all()

def get_subject_group_by_id(db: Session, subject_group_id: int) -> SubjectGroup:
    """
    Get a subject-group relationship by its ID
    """
    subject_group = db.query(SubjectGroup).filter(SubjectGroup.id == subject_group_id).first()
    if not subject_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject-group relationship with ID {subject_group_id} not found"
        )
    return subject_group

# Grade services
def create_grade(db: Session, grade: GradeCreate) -> Grade:
    """
    Create a new grade
    """
    # Check if the student exists
    student = db.query(User).filter(User.id == grade.student_id).first()
    if not student or student.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student with ID {grade.student_id} not found"
        )
    
    # Check if the subject-group relationship exists
    subject_group = get_subject_group_by_id(db, grade.subject_group_id)
    
    # Create the grade
    db_grade = Grade(
        student_id=grade.student_id,
        subject_group_id=grade.subject_group_id,
        grade=grade.grade,
        date=grade.date,
        description=grade.description
    )
    
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)
    
    return db_grade

def get_grades(
    db: Session, 
    student_id: Optional[int] = None, 
    subject_group_id: Optional[int] = None, 
    skip: int = 0, 
    limit: int = 100
) -> List[Grade]:
    """
    Get a list of grades, optionally filtered by student or subject-group
    """
    query = db.query(Grade)
    
    if student_id:
        query = query.filter(Grade.student_id == student_id)
    
    if subject_group_id:
        query = query.filter(Grade.subject_group_id == subject_group_id)
    
    return query.offset(skip).limit(limit).all()

def update_grade(db: Session, grade_id: int, grade_data: GradeUpdate) -> Grade:
    """
    Update a grade
    """
    # Get the grade
    grade = db.query(Grade).filter(Grade.id == grade_id).first()
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grade with ID {grade_id} not found"
        )
    
    # Update grade value if provided
    if grade_data.grade is not None:
        grade.grade = grade_data.grade
    
    # Update date if provided
    if grade_data.date is not None:
        grade.date = grade_data.date
    
    # Update description if provided
    if grade_data.description is not None:
        grade.description = grade_data.description
    
    db.commit()
    db.refresh(grade)
    
    return grade

# Attendance services
def create_attendance(db: Session, attendance: AttendanceCreate) -> Attendance:
    """
    Create a new attendance record
    """
    # Check if the student exists
    student = db.query(User).filter(User.id == attendance.student_id).first()
    if not student or student.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student with ID {attendance.student_id} not found"
        )
    
    # Check if the subject-group relationship exists
    subject_group = get_subject_group_by_id(db, attendance.subject_group_id)
    
    # Check if an attendance record for this student on this date already exists
    existing_attendance = db.query(Attendance).filter(
        Attendance.student_id == attendance.student_id,
        Attendance.subject_group_id == attendance.subject_group_id,
        Attendance.date == attendance.date
    ).first()
    
    if existing_attendance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Attendance record for student ID {attendance.student_id} on date {attendance.date} already exists"
        )
    
    # Create the attendance record
    db_attendance = Attendance(
        student_id=attendance.student_id,
        subject_group_id=attendance.subject_group_id,
        date=attendance.date,
        is_present=attendance.is_present
    )
    
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    
    return db_attendance

def get_attendance(
    db: Session, 
    student_id: Optional[int] = None, 
    subject_group_id: Optional[int] = None, 
    skip: int = 0, 
    limit: int = 100
) -> List[Attendance]:
    """
    Get a list of attendance records, optionally filtered by student or subject-group
    """
    query = db.query(Attendance)
    
    if student_id:
        query = query.filter(Attendance.student_id == student_id)
    
    if subject_group_id:
        query = query.filter(Attendance.subject_group_id == subject_group_id)
    
    return query.offset(skip).limit(limit).all()

def update_attendance(db: Session, attendance_id: int, attendance_data: AttendanceUpdate) -> Attendance:
    """
    Update an attendance record
    """
    # Get the attendance record
    attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendance record with ID {attendance_id} not found"
        )
    
    # Update is_present if provided
    if attendance_data.is_present is not None:
        attendance.is_present = attendance_data.is_present
    
    # Update date if provided
    if attendance_data.date is not None:
        attendance.date = attendance_data.date
    
    db.commit()
    db.refresh(attendance)
    
    return attendance

# Journal view service
def get_journal_view(db: Session, subject_id: int, group_id: int) -> JournalView:
    """
    Get a structured view of the journal for a specific subject and group
    """
    try:
        print(f"Starting get_journal_view for subject_id={subject_id}, group_id={group_id}")
        
        # Get the subject
        print(f"Getting subject with ID {subject_id}")
        subject = get_subject_by_id(db, subject_id)
        print(f"Found subject: {subject.name}")
        
        # Get the group
        print(f"Getting group with ID {group_id}")
        group = get_group_by_id(db, group_id)
        print(f"Found group: {group.name}")
        
        # Get the faculty
        print(f"Getting faculty with ID {group.faculty_id}")
        faculty = get_faculty_by_id(db, group.faculty_id)
        print(f"Found faculty: {faculty.name}")
        
        # Get the subject-group relationship
        print(f"Looking for subject-group relationship")
        subject_group = db.query(SubjectGroup).filter(
            SubjectGroup.subject_id == subject_id,
            SubjectGroup.group_id == group_id
        ).first()
        
        if not subject_group:
            print(f"No subject-group relationship found, creating one")
            # Create the relationship if it doesn't exist
            subject_group = SubjectGroup(
                subject_id=subject_id,
                group_id=group_id
            )
            db.add(subject_group)
            db.commit()
            db.refresh(subject_group)
            print(f"Created new subject-group relationship with ID {subject_group.id}")
        else:
            print(f"Found subject-group relationship with ID {subject_group.id}")
        
        # Get students in the group
        print(f"Getting students in group {group_id}")
        students = db.query(User).filter(
            User.group_id == group_id,
            User.role == UserRole.STUDENT,
            User.is_active == True,
            User.is_verified == True
        ).all()
        
        print(f"Found {len(students)} students in the group")
        
        # Get all grades for this subject-group
        print(f"Getting grades for subject-group {subject_group.id}")
        grades = db.query(Grade).filter(
            Grade.subject_group_id == subject_group.id
        ).all()
        print(f"Found {len(grades)} grades")
        
        # Get all attendance records for this subject-group
        print(f"Getting attendance records for subject-group {subject_group.id}")
        attendance_records = db.query(Attendance).filter(
            Attendance.subject_group_id == subject_group.id
        ).all()
        print(f"Found {len(attendance_records)} attendance records")
        
        # Extract unique dates from grades and attendance
        print("Extracting unique dates")
        grade_dates = [g.date for g in grades]
        attendance_dates = [a.date for a in attendance_records]
        all_dates = sorted(list(set(grade_dates + attendance_dates)))
        print(f"Found {len(all_dates)} unique dates")
        
        # If no dates, add today's date to avoid empty journal
        if not all_dates:
            print("No dates found, adding today's date")
            today = date.today()
            all_dates = [today]
        
        # Prepare the student data - allow empty list if no students
        print("Preparing student data")
        student_data = []
        for s in students:
            student_data.append({
                "id": s.id, 
                "name": s.full_name if s.full_name else f"Student {s.id}", 
                "username": s.username
            })
        print(f"Prepared data for {len(student_data)} students")
        
        # Prepare the grades data - allow empty dict if no students
        print("Preparing grades data")
        grades_data = {}
        for student in students:
            grades_data[str(student.id)] = {}
            for d in all_dates:
                grades_data[str(student.id)][d.isoformat()] = None
        
        for grade in grades:
            student_id = str(grade.student_id)
            date_str = grade.date.isoformat()
            if student_id in grades_data and date_str in grades_data[student_id]:
                grades_data[student_id][date_str] = grade.grade
        print("Grades data prepared")
        
        # Prepare the attendance data - allow empty dict if no students
        print("Preparing attendance data")
        attendance_data = {}
        for student in students:
            attendance_data[str(student.id)] = {}
            for d in all_dates:
                attendance_data[str(student.id)][d.isoformat()] = None
        
        for attendance in attendance_records:
            student_id = str(attendance.student_id)
            date_str = attendance.date.isoformat()
            if student_id in attendance_data and date_str in attendance_data[student_id]:
                attendance_data[student_id][date_str] = attendance.is_present
        print("Attendance data prepared")
        
        # Create the journal view
        print("Creating JournalView object")
        date_strings = [d.isoformat() for d in all_dates]
        print(f"Date strings: {date_strings}")
        
        try:
            journal = JournalView(
                subject=subject.name,
                group=group.name,
                faculty=faculty.name,
                subject_group_id=subject_group.id,
                students=student_data,
                dates=date_strings,
                grades=grades_data,
                attendance=attendance_data
            )
            print("JournalView object created successfully")
            
            return journal
        except Exception as model_error:
            print(f"Error creating JournalView object: {str(model_error)}")
            raise Exception(f"Failed to create JournalView model: {str(model_error)}")
            
    except HTTPException as http_exc:
        # Re-raise HTTP exceptions as they already have status codes and details
        print(f"HTTP exception in get_journal_view: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        # For other exceptions, wrap them in an HTTPException with a detailed message
        print(f"Error in get_journal_view: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get journal data: {str(e)}"
        )

def assign_subject_to_teacher(db: Session, teacher_id: int, subject_id: int) -> bool:
    """
    Assign a subject to a teacher
    """
    # Check if teacher exists
    teacher = db.query(User).filter(
        User.id == teacher_id,
        User.role == UserRole.TEACHER
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with ID {teacher_id} not found"
        )
    
    # Check if subject exists
    subject = get_subject_by_id(db, subject_id)
    
    # Check if the assignment already exists
    existing = db.query(teacher_subject).filter(
        teacher_subject.c.user_id == teacher_id,
        teacher_subject.c.subject_id == subject_id
    ).first()
    
    if existing:
        return True  # Already assigned
    
    # Create the assignment
    db.execute(
        teacher_subject.insert().values(
            user_id=teacher_id,
            subject_id=subject_id
        )
    )
    db.commit()
    
    return True

def remove_subject_from_teacher(db: Session, teacher_id: int, subject_id: int) -> bool:
    """
    Remove a subject assignment from a teacher
    """
    # Check if teacher exists
    teacher = db.query(User).filter(
        User.id == teacher_id,
        User.role == UserRole.TEACHER
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with ID {teacher_id} not found"
        )
    
    # Check if subject exists
    subject = get_subject_by_id(db, subject_id)
    
    # Delete the assignment
    result = db.execute(
        teacher_subject.delete().where(
            teacher_subject.c.user_id == teacher_id,
            teacher_subject.c.subject_id == subject_id
        )
    )
    db.commit()
    
    return True

def get_teacher_subjects(db: Session, teacher_id: int) -> List[Subject]:
    """
    Get all subjects assigned to a teacher
    """
    # Check if teacher exists
    teacher = db.query(User).filter(
        User.id == teacher_id,
        User.role == UserRole.TEACHER
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with ID {teacher_id} not found"
        )
    
    return teacher.subjects 