import logging
from flask import Flask, redirect, render_template, request, session, url_for
from flask_login import LoginManager, UserMixin
import psycopg
from datetime import datetime

try:
    connection = psycopg.connect("host=localhost dbname=fitnessManager user=postgres password=postgres")
except Exception as e:
    print("ERROR: Cannot connect to database. ", e)

app = Flask(__name__, template_folder="templates", static_url_path='/static')
app.config["SECRET_KEY"] = "ENTER YOUR SECRET KEY"


login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        birthday = request.form.get("birthday")
        phone_number = request.form.get("phone_number")

        with connection.cursor() as cur:
            try:
                cur.execute("INSERT INTO member (member_id, password, first_name, last_name, birthday, phone_number, register_date) VALUES (%s, %s, %s, %s, %s, %s, %s)", (username, password, first_name, last_name, birthday, phone_number, datetime.now().date().strftime("%Y-%m-%d")))
                connection.commit()
                return redirect(url_for("login"))
            except Exception as e:
                logging.error(f"Error while registering user: {e}")
                error="Error: Cannot add value to database. ", e
                return render_template("register.html", error = error)
    return render_template("register.html")

@app.route('/', methods=["GET", "POST"])
@app.route('/login', methods=["GET", "POST"])
def login():
    session['members'] = []
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user_type = request.form.get("type")
        
        with connection.cursor() as cur:
            try:
                query = f"SELECT password FROM {user_type} WHERE {user_type}_id = %s"
                cur.execute(query,(username,))
                db_password = cur.fetchall()
                print("db_password", db_password[0][0])
                if db_password and db_password[0][0] == password:
                    session['user_id'] = username
                    return redirect(url_for(user_type))
            except Exception as e:
                logging.error(f"Error while logging in user: {e}")
                error="Error: Cannot log in. ", e
                return render_template("login.html", error = error)
    return render_template("login.html")

@app.route('/member', methods=["GET","POST"])
def member():
    print("session id:", session['user_id'])
    if request.method=="POST":
        weight = request.form.get("weight")
        rest_heart_rate = request.form.get("rest_heart_rate")
        pace = request.form.get("pace")
        blood_pressure = request.form.get("blood_pressure")

        columns = []
        values = []
        params = []

        if weight:
            columns.append("weight")
            values.append(weight)
            params.append("%s")
        if rest_heart_rate:
            columns.append("rest_heart_rate")
            values.append(rest_heart_rate)
            params.append("%s")
        if pace:
            columns.append("pace")
            values.append(pace)
            params.append("%s")
        if blood_pressure:
            columns.append("blood_pressure")
            values.append(blood_pressure)
            params.append("%s")

        with connection.cursor() as cur:
            try:
                cur.execute("SELECT * FROM metrics WHERE member_id = %s", (session['user_id'],))
                metrics_exist = cur.fetchone()
                if metrics_exist:
                    set = []
                    pos = 0
                    for val in columns:
                        set.append(f"{val}='{values[pos]}'")
                        pos+=1 
                    set_str = ','.join(set)
                    cur.execute(f"UPDATE metrics SET {set_str} WHERE member_id = %s", (session['user_id'],))
                else:
                    columns.append('member_id')
                    params.append('%s')
                    columns_str = ','.join(columns)
                    params_str = ','.join(params)
                    values.append(session['user_id'])
                    cur.execute(f"INSERT INTO metrics ({columns_str}) VALUES ({params_str})", values)
                print("Metrics update successful")
                connection.commit()
            except Exception as e:
                connection.rollback()
                print(f"Error: {e}")

    with connection.cursor() as cur:
        current_date = datetime.now().date()
    #User info
        cur.execute("SELECT member.first_name, member.last_name FROM member WHERE member_id = %s",(session['user_id'],))
        user = cur.fetchall()
    #Upcoming Classes
        cur.execute("SELECT bookings.room_id, class.name, class.description, bookings.date, bookings.start_time, bookings.end_time, class.class_id FROM bookings JOIN class ON bookings.class_id = class.class_id JOIN member_schedule ON bookings.class_id = member_schedule.class_id WHERE member_schedule.member_id = %s AND bookings.date >= %s ",(session['user_id'], current_date,))
        classes = cur.fetchall()

    #Upcoming Private Sessions
        cur.execute("SELECT session.session_type, trainer.first_name, session.date, session.start_time, session.end_time, session.location, session.session_id FROM session JOIN trainer ON session.trainer_id = trainer.trainer_id WHERE session.member_id = %s AND session.date >= %s", (session['user_id'], current_date,))
        private = cur.fetchall()
    
    #Health Metrics
        cur.execute("SELECT * FROM metrics WHERE member_id = %s", (session['user_id'],))
        metrics = cur.fetchall()

    #Goals
        cur.execute("SELECT exercise.routine_name, exercise.sets, exercise.reps, exercise.weight, exercise.distance, goals.description FROM exercise JOIN goals ON exercise.exercise_id = goals.exercise_id WHERE goals.member_id = %s", (session['user_id'],))
        goals = cur.fetchall()

    #Fitness Routines
        cur.execute("SELECT exercise.routine_name, exercise.sets, exercise.reps, exercise.weight, exercise.distance, exercise.date, exercise.start_time, exercise.end_time FROM exercise JOIN completed ON exercise.exercise_id = completed.exercise_id WHERE completed.member_id = %s",(session['user_id'],))
        routines = cur.fetchall()

    #Class History
        cur.execute("SELECT bookings.room_id, class.name, class.description, bookings.date, bookings.start_time, bookings.end_time FROM bookings JOIN class ON bookings.class_id = class.class_id JOIN member_schedule ON bookings.class_id = member_schedule.class_id WHERE member_schedule.member_id = %s AND bookings.date < %s",(session['user_id'], current_date,))
        history = cur.fetchall()

    #Session History
        cur.execute("SELECT session.session_type, trainer.first_name, session.date, session.start_time, session.end_time, session.location FROM session JOIN trainer ON session.trainer_id = trainer.trainer_id WHERE session.member_id = %s AND session.date < %s", (session['user_id'], current_date,))
        completed = cur.fetchall() 

    #Billing History
        cur.execute("SELECT billing_id, type, date, amount FROM billing WHERE member_id = %s",(session['user_id'],))
        billing = cur.fetchall()

        return render_template("member.html", user = user, classes = classes, private = private, metrics = metrics, goals = goals, routines = routines, completed = completed, billing = billing, history = history)

