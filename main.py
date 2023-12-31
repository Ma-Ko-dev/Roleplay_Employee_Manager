from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Date, DateTime, Float, Boolean, Table
from sqlalchemy.orm import declarative_base, relationship
from flask_login import UserMixin

# Datenbank initialisieren
engine = create_engine('sqlite:///employee.db')
Base = declarative_base()


class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    position = Column(String)
    ooc_age = Column(Integer)
    ig_age = Column(Integer)
    department = Column(String)
    hire_date = Column(Date)
    termination_date = Column(Date, default=None)
    discord_handle = Column(String, nullable=False, unique=True)

    # Hier die Beziehung zu den Notizen
    notes = relationship("Note", back_populates="employee")
    # Hier die Beziehung zu der Arbeitszeit
    monthly_durations = relationship("MonthlyDuration", back_populates="employee")


class Note(Base):
    __tablename__ = 'notes'
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    creator_name = Column(String)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime)
    note_type = Column(String)

    employee = relationship("Employee", back_populates="notes")


class MonthlyDuration(Base):
    __tablename__ = 'monthly_durations'
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    month = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    last_seen = Column(DateTime, default=None)

    employee = relationship("Employee", back_populates="monthly_durations")


class RegisteredUser(UserMixin, Base):
    __tablename__ = 'registered_users'
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)

    # Definiere die Beziehung zu Abteilungen
    departments = relationship('Department', secondary='user_departments', back_populates='users')

    def __init__(self, username, password):
        self.username = username
        self.password = password


class Department(Base):
    __tablename__ = 'departments'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    # Definiere die Beziehung zu Benutzern
    users = relationship('RegisteredUser', secondary='user_departments', back_populates='departments')


# Erstelle die Verknüpfungstabelle user_departments
user_departments = Table(
    'user_departments',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('registered_users.id')),
    Column('department_id', Integer, ForeignKey('departments.id'))
)

# Tabelle in der Datenbank erstellen
Base.metadata.create_all(engine)
