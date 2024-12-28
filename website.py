from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from datetime import datetime
import socket
import webbrowser
import pickle
import numpy as np
import torch
import shutil
import time
import adafruit_fingerprint
import serial
from contextlib import closing  

app = Flask(__name__)
app.secret_key = 'your_secret_key'

finger = None


def get_fingerprint_sensor():
    global finger
    if finger is None:
        try:
            uart = serial.Serial('/dev/ttyTHS1', 57200, timeout=5)
            finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
        except Exception as e:
            print("Fingerprint sensor not connected:", e)
            finger = None
    return finger


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
    except Exception:
        ip_address = "Unable to get IP"
    return ip_address


@app.route('/')
def welcome():
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        session.pop('user', None)
    error = None
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            db_username = None
            db_password = None
            with closing(sqlite3.connect('database/web.db', timeout=1)) as conn_web:
                conn_web.execute('PRAGMA journal_mode=WAL;')
                with closing(conn_web.cursor()) as cursor_web:
                    cursor_web.execute('SELECT Username, Password FROM web LIMIT 1')
                    db_username, db_password = cursor_web.fetchone()
            if db_username is None or db_password is None:
                return render_template('login.html', error=error)
            if username != db_username or password != db_password:
                error = 'Username or Password is not valid'
            else:
                session['user'] = username
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(f"login error as {e}")
            error = 'login error as {e}'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')


@app.route('/status', methods=['GET'])
def status():
    if 'user' not in session:
        return redirect(url_for('login'))
    ip_address = "Not found"
    user_count = 0
    try:
        with closing(sqlite3.connect('database/dataset.db', timeout=1)) as conn_dataset:
            conn_dataset.execute('PRAGMA journal_mode=WAL;')
            with closing(conn_dataset.cursor()) as cursor_dataset:
                cursor_dataset.execute('SELECT COUNT(*) FROM dataset')
                user_count = cursor_dataset.fetchone()[0]
            ip_address = get_ip()
            user_capacity = user_count
    except Exception as e:
        print(f" status page eror at {e}")
        ip_address = "Not found"
        user_capacity = 0
    return render_template('status.html', ip_address=ip_address, user_capacity=user_capacity)


@app.route('/account', methods=['GET'])
def account():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = ("Error", "Error")
    try:
        with closing(sqlite3.connect('database/web.db', timeout=1)) as conn_web:
            conn_web.execute('PRAGMA journal_mode=WAL;')
            with closing(conn_web.cursor()) as cursor_web:
                cursor_web.execute('SELECT Username, Password FROM web LIMIT 1')
                user = cursor_web.fetchone()
    except Exception as e:
        print(f" status page eror at {e}")
    return render_template('account.html', username=user[0], password=user[1])


@app.route('/update_account', methods=['POST'])
def update_account():
    try:
        new_username = request.form['new_username']
        new_password = request.form['new_password']
        with closing(sqlite3.connect('database/web.db', timeout=1)) as conn_web:
            conn_web.execute('PRAGMA journal_mode=WAL;')
            with closing(conn_web.cursor()) as cursor_web:
                cursor_web.execute('UPDATE web SET Username = ?, Password = ?', (new_username, new_password))
            conn_web.commit()
    except Exception as e:
        print(f"update_account error as {e}")
    return redirect(url_for('account'))


@app.route('/time_table', methods=['GET', 'POST'])
def time_table():
    if 'user' not in session:
        return redirect(url_for('login'))
    data = []
    departments = []
    try:
        with closing(sqlite3.connect('database/department.db', timeout=1)) as conn_department:
            conn_department.execute('PRAGMA journal_mode=WAL;')
            with closing(conn_department.cursor()) as cursor_department:
                cursor_department.execute('SELECT department FROM departments')
                departments = [row[0] for row in cursor_department.fetchall()]
        if request.method == 'POST':
            date_from = request.form.get('date_from')
            date_to = request.form.get('date_to')
            search_type = request.form.get('search_type')
            search_value = request.form.get('search_value')
            search_department = request.form.get('search_department')
            try:
                with closing(sqlite3.connect('database/timekeeping.db', timeout=1)) as conn_timekeeping:
                    conn_timekeeping.execute('PRAGMA journal_mode=WAL;')
                    with closing(conn_timekeeping.cursor()) as cursor_timekeeping:
                        query = 'SELECT Date, Department, ID, Name, "In", "Out" FROM timekeeping'
                        params = []
                        conditions = []
                        if date_from and date_to:
                            conditions.append('Date BETWEEN ? AND ?')
                            params.extend([date_from, date_to])
                        if search_type and search_value:
                            conditions.append('{} LIKE ?'.format(search_type))
                            params.append('%' + search_value + '%')
                        if search_department and search_department != "":
                            conditions.append('Department = ?')
                            params.append(search_department)
                        if conditions:
                            query += ' WHERE ' + ' AND '.join(conditions)
                        cursor_timekeeping.execute(query, params)
                        data = cursor_timekeeping.fetchall()
            except Exception as e:
                print(f"Error in time_table: {e}")
                data = []
                departments = []
        else:
            try:
                with closing(sqlite3.connect('database/timekeeping.db', timeout=1)) as conn_timekeeping:
                    conn_timekeeping.execute('PRAGMA journal_mode=WAL;')
                    with closing(conn_timekeeping.cursor()) as cursor_timekeeping:
                        cursor_timekeeping.execute('SELECT Date, Department, ID, Name, "In", "Out" FROM timekeeping')
                        data = cursor_timekeeping.fetchall()
            except Exception as e:
                print(f"Error in time_table: {e}")
                data = []
                departments = []
    except Exception as e:
        print(f"Error in time_table: {e}")
        data = []
        departments = []
    return render_template('time_table.html', data=data, departments=departments)


