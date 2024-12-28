import sqlite3
import os


def create_databases():
    department_conn = sqlite3.connect('database/department.db')
    department_cursor = department_conn.cursor()
    department_cursor.execute('''
    CREATE TABLE IF NOT EXISTS departments (
        department TEXT
    )
    ''')
    departments = ["HR", "Engineering", "IT", "Finance", "Marketing", "Sales", "R&D", "QA", "BD", "Customer Service",
                   "None"]
    department_cursor.executemany('''
    INSERT INTO departments (department)
    VALUES (?)
    ''', [(dept,) for dept in departments])
    department_conn.commit()
    department_conn.close()

    connnn = sqlite3.connect('database/web.db')
    cursorrr = connnn.cursor()
    cursorrr.execute('''
    CREATE TABLE IF NOT EXISTS web (
        Username TEXT,
        Password TEXT
    )
    ''')
    data = [
        ('1', '2'),
    ]
    cursorrr.executemany('''
    INSERT INTO web (Username, Password)
    VALUES (?, ?)
    ''', data)
    connnn.commit()
    connnn.close()
    connn = sqlite3.connect('database/timekeeping.db')
    cursorr = connn.cursor()
    data = [
        ('2024-08-14', 'Sales', 1, 'Messi', '07:30:23', '11:30:00'),
        ('2024-08-14', 'Sales', 1, 'Messi', '13:30:23', '17:30:00'),
        ('2024-08-14', 'Sales', 1, 'Messi', '18:00:23', '21:00:00'),
        ('2024-06-26', 'Engineering', 2, 'Neymar', '07:00:00', '11:00:00'),
        ('2024-06-26', 'Engineering', 2, 'Neymar', '13:00:00', '17:00:00'),
        ('2024-06-26', 'Engineering', 2, 'Neymar', '18:00:00', '21:00:00'),
        ('2024-09-28', 'HR', 3, 'Ronaldo', '07:00:00', '17:00:00'),
        ('2024-09-28', 'HR', 3, 'Ronaldo', '13:00:00', '17:00:00')
    ]

    cursorr.executemany('''
    INSERT INTO timekeeping (Date,Department, ID, Name, "In", "Out")
    VALUES (?,?, ?, ?, ?, ?)
    ''', data)
    connn.commit()
    connn.close()

    conn = sqlite3.connect('database/dataset.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dataset (
            ID INTEGER PRIMARY KEY,
            Name TEXT,
            Authority TEXT,
            Department TEXT
        )
    ''')
    conn.commit()
    data = [
        (1, 'Messi', 'user', 'Sales'),
        (2, 'Neymar', 'user', 'Engineering'),(4, 'Neymar4', 'user', 'Engineering'),(5, 'Neymar5', 'user', 'Engineering'),(6, 'Neymar6', 'user', 'Engineering'),(7, 'Neymar7', 'user', 'Engineering'),(8, 'Neymar8', 'user', 'Engineering'),(9, 'Neymar9', 'user', 'Engineering'),(10, 'Neymar10', 'user', 'Engineering'),(12, 'Neymar12', 'user', 'Engineering'),(11, 'Neymar11', 'user', 'Engineering'),(14, 'Neymar14', 'user', 'Engineering'),(13, 'Neymar13', 'user', 'Engineering'),(15, 'Neymar15', 'user', 'Engineering'),(16, 'Neymar16', 'user', 'Engineering'),
        (3, 'Ronaldo', 'user', 'HR')
    ]
    cursor.executemany('''
        INSERT OR IGNORE INTO dataset (ID, Name, Authority, Department)
        VALUES (?, ?, ?, ?)
    ''', data)

    conn.commit()
    conn.close()

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


def clear_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        cursor.execute(f"DELETE FROM {table[0]}")
    conn.commit()
    conn.close()

clear_database('database/dataset.db')
clear_database('database/timekeeping.db')

# clear_database('database/department.db')
# clear_database('database/web.db')
# create_databases()

