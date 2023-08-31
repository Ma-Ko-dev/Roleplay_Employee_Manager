from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Date, DateTime, Float, Boolean
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
    termination_date = Column(Date)
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
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.now)  # Neues Feld für das Erstellungsdatum

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


class RegisteredUser(Base, UserMixin):
    __tablename__ = 'registered_users'
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password


class Department(Base):
    __tablename__ = 'departments'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)


# # Tabelle in der Datenbank erstellen
Base.metadata.create_all(engine)

# Mit der Datenbank interagieren
# Session = sessionmaker(bind=engine)
# session = Session()

# Mitarbeiter hinzufügen
# new_employee = Employee(
#     name='Gariot Grau',
#     position='Leitender Branddirektor',
#     ooc_age=38,
#     ig_age=38,
#     department='Feuerwehr',
#     hire_date=datetime.strptime('15.06.2023', '%d.%m.%Y'),
#     termination_date=None,
#     discord_handle='Gariot.Grau#1234'
# )

# Füge den neuen Mitarbeiter zur Datenbank hinzu
# session.add(new_employee)
# session.commit()

# Notiz hinzufügen
# Finde den Mitarbeiter "John Doe" in der Datenbank
# mitarbeiter = session.query(Employee).filter_by(name='Gariot Grau').first()

# Notiz hinzufügen
# new_note = Note(
#     employee=mitarbeiter,
#     creator_name='Alice',
#     text='Eine wichtige Notiz für Gariot Grau!'
# )

# Füge die Notiz zur Datenbank hinzu
# session.add(new_note)
# session.commit()

# Session schließen
# session.close()