@app.route('/bulk_delete', methods=['POST'])
def bulk_delete():
    delete_entries = request.form.getlist('delete_entries')
    if not delete_entries:
        print("No entries selected for deletion.")
        return redirect(url_for('time_table'))
    try:
        with closing(sqlite3.connect('database/timekeeping.db', timeout=1)) as conn_timekeeping:
            conn_timekeeping.execute('PRAGMA journal_mode=WAL;')
            with closing(conn_timekeeping.cursor()) as cursor_timekeeping:
                for entry in delete_entries:
                    try:
                        fields = entry.split(',')
                        if len(fields) != 6:
                            raise ValueError(f"Entry has an invalid format: {entry}")
                        date, department, id, name, in_time, out_time = fields
                        cursor_timekeeping.execute(
                            'DELETE FROM timekeeping WHERE Date = ? AND Department = ? AND ID = ? AND Name = ? AND "In" = ? AND "Out" = ?',
                            (date, department, id, name, in_time, out_time))
                    except ValueError as ve:
                        print(f"Skipping invalid entry: {entry} - {ve}")
            conn_timekeeping.commit()
    except Exception as e:
        print(f"Error during bulk delete operation: {e}")
    return redirect(url_for('time_table'))


@app.route('/user_analysis', methods=['GET', 'POST'])
def user_analysis():
    if 'user' not in session:
        return redirect(url_for('login'))
    users = []
    departments = []
    try:
        with closing(sqlite3.connect('database/department.db', timeout=1)) as conn_department:
            conn_department.execute('PRAGMA journal_mode=WAL;')
            with closing(conn_department.cursor()) as cursor_department:
                cursor_department.execute('SELECT department FROM departments')
                departments = [row[0] for row in cursor_department.fetchall()]
        with closing(sqlite3.connect('database/dataset.db', timeout=1)) as conn_dataset:
            conn_dataset.execute('PRAGMA journal_mode=WAL;')
            conn_dataset.row_factory = sqlite3.Row
            if request.method == 'POST':
                search_type = request.form['search_type']
                search_value = request.form['search_value']
                search_department = request.form['search_department']
                query = 'SELECT * FROM dataset WHERE {} LIKE ?'.format(search_type)
                params = [f"%{search_value}%"]
                if search_department:
                    query += ' AND Department = ?'
                    params.append(search_department)
                users = conn_dataset.execute(query, params).fetchall()
            else:
                users = conn_dataset.execute('SELECT * FROM dataset').fetchall()
    except Exception as e:
        print(f"error in user_analysis as {e}")
    return render_template('user_analysis.html', users=users, departments=departments)