@app.route('/memremoveclass', methods=["GET"])
def memremoveclass():
    with connection.cursor() as cur:
        try:
            id = request.args.get('id')
            cur.execute("DELETE FROM member_schedule WHERE class_id = %s AND member_id = %s", (id, session['user_id'],))
            connection.commit()
        except Exception as e:
            print("Error: " +str(e))
    return redirect(url_for('member'))

@app.route('/memremovesession', methods=["GET"])
def memremovesession():
    with connection.cursor() as cur:
        try:
            id = request.args.get('id')
            cur.execute("DELETE FROM session WHERE session_id = %s AND member_id = %s", (id, session['user_id'],))
            connection.commit()
        except Exception as e:
            print("Error: " +str(e))
    return redirect(url_for('member'))

@app.route('/addexercise', methods=["GET","POST"])
def addexercise():
    if request.method == "POST":
        form_data = {
            'routine_name': request.form.get('routine_name'),
            'sets': request.form.get('sets'),
            'reps': request.form.get('reps'),
            'weight': request.form.get('weight'),
            'distance': request.form.get('distance'),
            'date': request.form.get('date'),
            'start_time': request.form.get('start_time'),
            'end_time': request.form.get('end_time')
        }

        for key, value in form_data.items():
            if value == '':
                form_data[key] = None

        parameters = [form_data[key] for key in form_data]

        with connection.cursor() as cur:
            try:
                cur.execute("INSERT INTO exercise (routine_name, sets, reps, weight, distance, date, start_time, end_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING exercise_id", parameters)
                exercise_id = cur.fetchone()[0]
                cur.execute("INSERT INTO completed (exercise_id, member_id) VALUES (%s, %s)", (exercise_id, session['user_id'],))
                connection.commit()
                return redirect(url_for('member'))
            except Exception as e:
                print(f"Error: {e}")
    return redirect(url_for('member'))

