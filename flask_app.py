from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import login_required, LoginManager, login_user, logout_user, current_user
from flask_paginate import Pagination
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from sqlite3 import IntegrityError
from main import Employee, RegisteredUser, Department, Note
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, BooleanField
from wtforms.validators import InputRequired, EqualTo, DataRequired
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'MySecretKey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employee.db'

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.unauthorized_view = 'unauthorized'

# SQLAlchemy Konfiguration
engine = create_engine('sqlite:///employee.db')
Session = sessionmaker(bind=engine)
db_session = Session()


# Register Form
class RegistrationForm(FlaskForm):
    username = StringField('Benutzername', validators=[InputRequired()])
    password = PasswordField('Passwort', validators=[InputRequired()])
    confirm_password = PasswordField('Passwort bestätigen', validators=[InputRequired(), EqualTo('password')])
    is_approved = BooleanField('Freigeschaltet', default=False)
    submit = SubmitField('Registrieren')


# Login Form
class LoginForm(FlaskForm):
    username = StringField('Benutzername', validators=[DataRequired()])
    password = PasswordField('Passwort', validators=[DataRequired()])
    submit = SubmitField('Anmelden')


# Settings Form
class SettingsForm(FlaskForm):
    department = StringField('Abteilung hinzufügen', validators=[DataRequired()])
    submit = SubmitField('Hinzufügen')


# Add Employee Form
class AddEmployeeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    department = StringField('Abteilung', default='')
    position = StringField('Position', validators=[DataRequired()])
    ooc_age = StringField('OOC Alter', validators=[DataRequired()])
    ig_age = StringField('IG Alter', validators=[DataRequired()])
    hire_date = StringField('Einstellungsdatum', default='', validators=[DataRequired()])
    discord_handle = StringField('Discord handle', validators=[DataRequired()])
    submit = SubmitField('Mitarbeiter hinzufügen')


# Add Employee Note
class EmployeeNoteForm(FlaskForm):
    author = StringField('Verfasser')
    timestamp = StringField('Datum und Uhrzeit', default=datetime.now().strftime("%d.%m.%Y - %H:%M Uhr"))
    note_type = SelectField('Kategorie', choices=[('notiz', 'Notiz'), ('positiv', 'Positiv'), ('negativ', 'Negativ')])
    note_text = TextAreaField('Akteneintrag', validators=[DataRequired()])
    submit = SubmitField('Notiz hinzufügen')


