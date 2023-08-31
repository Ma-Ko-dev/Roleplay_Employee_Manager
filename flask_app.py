from flask import Flask, render_template, redirect, url_for, flash
from flask_login import login_required, LoginManager, login_user, logout_user
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import Employee, RegisteredUser
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, EqualTo, DataRequired
from werkzeug.security import check_password_hash, generate_password_hash

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
    departments = db_session.query(Employee.department).distinct().all()
    departments = [department[0] for department in departments]

    if not departments:
        departments.append("Keine Einträge gefunden.")

    return render_template('index.html', departments=departments, title="Personal Verwaltungs System")


@app.route('/department/<string:dep>')
@login_required
def department_list(dep):
    employees = db_session.query(Employee).filter_by(department=dep).all()
    return render_template('department_list.html', employees=employees, title="Mitarbeiterliste")


@app.route('/employee/<int:employee_id>')
@login_required
def employee_detail(employee_id):
    employee = db_session.query(Employee).get(employee_id)
    return render_template('employee_detail.html', employee=employee)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data.lower()
        password = form.password.data

        hashed_password = generate_password_hash(password)

        new_user = RegisteredUser(username=username, password=hashed_password)
        db_session.add(new_user)
        db_session.commit()

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