@app.route('/schedule', methods=["GET"])
def schedule():
    #Group classes
    current_date = datetime.now().date()
    with connection.cursor() as cur:
        cur.execute("SELECT c.name, t.first_name, c.description, c.cost, b.date, b.start_time, b.end_time, (c.capacity - COUNT(m.class_id)) AS available, c.class_id FROM class c JOIN trainer t ON c.trainer_id = t.trainer_id JOIN bookings b ON b.class_id = c.class_id LEFT JOIN member_schedule m ON c.class_id = m.class_id WHERE b.date >= %s GROUP BY c.name, t.trainer_id, c.description, c.cost, b.date, b.start_time, b.end_time, c.class_id", (current_date,))
        classes = cur.fetchall()
        print(classes)
        #Personal trainer sessions
        cur.execute("SELECT trainer.first_name, t.date, t.start_time, t.end_time, t.schedule_id FROM trainer JOIN trainer_availability t ON trainer.trainer_id = t.trainer_id WHERE t.date >= %s", (current_date,))   
        session = cur.fetchall()
    return render_template("schedule.html", classes = classes, session = session)

@app.route('/addsession', methods=["GET"])
def addsession():
    current_date = datetime.now().date()
    with connection.cursor() as cur:
        session_id = request.args.get('id')
        if cur.execute("INSERT INTO session (session_id, trainer_id, member_id, session_type, date, start_time, end_time) SELECT t.schedule_id, t.trainer_id, %s, %s, t.date, t.start_time, t.end_time FROM trainer_availability t WHERE t.schedule_id = %s", (session['user_id'], "Private", session_id,)):
            cur.execute("DELETE FROM trainer_availability WHERE schedule_id = %s", (session_id,))
        cur.execute("INSERT INTO billing (admin_id, member_id, type, date, amount) VALUES(%s,%s,%s,%s,%s)",('admin',session['user_id'], 'Private',current_date, '100'))
        connection.commit()
        return redirect(url_for('schedule'))
    
@app.route('/addclassmem', methods=["GET"])
def addclassmem():
    current_date = datetime.now().date()
    with connection.cursor() as cur:
        id = request.args.get('id')
        cur.execute("INSERT INTO member_schedule (member_id, class_id) VALUES (%s,%s)", (session['user_id'], id,))
        cur.execute("SELECT name, cost FROM class WHERE class_id = %s", (id,))
        class_info = cur.fetchone()
        cur.execute("INSERT INTO billing (admin_id, member_id, type, date, amount) VALUES(%s,%s, %s,%s, %s)", ('admin',session['user_id'],class_info[0],current_date, class_info[1],))
        connection.commit()
    return redirect(url_for('schedule'))


@app.route('/editmem', methods=["GET","POST"])
def editmem():
    print("session id:", session['user_id'])
    result = ''
    if request.method=="POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        phone_number = request.form.get("phone_number")
        birthday = request.form.get("birthday")
        card_number = request.form.get("card_number")

        columns = []
        values = []
        params = []

        if first_name:
            columns.append("first_name")
            values.append(first_name)
            params.append("%s")
        if last_name:
            columns.append("last_name")
            values.append(last_name)
            params.append("%s")
        if phone_number:
            columns.append("phone_number")
            values.append(phone_number)
            params.append("%s")
        if birthday:
            columns.append("birthday")
            values.append(birthday)
            params.append("%s")

        if card_number:
            columns.append("card_number")
            values.append(card_number)
            params.append("%s")

        with connection.cursor() as cur:
            try:
                set = []
                pos = 0
                for val in columns:
                    set.append(f"{val}='{values[pos]}'")
                    pos+=1 
                set_str = ','.join(set)
                cur.execute(f"UPDATE member SET {set_str} WHERE member_id = %s", (session['user_id'],))
                print("Metrics update successful")
                connection.commit()
                result ="Info updated successfully!"
            except Exception as e:
                connection.rollback()
                print(f"Error: {e}")
                result = "Info not updated."
    return render_template("editmem.html", result = result)

@app.route('/goal', methods=["GET","POST"])
def goal():
    if request.method == 'POST':
        with connection.cursor() as cur:
            form_data = {
                'routine_name': request.form.get('routine_name'),
                'sets': request.form.get('sets'),
                'reps': request.form.get('reps'),
                'weight': request.form.get('weight'),
                'distance': request.form.get('distance'),
                'date': request.form.get('date'),
                'start_time': request.form.get('start_time'),
                'end_time': request.form.get('end_time')
            }
            for key, value in form_data.items():
                if value == '':
                    form_data[key] = None

            parameters = [form_data[key] for key in form_data]

            description = request.form.get("description")
            cur.execute("INSERT INTO exercise (routine_name, sets, reps, weight, distance, date, start_time, end_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING exercise_id", parameters)
            exercise_id = cur.fetchone()[0]
            cur.execute("INSERT INTO goals (exercise_id, member_id, description) VALUES (%s,%s, %s)", (exercise_id, session['user_id'],description,))
            connection.commit()
            return redirect(url_for('member'))