@login_manager.user_loader
def load_user(user_id):
    return db_session.get(RegisteredUser, int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    flash('Du musst eingeloggt sein, um auf diese Seite zuzugreifen.', 'danger')
    return redirect(url_for('login'))


# Startseite mit allen Abteilungen anzeigen.
@app.route('/')
@login_required
def index():
    # Alle Abteilungen abrufen und dem html teil bereitstellen.
    departments = db_session.query(Department.name).distinct().all()
    departments = [department[0] for department in departments]
    return render_template('index.html', departments=departments, title="Personal Verwaltungs System")


# Abteilungsseite mit allen Angestellten anzeigen.
@app.route('/department/<string:dep>')
@login_required
def department_list(dep):
    # Alle Angestellten abrufen und dem html teil bereitstellen.
    employees = db_session.query(Employee).filter(and_(Employee.department == dep)).all()
    return render_template('department_list.html', employees=employees, dep=dep, title="Mitarbeiterliste")


# Seite fuer Mitarbeiter details.
@app.route('/employee/<int:employee_id>')
@login_required
def employee_detail(employee_id):
    # Alles details eines Mitarbeiters aufrufen und dem html teil bereitstellen.
    employee = db_session.get(Employee, employee_id)
    return render_template('employee_detail.html', employee=employee, employee_id=employee_id,
                           title="Mitarbeiterdetails")


# Seite zum hinzufuegen von Mitarbeitern
@app.route('/add_employee/<string:department>', methods=['GET', 'POST'])
@login_required
def add_employee(department):
    form = AddEmployeeForm()
    hire_date_default = datetime.today().strftime("%d.%m.%Y")

    if form.validate_on_submit():
        name = form.name.data.strip()
        dchandle = form.discord_handle.data.strip()
        existing_employee = db_session.query(Employee).filter(and_(Employee.name == name,
                                                                   Employee.department == department)).first()
        existing_dc_handle = db_session.query(Employee).filter(and_(Employee.discord_handle == dchandle)).first()
        # check ob der user bereits existiert. Wenn ja, dann eintrag verhindern und warnung anzeigen.
        # Spaeter muss noch geprueft werden ob der discord handle bereits existiert und entsprechend eine meldung
        # ausgegeben werden.
        if existing_employee or existing_dc_handle:
            flash("Ein Mitarbeiter mit diesem Namen oder Discord Handle existiert bereits.", "danger")
        else:
            position = form.position.data.strip()
            ooc_age = form.ooc_age.data.strip()
            ig_age = form.ig_age.data.strip()
            hire_date = datetime.strptime(form.hire_date.data, "%d.%m.%Y").date()
            discord_handle = form.discord_handle.data.strip()

            new_employee = Employee(
                name=name,
                department=department,
                position=position,
                ooc_age=ooc_age,
                ig_age=ig_age,
                hire_date=hire_date,
                discord_handle=discord_handle
            )
            try:
                db_session.add(new_employee)
                db_session.commit()
                flash("Mitarbeiter hinzugefügt", "success")
            except IntegrityError:
                db_session.rollback()
                flash("Fehler beim hinzufügen des Mitarbeiters", "danger")
            except Exception:
                db_session.rollback()
                flash("Fehler beim hinzufügen des Mitarbeiters", "danger")
            return redirect(url_for('department_list', dep=department))
    db_session.close()
    return render_template('add_employee.html', form=form, dep=department, hire_date_default=hire_date_default,
                           title="Mitarbeiter hinzufügen")


# Akteneintrag fuer Mitarbeiter hinzufuegen.
@app.route('/add_employee_note/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def add_employee_note(employee_id):
    form = EmployeeNoteForm()

    if request.method == 'POST':
        # Check ob der note text leer ist.
        if form.note_text.data.strip() == '':
            flash("Kein Text eingegeben", "danger")
        elif form.validate_on_submit():
            employee = db_session.query(Employee).filter_by(name=request.args.get('employee')).first()
            new_note = Note(
                employee=employee,
                creator_name=form.author.data.strip(),
                text=form.note_text.data.strip(),
                created_at=datetime.strptime(form.timestamp.data, "%d.%m.%Y - %H:%M Uhr"),
                note_type=form.note_type.data
                )
            db_session.add(new_note)
            try:
                db_session.commit()
                flash("Notiz hinzugefügt", "success")
            except IntegrityError:
                db_session.rollback()
                flash("Fehler beim hinzufügen des Akteneintrags", "danger")

            return redirect(url_for('employee_detail', employee_id=employee_id))
    db_session.close()
    return render_template('add_employee_note.html', employee_id=employee_id, form=form, title="Notiz hinzufügen")


# Einstellungsseite um z.b. Abteilungen hinzuzufuegen und zu loeschen.
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm()
    departments = db_session.query(Department.name).distinct().all()
    departments = [department[0] for department in departments]
    users_to_approve = db_session.query(RegisteredUser).filter_by(is_approved=False).all()
    users = db_session.query(RegisteredUser).all()

    page = request.args.get('page', type=int, default=1)
    per_page = 2  # Anzahl der Benutzer pro Seite
    offset = (page - 1) * per_page
    total = len(users)  # Die Gesamtanzahl der Benutzer
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')
    pagination.next_label = "Weiter"
    pagination.prev_label = "Zurück"
    paginated_users = users[offset:offset + per_page]

    if form.validate_on_submit():
        department = form.department.data.strip()
        # check ob abteilung bereits existiert
        if department in departments:
            flash('Abteilung existiert bereits.', 'danger')
        else:
            new_department = Department(name=department)
            db_session.add(new_department)
            try:
                db_session.commit()
                flash("Abteilung hinzugefügt", "success")
            except IntegrityError:
                db_session.rollback()
                flash('Fehler beim Hinzufügen der Abteilung', 'danger')
        return redirect(url_for('settings'))

    db_session.close()
    return render_template('settings.html', departments=departments, users_to_approve=users_to_approve,
                           form=form, users=paginated_users, pagination=pagination, title="Einstellungen")


# Hier werden Abteilungen geloescht.
@app.route('/delete_department/<string:department>')
@login_required
def delete_department(department):
    department_to_delete = db_session.query(Department).filter_by(name=department).first()

    # kleine sicherheitspruefung ob die abteilung wirklich existiert
    if department_to_delete:
        # pruefen ob noch mitarbeiter in der abteilung sind
        employee_count = db_session.query(Employee).filter_by(department=department).count()
        if employee_count > 0:
            flash("Es befinden sich noch Mitarbeiter in der Abteilung.", "danger")
        else:
            try:
                db_session.delete(department_to_delete)
                db_session.commit()
                flash(f"Abteilung '{department}' wurde gelöscht", "success")
            except Exception as e:
                flash(f"Fehler beim Löschen der Abteilung '{department}': {str(e)}", "danger")
            finally:
                db_session.close()
    else:
        flash(f"Abteilung '{department}' wurde nicht gefunden und konnte nicht gelöscht werden", "danger")

    return redirect(url_for('settings'))


@app.route('/approve_user/<int:user_id>')
@login_required
def approve_user(user_id):
    if current_user.is_admin:
        user = db_session.query(RegisteredUser).get(user_id)
        user.is_approved = True
        db_session.commit()
        flash("Benutzer wurde genehmigt", "success")
    else:
        flash("Nur Administratoren können Benutzer genehmigen", "danger")

    return redirect(url_for('settings'))


@app.route('/user_detail/<int:user_id>')
@login_required
def user_detail(user_id):
    user = db_session.query(RegisteredUser).get(user_id)
    all_departments = db_session.query(Department).all()
    user_data = {}

    # Durch alle Abteilungen iterieren und überprüfen, ob der Benutzer in dieser Abteilung ist
    for department in all_departments:
        user_data[department.name] = department in user.departments

    # TODO Departments zuweisen in eigener route. Beispielcode s.u.
    # department zuweisen
    # departments_to_assign = db_session.query(Department).filter(Department.id.in_([2])).all()
    # user.departments.extend(departments_to_assign)
    # db_session.commit()

    departments = db_session.query(Department.name).distinct().all()

    return render_template('user_detail.html', user_data=user_data, user=user, departments=departments)


# Registrierungsseite
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data.lower().strip()
        password = form.password.data

        existing_user = db_session.query(RegisteredUser).filter_by(username=username).first()
        if existing_user:
            # check ob benutzername belegt ist
            flash("Benutzername existiert bereits", "danger")
            return render_template('register.html', form=form, title="Registrierung")

        # abfrage aller eintraege um spaeter zu pruefen ob der erste user admin werden soll
        existing_users = db_session.query(RegisteredUser).all()
        is_first_user = not existing_users

        hashed_password = generate_password_hash(password)
        new_user = RegisteredUser(username=username, password=hashed_password)

        if is_first_user:
            # wenn keine user vorhanden sind ist der erste registrierte User "Super Admin" und sofort freigeschaltet
            new_user.is_admin = True
            new_user.is_approved = True

        db_session.add(new_user)
        try:
            db_session.commit()
        except IntegrityError:
            db_session.rollback()
            flash("Fehler beim Registrieren des Benutzers", "danger")
            return render_template('register.html', form=form, title="Registrierung")

        db_session.close()
        return redirect(url_for('login'))

    return render_template('register.html', form=form, title="Registrierung")


# Loginseite
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data.lower().strip()
        password = form.password.data

        user = db_session.query(RegisteredUser).filter_by(username=username).first()
        if not user.is_approved:
            # User wurde noch nicht freigeschaltet
            flash("Du bist noch nicht freigeschaltet", "danger")
        elif user and check_password_hash(user.password, password):
            # Benutzer erfolgreich eingeloggt
            login_user(user)
            db_session.refresh(user)
            return redirect(url_for('index'))
        else:
            flash('Falscher Benutzername oder Passwort', 'danger')

    return render_template('login.html', form=form, title="Anmelden")


# Logoutseite
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
