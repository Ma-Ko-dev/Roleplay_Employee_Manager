from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import login_required, LoginManager, login_user, logout_user
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlite3 import IntegrityError
from main import Employee, RegisteredUser, Department
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
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


@login_manager.user_loader
def load_user(user_id):
    return db_session.query(RegisteredUser).get(int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    flash('Du musst eingeloggt sein, um auf diese Seite zuzugreifen.', 'danger')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    departments = db_session.query(Department.name).distinct().all()
    departments = [department[0] for department in departments]

    if not departments:
        departments.append("Keine Einträge gefunden.")

    return render_template('index.html', departments=departments, title="Personal Verwaltungs System")


@app.route('/department/<string:dep>')
@login_required
def department_list(dep):
    employees = db_session.query(Employee).filter_by(department=dep).all()
    return render_template('department_list.html', employees=employees, dep=dep, title="Mitarbeiterliste")


@app.route('/employee/<int:employee_id>')
@login_required
def employee_detail(employee_id):
    employee = db_session.query(Employee).get(employee_id)
    return render_template('employee_detail.html', employee=employee, title="Mitarbeiterdetails")


@app.route('/add_employee/<string:department>', methods=['GET', 'POST'])
@login_required
def add_employee(department):
    form = AddEmployeeForm()
    hire_date_default = datetime.today().strftime("%d.%m.%Y")

    if form.validate_on_submit():
        name = form.name.data
        position = form.position.data
        ooc_age = form.ooc_age.data
        ig_age = form.ig_age.data
        hire_date = datetime.strptime(form.hire_date.data, "%d.%m.%Y").date()
        discord_handle = form.discord_handle.data

        new_employee = Employee(
            name=name,
            department=department,
            position=position,
            ooc_age=ooc_age,
            ig_age=ig_age,
            hire_date=hire_date,
            discord_handle=discord_handle
        )
        db_session.add(new_employee)
        db_session.commit()

        flash("Mitarbeiter hinzugefügt", "success")
        return redirect(url_for('department_list', dep=department))

    return render_template('add_employee.html', form=form, dep=department, hire_date_default=hire_date_default, title="Mitarbeiter hinzufügen")


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm()
    departments = db_session.query(Department.name).distinct().all()
    departments = [department[0] for department in departments]

    if not departments:
        departments.append("Keine Einträge gefunden.")

    if form.validate_on_submit():
        department = form.department.data
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
    return render_template('settings.html', departments=departments, form=form, title="Einstellungen")


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data.lower()
        password = form.password.data

        existing_user = db_session.query(RegisteredUser).filter_by(username=username).first()
        if existing_user:
            flash("Benutzername existiert bereits", "danger")
            return render_template('register.html', form=form, title="Registrierung")
        else:
            hashed_password = generate_password_hash(password)
            new_user = RegisteredUser(username=username, password=hashed_password)
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


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data.lower()
        password = form.password.data

        user = db_session.query(RegisteredUser).filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            # Benutzer erfolgreich eingeloggt
            login_user(user)
            db_session.refresh(user)
            return redirect(url_for('index'))
        else:
            flash('Falscher Benutzername oder Passwort', 'danger')

    return render_template('login.html', form=form, title="Anmelden")


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