@app.route('/edit_user/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    user = []
    departments = []
    try:
        with closing(sqlite3.connect('database/dataset.db', timeout=1)) as conn_dataset:
            conn_dataset.execute('PRAGMA journal_mode=WAL;')
            conn_dataset.row_factory = sqlite3.Row
            user = conn_dataset.execute('SELECT * FROM dataset WHERE ID = ?', (id,)).fetchone()
            if not user:
                print("there is no user to edit")
            else:
                old_folder_name = f"{user['ID']}-{user['Name']}-{user['Authority']}-{user['Department']}"
                with closing(sqlite3.connect('database/department.db', timeout=1)) as conn_department:
                    conn_department.execute('PRAGMA journal_mode=WAL;')
                    with closing(conn_department.cursor()) as cursor_department:
                        cursor_department.execute('SELECT department FROM departments')
                        departments = [row[0] for row in cursor_department.fetchall()]
                if not departments:
                    print("departments == None")
                else:
                    if request.method == 'POST':
                        name = request.form['name']
                        authority = request.form['authority']
                        department = request.form['department']
                        new_folder_name = f"{id}-{name}-{authority}-{department}"
                        try:
                            conn_dataset.execute('UPDATE dataset SET Name = ?, Authority = ?, Department = ? WHERE ID = ?',(name, authority, department, id))
                            conn_dataset.commit()
                            with closing(sqlite3.connect('database/timekeeping.db', timeout=1)) as conn_timekeeping:
                                conn_timekeeping.execute('PRAGMA journal_mode=WAL;')
                                with closing(conn_timekeeping.cursor()) as cursor_timekeeping:
                                    cursor_timekeeping.execute('UPDATE timekeeping SET Name = ?, Department = ? WHERE ID = ?',(name, department, id))
                                conn_timekeeping.commit()
                            with open('facebank/data.pickle', 'rb') as f:
                                data = pickle.load(f)
                            existing_names = data['names']
                            print(f"Existing names in data before edit:{existing_names}")
                            person_to_update = f"{user['ID']}-{user['Name']}-{user['Authority']}-{user['Department']}"
                            if person_to_update in data['names'].tolist():
                                index = data['names'].tolist().index(person_to_update)
                                data['names'][index] = f"{id}-{name}-{authority}-{department}"
                                with open('facebank/data.pickle', 'wb') as f:
                                    pickle.dump(data, f)
                            with open('facebank/data.pickle', 'rb') as f:
                                data = pickle.load(f)
                            existing_names = data['names']
                            print(f"Existing names in data after edit:{existing_names}")
                            old_folder_path = os.path.join('dataset', old_folder_name)
                            new_folder_path = os.path.join('dataset', new_folder_name)
                            if os.path.exists(old_folder_path):
                                os.rename(old_folder_path, new_folder_path)
                        except Exception as e:
                            print(f"Error during the edit operation: {e}")
                        return redirect(url_for('user_analysis'))
    except Exception as e:
        print(f"error in edit user as {e}")
        return redirect(url_for('user_analysis'))
    return render_template('edit_user.html', user=user, departments=departments)


@app.route('/delete_user/<int:id>', methods=['POST'])
def delete_user(id):
    try:
        with closing(sqlite3.connect('database/dataset.db', timeout=1)) as conn_dataset:
            conn_dataset.execute('PRAGMA journal_mode=WAL;')
            conn_dataset.row_factory = sqlite3.Row
            user = conn_dataset.execute('SELECT * FROM dataset WHERE ID = ?', (id,)).fetchone()
            conn_dataset.execute('DELETE FROM dataset WHERE ID = ?', (id,))
            conn_dataset.commit()
        with closing(sqlite3.connect('database/timekeeping.db', timeout=1)) as conn_timekeeping:
            conn_timekeeping.execute('PRAGMA journal_mode=WAL;')
            with closing(conn_timekeeping.cursor()) as cursor_timekeeping:
                cursor_timekeeping.execute('DELETE FROM timekeeping WHERE ID = ?', (id,))
                conn_timekeeping.commit()
        sensor = get_fingerprint_sensor()
        if sensor is None:
            print("Fingerprint sensor not connected.")
            #return redirect(url_for('user_analysis'))
        else:
            try:
                sensor.delete_model(user['ID'])
            except:
                print("Error in delete finger")
        with open('facebank/data.pickle', 'rb') as f:
            data = pickle.load(f)
        existing_names = data['names']
        print(f"Existing names in data before delete:{existing_names}")
        person_to_delete = f"{user['ID']}-{user['Name']}-{user['Authority']}-{user['Department']}"
        if person_to_delete in data['names'].tolist():
            index = data['names'].tolist().index(person_to_delete)
            data['names'] = np.delete(data['names'], index)
            data['embeddings'] = torch.cat((data['embeddings'][:index], data['embeddings'][index + 1:]))
            with open('facebank/data.pickle', 'wb') as f:
                pickle.dump(data, f)
        with open('facebank/data.pickle', 'rb') as f:
            data = pickle.load(f)
        existing_names = data['names']
        print(f"Existing names in data after delete:{existing_names}")
        folder_name = f"{user['ID']}-{user['Name']}-{user['Authority']}-{user['Department']}"
        folder_path = os.path.join('dataset', folder_name)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
    except Exception as e:
        print(f"Error in delete_user: {e}")
    return redirect(url_for('user_analysis'))


def main():
    def open_browser():
        with app.test_request_context():
            ip_address = get_ip()
            if ip_address != "Unable to get IP":
                url = "http://" + ip_address + ":5000"
            # webbrowser.open(url)
            else:
                print("No wifi")
                time.sleep(2)
                open_browser()

    open_browser()
    app.run(host='0.0.0.0')


if __name__ == '__main__':
    main()