@app.route('/trainer', methods=["GET","POST"])
def trainer():  
    members = session.get('members', [])
    with connection.cursor() as cur:
        # Unbooked avaliability
        cur.execute("SELECT date, start_time, end_time, schedule_id FROM trainer_availability WHERE trainer_id=%s", (session['user_id'],))
        availability = cur.fetchall()
        
        current_date = datetime.now().date()
        #Upcoming sessions
        cur.execute("SELECT member.first_name, member.last_name, session.session_type, session.date, session.start_time, session.end_time FROM session JOIN member ON session.member_id = member.member_id WHERE session.trainer_id = %s AND session.date >= %s",(session['user_id'], current_date,))
        sessions = cur.fetchall()

        #Completed sessions
        cur.execute("SELECT session.session_id, session.trainer_id, member.first_name, member.last_name, session.session_type, session.date, session.start_time, session.end_time FROM session JOIN member ON session.member_id = member.member_id WHERE session.trainer_id = %s AND session.date < %s",(session['user_id'], current_date,))
        completed = cur.fetchall()


    return render_template("trainer.html", availability = availability, sessions = sessions, comlpeted = completed, members=members)

@app.route('/lookup', methods=["POST"])
def lookup():
    if request.method=="POST":
        name = request.form.get("name")
        split_name = name.split()
        if not split_name: #if request was empty, will exit this post request
            return redirect(url_for('trainer'))
        if len(split_name) == 1: #if only one value was typed, will set second value as None
            split_name.append(None)
        with connection.cursor() as cur: #This query will check if there are any members in the table that match any of the names given
            cur.execute("SELECT m.first_name, m.last_name, mt.weight, mt.rest_heart_rate, mt.pace, mt.blood_pressure FROM member m LEFT JOIN metrics mt ON m.member_id = mt.member_id WHERE m.first_name = %s OR m.first_name = %s OR m.last_name = %s OR m.last_name = %s", (split_name[0], split_name[1], split_name[0], split_name[1],))
            members_metrics = cur.fetchall()
            session['members'] = members_metrics
            
        return redirect(url_for('trainer'))

@app.route('/add', methods=["POST"])
def add():
    with connection.cursor() as cur:
        try:
            date = request.form.get("date")
            print("date:",date)
            time = request.form.get("time")
            time+=':00'
            print("time: ",time)
            hours, minutes, seconds = map(int, time.split(":"))
            hours += 1
            hours%24
            end_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            print("end time: ", end_time)
            cur.execute("INSERT INTO trainer_availability (trainer_id, date, start_time, end_time) VALUES (%s,%s,%s,%s)",(session['user_id'], date, time, end_time,))
            connection.commit()
            return redirect(url_for('trainer'))
        except Exception as e:
            return "Error occurred: " + str(e)
        
@app.route('/removesession', methods=["GET"])
def removesession():
    with connection.cursor() as cur:
        try:
            id = request.args.get('id')
            cur.execute("DELETE FROM trainer_availability WHERE schedule_id  = %s AND trainer_id = %s", (id, session['user_id'],))
            connection.commit()
            return redirect(url_for('trainer'))
        except Exception as e:
            return "Error occurred: " + str(e)   

@app.route('/admin', methods=["GET","POST"])
def admin():
    if request.method == "POST":
        current_date = datetime.now().date()
        member = request.form.get('member')
        ses = request.form.get('session')
        amount = request.form.get('amount')
        with connection.cursor() as cur:
            cur.execute("INSERT INTO billing (admin_id, member_id, type, date, amount) VALUES(%s,%s,%s,%s,%s)", (session['user_id'], member,ses, current_date, amount))

    with connection.cursor() as cur:
        #Classes
        cur.execute("SELECT c.class_id, c.name, c.trainer_id, c.description, c.cost, b.date, b.start_time, b.end_time, c.capacity, (c.capacity - (c.capacity - COUNT(m.class_id))), c.class_id AS avaliable FROM class c JOIN bookings b ON c.class_id = b.class_id LEFT JOIN member_schedule m ON c.class_id = m.class_id GROUP BY c.name, c.trainer_id, c.description, c.cost, b.date, b.start_time, b.end_time, c.capacity, c.class_id")
        classes = cur.fetchall()      
        #Personal trainer sessions
        cur.execute("SELECT t.session_id, trainer.trainer_id, t.member_id, t.date, t.start_time, t.end_time, t.location FROM trainer JOIN session t ON trainer.trainer_id = t.trainer_id ",)   
        sessions = cur.fetchall()
        #Equipment
        cur.execute("SELECT * FROM equipment")
        equipment = cur.fetchall()
        #Billing
        cur.execute("SELECT billing_id, admin_id, member_id, type,date, amount FROM billing")
        billing = cur.fetchall()
        #Booking
        cur.execute("SELECT class_id, room_id, date, start_time, end_time FROM bookings")
        bookings= cur.fetchall()

    return render_template("admin.html", bookings = bookings, billing = billing, classes = classes, sessions = sessions, equipment = equipment)

