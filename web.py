from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from datetime import datetime
import webbrowser

app = Flask(__name__)
app.secret_key = 'your_secret_key'
def open_db_connection(db_name):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    return connection, cursor

def close_db_connection(connection):
    if connection:
        connection.commit()
        connection.close()

#
# connn = sqlite3.connect('database/timekeeping.db')
# cursorr = connn.cursor()
#
# data = [
#     ('2024-08-14','Sales', 1, 'Hung', '07:30:23', '11:30:00'),('2024-08-14','Sales', 1, 'Hung', '13:30:23', '17:30:00'),('2024-08-14','Sales', 1, 'Hung', '18:00:23', '21:00:00'),
#     ('2024-06-26','Engineering', 2, 'Hugh Jackman', '07:00:00', '11:00:00'),('2024-06-26','Engineering', 2, 'Hugh Jackman', '13:00:00', '17:00:00'),('2024-06-26','Engineering', 2, 'Hugh Jackman', '18:00:00', '21:00:00'),
#     ('2024-09-28','Hr', 3, 'Zac Efron', '07:00:00', '17:00:00'),('2024-09-28','Hr', 3, 'Zac Efron', '13:00:00', '17:00:00')
# ]
#
# cursorr.executemany('''
# INSERT INTO timekeeping (Date,Department, ID, Name, "In", "Out")
# VALUES (?,?, ?, ?, ?, ?)
# ''', data)
# connn.commit()
# connn.close()
#
# # Create or connect to the dataset.db database
# conn = sqlite3.connect('database/dataset.db')
# cursor = conn.cursor()
#
# # Create the dataset table if it doesn't exist
# cursor.execute('''
#     CREATE TABLE IF NOT EXISTS dataset (
#         ID INTEGER PRIMARY KEY,
#         Name TEXT,
#         Authority TEXT,
#         Department TEXT
#     )
# ''')
# conn.commit()
#
# data = [
#     (1, 'Hung','user', 'Sales'),
#     (2, 'Hugh Jackman','user', 'Engineering'),
#     (3, 'Zac Efron', 'user', 'Hr')
# ]
#
# cursor.executemany('''
#     INSERT OR IGNORE INTO dataset (ID, Name, Authority, Department)
#     VALUES (?, ?, ?, ?)
# ''', data)
#
# conn.commit()
# conn.close()

connnn = sqlite3.connect('database/shift_settings.db')
cursorrr = connnn.cursor()
cursorrr.execute('''
    CREATE TABLE IF NOT EXISTS shift_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shift_name TEXT NOT NULL,
        credit INTEGER NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        late_after INTEGER NOT NULL,
        early_leave INTEGER NOT NULL,
        department TEXT NOT NULL,
        days TEXT NOT NULL
    )
''')
connnn.commit()
connnn.close()

