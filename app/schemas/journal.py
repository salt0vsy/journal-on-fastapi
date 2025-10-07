from pydantic import BaseModel
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Annotated
from datetime import date as DateType

if TYPE_CHECKING:
    from app.schemas.user import UserDisplay

# Faculty Schemas
class FacultyBase(BaseModel):
    name: str

class FacultyCreate(FacultyBase):
    pass

class FacultyDisplay(FacultyBase):
    id: int
    
    model_config = {"from_attributes": True}

# Group Schemas
class GroupBase(BaseModel):
    name: str
    faculty_id: int

class GroupCreate(GroupBase):
    pass

class GroupDisplay(GroupBase):
    id: int
    
    model_config = {"from_attributes": True}

class GroupWithStudents(GroupDisplay):
    students: List["UserDisplay"] = []
    
    model_config = {"from_attributes": True}

# Subject Schemas
class SubjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    faculty_id: int

class SubjectCreate(SubjectBase):
    pass

class SubjectDisplay(SubjectBase):
    id: int
    
    model_config = {"from_attributes": True}

class SubjectWithTeachers(SubjectDisplay):
    teachers: List["UserDisplay"] = []
    
    model_config = {"from_attributes": True}

# SubjectGroup Schemas
class SubjectGroupBase(BaseModel):
    subject_id: int
    group_id: int

class SubjectGroupCreate(SubjectGroupBase):
    pass

class SubjectGroupDisplay(SubjectGroupBase):
    id: int
    
    model_config = {"from_attributes": True}

# Grade Schemas
class GradeBase(BaseModel):
    student_id: int
    subject_group_id: int
    grade: int
    date: DateType
    description: Optional[str] = None

class GradeCreate(GradeBase):
    pass

class GradeUpdate(BaseModel):
    grade: Optional[int] = None
    date: Optional[DateType] = None
    description: Optional[str] = None

class GradeDisplay(GradeBase):
    id: int
    
    model_config = {"from_attributes": True}

# Attendance Schemas
class AttendanceBase(BaseModel):
    student_id: int
    subject_group_id: int
    date: DateType
    is_present: bool

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceUpdate(BaseModel):
    is_present: Optional[bool] = None
    date: Optional[DateType] = None

class AttendanceDisplay(AttendanceBase):
    id: int
    
    model_config = {"from_attributes": True}

# Journal View Schema (for displaying data in tables)
class JournalView(BaseModel):
    subject: str
    group: str
    faculty: str
    subject_group_id: int
    students: List[Dict[str, Any]]
    dates: List[str]  # ISO-formatted date strings
    grades: Dict[str, Dict[str, Optional[int]]]
    attendance: Dict[str, Dict[str, Optional[bool]]]
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            DateType: lambda d: d.isoformat() if d else None
        }
    }

# Student-Subject Schemas
class StudentSubjectBase(BaseModel):
    student_id: int
    subject_id: int

class StudentSubjectCreate(StudentSubjectBase):
    pass

class StudentSubjectDisplay(StudentSubjectBase):
    id: int
    
    model_config = {"from_attributes": True} 