@app.route('/deletebill', methods=["GET"])
def deletebill():
    with connection.cursor() as cur:
        id = request.args.get('id')
        cur.execute("DELETE FROM billing WHERE billing_id = %s", (id,))
        connection.commit()
    return redirect(url_for('admin'))

@app.route('/editclass', methods=["GET","POST"])
def editclass():
    id = request.args.get('id')
    if request.method=="POST":
        name = request.form.get('name')
        trainer_id = request.form.get('trainer_id')
        description = request.form.get('description')
        cost = request.form.get('cost')
        date = request.form.get('date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        capacity = request.form.get('capacity')
        
        try:
            with connection.cursor() as cur:
                cur.execute("UPDATE class SET name=%s, trainer_id=%s, description=%s, capacity=%s, cost=%s WHERE class_id = %s",(name, trainer_id, description, capacity,cost,id,))
                cur.execute("UPDATE bookings SET date=%s, start_time =%s, end_time = %s WHERE class_id = %s",(date, start_time,end_time, id,))
                connection.commit()
        except Exception as e:
            print("Error:", e)

    with connection.cursor() as cur:
        cur.execute("SELECT c.name, c.trainer_id, c.description, c.cost, b.date, b.start_time, b.end_time, c.capacity, b.room_id FROM class c JOIN bookings b ON c.class_id = b.class_id WHERE c.class_id = %s", (id,))
        values = cur.fetchone()
        cur.execute("SELECT room_id FROM room")
        rooms = cur.fetchall()

    return render_template("editclass.html", name = values[0], trainer_id = values[1], description = values[2], cost = values[3], date = values[4], start_time = values[5], end_time = values[6], capacity = values[7], location = values[8], rooms = rooms)

@app.route('/deletebooking', methods=["GET"])
def deletebooking():
    with connection.cursor() as cur:
        try:
            id = request.args.get('id')
            cur.execute("DELETE FROM bookings WHERE class_id= %s", (id,))
            cur.execute("DELETE FROM class WHERE class_id= %s", (id,))
            connection.commit()
        except Exception as e:
            print("Error:", e)  
    return redirect(url_for('admin'))


@app.route('/addclass', methods=["POST"])
def addclass():
    if request.method == "POST":
        name = request.form.get('name')
        trainer_id = request.form.get('trainer_id')
        description = request.form.get('description')
        cost = request.form.get('cost')
        capacity = request.form.get('capacity')
        date = request.form.get('date')
        room = request.form.get('room')
        start = request.form.get('start_time')
        end = request.form.get('end_time')
        with connection.cursor() as cur:
            try:
                cur.execute("INSERT INTO class (name, trainer_id, description, cost, capacity) VALUES (%s, %s, %s, %s, %s) RETURNING class_id",
                (name, trainer_id, description, cost, capacity))
                id = cur.fetchone()[0]
                cur.execute("SELECT room_id FROM room WHERE room_id = %s", (room,))
                room = cur.fetchall()[0][0]
                cur.execute("INSERT INTO bookings (class_id, room_id, date, start_time, end_time) VALUES (%s,%s,%s,%s,%s)",(id,room, date, start, end,))
                connection.commit()
                return redirect(url_for('admin'))
            except Exception as e:
                return "Error occurred: " + str(e) 
    return redirect(url_for('admin'))

@app.route('/updateeqip', methods=["POST"])
def updateeqip():
    if request.method == "POST":
        id = request.form.get('id')
        date = request.form.get('date')

        with connection.cursor() as cur:
            try:
                cur.execute("UPDATE equipment SET maintinence_date = %s WHERE equipment_id = %s", (date, id,))
                connection.commit()
                print("Update successful")
            except Exception as e:
                print("Error occurred: " + str(e))
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)