def get_credentials_from_db():
    conn, cursor = open_db_connection('database/web.db')
    cursor.execute('SELECT Username, Password FROM web LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    return result

def get_departments_from_db():
    conn, cursor = open_db_connection('database/department.db')
    cursor.execute('SELECT department FROM departments')
    departments = [row[0] for row in cursor.fetchall()]
    conn.close()
    return departments

def get_timekeeping_data(date_from=None, date_to=None, search_type=None, search_value=None, search_department=None):
    conn, cursor = open_db_connection('database/timekeeping.db')
    query = 'SELECT Date, Department, ID, Name, "In", "Out" FROM timekeeping'
    params = []
    conditions = []
    # Date range search
    if date_from and date_to:
        conditions.append('Date BETWEEN ? AND ?')
        params.extend([date_from, date_to])
    # Search by selected field (ID, Name, etc.)
    if search_type and search_value:
        conditions.append('{} LIKE ?'.format(search_type))
        params.append('%' + search_value + '%')
    # Search by department
    if search_department and search_department != "":
        conditions.append('Department = ?')
        params.append(search_department)
    # Apply conditions to the query
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    cursor.execute(query, params)
    data = cursor.fetchall()
    conn.close()
    return data


@app.route('/')
def welcome():
    return render_template('welcome.html')

import socket

@app.route('/status', methods=['GET'])
def status():
    conn, cursor = open_db_connection('database/dataset.db')
    cursor.execute('SELECT COUNT(*) FROM dataset')
    user_count = cursor.fetchone()[0]
    conn.close()
    ip_address = socket.gethostbyname(socket.gethostname())
    user_capacity = user_count
    return render_template('status.html', ip_address=ip_address, user_capacity=user_capacity)


@app.route('/account', methods=['GET'])
def account():
    conn, cursor = open_db_connection('database/web.db')
    cursor.execute('SELECT Username, Password FROM web LIMIT 1')
    user = cursor.fetchone()
    conn.close()
    return render_template('account.html', username=user[0], password=user[1])

@app.route('/update_account', methods=['POST'])
def update_account():
    new_username = request.form['new_username']
    new_password = request.form['new_password']
    conn, cursor = open_db_connection('database/web.db')
    cursor.execute('UPDATE web SET Username = ?, Password = ?', (new_username, new_password))
    conn.commit()
    conn.close()
    return redirect(url_for('account'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db_username, db_password = get_credentials_from_db()
        if username != db_username or password != db_password:
            error = 'Username or Password is not valid'
        else:
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
    return render_template('login.html', error=error)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/time_table', methods=['GET', 'POST'])
def time_table():
    data = []
    departments = get_departments_from_db()
    if request.method == 'POST':
        date_from = request.form.get('date_from')
        date_to = request.form.get('date_to')
        search_type = request.form.get('search_type')
        search_value = request.form.get('search_value')
        search_department = request.form.get('search_department')  # Get department selection
        data = get_timekeeping_data(date_from, date_to, search_type, search_value, search_department)
    else:
        data = get_timekeeping_data()
    return render_template('time_table.html', data=data, departments=departments)


@app.route('/bulk_delete', methods=['POST'])
def bulk_delete():
    delete_entries = request.form.getlist('delete_entries')
    if delete_entries:
        print(delete_entries)
        conn, cursor = open_db_connection('database/timekeeping.db')
        for entry in delete_entries:
            try:
                date, department, id, name, in_time, out_time = entry.split(',')
                cursor.execute('DELETE FROM timekeeping WHERE Date = ? AND Department = ? AND ID = ? AND Name = ? AND "In" = ? AND "Out" = ?',(date, department, id, name, in_time, out_time))
            except ValueError:
                print(f"Skipping invalid entry: {entry}")
        conn.commit()
        conn.close()
    return redirect(url_for('time_table'))


@app.route('/bulk_delete_inspect_user', methods=['POST'])
def bulk_delete_inspect_user():
    delete_entries = request.form.getlist('delete_entries_inspect_user')
    user_id = request.form.get('user_id')
    if delete_entries:
        print(delete_entries)
        conn, cursor = open_db_connection('database/timekeeping.db')
        for entry in delete_entries:
            try:
                date, in_time, out_time = entry.split(',')
                cursor.execute('DELETE FROM timekeeping WHERE Date = ? AND "In" = ? AND "Out" = ?',
                               (date, in_time, out_time))
            except ValueError:
                print(f"Skipping invalid entry: {entry}")
        conn.commit()
        conn.close()
    return redirect(url_for('inspect_user', id=user_id))



def get_db_connection(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Route to display user analysis page
@app.route('/user_analysis', methods=['GET', 'POST'])
def user_analysis():
    conn = get_db_connection('database/dataset.db')
    departments = get_departments_from_db()
    if request.method == 'POST':
        search_type = request.form['search_type']
        search_value = request.form['search_value']
        search_department = request.form['search_department']
        query = 'SELECT * FROM dataset WHERE {} LIKE ?'.format(search_type)
        params = [f"%{search_value}%"]
        if search_department:
            query += ' AND Department = ?'
            params.append(search_department)
        users = conn.execute(query, params).fetchall()
    else:
        users = conn.execute('SELECT * FROM dataset').fetchall()
    conn.close()
    return render_template('user_analysis.html', users=users, departments=departments)



@app.route('/edit_user/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    conn = get_db_connection('database/dataset.db')
    user = conn.execute('SELECT * FROM dataset WHERE ID = ?', (id,)).fetchone()
    departments = get_departments_from_db()
    if request.method == 'POST':
        name = request.form['name']
        authority = request.form['authority']
        department = request.form['department']
        conn.execute('UPDATE dataset SET Name = ?, Authority = ?, Department = ? WHERE ID = ?', (name, authority, department, id))
        conn.commit()
        conn.close()
        flash('User updated successfully!')
        return redirect(url_for('user_analysis'))

    conn.close()
    return render_template('edit_user.html', user=user,departments=departments)


# Route to delete a user with confirmation
@app.route('/delete_user/<int:id>', methods=['POST'])
def delete_user(id):
    conn = get_db_connection('database/dataset.db')
    conn.execute('DELETE FROM dataset WHERE ID = ?', (id,))
    conn.commit()
    conn.close()
    flash('User deleted successfully!')
    return redirect(url_for('user_analysis'))


def is_valid_time(time_str):
    if time_str and isinstance(time_str, str):
        try:
            datetime.strptime(time_str, '%H:%M:%S')
            return True
        except ValueError:
            return False
    return False


@app.context_processor
def utility_processor():
    return dict(is_valid_time=is_valid_time, datetime=datetime)


@app.route('/inspect_user/<int:id>', methods=['GET', 'POST'])
def inspect_user(id):
    conn_dataset,cursor_dataset = open_db_connection('database/dataset.db')
    cursor_dataset.execute("SELECT Name, Authority, Idcard, Department FROM dataset WHERE ID = ?", (id,))
    user = cursor_dataset.fetchone()
    if user:
        user = {'ID': id, 'Name': user[0], 'Authority': user[1], 'Department': user[2]}
    else:
        user = {}
    conn_dataset.close()
    conn_timekeeping,cursor_timekeeping = open_db_connection('database/timekeeping.db')
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    query = 'SELECT Date, "In", "Out" FROM timekeeping WHERE ID = ? AND Department = ?'
    params = [id, user['Department']]
    if date_from and date_to:
        query += " AND Date BETWEEN ? AND ?"
        params.extend([date_from, date_to])
    cursor_timekeeping.execute(query, params)
    time_entries = cursor_timekeeping.fetchall()

    total_hours = 0
    for entry in time_entries:
        if is_valid_time(entry[1]) and is_valid_time(entry[2]):
            total_hours += (datetime.strptime(entry[2], '%H:%M:%S') - datetime.strptime(entry[1],'%H:%M:%S')).seconds / 3600

    conn_timekeeping.close()
    return render_template('inspect_user.html', user=user, time_entries=time_entries, total_hours=total_hours, salary=0)

@app.route('/shift_setting', methods=['GET', 'POST'])
def shift_setting():
    conn,cursor = open_db_connection('database/shift_settings.db')
    cursor.execute('SELECT id, shift_name, credit, start_time, end_time, late_after, early_leave, department, days FROM shift_settings')
    shifts = cursor.fetchall()
    conn.close()
    # Convert tuples to dictionaries
    shifts = [dict(id=row[0], shift_name=row[1], credit=row[2], start_time=row[3], end_time=row[4], late_after=row[5],early_leave=row[6], department=row[7], days=row[8]) for row in shifts]
    return render_template('shift_setting.html', shifts=shifts)


@app.route('/shift_create', methods=['GET', 'POST'])
def shift_create():
    departments = get_departments_from_db()
    conn, cursor = open_db_connection('database/shift_settings.db')
    cursor.execute('SELECT shift_name, start_time, end_time, department, days FROM shift_settings')
    existing_shifts = cursor.fetchall()
    conn.close()
    existing_shifts = [
        {'shift_name': row[0], 'start_time': row[1], 'end_time': row[2], 'department': row[3].split(','), 'days': row[4].split(',')}
        for row in existing_shifts
    ]

    if request.method == 'POST':
        shift_name = request.form['shift_name']
        credit = request.form['credit']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        late_after = request.form['late_after']
        early_leave = request.form['early_leave']
        departments = ','.join(request.form.getlist('departments'))
        days = ','.join(request.form.getlist('days'))
        conn,cursor = open_db_connection('database/shift_settings.db')
        cursor.execute('''
            INSERT INTO shift_settings (shift_name, credit, start_time, end_time, late_after, early_leave, department, days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (shift_name, credit, start_time, end_time, late_after, early_leave, departments, days))
        conn.commit()
        conn.close()

        return redirect(url_for('shift_setting'))
    return render_template('shift_create.html', departments=departments, existing_shifts=existing_shifts)


@app.route('/shift_edit/<int:id>', methods=['GET', 'POST'])
def shift_edit(id):
    conn = sqlite3.connect('database/shift_settings.db')
    departments = get_departments_from_db()
    cursor = conn.cursor()
    if request.method == 'POST':
        shift_name = request.form['shift_name']
        credit = request.form['credit']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        late_after = request.form['late_after']
        early_leave = request.form['early_leave']
        departments = ','.join(request.form.getlist('departments'))
        days = ','.join(request.form.getlist('days'))

        cursor.execute('''
            UPDATE shift_settings
            SET shift_name = ?, credit = ?, start_time = ?, end_time = ?, late_after = ?, early_leave = ?, department = ?, days = ?
            WHERE id = ?
        ''', (shift_name, credit, start_time, end_time, late_after, early_leave, departments, days, id))
        conn.commit()
        conn.close()

        return redirect(url_for('shift_setting'))
    else:
        cursor.execute('SELECT id, shift_name, credit, start_time, end_time, late_after, early_leave, department, days FROM shift_settings WHERE id = ?', (id,))
        shift = cursor.fetchone()
        conn.close()
        # Convert tuple to dictionary
        shift = dict(id=shift[0], shift_name=shift[1], credit=shift[2], start_time=shift[3], end_time=shift[4], late_after=shift[5], early_leave=shift[6], department=shift[7].split(','), days=shift[8].split(','))
        return render_template('shift_edit.html', shift=shift, departments=departments)

@app.route('/shift_delete/<int:id>', methods=['POST'])
def shift_delete(id):
    conn,cursor = open_db_connection('database/shift_settings.db')
    cursor.execute('DELETE FROM shift_settings WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('shift_setting'))


def get_shift_for_department(department, day, in_time, shift_data):
    in_time = datetime.strptime(in_time, '%H:%M:%S')
    for shift in shift_data:
        shift_departments = shift['department'].split(',')
        shift_start_time = datetime.strptime(shift['start_time'], '%H:%M')
        if department in shift_departments and day in shift['days'] and abs((in_time - shift_start_time).total_seconds()) <= 3600:
            return {
                'name': shift['shift_name'],
                'start_time': shift['start_time'],
                'end_time': shift['end_time'],
                'credit': shift['credit'],
                'late_after': shift['late_after'],
                'early_leave': shift['early_leave']
            }
    return None  # Handle cases where no shift is found


def calculate_late_early(shift, in_time, out_time):
    shift_start = datetime.strptime(shift['start_time'], '%H:%M')
    shift_end = datetime.strptime(shift['end_time'], '%H:%M')
    in_time = datetime.strptime(in_time, '%H:%M:%S')
    out_time = datetime.strptime(out_time, '%H:%M:%S')
    late_threshold = shift_start.replace(minute=(shift_start.minute + shift['late_after']) % 60)
    early_threshold = shift_end.replace(minute=(shift_end.minute - shift['early_leave']) % 60)
    if shift_start.minute + shift['late_after'] >= 60:
        late_threshold = late_threshold.replace(hour=shift_start.hour + 1)
    if shift_end.minute - shift['early_leave'] < 0:
        early_threshold = early_threshold.replace(hour=shift_end.hour - 1)
    late = 1 if in_time > late_threshold else 0
    early = 1 if out_time < early_threshold else 0
    return late, early


def get_day_from_date(date_str):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    day_full = date_obj.strftime('%a')  # Wed, Thu, etc.
    day_short = day_full[:2]  # We, Th, etc.
    return day_short


@app.route('/calculate_merit', methods=['GET', 'POST'])
def calculate_merit():
    # Establish connections to the databases
    connection_timekeeping,cursor_timekeeping = open_db_connection('database/timekeeping.db')
    connection_dataset, cursor_dataset = open_db_connection('database/dataset.db')
    connection_shift, cursor_shift = open_db_connection('database/shift_settings.db')

    # Fetch shifts from shift_settings.db
    cursor_shift.execute("SELECT shift_name, credit, start_time, end_time, late_after, early_leave, department, days FROM shift_settings")
    shift_data = []
    for row in cursor_shift.fetchall():
        shift_data.append({
            'shift_name': row[0],
            'credit': row[1],
            'start_time': row[2],
            'end_time': row[3],
            'late_after': row[4],
            'early_leave': row[5],
            'department': row[6],
            'days': row[7].split(',')  # Assuming days are stored as comma-separated values (Mo, Tu, etc.)
        })
    print("shift_data:", shift_data)
    # Fetch departments and employees from dataset.db
    cursor_dataset.execute("SELECT Department, ID, Name FROM dataset")
    dataset_data = cursor_dataset.fetchall()
    departments = {}
    for row in dataset_data:
        department = row[0]
        if department not in departments:
            departments[department] = []
        departments[department].append({'id': row[1], 'name': row[2]})
    print("departments:", departments)
    results = []
    if request.method == 'POST':
        departments_selected = request.form.getlist('departments')  # Selected departments
        print("departments_selected:", departments_selected)
        from_date = request.form['from_date']
        print("from_date:", from_date)
        to_date = request.form['to_date']
        print("to_date:", to_date)
        compensate = float(request.form['compensate']) / 100.0
        print("compensate:", compensate)
        query = """
            SELECT Date, ID, Department, Name, "In", "Out"
            FROM timekeeping
            WHERE Date BETWEEN ? AND ? AND Department IN ({})
        """.format(','.join('?' for _ in departments_selected))
        params = [from_date, to_date] + departments_selected
        print("params:", params)
        timekeeping_data = cursor_timekeeping.execute(query, params).fetchall()
        print("timekeeping_data",timekeeping_data)
        # Process each timekeeping entry
        for row in timekeeping_data:
            date, id, dept, name, in_time, out_time = row
            day = get_day_from_date(date)
            print("row:", row)
            print("day:", day)
            if in_time == '-' or out_time == '-':
                results.append(
                    {'date': date, 'id': id, 'department': dept, 'name': name, 'day': day, 'shift': '-','in': in_time, 'out': out_time, 'late': '-', 'early': '-', 'total_credit': '-'})
                continue
            shift = get_shift_for_department(dept, day,in_time, shift_data)
            if shift:
                late, early = calculate_late_early(shift, in_time, out_time)
                shift_credit = shift['credit']
                total_credit = shift_credit - compensate * shift_credit * late - compensate * shift_credit * early
                results.append({'date': date,'id': id,'department': dept,'name': name,'day': day,'shift': shift['name'],'in': in_time,'out': out_time,'late': late,'early': early,'total_credit': total_credit})
            else:
                results.append({'date': date,'id': id,'department': dept,'name': name,'day': day,'shift': '-','in': in_time,'out': out_time,'late': '-','early': '-','total_credit': '-'})

    # Close the database connections
    connection_timekeeping.close()
    connection_dataset.close()
    connection_shift.close()

    # Render the template with the results
    return render_template('calculate_merit.html', results=results, departments=departments)

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to reach the external server; just used to get the local IP.
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    except Exception:
        ip_address = "Unable to get IP"
    finally:
        s.close()
    return ip_address
    
def main():
    def open_browser():
        with app.test_request_context():
            ip_address = get_ip()
            url = "http://" + ip_address + ":5000"
            webbrowser.open(url)

    open_browser()
    app.run( host='0.0.0.0')

if __name__ == '__main__':
    main()
