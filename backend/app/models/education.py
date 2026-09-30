import enum
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, IdMixin, TenantMixin, TimestampMixin, enum_col


class LessonKind(str, enum.Enum):
    vocabulary = "vocabulary"
    grammar = "grammar"
    reading = "reading"
    listening = "listening"
    speaking = "speaking"
    writing = "writing"
    test = "test"


class Skill(str, enum.Enum):
    reading = "reading"
    listening = "listening"
    speaking = "speaking"
    writing = "writing"
    vocabulary = "vocabulary"
    grammar = "grammar"


class QuestionSource(str, enum.Enum):
    platform = "platform"  # locked, faqat super_admin o'zgartiradi (daraja aniqlash)
    teacher = "teacher"


class QuestionStatus(str, enum.Enum):
    draft = "draft"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class TestKind(str, enum.Enum):
    placement = "placement"
    quick = "quick"      # 10 savol / 10 daqiqa
    mock = "mock"        # 30 savol / 45 daqiqa
    mistakes = "mistakes"
    topic = "topic"
    lesson = "lesson"


class Subject(IdMixin, Base):
    """Hozir faqat 'english'. Keyinchalik boshqa fanlar shu jadvalga qo'shiladi."""

    __tablename__ = "subjects"
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(80))


class Course(IdMixin, TimestampMixin, Base):
    """center_id NULL = platforma kursi (sotish/biriktirish mumkin)."""

    __tablename__ = "courses"
    center_id: Mapped[int | None] = mapped_column(ForeignKey("centers.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    title: Mapped[str] = mapped_column(String(160))
    level: Mapped[str] = mapped_column(String(3))
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)


class Unit(IdMixin, Base):
    __tablename__ = "units"
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    position: Mapped[int] = mapped_column(Integer, default=0)


class Lesson(IdMixin, Base):
    __tablename__ = "lessons"
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id", ondelete="CASCADE"), index=True)
    kind: Mapped[LessonKind] = mapped_column(enum_col(LessonKind))
    title: Mapped[str] = mapped_column(String(160))
    content: Mapped[dict | None] = mapped_column(JSON)
    position: Mapped[int] = mapped_column(Integer, default=0)


# ---------- Guruhlar ----------
class Group(IdMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "groups"
    name: Mapped[str] = mapped_column(String(120))
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id"))
    teacher_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    schedule: Mapped[str | None] = mapped_column(String(160))  # "Du-Chor-Ju 17:00"
    monthly_fee: Mapped[int] = mapped_column(Integer, default=0)  # so'm
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class GroupStudent(IdMixin, TenantMixin, Base):
    __tablename__ = "group_students"
    __table_args__ = (UniqueConstraint("group_id", "student_id", name="uq_group_student"),)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    joined_on: Mapped[date] = mapped_column(Date)
    left_on: Mapped[date | None] = mapped_column(Date)


# ---------- Savol banki ----------
class Question(IdMixin, TimestampMixin, Base):
    """center_id NULL + source=platform -> umumiy 500 ta daraja aniqlash savoli."""

    __tablename__ = "questions"
    center_id: Mapped[int | None] = mapped_column(ForeignKey("centers.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    source: Mapped[QuestionSource] = mapped_column(enum_col(QuestionSource))
    status: Mapped[QuestionStatus] = mapped_column(enum_col(QuestionStatus), default=QuestionStatus.draft)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    level: Mapped[str] = mapped_column(String(3), index=True)      # A1..C1
    skill: Mapped[Skill] = mapped_column(enum_col(Skill))
    topic: Mapped[str | None] = mapped_column(String(80), index=True)
    difficulty: Mapped[int] = mapped_column(Integer, default=2)   # 1..3
    text: Mapped[str] = mapped_column(Text)
    options: Mapped[list | None] = mapped_column(JSON)            # ["a","b","c","d"]
    correct: Mapped[list] = mapped_column(JSON)                   # to'g'ri variant indekslari
    explanation: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    times_asked: Mapped[int] = mapped_column(Integer, default=0)
    times_correct: Mapped[int] = mapped_column(Integer, default=0)


class Test(IdMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "tests"
    title: Mapped[str] = mapped_column(String(160))
    kind: Mapped[TestKind] = mapped_column(enum_col(TestKind))
    duration_min: Mapped[int] = mapped_column(Integer, default=10)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))


class TestQuestion(IdMixin, Base):
    __tablename__ = "test_questions"
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    position: Mapped[int] = mapped_column(Integer, default=0)


class TestAttempt(IdMixin, TenantMixin, Base):
    __tablename__ = "test_attempts"
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    test_id: Mapped[int | None] = mapped_column(ForeignKey("tests.id"))
    kind: Mapped[TestKind] = mapped_column(enum_col(TestKind))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    score: Mapped[int] = mapped_column(Integer, default=0)
    max_score: Mapped[int] = mapped_column(Integer, default=0)
    level_result: Mapped[str | None] = mapped_column(String(3))  # placement natijasi


class AttemptAnswer(IdMixin, Base):
    __tablename__ = "attempt_answers"
    attempt_id: Mapped[int] = mapped_column(ForeignKey("test_attempts.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    answer: Mapped[list | None] = mapped_column(JSON)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    time_ms: Mapped[int | None] = mapped_column(Integer)


class Mistake(IdMixin, TenantMixin, Base):
    """Xatolar tarixi: o'quvchi qaysi savolda necha marta xato qilgan."""

    __tablename__ = "mistakes"
    __table_args__ = (UniqueConstraint("student_id", "question_id", name="uq_mistake"),)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    times_wrong: Mapped[int] = mapped_column(Integer, default=1)
    last_wrong_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Assignment(IdMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "assignments"
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text)
    test_id: Mapped[int | None] = mapped_column(ForeignKey("tests.id"))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Submission(IdMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "submissions"
    __table_args__ = (UniqueConstraint("assignment_id", "student_id", name="uq_submission"),)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    content: Mapped[str | None] = mapped_column(Text)
    score: Mapped[int | None] = mapped_column(Integer)
    feedback: Mapped[str | None] = mapped_column(Text)
    graded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    graded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Certificate(IdMixin, TenantMixin, Base):
    __tablename__ = "certificates"
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    level: Mapped[str] = mapped_column(String(3))
    code: Mapped[str] = mapped_column(String(24), unique=True)  # tekshirish uchun
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
