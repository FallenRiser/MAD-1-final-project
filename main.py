from flask import Flask,render_template, request, flash, redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_login import UserMixin
from flask_login import login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import datetime
import sqlite3
import matplotlib.pyplot as plt
from matplotlib import style



##----------------------------------------------------------------------------------------------------------------------------------##
app = Flask(__name__)
bcrypt = Bcrypt()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_pyfile('config.py')
##app.config['SECRET_KEY'] = 'this is a secret key'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.sqlite3'
db=SQLAlchemy(app)
db.init_app(app)


login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))



##---------------------MODELS--------------------------------------------------------------------------------------------------##
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    city = db.Column(db.String(150))
    tracker = db.relationship('Tracker')
    log = db.relationship('Log')


class Tracker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    description = db.Column(db.String(150))
    tracker_type = db.Column(db.String(150))
    settings = db.Column(db.String(150))
    log = db.relationship('Log')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.String(150))
    value = db.Column(db.Integer)
    notes = db.Column(db.String(150))
    tracker_id = db.Column(db.Integer, db.ForeignKey('tracker.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    added_date_time = db.Column(db.String(150))

##------------------------------------------------------AUTHENTICATION------------------------------------------------------------##

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')


        user = User.query.filter_by(email=email).first()
        if user:
            if bcrypt.check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('home'))
            else:
                flash('Incorrect password', category='error')

        else:
            flash('User does not exist.', category='error')
    return render_template("login.html", user=current_user)


@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        fullname = request.form.get('name')
        city = request.form.get('city')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email is already taken, try another email.', category='error')
        elif len(fullname) < 3:
            flash('Full name must be greater than 2 characters.', category='error')
        elif len(email) < 6:
            flash('Email must be greater than 5 characters.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        elif password1 != password2:
            flash('Passwords dont match.', category='error')
        else:
            new_user = User(fullname=fullname, email=email,  password=bcrypt.generate_password_hash(password1), city=city)
            db.session.add(new_user)
            db.session.commit()
            flash('Successfully signed up.', category='success')

    return render_template("sign_up.html", user=current_user)        

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged Out', category='success')
    return redirect(url_for('login'))


##------------------------------------------------------TRACKS----------------------------------------------------------------------##


@app.route('/')
@login_required
def home():
    tracker = Tracker.query.all()
    return render_template("home.html", user=current_user, tracker=tracker)


@app.route('/view-profile', methods=['GET', 'POST'])
@login_required
def view_profile():
    return render_template("profile_page.html", user=current_user)


@app.route('/edit-profile-page', methods=['GET', 'POST'])
@login_required
def edit_profile_page():
    try:
        if request.method == 'POST':
            email = request.form.get('email')
            fullname = request.form.get('name')
            city = request.form.get('city')
            user_id = current_user.id
            current_user_email = current_user.email

            user = User.query.filter_by(email=email).first()
            if user and current_user_email != email:
                flash('Email is already taken, try another email.', category='error')
            elif len(fullname) < 3:
                flash('Full name must be greater than 2 characters.', category='error')
            elif len(email) < 4:
                flash('Email must be greater than 3 characters.', category='error')
            else:
                edit_user = User.query.get(user_id)
                edit_user.fullname = fullname
                edit_user.email = email
                edit_user.city = city

                db.session.commit()
                flash('Profile Updated Successfully.', category='success')
                return redirect(url_for('view_profile'))
    except Exception as e:
        print(e)
        flash('Something went wrong.', category='error')
    return render_template("edit_profile_page.html", user=current_user)


@app.route('/add-tracker-page', methods=['GET', 'POST'])
@login_required
def add_tracker_page():
    try:
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            tracker_type = request.form.get('type')
            settings = request.form.get('settings')

            current_user_id = current_user.id
            tracker = Tracker.query.filter_by(name=name).first()
            if tracker and current_user_id == tracker.user_id:
                flash('The tracker "' + name + '" is already added by you.', category='error')
                return redirect(url_for('home'))
            else:
                new_tracker = Tracker(name=name, description=description, tracker_type=tracker_type, settings=settings,user_id=current_user_id)
                db.session.add(new_tracker)
                db.session.commit()
                flash('New Tracker Added.', category='success')
                 
                return redirect(url_for('home'))
    except Exception as e:
        print(e)
        flash('Something went wrong.', category='error')
    return render_template("add_tracker_page.html", user=current_user)


@app.route('/delete-tracker/<int:record_id>', methods=['GET', 'POST'])
@login_required
def delete_tracker(record_id):
    try:
        Tracker_details = Tracker.query.get(record_id)
        Tracker_name = Tracker_details.name
        db.session.delete(Tracker_details)
        db.session.commit()
        flash(Tracker_name + ' Tracker Removed Successfully.', category='success')
    except Exception as e:
        print(e)
        flash('Something went wrong.', category='error')
    return redirect(url_for('home'))


@app.route('/edit-tracker/<int:record_id>', methods=['GET', 'POST'])
@login_required
def edit_tracker(record_id):
    this_tracker = Tracker.query.get(record_id)
    this_tracker_name = this_tracker.name
    try:
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            tracker_type = request.form.get('type')
            settings = request.form.get('settings')

            current_user_id = current_user.id
            tracker = Tracker.query.filter_by(name=name).first()
            if tracker and tracker.user_id == current_user_id and this_tracker_name != name:
                flash('The tracker "' + name + '" is already added by you, Try a new name for your tracker.',
                      category='error')
            else:

                this_tracker.name = name
                this_tracker.description = description
                this_tracker.tracker_type = tracker_type
                this_tracker.settings = settings

                db.session.commit()
                flash('Tracker Updated Successfully.', category='success')
                return redirect(url_for('home'))
    except Exception as e:
        print(e)
        flash('Something went wrong.', category='error')

    return render_template("edit_tracker_page.html", user=current_user, tracker=this_tracker)


@app.route('/add-log-page/<int:record_id>', methods=['GET', 'POST'])
@login_required
def add_log(record_id):
    this_tracker = Tracker.query.get(record_id)
    now = datetime.datetime.now()
    try:
        if request.method == 'POST':
            when = request.form.get('date')
            value = request.form.get('value')
            notes = request.form.get('notes')

            new_log = Log(timestamp=when, value=value, notes=notes, tracker_id=record_id, user_id=current_user.id,added_date_time=now)
            db.session.add(new_log)
            db.session.commit()
            flash('New Log Added For ' + this_tracker.name + ' Tracker', category='success')
            return redirect(url_for('home'))
    except Exception as e:
        print(e)
        flash('Something went wrong.', category='error')
    return render_template("add_log_page.html", user=current_user, tracker=this_tracker, now=now)


@app.route('/view-tracker-graph-logs/<int:record_id>', methods=['GET', 'POST'])
@login_required
def view_tracker(record_id):
    import datetime
    now = datetime.datetime.now()
    selected_tracker = Tracker.query.get(record_id)
    logs = Log.query.all()
    try:
        con = sqlite3.connect('./database.sqlite3')
        print("Database opened successfully")
        c = con.cursor()
        c.execute('SELECT timestamp, value FROM Log WHERE user_id={} AND tracker_id={}'.format(current_user.id,selected_tracker.id))
        data = c.fetchall()

        dates = []
        values = []
        
        style.use('fivethirtyeight')
        from dateutil import parser

        for row in data:
            dates.append(parser.parse(row[0]))
            print(type(dates[0]))
            values.append(row[1])

        fig = plt.figure(figsize=(18, 8))
        plt.pie(values, labels=dates)
        ##plt.xlabel('Date and Time')
        ##plt.ylabel('Values')
        ##plt.tight_layout()
        plt.savefig('static\Images\graph.png')
        ##plt.show()

        gon = sqlite3.connect('./database.sqlite3')
        g = gon.cursor()
        added_date_time = g.execute('SELECT added_date_time FROM Log WHERE '
                                    'id=(SELECT max(id) FROM Log WHERE tracker_id={})'.format(record_id))

        added_date_time = added_date_time.fetchone()
        added_date_time = ''.join(added_date_time)
        print(added_date_time)
        from datetime import datetime
        last_updated = now - parser.parse(added_date_time)
        last_updated_str = str(last_updated)
        hour = last_updated_str[:1]
        min1 = last_updated_str[2]
        min2 = last_updated_str[3]
        minute = min1 + min2
        sec1 = last_updated_str[5]
        sec2 = last_updated_str[6]
        second = sec1 + sec2
        return render_template("view_tracker_logs_and_graph.html", user=current_user, tracker=selected_tracker,logs=logs, hour=hour, min=minute, sec=second)
    except Exception as e:
        print(e)
        flash('Something went wrong.', category='error')
        return render_template("view_tracker_logs_and_graph.html", user=current_user, tracker=selected_tracker,logs=logs)


@app.route('/delete-log/<int:record_id>', methods=['GET', 'POST'])
@login_required
def delete_log(record_id):
    Log_details = Log.query.get(record_id)
    tracker_id = Log_details.tracker_id
    try:
        db.session.delete(Log_details)
        db.session.commit()
        flash('Log Removed Successfully', category='success')
    except Exception as e:
        print(e)
        flash('Something went wrong.', category='error')
    return redirect(url_for('view_tracker', record_id=tracker_id))


@app.route('/edit-log/<int:record_id>', methods=['GET', 'POST'])
@login_required
def edit_log(record_id):
    this_log = Log.query.get(record_id)
    this_tracker = Tracker.query.get(this_log.tracker_id)
    try:
        if request.method == 'POST':
            when = request.form.get('date')
            value = request.form.get('value')
            notes = request.form.get('notes')

            this_log.timestamp = when
            this_log.value = value
            this_log.notes = notes

            db.session.commit()
            flash(this_tracker.name + ' Log Updated Successfully.', category='success')
            return redirect(url_for('view_tracker', record_id=this_log.tracker_id))
    except Exception as e:
        print(e)
        flash('Something went wrong.', category='error')

    return render_template("edit_log_page.html", user=current_user, tracker=this_tracker, log=this_log)

##----------------------------------------------------------------------------------------------------------------------------------##

db.create_all(app=app)
if __name__ == '__main__':
    app.run(debug=True)