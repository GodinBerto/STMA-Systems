# Imports
import os
from flask import Flask, Response, render_template, request, redirect, url_for, session, flash, make_response, g, send_file
import pandas as pd
from werkzeug.utils import secure_filename
from reportlab.pdfgen import canvas
import csv
from functools import wraps
import sqlite3
from datetime import datetime
import threading
from io import BytesIO

# Flask
app = Flask(__name__)
app.secret_key = "GodinBerto"


# Use a lock to synchronize table creation
table_creation_lock = threading.Lock()


# Users Database
def get_users_db_connection():
    conn_users = sqlite3.connect('instance/users.db')
    conn_users.row_factory = sqlite3.Row
    return conn_users, conn_users.cursor()


# Create Users Table
def create_users_table():
    with table_creation_lock:
        conn_users, cursor = get_users_db_connection()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                phone_number integer,
                role text,
                password text,
                email text,
                gender text,
                access text,
                image BLOB
            )
        ''')
        conn_users.commit()
        conn_users.close()


# User Validation
def validate_user_login(username, password):
    conn_users, cursor = get_users_db_connection()
    cursor.execute(
        'SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    conn_users.close()
    return user


def get_user_by_id(user_id):
    conn_users, cursor = get_users_db_connection()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn_users.close()
    return user


def login_required(role=None):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            # Check if the user is logged in
            if 'user_id' not in session:
                return redirect(url_for('index'))

            # Get the user's role from the database
            user_id = session['user_id']
            user = get_user_by_id(user_id)

            if not user:
                return redirect(url_for('index'))

            user_role = user['role']

            # Check if the user has the required role
            if role and user_role != role:
                # Redirect to the index page or another page of your choice
                return redirect(url_for('index'))

            return fn(*args, **kwargs)
        return decorated_view
    return wrapper


@app.route('/', methods=['GET', 'POST'])
def index():
    create_users_table()
    create_store_table()
    create_tenant_table()
    create_occupant_table()
    create_asset_table()
    create_department_table()
    create_unit_table()
    create_sms_received_table()
    create_sms_dispatch_table()
    create_artisan_table()
    create_cs_table()

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = validate_user_login(username, password)

        if user:
            user_id = user['id']
            role = user['role']
            access = user['access']

            # Successful login, store user info in session
            session['user_id'] = user_id

            if role == 'SUPER ADMIN':
                return redirect(url_for('dashboard'))
            elif role == 'ADMIN':
                return redirect(url_for('admin_stores'))
            elif role == 'DATA ENTRY':
                if access == 'Store Rent':
                    return redirect(url_for('staff_stores'))
                elif access == 'Assets':
                    return redirect(url_for('staff_asset'))
                elif access == 'Artisan':
                    return redirect(url_for('staff_artisan'))
                elif access == 'Stores Management':
                    return redirect(url_for('staff_sms'))
                else:
                    return render_template('index.html', error='Invalid username or password')
            else:
                # Handle other roles or redirect to a default page
                return render_template('index.html', error='Invalid username or password')

        else:
            # Invalid login, show error message
            return render_template('index.html', error='Invalid username or password')

    return render_template('index.html')


@app.route('/logout')
def logout():
    # Clear the user_id from the session, effectively logging the user out
    session.pop('user_id', None)
    return redirect(url_for('index'))


# Stores Database
def get_stores_db_connection():
    conn_stores = sqlite3.connect('instance/stores.db')
    conn_stores.row_factory = sqlite3.Row
    return conn_stores, conn_stores.cursor()


# Use this function to get a database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('instance/stores.db')
        db.row_factory = sqlite3.Row
    return db


# Close the database connection when the request context is torn down
@app.teardown_appcontext
def close_db(error):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# Create Store Table
def create_store_table():
    with table_creation_lock:
        conn, cursor = get_stores_db_connection()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shop (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_number text,
                store_size text,
                rent number,
                sector text,
                business text,
                staff text
            )
        ''')
        conn.commit()
        conn.close()


# Create Tenant Table
def create_tenant_table():
    with table_creation_lock:
        conn, cursor = get_stores_db_connection()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tenant (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name text,
                gender text,
                number number,
                birth date,
                image blob,
                house_number text,
                store_number text,
                id_number number,
                id_image blob, 
                FOREIGN KEY (store_number) REFERENCES store(store_number)
                )
        ''')
        conn.commit()
        conn.close()


# Create Occupant Table
def create_occupant_table():
    with table_creation_lock:
        conn, cursor = get_stores_db_connection()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS occupant (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name text,
                gender text,
                number number,
                birth date,
                image blob,
                house_number text,
                store_number text,
                id_number number,
                id_image blob,
                FOREIGN KEY (store_number) REFERENCES store(store_number)
                )
        ''')
        conn.commit()
        conn.close()


def get_asset_db_connection():
    conn_asset = sqlite3.connect('instance/asset.db')
    conn_asset.row_factory = sqlite3.Row
    return conn_asset, conn_asset.cursor()


# Create Asset Table
def create_asset_table():
    with table_creation_lock:
        conn, cursor = get_asset_db_connection()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department text,
                unit text,
                device_name text,
                brand text,
                serial_number text,
                embosenuit_number text,
                device_status text,
                device_capacity number,
                toner text,
                division text,
                date_purchased date,
                user text,
                staff text
                )
        ''')
        conn.commit()
        conn.close()


# Create SMS Table
def get_sms_db_connection():
    conn_asset = sqlite3.connect('instance/sms.db')
    conn_asset.row_factory = sqlite3.Row
    return conn_asset, conn_asset.cursor()


def create_sms_received_table():
    with table_creation_lock:
        conn, cursor = get_sms_db_connection()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stores_received (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item text,
                serial_number text,
                quantity_received number,
                quantity_requested number,
                supplier_name text,
                requested_dept text,
                date_recieved date,
                difference number,
                staff text
                )
        ''')
        conn.commit()
        conn.close()


def create_sms_dispatch_table():
    with table_creation_lock:
        conn, cursor = get_sms_db_connection()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stores_dispatch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item text,
                type text,
                department text,
                officer_receiver text,
                name_receiver text,
                phone_number number,
                quantity text,
                date_recieved date,
                description text,
                staff text
                )
        ''')
        conn.commit()
        conn.close()


# Create Department Table
def get_department_db_connection():
    conn = sqlite3.connect('instance/department.db')
    conn.row_factory = sqlite3.Row
    return conn, conn.cursor()


def create_department_table():
    with table_creation_lock:
        conn, cursor = get_department_db_connection()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS department (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department_name text,
                hod text
                )
        ''')
        conn.commit()
        conn.close()


# Create Unit Table
def create_unit_table():
    with table_creation_lock:
        conn, cursor = get_department_db_connection()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department_name text,
                unit text,
                officer text,
                FOREIGN KEY (department_name) REFERENCES store(department_name)
                )
        ''')
        conn.commit()
        conn.close()


# Create Artisan Table
def get_artisan_db_connection():
    conn = sqlite3.connect('instance/artisan.db')
    conn.row_factory = sqlite3.Row
    return conn, conn.cursor()


def create_artisan_table():
    with table_creation_lock:
        conn, cursor = get_artisan_db_connection()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS artisan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name text,
                profession text,
                gender text,
                year_profession number,
                email text,
                phone_number number,
                shop_location text,
                shop_gps text,
                date_registered date,
                image blob,
                birth date,
                id_type text,
                id_number number,
                id_image blob,
                nationality text,
                fathers_name text,
                fathers_status text,
                fathers_number number,
                mothers_name text,
                mothers_status text,
                mothers_number text,
                residential_postal text,
                residential_gps text,
                home_postal text,
                home_gps text,
                staff text,
                FOREIGN KEY (name) REFERENCES store(name)
                )
        ''')
        conn.commit()
        conn.close()


# Create cs Table
def get_cs_db_connection():
    conn = sqlite3.connect('instance/cs.db')
    conn.row_factory = sqlite3.Row
    return conn, conn.cursor()


def create_cs_table():
    with table_creation_lock:
        conn, cursor = get_cs_db_connection()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name text,
                gender text,
                address text,
                phone_number number,
                age_bracket number,
                disability_status text,
                unique_code text,
                purpose text,
                complaint_to text,
                complaint_content text,
                complaint_response text,
                enquiries_content text,
                enquiries_response text,
                tag_number number,
                office text,
                receipient_name text,
                purpose_visit text,
                date_time date
                )
        ''')
        conn.commit()
        conn.close()
#

# --------------------------------------------------------------Super Admin------------------------------------------------------------------------------


@app.route('/dashboard')
@login_required(role='SUPER ADMIN')
def dashboard():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if request.method == 'POST':
            # Handle form submission (if needed)
            pass

        # Create the "stores" table if it doesn't exist
        create_store_table()

        conn, cursor = get_stores_db_connection()
        cursor.execute("SELECT * FROM shop ORDER BY id DESC LIMIT 10")
        store_list = cursor.fetchall()
        conn.close()

        conn, cursor = get_department_db_connection()
        cursor.execute("SELECT * FROM department ORDER BY id DESC LIMIT 10")
        department_list = cursor.fetchall()
        conn.close()

        conn, cursor = get_stores_db_connection()
        cursor.execute('SELECT COUNT(id) FROM shop')
        total_store_count = cursor.fetchone()[0]
        conn.close()

        conn, cursor = get_users_db_connection()
        cursor.execute('SELECT COUNT(id) FROM users')
        total_staff_count = cursor.fetchone()[0]
        conn.close()

        conn, cursor = get_stores_db_connection()
        cursor.execute("SELECT rent FROM shop")
        store_lists = cursor.fetchall()
        conn.close()

        conn, cursor = get_asset_db_connection()
        cursor.execute("SELECT COUNT(id) FROM asset")
        asset_count = cursor.fetchone()[0]
        conn.close()

        conn, cursor = get_department_db_connection()
        cursor.execute("SELECT COUNT(id) FROM department")
        department_count = cursor.fetchone()[0]
        conn.close()

        conn, cursor = get_sms_db_connection()
        cursor.execute("SELECT COUNT(id) FROM stores_received")
        item_count = cursor.fetchone()[0]
        conn.close()

        total_rent = sum(store['rent'] for store in store_lists)
        formatted_total_rent = '{:,}'.format(total_rent)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/super_admin/dashboard.html', username=username, role=role, image=image, stores=store_list,  count_stores=total_store_count, count_staff=total_staff_count, total_rent=formatted_total_rent, asset_count=asset_count, item_count=item_count, department_count=department_count, department_list=department_list)  # noqa
    return redirect(url_for('index'))


# Stores
@app.route('/stores')
@login_required(role='SUPER ADMIN')
def stores():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        conn, cursor = get_stores_db_connection()
        cursor.execute("SELECT * FROM shop")
        store_list = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/super_admin/stores.html', username=username, role=role, stores=store_list, image=image)  # noqa
    return redirect(url_for('index'))


@app.route('/search', methods=['GET'])
@login_required(role='SUPER ADMIN')
def search():

    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        search_query = request.args.get('search')
        session['search_query'] = search_query

        if not search_query:
            return redirect(url_for('stores'))

        # Create the "stores" table if it doesn't exist

        # Fetch data from the "stores" table that matches the search query
        conn, cursor = get_stores_db_connection()
        cursor.execute("SELECT * FROM shop WHERE store_number LIKE ? OR store_size LIKE ? OR business LIKE ?",
                       ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))
        search_results = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/super_admin/stores.html', username=username, role=role, stores=search_results, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/store_reg')
@login_required(role='SUPER ADMIN')
def store_reg():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)
        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/super_admin/store-reg.html', username=username, role=role, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/add_stores_one')
@login_required(role='SUPER ADMIN')
def add_stores_one():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)
        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/super_admin/add-stores.html', username=username, role=role, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/add_stores_both')
@login_required(role='SUPER ADMIN')
def add_stores_both():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)
        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/super_admin/add-stores-both.html', username=username, role=role, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/add_stores', methods=['GET', 'POST'])
@login_required(role='SUPER ADMIN')
def add_stores():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if request.method == 'POST':
            store_number = request.form.get('store_number')

            # Check if the store number already exists
            conn, cursor = get_stores_db_connection()
            cursor.execute(
                "SELECT store_number FROM shop WHERE store_number = ?", (store_number,))
            existing_store = cursor.fetchone()
            conn.close()

            if existing_store:
                flash("Store number already exists in the database.", "error")
                return redirect(url_for('stores'))

            conn = get_db()
            cursor = conn.cursor()

            try:
                # Your database operations here
                with get_db() as conn:
                    cursor = conn.cursor()
                    # Get data from the form for the shop
                    store_size = request.form.get('size')
                    rent = request.form.get('rent')
                    business = request.form.get('business')
                    staff = request.form.get('staff')  # Use get method here
                    sector = request.form.get('sector')

                    conn, cursor = get_stores_db_connection()
                    cursor.execute("INSERT INTO shop (store_number, store_size, rent, business, sector, staff) VALUES (?, ?, ?, ?, ?, ?)",
                                   (store_number, store_size, rent, business, sector, staff))

                    t_fullname = request.form.get('t_fullname')
                    t_telnumber = request.form.get('t_telnumber')
                    t_gender = request.form.get('t_gender')
                    t_birth = request.form.get('t_birth')
                    t_house_number = request.form.get('t_house_number')
                    t_id_number = request.form.get('t_id_number')

                    t_image = request.files['t_image']
                    t_image_filename = secure_filename(t_image.filename)
                    t_image_path = os.path.join(
                        "static/images", t_image_filename)
                    t_image.save(t_image_path)

                    cursor.execute("INSERT INTO tenant (name, number, birth, gender, house_number, id_number, image, store_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                   (t_fullname, t_telnumber, t_birth, t_gender, t_house_number, t_id_number, t_image_filename, store_number))

                    if 'o_fullname' in request.form:
                        o_fullname = request.form.get('o_fullname')
                        o_telnumber = request.form.get('o_telnumber')
                        o_gender = request.form.get('o_gender')
                        o_birth = request.form.get('o_birth')
                        o_house_number = request.form.get('o_house_number')
                        o_id_number = request.form.get('o_id_number')

                        o_image = request.files['o_image']
                        o_image_filename = secure_filename(o_image.filename)
                        o_image_path = os.path.join(
                            "static/images", o_image_filename)
                        o_image.save(o_image_path)

                        cursor.execute("INSERT INTO occupant (name, number, birth, gender, house_number, id_number, image, store_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                       (o_fullname, o_telnumber, o_birth, o_gender, o_house_number, o_id_number, o_image_filename, store_number))
                    else:
                        o_fullname = "None"
                        o_telnumber = "None"
                        o_gender = "None"
                        o_birth = "None"
                        o_house_number = "None"
                        o_id_number = "None"
                        o_image_filename = "None"

                        cursor.execute("INSERT INTO occupant (name, number, birth, gender, house_number, id_number, image, store_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                       (o_fullname, o_telnumber, o_birth, o_gender, o_house_number, o_id_number, o_image_filename, store_number))

                    # Commit the changes to the database
                    conn.commit()
                    flash("Store Successfully Added")
            except sqlite3.Error as e:
                conn.rollback()  # Rollback changes if an error occurs
                flash(f"Database error: {e}", "error")

            conn.close()  # Close the connection

            # Redirect to the home page after submission
            return redirect(url_for('stores'))

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/super_admin/add-stores.html', username=username, role=role, image=image)

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/delete_store/<string:store_number>')
@login_required(role='SUPER ADMIN')
def delete_store(store_number):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        # Delete the record with the specified store_id
        conn, cursor = get_stores_db_connection()
        cursor.execute("DELETE FROM shop WHERE store_number=?",
                       (store_number,))

        cursor.execute(
            "DELETE FROM tenant WHERE store_number=?", (store_number,))

        cursor.execute(
            "DELETE FROM occupant WHERE store_number=?", (store_number,))

        conn.commit()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return redirect(url_for('stores', username=username, role=role, image=image))
    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/more_stores/<string:store_number>')
@login_required(role='SUPER ADMIN')
def more_stores(store_number):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            # Fetch additional details for the selected store using the store_id
            conn, cursor = get_stores_db_connection()

            cursor.execute(
                "SELECT * FROM shop WHERE store_number = ?", (store_number,))

            store_details = cursor.fetchone()

            cursor.execute(
                "SELECT * FROM tenant WHERE store_number = ?", (store_number,))

            tenant_details = cursor.fetchone()

            cursor.execute(
                "SELECT * FROM occupant WHERE store_number = ?", (store_number,))

            occupant_details = cursor.fetchone()
            conn.close()

            if store_details:
                # Pass the store details to the template
                return render_template('/super_admin/full-details.html', username=username, role=role, store=store_details, tenant=tenant_details, occupant=occupant_details, image=image)
            else:
                # Flash an error message when store details are not found
                flash("Store details not found", 'error')
                return redirect(url_for('stores'))

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/update_stores/<string:store_number>', methods=['GET', 'POST'])
@login_required(role='SUPER ADMIN')
def update_stores(store_number):
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            conn, cursor = get_stores_db_connection()
            cursor.execute(
                "SELECT * FROM shop WHERE store_number = ?", (store_number,))
            store = cursor.fetchone()

            cursor.execute(
                "SELECT * FROM tenant WHERE store_number = ?", (store_number,))
            tenant = cursor.fetchone()

            cursor.execute(
                "SELECT * FROM occupant WHERE store_number = ?", (store_number,))
            occupant = cursor.fetchone()

            if request.method == 'POST':
                store_number = request.form['store_number']
                store_size = request.form['size']
                rent = request.form['rent']
                business = request.form['business']

                store_number = request.form.get('store_number')

                # Check if the store number already exist
                cursor.execute(
                    "SELECT store_number FROM shop WHERE store_number = ?", (store_number,))
                existing_store = cursor.fetchone()

                if existing_store and existing_store[0] != store_number:
                    flash("Store number already exists in the database.", "error")
                    return redirect(url_for('stores'))
                else:
                    try:
                        # Your database operations here
                        store_number_form = request.form['store_number']
                        # Get data from the form for the shop
                        store_size = request.form.get('size')
                        rent = request.form.get('rent')
                        business = request.form.get('business')
                        staff = request.form.get(
                            'staff')  # Use get method here
                        sector = request.form.get('sector')

                        cursor.execute("UPDATE shop SET store_size=?, rent=?, business=?, sector=?, staff=? WHERE store_number=?",
                                       (store_size, rent, business, sector, staff, store_number_form))

                        t_fullname = request.form.get('t_fullname')
                        t_telnumber = request.form.get('t_telnumber')
                        t_gender = request.form.get('t_gender')
                        t_birth = request.form.get('t_birth')
                        t_house_number = request.form.get('t_house_number')
                        t_id_number = request.form.get('t_id_number')

                        t_image = request.files['t_image']

                        if t_image:
                            t_image_filename = secure_filename(
                                t_image.filename)
                            t_image_path = os.path.join(
                                "static/images", t_image_filename)
                            t_image.save(t_image_path)

                            cursor.execute("UPDATE tenant SET name=?, number=?, birth=?, gender=?, house_number=?, id_number=?, image=? WHERE store_number=?",
                                           (t_fullname, t_telnumber, t_birth, t_gender, t_house_number, t_id_number, t_image_filename, store_number))
                        else:
                            cursor.execute("UPDATE tenant SET name=?, number=?, birth=?, gender=?, house_number=?, id_number=? WHERE store_number=?",
                                           (t_fullname, t_telnumber, t_birth, t_gender, t_house_number, t_id_number, store_number))

                        if 'o_fullname' in request.form:
                            o_fullname = request.form.get('o_fullname')
                            o_telnumber = request.form.get('o_telnumber')
                            o_gender = request.form.get('o_gender')
                            o_birth = request.form.get('o_birth')
                            o_house_number = request.form.get('o_house_number')
                            o_id_number = request.form.get('o_id_number')

                            o_image = request.files['o_image']

                            if o_image:
                                o_image_filename = secure_filename(
                                    o_image.filename)
                                o_image_path = os.path.join(
                                    "static/images", o_image_filename)
                                o_image.save(o_image_path)

                                cursor.execute("UPDATE shop SET name=?, number=?, birth=?, gender=?, house_number=?, id_number=?, image=? WHERE store_number=?",
                                               (o_fullname, o_telnumber, o_birth, o_gender, o_house_number, o_id_number, o_image_filename, store_number))
                            else:
                                cursor.execute("UPDATE occupant SET name=?, number=?, birth=?, gender=?, house_number=?, id_number=? WHERE store_number=?",
                                               (o_fullname, o_telnumber, o_birth, o_gender, o_house_number, o_id_number, store_number))

                        # Commit the changes to the database
                        conn.commit()
                        flash("Store Successfully Updated")
                    except sqlite3.Error as e:
                        conn.rollback()  # Rollback changes if an error occurs
                        flash(f"Database error: {e}", "error")

                conn.close()
                # Close the connection

                # Redirect to the home page after submission
                return redirect(url_for('stores'))

            return render_template('/super_admin/store/update.html', username=username, role=role, image=image, stores=store, tenant=tenant, occupant=occupant)

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


# Assets
@app.route('/asset')
@login_required(role='SUPER ADMIN')
def asset():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        conn, cursor = get_asset_db_connection()
        cursor.execute("SELECT * FROM asset")
        asset_list = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/super_admin/asset.html', username=username, role=role, image=image, asset=asset_list)  # noqa
    return redirect(url_for('index'))


@app.route('/asset_search', methods=['GET'])
@login_required(role='SUPER ADMIN')
def asset_search():

    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        search_query = request.args.get('search')
        session['search_query'] = search_query

        if not search_query:
            return redirect(url_for('asset'))

        # Create the "stores" table if it doesn't exist

        # Fetch data from the "stores" table that matches the search query
        conn, cursor = get_asset_db_connection()
        cursor.execute("SELECT * FROM asset WHERE department LIKE ? OR officer LIKE ? OR unit LIKE ? OR device_name LIKE ? OR division LIKE ?",
                       ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))

        search_results = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/super_admin/asset.html', username=username, role=role, asset=search_results, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/delete_asset/<int:id>')
@login_required(role='SUPER ADMIN')
def delete_asset(id):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:

            # Delete the record with the specified store_id
            conn, cursor = get_asset_db_connection()
            cursor.execute("DELETE FROM asset WHERE id=?",
                           (id,))

            conn.commit()
            conn.close()

            username = user['username']
            role = user['role']
            image = user['image']
        return redirect(url_for('asset', username=username, role=role, image=image))
    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/more_asset/<int:id>')
@login_required(role='SUPER ADMIN')
def more_asset(id):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            # Fetch additional details for the selected store using the store_id
            conn, cursor = get_asset_db_connection()

            cursor.execute(
                "SELECT * FROM asset WHERE id = ?", (id,))
            asset_details = cursor.fetchone()
            conn.close()

            if asset_details:
                # Pass the store details to the template
                return render_template('/super_admin/add-assets-form/more.html', username=username, role=role, asset=asset_details, image=image)
            else:
                # Flash an error message when store details are not found
                flash("Asset details not found", 'error')
                return redirect(url_for('asset'))

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/add_asset', methods=['GET', 'POST'])
@login_required(role='SUPER ADMIN')
def add_asset():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        # Handle the GET request (initial form display)
        conn, cursor = get_department_db_connection()
        cursor.execute('SELECT * FROM department')
        departments = [row['department_name'] for row in cursor.fetchall()]

        cursor.execute('SELECT * FROM unit')
        units = [row['unit'] for row in cursor.fetchall()]
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/super_admin/add-assets-form/assets-form.html', username=username, role=role, image=image, departments=departments, units=units)

    return redirect(url_for('index'))


@app.route('/asset_add', methods=['GET', 'POST'])
@login_required(role='SUPER ADMIN')
def asset_add():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)
        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            if request.method == 'POST':
                # Get data from the form for the asset
                department = request.form['department']
                division = request.form['division']
                unit = request.form['unit']
                device = request.form['device']
                date_purchased = request.form['date_purchased']
                using = request.form['using']
                serial_number = request.form['serial_number']
                embosenuit = request.form['embosenuit']
                status = request.form['status']
                brand = request.form['brand']
                # Use get() with a default value
                toner = request.form.get('toner_type', None)
                # Use get() with a default value
                capacity = request.form.get('device_capacity', None)

                staff = request.form['staff']

                conn, cursor = get_asset_db_connection()
                if toner is not None and capacity is not None:
                    cursor.execute('''
                        INSERT INTO asset (department, unit, device_name, brand, serial_number, embosenuit_number,
                        device_status, toner, device_capacity, division, date_purchased, user, staff)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (department, unit, device, brand, serial_number, embosenuit, status, toner, capacity, division, date_purchased, using, staff))
                elif toner is not None:
                    cursor.execute('''
                        INSERT INTO asset (department, unit, device_name, brand, serial_number, embosenuit_number,
                        device_status, toner, division, date_purchased, user, staff)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (department, unit, device, brand, serial_number, embosenuit, status, toner, division, date_purchased, using, staff))
                elif capacity is not None:
                    cursor.execute('''
                        INSERT INTO asset (department, unit, device_name, brand, serial_number, embosenuit_number,
                        device_status, device_capacity, division, date_purchased, user, staff)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (department, unit, device, brand, serial_number, embosenuit, status, capacity, division, date_purchased, using, staff))
                else:
                    cursor.execute('''
                        INSERT INTO asset (department, unit, device_name, brand, serial_number, embosenuit_number,
                        device_status, division, date_purchased, user, staff)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (department, unit, device, brand, serial_number, embosenuit, status, division, date_purchased, using, staff))
                conn.commit()
                conn.close()

                flash("Asset Successfully Added")

                return redirect('asset')

            # Render the template with username and role
            return render_template('super_admin/add-assets-form/assets-form.html', username=username, role=role, image=image)

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/update_asset/<int:id>', methods=['GET', 'POST'])
@login_required(role='SUPER ADMIN')
def update_asset(id):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            # Fetch additional details for the selected department using the department_name
            conn, cursor = get_asset_db_connection()
            cursor.execute(
                "SELECT * FROM asset WHERE id = ?", (id,))
            asset_details = cursor.fetchone()

            conn, cursor = get_department_db_connection()
            cursor.execute('SELECT * FROM department')
            departments = [row['department_name']
                           for row in cursor.fetchall()]

            cursor.execute('SELECT * FROM unit')
            units = [row['unit'] for row in cursor.fetchall()]

            if request.method == 'POST':
                # Get data from the form for the asset
                department = request.form['department']
                division = request.form['division'].upper()
                unit = request.form['unit']
                device = request.form['device']
                date_purchased = request.form['date_purchased']
                using = request.form['using']
                serial_number = request.form['serial_number']
                embosenuit = request.form['embosenuit']
                status = request.form['status']
                brand = request.form['brand']
                # Use get() with a default value
                toner = request.form.get('toner_type', None)
                # Use get() with a default value
                capacity = request.form.get('device_capacity', None)

                # Update the asset in the 'department' table
                conn, cursor = get_asset_db_connection()
                cursor.execute(
                    'UPDATE asset SET department=?, unit=?, division=?, device_name=?, date_purchased=?, serial_number=?, embosenuit_number=?, brand=?, toner=?, device_capacity=?, device_status=?, user=? WHERE id=?', (department, unit, division, device, date_purchased, serial_number, embosenuit, brand, toner, capacity, status, using, id))

                conn.commit()

                flash("Asset Successfully Updated")

                return redirect(url_for('asset'))

            conn.close()
            if asset_details:
                # Pass the department details to the template
                return render_template('/super_admin/add-assets-form/update.html', username=username, role=role, asset=asset_details, departments=departments, units=units, image=image)
            else:
                # Flash an error message when department details are not found
                flash("Asset details not found", 'error')
                return redirect(url_for('asset'))

    return redirect(url_for('index'))


# Stores Management Systems
@app.route('/sms')
@login_required(role='SUPER ADMIN')
def sms():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        conn, cursor = get_sms_db_connection()
        cursor.execute("SELECT COUNT(id) FROM stores_received")
        item_count = cursor.fetchone()[0]
        conn.close()

        conn, cursor = get_sms_db_connection()
        cursor.execute("SELECT COUNT(id) FROM stores_dispatch")
        dispatch_count = cursor.fetchone()[0]
        conn.close()

        conn, cursor = get_sms_db_connection()
        cursor.execute("SELECT * FROM stores_received")
        sms_list_receiver = cursor.fetchall()
        conn.close()

        conn, cursor = get_sms_db_connection()
        cursor.execute("SELECT * FROM stores_dispatch")
        sms_list_dispatch = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/super_admin/sms.html', username=username, role=role, image=image, sms_list_receiver=sms_list_receiver, item_count=item_count, dispatch_count=dispatch_count, sms_list_dispatch=sms_list_dispatch)  # noqa
    return redirect(url_for('index'))


@app.route('/sms_search', methods=['GET'])
@login_required(role='SUPER ADMIN')
def sms_search():

    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        search_query = request.args.get('search')
        session['search_query'] = search_query

        if not search_query:
            return redirect(url_for('sms'))

        # Fetch data from the "stores" table that matches the search query
        conn, cursor = get_sms_db_connection()
        cursor.execute("SELECT * FROM stores_received WHERE item LIKE ? OR serial_number LIKE ?",
                       ('%' + search_query + '%', '%' + search_query + '%'))
        search_results_receiver = cursor.fetchall()

        cursor.execute("SELECT * FROM stores_dispatch WHERE item LIKE ? OR name_receiver LIKE ?",
                       ('%' + search_query + '%', '%' + search_query + '%'))

        search_results_dispatch = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/super_admin/sms.html', username=username, role=role, sms_receiver=search_results_receiver, sms_dispatch=search_results_dispatch,  image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/sms_delete/<int:id>')
@login_required(role='SUPER ADMIN')
def sms_delete(id):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:

            # Delete the record with the specified store_id
            conn, cursor = get_sms_db_connection()
            cursor.execute("DELETE FROM stores_received WHERE id=?",
                           (id,))

            conn.commit()
            conn.close()

            username = user['username']
            role = user['role']
            image = user['image']
        return redirect(url_for('sms', username=username, role=role, image=image))
    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/sms_delete_dispatch/<int:id>')
@login_required(role='SUPER ADMIN')
def sms_delete_dispatch(id):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:

            # Delete the record with the specified store_id
            conn, cursor = get_sms_db_connection()
            cursor.execute("DELETE FROM stores_dispatch WHERE id=?",
                           (id,))

            conn.commit()
            conn.close()

            username = user['username']
            role = user['role']
            image = user['image']
        return redirect(url_for('sms', username=username, role=role, image=image))
    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/more_sms/<int:id>')
@login_required(role='SUPER ADMIN')
def more_sms(id):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            # Fetch additional details for the selected store using the store_id
            conn, cursor = get_sms_db_connection()

            cursor.execute(
                "SELECT * FROM stores_received WHERE id = ?", (id,))
            sms_details = cursor.fetchone()
            conn.close()

            if sms_details:
                # Pass the store details to the template
                return render_template('/super_admin/sms/more.html', username=username, role=role, sms=sms_details, image=image)
            else:
                # Flash an error message when store details are not found
                flash("Asset details not found", 'error')
                return redirect(url_for('sms'))

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/more_sms_dispatch/<int:id>')
@login_required(role='SUPER ADMIN')
def more_sms_dispatch(id):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            # Fetch additional details for the selected store using the store_id
            conn, cursor = get_sms_db_connection()

            cursor.execute(
                "SELECT * FROM stores_dispatch WHERE id = ?", (id,))
            sms_details_dispatch = cursor.fetchone()
            conn.close()

            if sms_details_dispatch:
                # Pass the store details to the template
                return render_template('/super_admin/sms/more-dispatch.html', username=username, role=role, sms=sms_details_dispatch, image=image)
            else:
                # Flash an error message when store details are not found
                flash("Asset details not found", 'error')
                return redirect(url_for('sms'))

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/sms_add', methods=['GET', 'POST'])
@login_required(role='SUPER ADMIN')
def sms_add():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)
        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            if request.method == 'POST':
                item = request.form['item'].upper()
                serial_number = request.form['serial_number'].upper()
                quantity_requested = request.form['requested_quantity']
                quantity_received = request.form['received_quantity']
                date_recieved = request.form['date_recieved']
                differnce = request.form['difference']
                supplier = request.form['supplier']
                department = request.form['department']
                staff = request.form['staff']

                conn, cursor = get_sms_db_connection()

                cursor.execute('''
                    INSERT INTO stores_received (item, serial_number, quantity_requested, quantity_received, date_recieved, staff, difference, supplier_name, requested_dept)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (item, serial_number, quantity_requested, quantity_received, date_recieved, staff, differnce, supplier, department))

                conn.commit()
                conn.close()

                flash("Item Successfully Added")

                return redirect('sms')

            # Render the template with username and role
            return render_template('super_admin/sms/add.html', username=username, role=role, image=image)

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/sms_dispatch', methods=['GET', 'POST'])
@login_required(role='SUPER ADMIN')
def sms_dispatch():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)
        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            if request.method == 'POST':
                item = request.form['item'].upper()
                quantity = request.form['quantity']
                dispatch = request.form['dispatch']
                date_received = request.form['date_recieved']
                officer = request.form.get('officer')
                person = request.form.get('person', None)
                department = request.form.get('department', None)
                desc = request.form.get('desc', None)
                number = request.form.get('number')
                staff = request.form['staff']

                conn, cursor = get_sms_db_connection()

                cursor.execute('''
                    INSERT INTO stores_dispatch (item, type, quantity, date_recieved, staff, department, officer_receiver, name_receiver, description, phone_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (item, dispatch, quantity, date_received, staff, department, officer, person, desc, number))

                conn.commit()
                conn.close()

                flash("Item Successfully Dispatched")

                return redirect('sms')

            # Render the template with username and role
            return render_template('super_admin/sms/dispatched.html', username=username, role=role, image=image)

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/sms_update/<int:id>', methods=['GET', 'POST'])
@login_required(role='SUPER ADMIN')
def sms_update(id):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            conn, cursor = get_sms_db_connection()
            cursor.execute('SELECT * FROM sms WHERE id=?', (id,))
            sms_details = cursor.fetchone()
            conn.close()

            if request.method == 'POST':
                # Get data from the form for the asset
                item = request.form['item']
                serial_number = request.form['serial_number'].upper()
                quantity = request.form['quantity']
                date_recieved = request.form['date_recieved']

                conn, cursor = get_sms_db_connection()
                cursor.execute(
                    'UPDATE sms SET item=?, serial_number=?, quantity=?, date_recieved=? WHERE id=?', (item, serial_number, quantity, date_recieved, id))
                conn.commit()
                conn.close()

                flash("Item Successfully Updated")

                return redirect(url_for('sms'))

            # Pass the department details to the template
            return render_template('/super_admin/sms/update.html', username=username, role=role, image=image, sms=sms_details)

    return redirect(url_for('index'))


# Department
@app.route('/department')
@login_required(role='SUPER ADMIN')
def department():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        conn, cursor = get_department_db_connection()
        cursor.execute("SELECT * FROM department")
        department_list = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('super_admin/department.html', username=username, role=role, departments=department_list, image=image)  # noqa
    return redirect(url_for('index'))


@app.route('/department_search', methods=['GET'])
@login_required(role='SUPER ADMIN')
def department_search():

    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        search_query = request.args.get('search')
        session['search_query'] = search_query

        if not search_query:
            return redirect(url_for('department'))

        # Create the "stores" table if it doesn't exist

        # Fetch data from the "stores" table that matches the search query
        conn, cursor = get_department_db_connection()
        cursor.execute("SELECT * FROM department WHERE department_name LIKE ? OR hod LIKE ?",
                       ('%' + search_query + '%', '%' + search_query + '%'))

        search_results = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/super_admin/department.html', username=username, role=role, departments=search_results, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/delete_department/<string:department_name>')
@login_required(role='SUPER ADMIN')
def delete_department(department_name):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        # Delete the record with the specified store_id
        conn, cursor = get_department_db_connection()
        cursor.execute("DELETE FROM department WHERE department_name=?",
                       (department_name,))

        cursor.execute("DELETE FROM unit WHERE department_name=?",
                       (department_name,))

        conn.commit()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return redirect(url_for('department', username=username, role=role, image=image))
    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/more_department/<string:department_name>')
@login_required(role='SUPER ADMIN')
def more_department(department_name):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            # Fetch additional details for the selected store using the store_id
            conn, cursor = get_department_db_connection()
            cursor.execute(
                "SELECT * FROM department WHERE department_name = ?", (department_name,))
            department_details = cursor.fetchone()

            cursor.execute(
                "SELECT * FROM unit WHERE department_name = ?", (department_name,))
            unit_details = cursor.fetchall()

            conn.close()

            if department_details:
                # Pass the store details to the template
                return render_template('/super_admin/department/more-department.html', username=username, role=role, department=department_details, units=unit_details, image=image)
            else:
                # Flash an error message when store details are not found
                flash("Store details not found", 'error')
                return redirect(url_for('department'))

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/choose')
@login_required(role='SUPER ADMIN')
def choose():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)
        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('super_admin/department/choose.html', username=username, role=role, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/form1', methods=['GET', 'POST'])
@login_required(role='SUPER ADMIN')
def form1():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if request.method == 'POST':
            department = request.form['department'].upper()
            hod = request.form['hod'].upper()

            conn, cursor = get_department_db_connection()

            # Check if the department already exists
            cursor.execute(
                'SELECT department_name FROM department WHERE department_name = ?', (department,))
            existing_department = cursor.fetchone()

            if existing_department:
                flash("Department Already Exists", "error")
            else:
                # Insert the department into the 'department' table
                cursor.execute(
                    'INSERT INTO department (department_name, hod) VALUES (?, ?)', (department, hod))

                # Commit the department insertion
                conn.commit()

                flash("Department Successfully Added")

            conn.close()

            return redirect(url_for('department'))

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('super_admin/department/form1.html', username=username, role=role, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/form2', methods=['GET', 'POST'])
@login_required(role='SUPER ADMIN')
def form2():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        conn, cursor = get_department_db_connection()
        cursor.execute('SELECT * FROM department')
        departments = [row['department_name']
                       for row in cursor.fetchall()]
        conn.close()

        if request.method == 'POST':
            department = request.form['department']
            unit = request.form['unit']

            conn, cursor = get_department_db_connection()

            # Insert the department into the 'department' table
            cursor.execute(
                'INSERT INTO unit (department_name, unit) VALUES (?, ?)', (department, unit))

            # Commit the department insertion
            conn.commit()
            conn.close()

            flash("Unit Successfully Added")

            return redirect(url_for('department'))

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('super_admin/department/form2.html', username=username, role=role, image=image, departments=departments)

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/add_department', methods=['GET', 'POST'])
@login_required(role='SUPER ADMIN')
def add_department():
    if 'user_id' in session:
        if request.method == 'POST':
            department = request.form['department']

            conn, cursor = get_department_db_connection()

            # Insert the department into the 'department' table
            cursor.execute(
                'INSERT INTO department (department_name) VALUES (?)', (department,))

            # Commit the department insertion
            conn.commit()

            # Get the ID of the inserted department
            cursor.execute('SELECT last_insert_rowid()')
            department_name = cursor.fetchone()[0]

            # Retrieve unit data from the request
            units = request.form.getlist('unit')

            # Insert each unit into the 'unit' table
            for unit in units:
                cursor.execute(
                    'INSERT INTO unit (department_name, unit) VALUES (?, ?)', (department_name, unit))

            # Commit the unit insertions
            conn.commit()

            conn.close()

            flash("Successfully Added")

            return redirect(url_for('department'))

        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/super_admin/department/department-form.html', username=username, role=role, image=image)

    return redirect(url_for('index'))


@app.route('/update_department/<string:department_name>', methods=['GET', 'POST'])
@login_required(role='SUPER ADMIN')
def update_department(department_name):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            # Fetch additional details for the selected department using the department_name
            conn, cursor = get_department_db_connection()
            cursor.execute(
                "SELECT * FROM department WHERE department_name = ?", (department_name,))
            department_details = cursor.fetchone()

            cursor.execute(
                "SELECT * FROM unit WHERE department_name = ?", (department_name,))
            unit_details = cursor.fetchall()

            if request.method == 'POST':
                department = request.form['department'].upper()
                hod = request.form['hod'].upper()
                unit = request.form['unit']

                # Check if the department already exists
                cursor.execute(
                    'SELECT department_name FROM department WHERE department_name = ?', (department,))
                existing_department = cursor.fetchone()

                if existing_department and existing_department[0] != department_name:
                    flash("Department Already Exists", "error")
                else:
                    # Update the department in the 'department' table
                    cursor.execute(
                        'UPDATE department SET department_name=?, hod=? WHERE department_name=?', (department, hod, department_name))

                    # Update the unit
                    cursor.execute(
                        "UPDATE unit SET unit=? WHERE department_name=?", (unit, department))

                    # Commit the department and unit updates
                    conn.commit()

                    flash("Department Successfully Updated")

                    return redirect(url_for('department'))

            conn.close()

            if department_details:
                # Pass the department details to the template
                return render_template('/super_admin/department/update.html', username=username, role=role, department=department_details, units=unit_details, image=image)
            else:
                # Flash an error message when department details are not found
                flash("Department details not found", 'error')
                return redirect(url_for('department'))

    return redirect(url_for('index'))


# Staff
@app.route('/staff')
@login_required(role='SUPER ADMIN')
def staff():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if request.method == 'POST':
            # Handle form submission (if needed)
            pass

        # Create the "stores" table if it doesn't exist

        conn, cursor = get_users_db_connection()
        cursor.execute("SELECT * FROM users")
        staff = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/super_admin/staff.html', username=username, role=role, staff=staff, image=image)  # noqa
    return redirect(url_for('index'))


@app.route('/search_staff', methods=['GET'])
@login_required(role='SUPER ADMIN')
def search_staff():

    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        search_query = request.args.get('search')

        if not search_query:
            return redirect(url_for('staff'))

        # Create the "stores" table if it doesn't exist

        # Fetch data from the "stores" table that matches the search query
        conn, cursor = get_users_db_connection()
        cursor.execute("SELECT * FROM users WHERE username LIKE ? OR role LIKE ?",
                       ('%' + search_query + '%', '%' + search_query + '%'))

        search_results = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/super_admin/staff.html', username=username, role=role, staff=search_results, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/staff_add', methods=['GET', 'POST'])
@login_required(role='SUPER ADMIN')
def staff_add():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            if request.method == 'POST':
                conn, cursor = get_users_db_connection()

                # Get data from the form for the users
                name = request.form['username']
                telnumber = request.form['telnumber']
                gender = request.form['gender']
                staff_email = request.form['email']
                staff_role = request.form['role']
                staff_password = request.form['password']
                access = request.form.get('access', None)

                if access is None:
                    # Insert data into the "users" table
                    cursor.execute("INSERT INTO users (username, phone_number, gender, email, role, password) VALUES (?,?,?,?,?,?)",
                                   (name, telnumber, gender, staff_email, staff_role, staff_password))
                else:
                    # Insert data into the "users" table
                    cursor.execute("INSERT INTO users (username, phone_number, gender, email, role, password, access) VALUES (?,?,?,?,?,?,?)",
                                   (name, telnumber, gender, staff_email, staff_role, staff_password, access))
                conn.commit()
                conn.close()

                flash("Staff Successfully Added")

                # Redirect to the home page after submission
                return redirect(url_for('staff'))

            return render_template('/super_admin/staff/staff-add.html', username=username, role=role, image=image)

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/delete_staff/<int:staff_id>')
@login_required(role='SUPER ADMIN')
def delete_staff(staff_id):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        # Delete the record with the specified store_id
        conn, cursor = get_users_db_connection()
        cursor.execute("DELETE FROM users WHERE id=?", (staff_id,))
        conn.commit()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return redirect(url_for('staff', username=username, role=role, image=image))
    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/more_info_staff/<int:staff_id>')
@login_required(role='SUPER ADMIN')
def more_info_staff(staff_id):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            # Fetch additional details for the selected store using the store_id
            conn, cursor = get_users_db_connection()
            cursor.execute("SELECT * FROM users WHERE id = ?", (staff_id,))
            staff = cursor.fetchone()
            conn.close()

            if staff:
                # Pass the store details to the template
                # Use 'store' instead of 'stores'
                return render_template('/super_admin/staff/staff-info.html', username=username, role=role, staff=staff, image=image)

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/edit_staff/<int:staff_id>', methods=['GET', 'POST'])
@login_required(role='SUPER ADMIN')
def edit_staff(staff_id):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            # Fetch additional details for the selected store using the store_id
            conn, cursor = get_users_db_connection()
            cursor.execute("SELECT * FROM users WHERE id = ?", (staff_id,))
            staff = cursor.fetchone()

            if request.method == 'POST':
                # Get data from the form for the tenant
                fullname = request.form['fullname']
                telnumber = request.form['telnumber']
                gender = request.form['gender']
                staff_email = request.form['email']
                staff_password = request.form['password']
                staff_role = request.form['role']
                access = request.form.get('access')  # Fix the syntax issue

                try:
                    if access is not None:
                        cursor.execute("""
                            UPDATE users
                            SET phone_number=?, gender=?, email=?, password=?, role=?, access=?, username=?
                            WHERE id=?
                        """, (telnumber, gender, staff_email, staff_password, staff_role, access, fullname, staff_id))
                    else:
                        cursor.execute("""
                            UPDATE users
                            SET phone_number=?, gender=?, email=?, password=?, role=?, username=?
                            WHERE id=?
                        """, (telnumber, gender, staff_email, staff_password, staff_role, fullname, staff_id))

                    conn.commit()
                    flash('Staff updated successfully', 'success')
                    # Redirect to the home page after submission
                    return redirect(url_for('staff'))
                except Exception as e:
                    print("Error updating staff:", str(e))
                    flash('Error updating staff. Please try again.', 'error')
                finally:
                    conn.close()

            if staff:
                # Pass the store details to the template
                # Use 'store' instead of 'stores'
                return render_template('/super_admin/staff/edit-staff.html', username=username, role=role, staff=staff, image=image)

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


# Artisans
@app.route('/artisan')
@login_required(role='SUPER ADMIN')
def artisan():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        conn, cursor = get_artisan_db_connection()
        cursor.execute("SELECT * FROM artisan")
        artisan_list = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/super_admin/artisans/artisans.html', username=username, role=role, artisan=artisan_list, image=image)  # noqa
    return redirect(url_for('index'))


@app.route('/artisan_search', methods=['GET'])
@login_required(role='SUPER ADMIN')
def artisan_search():

    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        search_query = request.args.get('search')
        session['search_query'] = search_query

        if not search_query:
            return redirect(url_for('artisan'))

        # Create the "stores" table if it doesn't exist

        # Fetch data from the "stores" table that matches the search query
        conn, cursor = get_artisan_db_connection()
        cursor.execute("SELECT * FROM artisan WHERE name LIKE ? OR profession LIKE ? OR date_registered LIKE ? OR nationality LIKE ? OR id_number LIKE ?",
                       ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))

        search_results = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/super_admin/artisans/artisans.html', username=username, role=role, artisan=search_results, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/delete_artisan/<int:id>')
@login_required(role='SUPER ADMIN')
def delete_artisan(id):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from thartisan
        user = get_user_by_id(user_id)

        # Delete the record with the specified store_id
        conn, cursor = get_artisan_db_connection()
        cursor.execute("DELETE FROM artisan WHERE id=?",
                       (id,))

        conn.commit()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return redirect(url_for('artisan', username=username, role=role, image=image))
    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/more_artisan/<int:id>')
@login_required(role='SUPER ADMIN')
def more_artisan(id):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            # Fetch additional details for the selected store using the store_id
            conn, cursor = get_artisan_db_connection()
            cursor.execute(
                "SELECT * FROM artisan WHERE id = ?", (id,))
            artisan_details = cursor.fetchone()
            conn.close()

            if artisan_details:
                # Pass the store details to the template
                return render_template('/super_admin/artisans/more.html', username=username, role=role, artisan=artisan_details, image=image)
            else:
                # Flash an error message when store details are not found
                flash("Artisan details not found", 'error')
                return redirect(url_for('artisan'))

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/add_artisan', methods=['GET', 'POST'])
@login_required(role='SUPER ADMIN')
def add_artisan():
    if 'user_id' in session:
        user_id = session['user_id']
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            if request.method == 'POST':
                conn, cursor = get_artisan_db_connection()

                name = request.form['name']
                gender = request.form['gender']
                phone = request.form['number']
                birth = request.form['birth']
                nationality = request.form['nationality']
                email = request.form['email']
                card = request.form['card']
                card_number = request.form['card_number']
                postal_address = request.form['postal_address']
                gps_address = request.form['gps_address']
                father = request.form['father']
                father_status = request.form['father_status']
                f_number = request.form.get('f_number', None)
                mother = request.form['mother']
                mother_status = request.form['mother_status']
                m_number = request.form.get('m_number', None)
                profession = request.form['profession']
                years = request.form['years']
                workshop = request.form['workshop']
                workshop_gps = request.form['workshop_gps']
                registration = request.form['registration']
                staff = request.form['staff']

                image = request.files['image']
                image_filename = secure_filename(image.filename)
                image_path = os.path.join("static/images", image_filename)
                image.save(image_path)

                id_image = request.files['id_image']
                id_image_filename = secure_filename(id_image.filename)
                id_image_path = os.path.join(
                    "static/images", id_image_filename)
                id_image.save(id_image_path)

                cursor.execute(
                    "INSERT INTO artisan (name, gender, phone_number, birth, nationality, email, id_type, id_number, home_postal, home_gps, fathers_name, fathers_status, fathers_number, mothers_name, mothers_status, mothers_number, profession, year_profession, shop_location, shop_gps, date_registered, image, id_image, staff) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (name, gender, phone, birth, nationality, email, card, card_number, postal_address, gps_address, father, father_status, f_number,
                     mother, mother_status, m_number, profession, years, workshop, workshop_gps, registration, image_filename, id_image_filename, staff)
                )

                conn.commit()
                conn.close()

                flash("Artisan Successfully Added")
                return redirect(url_for('artisan'))

            return render_template('/super_admin/artisans/add.html', username=username, role=role, image=image)

    return redirect(url_for('index'))


@app.route('/update_artisan/<int:id>', methods=['GET', 'POST'])
@login_required(role='SUPER ADMIN')
def update_artisan(id):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            # Fetch additional details for the selected artisan using the artisan ID
            conn, cursor = get_artisan_db_connection()
            cursor.execute("SELECT * FROM artisan WHERE id = ?", (id,))
            artisan_details = cursor.fetchone()

            if request.method == 'POST':
                # Get data from the form for the artisan
                name = request.form['name']
                gender = request.form['gender']
                phone = request.form['number']
                birth = request.form['birth']
                nationality = request.form['nationality']
                email = request.form['email']
                card = request.form['card']
                card_number = request.form['card_number']
                postal_address = request.form['postal_address']
                gps_address = request.form['gps_address']
                father = request.form['father']
                father_status = request.form['father_status']
                f_number = request.form.get('f_number', None)
                mother = request.form['mother']
                mother_status = request.form['mother_status']
                m_number = request.form.get('m_number', None)
                profession = request.form['profession']
                years = request.form['years']
                workshop = request.form['workshop']
                workshop_gps = request.form['workshop_gps']
                registration = request.form['registration']
                staff = request.form['staff']
                image = request.files['image']
                id_image = request.files['id_image']

                if father_status == 'Dead':
                    f_number = 'None'

                # Save the uploaded images
                if image:
                    image_filename = secure_filename(
                        image.filename)
                    image_path = os.path.join(
                        "static/images", image_filename)
                    image.save(image_path)

                    cursor.execute(
                        'UPDATE artisan SET name=?, gender=?, phone_number=?, birth=?, nationality=?, email=?, id_type=?, id_number=?, home_postal=?, home_gps=?, fathers_name=?, fathers_status=?, fathers_number=?, mothers_name=?, mothers_status=?, mothers_number=?, profession=?, year_profession=?, shop_location=?, shop_gps=?, date_registered=?, image=?, staff=? WHERE id=?',
                        (name, gender, phone, birth, nationality, email, card, card_number, postal_address, gps_address, father, father_status,
                         f_number, mother, mother_status, m_number, profession, years, workshop, workshop_gps, registration, image_filename, staff, id)
                    )
                else:
                    cursor.execute(
                        'UPDATE artisan SET name=?, gender=?, phone_number=?, birth=?, nationality=?, email=?, id_type=?, id_number=?, home_postal=?, home_gps=?, fathers_name=?, fathers_status=?, fathers_number=?, mothers_name=?, mothers_status=?, mothers_number=?, profession=?, year_profession=?, shop_location=?, shop_gps=?, date_registered=?, staff=? WHERE id=?',
                        (name, gender, phone, birth, nationality, email, card, card_number, postal_address, gps_address, father, father_status,
                         f_number, mother, mother_status, m_number, profession, years, workshop, workshop_gps, registration, staff, id)
                    )

                if id_image:
                    id_image_filename = secure_filename(
                        id_image.filename)
                    id_image_path = os.path.join(
                        "static/images", id_image_filename)
                    id_image.save(id_image_path)

                    cursor.execute(
                        'UPDATE artisan SET name=?, gender=?, phone_number=?, birth=?, nationality=?, email=?, id_type=?, id_number=?, home_postal=?, home_gps=?, fathers_name=?, fathers_status=?, fathers_number=?, mothers_name=?, mothers_status=?, mothers_number=?, profession=?, year_profession=?, shop_location=?, shop_gps=?, date_registered=?, id_image=?, staff=? WHERE id=?',
                        (name, gender, phone, birth, nationality, email, card, card_number, postal_address, gps_address, father, father_status,
                         f_number, mother, mother_status, m_number, profession, years, workshop, workshop_gps, registration, id_image_filename, staff, id)
                    )
                else:
                    cursor.execute(
                        'UPDATE artisan SET name=?, gender=?, phone_number=?, birth=?, nationality=?, email=?, id_type=?, id_number=?, home_postal=?, home_gps=?, fathers_name=?, fathers_status=?, fathers_number=?, mothers_name=?, mothers_status=?, mothers_number=?, profession=?, year_profession=?, shop_location=?, shop_gps=?, date_registered=?, staff=? WHERE id=?',
                        (name, gender, phone, birth, nationality, email, card, card_number, postal_address, gps_address, father, father_status,
                         f_number, mother, mother_status, m_number, profession, years, workshop, workshop_gps, registration, staff, id)
                    )

                conn.commit()

                flash("Artisan Successfully Updated")

                return redirect(url_for('artisan'))

            conn.close()
            if artisan_details:
                # Pass the artisan details to the template
                return render_template('/super_admin/artisans/update.html', username=username, role=role, artisan=artisan_details, image=image)
            else:
                # Flash an error message when artisan details are not found
                flash("Artisan details not found", 'error')
                return redirect(url_for('artisan'))

    return redirect(url_for('index'))


# Client Srvice Unit
@app.route('/cs')
@login_required(role='SUPER ADMIN')
def cs():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        conn, cursor = get_cs_db_connection()
        cursor.execute("SELECT * FROM cs")
        cs_list = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/super_admin/cs/cs.html', username=username, role=role, cs=cs_list, image=image)  # noqa
    return redirect(url_for('index'))


@app.route('/cs_search', methods=['GET'])
@login_required(role='SUPER ADMIN')
def cs_search():

    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        search_query = request.args.get('search')
        session['search_query'] = search_query

        if not search_query:
            return redirect(url_for('cs'))

        # Create the "stores" table if it doesn't exist

        # Fetch data from the "stores" table that matches the search query
        conn, cursor = get_cs_db_connection()
        cursor.execute("SELECT * FROM cs WHERE name LIKE ? OR purpose LIKE ? OR unique_code LIKE ? OR phone_number LIKE ?",
                       ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))

        search_results = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/super_admin/cs/cs.html', username=username, role=role, cs=search_results, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/delete_cs/<int:id>')
@login_required(role='SUPER ADMIN')
def delete_cs(id):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from thartisan
        user = get_user_by_id(user_id)

        # Delete the record with the specified store_id
        conn, cursor = get_cs_db_connection()
        cursor.execute("DELETE FROM cs WHERE id=?",
                       (id,))

        conn.commit()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return redirect(url_for('cs', username=username, role=role, image=image))
    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/more_cs/<int:id>')
@login_required(role='SUPER ADMIN')
def more_cs(id):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            # Fetch additional details for the selected store using the store_id
            conn, cursor = get_cs_db_connection()
            cursor.execute(
                "SELECT * FROM cs WHERE id = ?", (id,))
            cs_details = cursor.fetchone()
            conn.close()

            if cs_details:
                # Pass the store details to the template
                return render_template('/super_admin/cs/more.html', username=username, role=role, cs=cs_details, image=image)
            else:
                # Flash an error message when store details are not found
                flash("Details not found", 'error')
                return redirect(url_for('cs'))

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/add_cs', methods=['GET', 'POST'])
@login_required(role='SUPER ADMIN')
def add_cs():
    if 'user_id' in session:
        user_id = session['user_id']
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            if request.method == 'POST':

                first_name = request.form['first_name']
                last_name = request.form['last_name']
                gender = request.form['gender']
                phone = request.form['number']
                address = request.form['address']
                age_bracket = request.form['age_bracket']
                disability_status = request.form['disability_status']
                complainant = request.form.get('complainant', None)
                complaint_textarea = request.form.get(
                    'complaint_textarea', None)
                enquiries_textarea = request.form.get(
                    'enquiries_textarea', None)
                tag_number = request.form.get('tag_number', None)
                office = request.form.get('office', None)
                receipient_name = request.form.get('receipient_name', None)
                purpose_visit = request.form.get('purpose_visit', None)
                purpose = request.form['purpose']

                phone_suffix = phone[-4:] if len(phone) >= 4 else phone
                current_datetime = datetime.now().strftime("%Y-%m-%d / %H%M:%S")
                current_time = datetime.now().strftime("%Y%m%d")

                unique_code = f"{last_name}{phone_suffix}{current_time}"

                conn, cursor = get_cs_db_connection()

                if purpose == 'Complaint' and complaint_textarea is not None:
                    cursor.execute(
                        "INSERT INTO cs (name, gender, phone_number, address, age_bracket, disability_status, complaint_to, complaint_content, purpose, unique_code, date_time) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (f"{first_name} {last_name}", gender, phone, address, age_bracket, disability_status, complainant,
                         complaint_textarea, purpose, unique_code, current_datetime)
                    )
                    flash("Complaint Successfully Sent")

                elif purpose == 'Enquiries' and enquiries_textarea is not None:
                    cursor.execute(
                        "INSERT INTO cs (name, gender, phone_number, address, age_bracket, disability_status, enquiries_content, purpose, unique_code, date_time) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (f"{first_name} {last_name}", gender, phone, address, age_bracket,
                         disability_status, enquiries_textarea, purpose, unique_code, current_datetime)
                    )
                    flash("Enquiries Successfully Sent")
                elif purpose == 'Visit':
                    # Ensure other necessary fields are provided before executing the query
                    cursor.execute(
                        "INSERT INTO cs (name, gender, phone_number, address, age_bracket, disability_status, tag_number, office, receipient_name, purpose_visit, purpose, unique_code, date_time) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (f"{first_name} {last_name}", gender, phone, address, age_bracket, disability_status,
                         tag_number, office, receipient_name, purpose_visit, purpose, unique_code, current_datetime)
                    )
                    flash("Successfully Added")
                else:
                    flash("Invalid form data for the selected purpose")

                conn.commit()
                conn.close()

                return redirect(url_for('cs'))

            return render_template('/super_admin/cs/add.html', username=username, role=role, image=image)

    return redirect(url_for('index'))


@app.route('/response_cs/<int:id>', methods=['GET', 'POST'])
@login_required(role='SUPER ADMIN')
def response_cs(id):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            # Fetch additional details for the selected store using the store_id
            conn, cursor = get_cs_db_connection()
            cursor.execute(
                "SELECT * FROM cs WHERE id = ?", (id,))
            cs_details = cursor.fetchone()
            conn.close()

            if request.method == 'POST':
                response_textarea = request.form.get('response_textarea')
                purpose = request.form.get('purpose')

                # Check if 'purpose' is present in the form data
                if purpose is None:
                    flash("Purpose is required", 'error')
                    return redirect(url_for('response_cs', id=id))

                conn, cursor = get_cs_db_connection()
                if purpose == "Complaint":
                    cursor.execute(
                        "UPDATE cs SET complaint_response=? WHERE id=?", (response_textarea, id))
                elif purpose == "Enquiries":
                    cursor.execute(
                        "UPDATE cs SET enquiries_response=? WHERE id=?", (response_textarea, id))
                conn.commit()
                conn.close()

                redirect(url_for('cs'))

                flash("Response Sent")

            if cs_details:
                # Pass the store details to the template
                return render_template('/super_admin/cs/response.html', username=username, role=role, cs=cs_details, image=image)
            else:
                # Flash an error message when store details are not found
                flash("Details not found", 'error')
                return redirect(url_for('cs'))

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


# Profile
@app.route('/profile', methods=['GET', 'POST'])
@login_required(role='SUPER ADMIN')
def profile():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)
        if user:
            username = user['username']
            role = user['role']
            password = user['password']
            email = user['email']
            phone = user['phone_number']
            gender = user['gender']
            image = user['image']  # Retrieve user's image path

            if request.method == 'POST':
                # Get data from the form for the tenant
                fullname = request.form['fullname']
                telnumber = request.form['telnumber']
                gender = request.form['gender']
                staff_email = request.form['email']
                staff_password = request.form['password']

                # Handle image upload
                image = request.files['image']
                if image:
                    image_filename = secure_filename(image.filename)
                    try:
                        # Create the target directory if it doesn't exist
                        image_folder = os.path.join("static", "images")
                        os.makedirs(image_folder, exist_ok=True)

                        # Save the image
                        image_path = os.path.join(image_folder, image_filename)
                        image.save(image_path)
                    except FileNotFoundError as e:
                        flash(f"Error saving image: {e}", "error")
                    except sqlite3.Error as e:
                        flash(f"Database error: {e}", "error")
                else:
                    image_filename = user['image']

                # If no new image is provided, update other fields
                conn, cursor = get_users_db_connection()
                cursor.execute("""
                    UPDATE users
                    SET username=?, phone_number=?, gender=?, email=?, password=?, image=?
                    WHERE id=?
                """, (fullname, telnumber, gender, staff_email, staff_password, image_filename, user_id,))
                conn.commit()
                conn.close()

                flash('Profile updated successfully', 'success')

                # Redirect to the home page after submission
                return redirect(url_for('profile'))
            return render_template('super_admin/profile.html', username=username, role=role, password=password, email=email, phone=phone, gender=gender, image=image)  # noqa

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/back')
@login_required(role='SUPER ADMIN')
def back():
    # Get the referrer, which is the previous route
    referrer = request.referrer

    # Check the referrer and redirect accordingly
    if 'department' in referrer:
        return redirect(url_for('department'))
    elif 'stores' in referrer:
        return redirect(url_for('stores'))
    elif 'staff' in referrer:
        return redirect(url_for('staff'))
    elif 'sms' in referrer:
        return redirect(url_for('sms'))
    elif 'asset' in referrer:
        return redirect(url_for('asset'))
    elif 'artisan' in referrer:
        return redirect(url_for('artisan'))
    elif 'cs' in referrer:
        return redirect(url_for('cs'))
    # Add more conditions for other routes as needed
    else:
        # Default to redirecting to the index page if none of the conditions match
        return redirect(url_for('dashboard'))


# -------------------------------------------------------------------------------Admin----------------------------------------------------------------------------------
# Stores
@app.route('/admin_stores')
@login_required(role='ADMIN')
def admin_stores():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        conn, cursor = get_stores_db_connection()
        cursor.execute("SELECT * FROM shop")
        store_list = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/admin/stores.html', username=username, role=role, stores=store_list, image=image)  # noqa
    return redirect(url_for('index'))


@app.route('/admin_search', methods=['GET'])
@login_required(role='ADMIN')
def admin_search():

    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        search_query = request.args.get('search')

        if not search_query:
            return redirect(url_for('admin_stores'))

        # Create the "stores" table if it doesn't exist

        # Fetch data from the "stores" table that matches the search query
        conn, cursor = get_stores_db_connection()
        cursor.execute("SELECT * FROM shop WHERE store_number LIKE ? OR store_size LIKE ? OR business LIKE ?",
                       ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))
        search_results = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/admin/stores.html', username=username, role=role, stores=search_results, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/admin_store_reg')
@login_required(role='ADMIN')
def admin_store_reg():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)
        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/admin/store-reg.html', username=username, role=role, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/admin_add_stores_one')
@login_required(role='ADMIN')
def admin_add_stores_one():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)
        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/admin/add-stores.html', username=username, role=role, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/admin_add_stores_both')
@login_required(role='ADMIN')
def admin_add_stores_both():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)
        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/admin/add-stores-both.html', username=username, role=role, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/admin_add_stores', methods=['GET', 'POST'])
@login_required(role='ADMIN')
def admin_add_stores():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if request.method == 'POST':
            store_number = request.form.get('store_number')

            # Check if the store number already exists
            conn, cursor = get_stores_db_connection()
            cursor.execute(
                "SELECT store_number FROM shop WHERE store_number = ?", (store_number,))
            existing_store = cursor.fetchone()
            conn.close()

            if existing_store:
                flash("Store number already exists in the database.", "error")
                return redirect(url_for('admin_stores'))

            conn = get_db()
            cursor = conn.cursor()

            try:
                # Your database operations here
                with get_db() as conn:
                    cursor = conn.cursor()
                    # Get data from the form for the shop
                    store_size = request.form.get('size')
                    rent = request.form.get('rent')
                    business = request.form.get('business')
                    staff = request.form.get('staff')  # Use get method here
                    sector = request.form.get('sector')

                    conn, cursor = get_stores_db_connection()
                    cursor.execute("INSERT INTO shop (store_number, store_size, rent, business, sector, staff) VALUES (?, ?, ?, ?, ?, ?)",
                                   (store_number, store_size, rent, business, sector, staff))

                    t_fullname = request.form.get('t_fullname')
                    t_telnumber = request.form.get('t_telnumber')
                    t_gender = request.form.get('t_gender')
                    t_birth = request.form.get('t_birth')
                    t_house_number = request.form.get('t_house_number')
                    t_id_number = request.form.get('t_id_number')

                    t_image = request.files['t_image']
                    t_image_filename = secure_filename(t_image.filename)
                    t_image_path = os.path.join(
                        "static/images", t_image_filename)
                    t_image.save(t_image_path)

                    cursor.execute("INSERT INTO tenant (name, number, birth, gender, house_number, id_number, image, store_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                   (t_fullname, t_telnumber, t_birth, t_gender, t_house_number, t_id_number, t_image_filename, store_number))

                    if 'o_fullname' in request.form:
                        o_fullname = request.form.get('o_fullname')
                        o_telnumber = request.form.get('o_telnumber')
                        o_gender = request.form.get('o_gender')
                        o_birth = request.form.get('o_birth')
                        o_house_number = request.form.get('o_house_number')
                        o_id_number = request.form.get('o_id_number')

                        o_image = request.files['o_image']
                        o_image_filename = secure_filename(o_image.filename)
                        o_image_path = os.path.join(
                            "static/images", o_image_filename)
                        o_image.save(o_image_path)

                        cursor.execute("INSERT INTO occupant (name, number, birth, gender, house_number, id_number, image, store_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                       (o_fullname, o_telnumber, o_birth, o_gender, o_house_number, o_id_number, o_image_filename, store_number))
                    else:
                        o_fullname = "None"
                        o_telnumber = "None"
                        o_gender = "None"
                        o_birth = "None"
                        o_house_number = "None"
                        o_id_number = "None"
                        o_image_filename = "None"

                        cursor.execute("INSERT INTO occupant (name, number, birth, gender, house_number, id_number, image, store_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                       (o_fullname, o_telnumber, o_birth, o_gender, o_house_number, o_id_number, o_image_filename, store_number))

                    # Commit the changes to the database
                    conn.commit()
                    flash("Store Successfully Added")
            except sqlite3.Error as e:
                conn.rollback()  # Rollback changes if an error occurs
                flash(f"Database error: {e}", "error")

            conn.close()  # Close the connection

            # Redirect to the home page after submission
            return redirect(url_for('admin_stores'))

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/admin/add-stores.html', username=username, role=role, image=image)

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/admin_more_stores/<string:store_number>')
@login_required(role='ADMIN')
def admin_more_stores(store_number):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            # Fetch additional details for the selected store using the store_id
            conn, cursor = get_stores_db_connection()

            cursor.execute(
                "SELECT * FROM shop WHERE store_number = ?", (store_number,))

            store_details = cursor.fetchone()

            cursor.execute(
                "SELECT * FROM tenant WHERE store_number = ?", (store_number,))

            tenant_details = cursor.fetchone()

            cursor.execute(
                "SELECT * FROM occupant WHERE store_number = ?", (store_number,))

            occupant_details = cursor.fetchone()
            conn.close()

            if store_details:
                # Pass the store details to the template
                return render_template('/admin/full-details.html', username=username, role=role, store=store_details, tenant=tenant_details, occupant=occupant_details, image=image)
            else:
                # Flash an error message when store details are not found
                flash("Store details not found", 'error')
                return redirect(url_for('admin_stores'))

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/admin_update_stores/<string:store_number>', methods=['GET', 'POST'])
@login_required(role='ADMIN')
def admin_update_stores(store_number):
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            conn, cursor = get_stores_db_connection()
            cursor.execute(
                "SELECT * FROM shop WHERE store_number = ?", (store_number,))
            store = cursor.fetchone()

            cursor.execute(
                "SELECT * FROM tenant WHERE store_number = ?", (store_number,))
            tenant = cursor.fetchone()

            cursor.execute(
                "SELECT * FROM occupant WHERE store_number = ?", (store_number,))
            occupant = cursor.fetchone()

            if request.method == 'POST':
                store_number = request.form['store_number']
                store_size = request.form['size']
                rent = request.form['rent']
                business = request.form['business']

                store_number = request.form.get('store_number')

                # Check if the store number already exist
                cursor.execute(
                    "SELECT store_number FROM shop WHERE store_number = ?", (store_number,))
                existing_store = cursor.fetchone()
                conn.close()

                if existing_store and existing_store[0] != store_number:
                    flash("Store number already exists in the database.", "error")
                    return redirect(url_for('admin_stores'))

                conn = get_db()
                cursor = conn.cursor()

                try:
                    # Your database operations here
                    with get_db() as conn:
                        cursor = conn.cursor()
                        # Get data from the form for the shop
                        store_size = request.form.get('size')
                        rent = request.form.get('rent')
                        business = request.form.get('business')
                        staff = request.form.get(
                            'staff')  # Use get method here
                        sector = request.form.get('sector')

                        cursor.execute("UPDATE shop SET store_size=?, rent=?, business=?, sector=?, staff=? WHERE store_number=?",
                                       (store_size, rent, business, sector, staff, store_number))

                        t_fullname = request.form.get('t_fullname')
                        t_telnumber = request.form.get('t_telnumber')
                        t_gender = request.form.get('t_gender')
                        t_birth = request.form.get('t_birth')
                        t_house_number = request.form.get('t_house_number')
                        t_id_number = request.form.get('t_id_number')

                        t_image = request.files['t_image']

                        if t_image:
                            t_image_filename = secure_filename(
                                t_image.filename)
                            t_image_path = os.path.join(
                                "static/images", t_image_filename)
                            t_image.save(t_image_path)

                            cursor.execute("UPDATE tenant SET name=?, number=?, birth=?, gender=?, house_number=?, id_number=?, image=? WHERE store_number=?",
                                           (t_fullname, t_telnumber, t_birth, t_gender, t_house_number, t_id_number, t_image_filename, store_number))
                        else:
                            cursor.execute("UPDATE tenant SET name=?, number=?, birth=?, gender=?, house_number=?, id_number=? WHERE store_number=?",
                                           (t_fullname, t_telnumber, t_birth, t_gender, t_house_number, t_id_number, store_number))

                        if 'o_fullname' in request.form:
                            o_fullname = request.form.get('o_fullname')
                            o_telnumber = request.form.get('o_telnumber')
                            o_gender = request.form.get('o_gender')
                            o_birth = request.form.get('o_birth')
                            o_house_number = request.form.get('o_house_number')
                            o_id_number = request.form.get('o_id_number')

                            o_image = request.files['o_image']

                            if o_image:
                                o_image_filename = secure_filename(
                                    o_image.filename)
                                o_image_path = os.path.join(
                                    "static/images", o_image_filename)
                                o_image.save(o_image_path)

                                cursor.execute("UPDATE shop SET name=?, number=?, birth=?, gender=?, house_number=?, id_number=?, image=? WHERE store_number=?",
                                               (o_fullname, o_telnumber, o_birth, o_gender, o_house_number, o_id_number, o_image_filename, store_number))
                            else:
                                cursor.execute("UPDATE occupant SET name=?, number=?, birth=?, gender=?, house_number=?, id_number=? WHERE store_number=?",
                                               (o_fullname, o_telnumber, o_birth, o_gender, o_house_number, o_id_number, store_number))

                        # Commit the changes to the database
                        conn.commit()
                        flash("Store Successfully Updated")
                except sqlite3.Error as e:
                    conn.rollback()  # Rollback changes if an error occurs
                    flash(f"Database error: {e}", "error")

                conn.close()  # Close the connection

                # Redirect to the home page after submission
                return redirect(url_for('admin_stores'))

            return render_template('/admin/store/update.html', username=username, role=role, image=image, stores=store, tenant=tenant, occupant=occupant)

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


# Assets
@app.route('/admin_asset')
@login_required(role='ADMIN')
def admin_asset():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        conn, cursor = get_asset_db_connection()
        cursor.execute("SELECT * FROM asset")
        asset_list = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/admin/asset.html', username=username, role=role, image=image, asset=asset_list)  # noqa
    return redirect(url_for('index'))


@app.route('/admin_asset_search', methods=['GET'])
@login_required(role='ADMIN')
def admin_asset_search():

    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        search_query = request.args.get('search')

        if not search_query:
            return redirect(url_for('admin_asset'))

        # Create the "stores" table if it doesn't exist

        # Fetch data from the "stores" table that matches the search query
        conn, cursor = get_asset_db_connection()
        cursor.execute("SELECT * FROM asset WHERE department LIKE ? OR officer LIKE ? OR unit LIKE ? OR device_name LIKE ? OR division LIKE ?",
                       ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))

        search_results = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/admin/asset.html', username=username, role=role, asset=search_results, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/admin_more_asset/<int:id>')
@login_required(role='ADMIN')
def admin_more_asset(id):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            # Fetch additional details for the selected store using the store_id
            conn, cursor = get_asset_db_connection()

            cursor.execute(
                "SELECT * FROM asset WHERE id = ?", (id,))
            asset_details = cursor.fetchone()
            conn.close()

            if asset_details:
                # Pass the store details to the template
                return render_template('/admin/add-assets-form/more.html', username=username, role=role, asset=asset_details, image=image)
            else:
                # Flash an error message when store details are not found
                flash("Asset details not found", 'error')
                return redirect(url_for('admin_asset'))

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/admin_add_asset', methods=['GET', 'POST'])
@login_required(role='ADMIN')
def admin_add_asset():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        # Handle the GET request (initial form display)
        conn, cursor = get_department_db_connection()
        cursor.execute('SELECT * FROM department')
        departments = [row['department_name'] for row in cursor.fetchall()]

        cursor.execute('SELECT * FROM unit')
        units = [row['unit'] for row in cursor.fetchall()]
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/admin/add-assets-form/assets-form.html', username=username, role=role, image=image, departments=departments, units=units)

    return redirect(url_for('index'))


@app.route('/admin_asset_add', methods=['GET', 'POST'])
@login_required(role='ADMIN')
def admin_asset_add():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)
        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            if request.method == 'POST':
                # Get data from the form for the asset
                department = request.form['department']
                division = request.form['division']
                unit = request.form['unit']
                device = request.form['device']
                date_purchased = request.form['date_purchased']
                officer = request.form['officer']
                serial_number = request.form['serial_number']
                embosenuit = request.form['embosenuit']
                status = request.form['status']
                brand = request.form['brand']
                # Use get() with a default value
                toner = request.form.get('toner_type', None)
                # Use get() with a default value
                capacity = request.form.get('device_capacity', None)

                staff = request.form['staff']

                conn, cursor = get_asset_db_connection()
                if toner is not None and capacity is not None:
                    cursor.execute('''
                        INSERT INTO asset (department, unit, device_name, brand, serial_number, embosenuit_number,
                        device_status, toner, device_capacity, division, date_purchased, officer, staff)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (department, unit, device, brand, serial_number, embosenuit, status, toner, capacity, division, date_purchased, officer, staff))
                elif toner is not None:
                    cursor.execute('''
                        INSERT INTO asset (department, unit, device_name, brand, serial_number, embosenuit_number,
                        device_status, toner, division, date_purchased, officer, staff)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (department, unit, device, brand, serial_number, embosenuit, status, toner, division, date_purchased, officer, staff))
                elif capacity is not None:
                    cursor.execute('''
                        INSERT INTO asset (department, unit, device_name, brand, serial_number, embosenuit_number,
                        device_status, device_capacity, division, date_purchased, officer, staff)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (department, unit, device, brand, serial_number, embosenuit, status, capacity, division, date_purchased, officer, staff))
                else:
                    cursor.execute('''
                        INSERT INTO asset (department, unit, device_name, brand, serial_number, embosenuit_number,
                        device_status, division, date_purchased, officer, staff)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (department, unit, device, brand, serial_number, embosenuit, status, division, date_purchased, officer, staff))
                conn.commit()
                conn.close()

                flash("Asset Successfully Added")

                return redirect('admin_asset')

            # Render the template with username and role
            return render_template('admin/add-assets-form/assets-form.html', username=username, role=role, image=image)

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/admin_update_asset/<int:id>', methods=['GET', 'POST'])
@login_required(role='ADMIN')
def admin_update_asset(id):
    if 'user_id' in session:
        user_id = session['user_id']
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            # Fetch additional details for the selected department using the department_name
            conn, cursor = get_asset_db_connection()
            cursor.execute(
                "SELECT * FROM asset WHERE id = ?", (id,))
            asset_details = cursor.fetchone()

            conn, cursor = get_department_db_connection()
            cursor.execute('SELECT * FROM department')
            departments = [row['department_name']
                           for row in cursor.fetchall()]

            cursor.execute('SELECT * FROM unit')
            units = [row['unit'] for row in cursor.fetchall()]

            if request.method == 'POST':
                # Get data from the form for the asset
                department = request.form['department']
                division = request.form['division'].upper()
                unit = request.form['unit']
                device = request.form['device']
                date_purchased = request.form['date_purchased']
                officer = request.form['officer']
                serial_number = request.form['serial_number']
                embosenuit = request.form['embosenuit']
                status = request.form['status']
                brand = request.form['brand']
                # Use get() with a default value
                toner = request.form.get('toner_type', None)
                # Use get() with a default value
                capacity = request.form.get('device_capacity', None)

                # Update the asset in the 'department' table
                conn, cursor = get_asset_db_connection()
                cursor.execute(
                    'UPDATE asset SET department=?, unit=?, division=?, device_name=?, date_purchased=?, serial_number=?, embosenuit_number=?, brand=?, toner=?, device_capacity=?, device_status=?, officer=? WHERE id=?', (department, unit, division, device, date_purchased, serial_number, embosenuit, brand, toner, capacity, status, officer, id))

                conn.commit()

                flash("Asset Successfully Updated")

                return redirect(url_for('admin_asset'))

            conn.close()
            if asset_details:
                # Pass the department details to the template
                return render_template('/admin/add-assets-form/update.html', username=username, role=role, asset=asset_details, departments=departments, units=units, image=image)
            else:
                # Flash an error message when department details are not found
                flash("Asset details not found", 'error')
                return redirect(url_for('admin_asset'))

    return redirect(url_for('index'))

# Profile


@app.route('/admin_profile', methods=['GET', 'POST'])
@login_required(role='ADMIN')
def admin_profile():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)
        if user:
            username = user['username']
            role = user['role']
            password = user['password']
            email = user['email']
            phone = user['phone_number']
            gender = user['gender']
            image = user['image']  # Retrieve user's image path

            if request.method == 'POST':
                # Get data from the form for the tenant
                fullname = request.form['fullname']
                telnumber = request.form['telnumber']
                gender = request.form['gender']
                staff_email = request.form['email']
                staff_password = request.form['password']

                # Handle image upload
                image = request.files['image']
                if image:
                    image_filename = secure_filename(image.filename)
                    try:
                        # Create the target directory if it doesn't exist
                        image_folder = os.path.join("static", "images")
                        os.makedirs(image_folder, exist_ok=True)

                        # Save the image
                        image_path = os.path.join(image_folder, image_filename)
                        image.save(image_path)
                    except FileNotFoundError as e:
                        flash(f"Error saving image: {e}", "error")
                    except sqlite3.Error as e:
                        flash(f"Database error: {e}", "error")
                else:
                    image_filename = user['image']

                # If no new image is provided, update other fields
                conn, cursor = get_users_db_connection()
                cursor.execute("""
                    UPDATE users
                    SET username=?, phone_number=?, gender=?, email=?, password=?, image=?
                    WHERE id=?
                """, (fullname, telnumber, gender, staff_email, staff_password, image_filename, user_id,))
                conn.commit()
                conn.close()

                flash('Profile updated successfully', 'success')

                # Redirect to the home page after submission
                return redirect(url_for('admin_profile'))
            return render_template('/admin/profile.html', username=username, role=role, password=password, email=email, phone=phone, gender=gender, image=image)  # noqa

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/admin_back')
@login_required(role='ADMIN')
def admin_back():
    # Get the referrer, which is the previous route
    referrer = request.referrer

    # Check the referrer and redirect accordingly
    if 'asset' in referrer:
        return redirect(url_for('admin_asset'))
    elif 'stores' in referrer:
        return redirect(url_for('admin_stores'))
    # Add more conditions for other routes as needed
    else:
        # Default to redirecting to the index page if none of the conditions match
        return redirect(url_for('admin_stores'))


# ------------------------------------------------------------------------------Data Entry---------------------------------------------------------------------------------
# Stores
@app.route('/staff_stores')
@login_required(role='DATA ENTRY')
def staff_stores():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        conn, cursor = get_stores_db_connection()
        cursor.execute("SELECT * FROM shop ORDER BY id DESC LIMIT 10")
        store_list = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/data_entry/stores/stores.html', username=username, role=role, stores=store_list, image=image)  # noqa
    return redirect(url_for('index'))


@app.route('/staff_search', methods=['GET'])
@login_required(role='DATA ENTRY')
def staff_search():

    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        search_query = request.args.get('search')

        if not search_query:
            return redirect(url_for('staff_stores'))

        # Create the "stores" table if it doesn't exist

        # Fetch data from the "stores" table that matches the search query
        conn, cursor = get_stores_db_connection()
        cursor.execute("SELECT * FROM shop WHERE store_number LIKE ? OR store_size LIKE ? OR business LIKE ?",
                       ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))
        search_results = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/data_entry/stores/stores.html', username=username, role=role, stores=search_results, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/staff_store_reg')
@login_required(role='DATA ENTRY')
def staff_store_reg():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)
        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/data_entry/stores/store-reg.html', username=username, role=role, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/staff_add_stores_one')
@login_required(role='DATA ENTRY')
def staff_add_stores_one():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)
        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/data_entry/stores/add-stores.html', username=username, role=role, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/staff_add_stores_both')
@login_required(role='DATA ENTRY')
def staff_add_stores_both():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)
        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/data_entry/stores/add-stores-both.html', username=username, role=role, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/staff_add_stores', methods=['GET', 'POST'])
@login_required(role='DATA ENTRY')
def staff_add_stores():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if request.method == 'POST':
            store_number = request.form.get('store_number')

            # Check if the store number already exists
            conn, cursor = get_stores_db_connection()
            cursor.execute(
                "SELECT store_number FROM shop WHERE store_number = ?", (store_number,))
            existing_store = cursor.fetchone()
            conn.close()

            if existing_store:
                flash("Store number already exists in the database.", "error")
                return redirect(url_for('staff_stores'))

            conn = get_db()
            cursor = conn.cursor()

            try:
                # Your database operations here
                with get_db() as conn:
                    cursor = conn.cursor()
                    # Get data from the form for the shop
                    store_size = request.form.get('size')
                    rent = request.form.get('rent')
                    business = request.form.get('business')
                    staff = request.form.get('staff')  # Use get method here
                    sector = request.form.get('sector')

                    conn, cursor = get_stores_db_connection()
                    cursor.execute("INSERT INTO shop (store_number, store_size, rent, business, sector, staff) VALUES (?, ?, ?, ?, ?, ?)",
                                   (store_number, store_size, rent, business, sector, staff))

                    t_fullname = request.form.get('t_fullname')
                    t_telnumber = request.form.get('t_telnumber')
                    t_gender = request.form.get('t_gender')
                    t_birth = request.form.get('t_birth')
                    t_house_number = request.form.get('t_house_number')
                    t_id_number = request.form.get('t_id_number')

                    t_image = request.files['t_image']
                    t_image_filename = secure_filename(t_image.filename)
                    t_image_path = os.path.join(
                        "static/images", t_image_filename)
                    t_image.save(t_image_path)

                    cursor.execute("INSERT INTO tenant (name, number, birth, gender, house_number, id_number, image, store_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                   (t_fullname, t_telnumber, t_birth, t_gender, t_house_number, t_id_number, t_image_filename, store_number))

                    if 'o_fullname' in request.form:
                        o_fullname = request.form.get('o_fullname')
                        o_telnumber = request.form.get('o_telnumber')
                        o_gender = request.form.get('o_gender')
                        o_birth = request.form.get('o_birth')
                        o_house_number = request.form.get('o_house_number')
                        o_id_number = request.form.get('o_id_number')

                        o_image = request.files['o_image']
                        o_image_filename = secure_filename(o_image.filename)
                        o_image_path = os.path.join(
                            "static/images", o_image_filename)
                        o_image.save(o_image_path)

                        cursor.execute("INSERT INTO occupant (name, number, birth, gender, house_number, id_number, image, store_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                       (o_fullname, o_telnumber, o_birth, o_gender, o_house_number, o_id_number, o_image_filename, store_number))

                    # Commit the changes to the database
                    conn.commit()
                    flash("Store Successfully Added")
            except sqlite3.Error as e:
                conn.rollback()  # Rollback changes if an error occurs
                flash(f"Database error: {e}", "error")

            conn.close()  # Close the connection

            # Redirect to the home page after submission
            return redirect(url_for('staff_stores'))

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/data_entry/stores/add-stores.html', username=username, role=role, image=image)

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


# Assets
@app.route('/staff_asset')
@login_required(role='DATA ENTRY')
def staff_asset():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        conn, cursor = get_asset_db_connection()
        cursor.execute("SELECT * FROM asset")
        asset_list = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/data_entry/asset/asset.html', username=username, role=role, image=image, asset=asset_list)  # noqa
    return redirect(url_for('index'))


@app.route('/staff_asset_search', methods=['GET'])
@login_required(role='DATA ENTRY')
def staff_asset_search():

    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        search_query = request.args.get('search')

        if not search_query:
            return redirect(url_for('staff_asset'))

        # Create the "stores" table if it doesn't exist

        # Fetch data from the "stores" table that matches the search query
        conn, cursor = get_asset_db_connection()
        cursor.execute("SELECT * FROM asset WHERE department LIKE ? OR user LIKE ? OR unit LIKE ? OR device_name LIKE ? OR division LIKE ?",
                       ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))

        search_results = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/data_entry/asset/asset.html', username=username, role=role, asset=search_results, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/staff_add_asset', methods=['GET', 'POST'])
@login_required(role='DATA ENTRY')
def staff_add_asset():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        # Handle the GET request (initial form display)
        conn, cursor = get_department_db_connection()
        cursor.execute('SELECT * FROM department')
        departments = [row['department_name'] for row in cursor.fetchall()]

        cursor.execute('SELECT * FROM unit')
        units = [row['unit'] for row in cursor.fetchall()]
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/data_entry/asset/add-assets-form/assets-form.html', username=username, role=role, image=image, departments=departments, units=units)

    return redirect(url_for('index'))


@app.route('/staff_asset_add', methods=['GET', 'POST'])
@login_required(role='DATA ENTRY')
def staff_asset_add():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)
        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            if request.method == 'POST':
                # Get data from the form for the asset
                department = request.form['department']
                division = request.form['division']
                unit = request.form['unit']
                device = request.form['device']
                date_purchased = request.form['date_purchased']
                using = request.form['using']
                serial_number = request.form['serial_number']
                embosenuit = request.form['embosenuit']
                status = request.form['status']
                brand = request.form['brand']
                # Use get() with a default value
                toner = request.form.get('toner_type', None)
                # Use get() with a default value
                capacity = request.form.get('device_capacity', None)

                staff = request.form['staff']

                conn, cursor = get_asset_db_connection()
                if toner is not None and capacity is not None:
                    cursor.execute('''
                        INSERT INTO asset (department, unit, device_name, brand, serial_number, embosenuit_number,
                        device_status, toner, device_capacity, division, date_purchased, user, staff)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (department, unit, device, brand, serial_number, embosenuit, status, toner, capacity, division, date_purchased, using, staff))
                elif toner is not None:
                    cursor.execute('''
                        INSERT INTO asset (department, unit, device_name, brand, serial_number, embosenuit_number,
                        device_status, toner, division, date_purchased, user, staff)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (department, unit, device, brand, serial_number, embosenuit, status, toner, division, date_purchased, using, staff))
                elif capacity is not None:
                    cursor.execute('''
                        INSERT INTO asset (department, unit, device_name, brand, serial_number, embosenuit_number,
                        device_status, device_capacity, division, date_purchased, user, staff)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (department, unit, device, brand, serial_number, embosenuit, status, capacity, division, date_purchased, using, staff))
                else:
                    cursor.execute('''
                        INSERT INTO asset (department, unit, device_name, brand, serial_number, embosenuit_number,
                        device_status, division, date_purchased, user, staff)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (department, unit, device, brand, serial_number, embosenuit, status, division, date_purchased, using, staff))
                conn.commit()
                conn.close()

                flash("Asset Successfully Added")

                return redirect('staff_asset')

            # Render the template with username and role
            return render_template('data_entry/asset/add-assets-form/assets-form.html', username=username, role=role, image=image)

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


# Stores Management Systems
@app.route('/staff_sms')
@login_required(role='DATA ENTRY')
def staff_sms():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        conn, cursor = get_sms_db_connection()
        cursor.execute("SELECT COUNT(id) FROM stores_received")
        item_count = cursor.fetchone()[0]
        conn.close()

        conn, cursor = get_sms_db_connection()
        cursor.execute("SELECT COUNT(id) FROM stores_dispatch")
        dispatch_count = cursor.fetchone()[0]
        conn.close()

        conn, cursor = get_sms_db_connection()
        cursor.execute(
            "SELECT * FROM stores_received ORDER BY id DESC LIMIT 10")
        sms_list_receiver = cursor.fetchall()
        conn.close()

        conn, cursor = get_sms_db_connection()
        cursor.execute(
            "SELECT * FROM stores_dispatch ORDER BY id DESC LIMIT 10")
        sms_list_dispatch = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/data_entry/sms/sms.html', username=username, role=role, image=image, sms_list_receiver=sms_list_receiver, item_count=item_count, dispatch_count=dispatch_count, sms_list_dispatch=sms_list_dispatch)  # noqa
    return redirect(url_for('index'))


@app.route('/staff_sms_search', methods=['GET'])
@login_required(role='DATA ENTRY')
def staff_sms_search():

    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        search_query = request.args.get('search')
        session['search_query'] = search_query

        if not search_query:
            return redirect(url_for('staff_sms'))

        # Fetch data from the "stores" table that matches the search query
        conn, cursor = get_sms_db_connection()
        cursor.execute("SELECT * FROM stores_received WHERE item LIKE ? OR serial_number LIKE ?",
                       ('%' + search_query + '%', '%' + search_query + '%'))
        search_results_receiver = cursor.fetchall()

        cursor.execute("SELECT * FROM stores_dispatch WHERE item LIKE ? OR name_receiver LIKE ?",
                       ('%' + search_query + '%', '%' + search_query + '%'))

        search_results_dispatch = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/data_entry/sms/sms.html', username=username, role=role, sms_receiver=search_results_receiver, sms_dispatch=search_results_dispatch,  image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/staff_sms_add', methods=['GET', 'POST'])
@login_required(role='DATA ENTRY')
def staff_sms_add():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)
        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            if request.method == 'POST':
                item = request.form['item'].upper()
                serial_number = request.form['serial_number'].upper()
                quantity_requested = request.form['requested_quantity']
                quantity_received = request.form['received_quantity']
                date_recieved = request.form['date_recieved']
                differnce = request.form['difference']
                supplier = request.form['supplier']
                department = request.form['department']
                staff = request.form['staff']

                conn, cursor = get_sms_db_connection()

                cursor.execute('''
                    INSERT INTO stores_received (item, serial_number, quantity_requested, quantity_received, date_recieved, staff, difference, supplier_name, requested_dept)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (item, serial_number, quantity_requested, quantity_received, date_recieved, staff, differnce, supplier, department))

                conn.commit()
                conn.close()

                flash("Item Successfully Added")

                return redirect('staff_sms')

            # Render the template with username and role
            return render_template('/data_entry/sms/add.html', username=username, role=role, image=image)

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


@app.route('/staff_sms_dispatch', methods=['GET', 'POST'])
@login_required(role='DATA ENTRY')
def staff_sms_dispatch():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)
        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            if request.method == 'POST':
                item = request.form['item'].upper()
                quantity = request.form['quantity']
                dispatch = request.form['dispatch']
                date_received = request.form['date_recieved']
                officer = request.form.get('officer')
                person = request.form.get('person', None)
                department = request.form.get('department', None)
                desc = request.form.get('desc', None)
                number = request.form.get('number')
                staff = request.form['staff']

                conn, cursor = get_sms_db_connection()

                cursor.execute('''
                    INSERT INTO stores_dispatch (item, type, quantity, date_recieved, staff, department, officer_receiver, name_receiver, description, phone_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (item, dispatch, quantity, date_received, staff, department, officer, person, desc, number))

                conn.commit()
                conn.close()

                flash("Item Successfully Dispatched")

                return redirect('staff_sms')

            # Render the template with username and role
            return render_template('/data_entry/sms/add-dispatch.html', username=username, role=role, image=image)

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))


# Artisans
@app.route('/staff_artisan')
@login_required(role='DATA ENTRY')
def staff_artisan():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        conn, cursor = get_artisan_db_connection()
        cursor.execute("SELECT * FROM artisan ORDER BY id DESC LIMIT 10")
        artisan_list = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/data_entry/artisans/artisans.html', username=username, role=role, artisan=artisan_list, image=image)  # noqa
    return redirect(url_for('index'))


@app.route('/staff_artisan_search', methods=['GET'])
@login_required(role='DATA ENTRY')
def staff_artisan_search():

    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        search_query = request.args.get('search')
        session['search_query'] = search_query

        if not search_query:
            return redirect(url_for('artisan'))

        # Create the "stores" table if it doesn't exist

        # Fetch data from the "stores" table that matches the search query
        conn, cursor = get_artisan_db_connection()
        cursor.execute("SELECT * FROM artisan WHERE name LIKE ? OR profession LIKE ? OR date_registered LIKE ? OR nationality LIKE ? OR id_number LIKE ?",
                       ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))

        search_results = cursor.fetchall()
        conn.close()

        if user:
            username = user['username']
            role = user['role']
            image = user['image']
            return render_template('/data_entry/artisans/artisans.html', username=username, role=role, artisan=search_results, image=image)  # noqa
    # If the user is not logged in or an error occurs, redirect to the index page# noqa
    return redirect(url_for('index'))


@app.route('/staff_add_artisan', methods=['GET', 'POST'])
@login_required(role='DATA ENTRY')
def staff_add_artisan():
    if 'user_id' in session:
        user_id = session['user_id']  # Get the user ID from the session
        # Retrieve user information from the database
        user = get_user_by_id(user_id)

        if user:
            username = user['username']
            role = user['role']
            image = user['image']

            if request.method == 'POST':
                conn, cursor = get_artisan_db_connection()

                # Get data from the form for the users
                name = request.form['name']
                gender = request.form['gender']
                phone = request.form['number']
                birth = request.form['birth']
                nationality = request.form['nationality']
                email = request.form['email']
                card = request.form['card']
                card_number = request.form['card_number']
                postal_address = request.form['postal_address']
                gps_address = request.form['gps_address']
                father = request.form['father']
                father_status = request.form['father_status']
                f_number = request.form.get('f_number', None)
                mother = request.form['mother']
                mother_status = request.form['mother_status']
                m_number = request.form.get('m_number', None)
                profession = request.form['profession']
                years = request.form['years']
                workshop = request.form['workshop']
                workshop_gps = request.form['workshop_gps']
                registration = request.form['registration']
                staff = request.form['staff']

                image = request.files['image']
                image_filename = secure_filename(image.filename)
                image_path = os.path.join(
                    "static/images", image_filename)
                image.save(image_path)

                id_image = request.files['id_image']
                id_image_filename = secure_filename(id_image.filename)
                id_image_path = os.path.join(
                    "static/images", id_image_filename)
                image.save(id_image_path)

                # Adjust the column names in the SQL query based on your database structure
                cursor.execute("""
                                    INSERT INTO artisan (
                                        name, gender, phone_number, birth, nationality, email, id_type, id_number, 
                                        home_postal, home_gps, fathers_name, fathers_status, fathers_number, 
                                        mothers_name, mothers_status, mothers_number, profession, year_profession, 
                                        shop_location, shop_gps, date_registered, image, id_image, staff
                                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                                """, (
                    name, gender, phone, birth, nationality, email, card, card_number,
                    postal_address, gps_address, father, father_status, f_number,
                    mother, mother_status, m_number, profession, years, workshop,
                    workshop_gps, registration, image_filename, id_image_filename, staff
                ))
                conn.commit()
                conn.close()

                flash("Artisan Successfully Added")

                # Redirect to the home page after submission
                return redirect(url_for('staff_artisan'))

            return render_template('/data_entry/artisans/add.html', username=username, role=role, image=image)

    # If the user is not logged in or an error occurs, redirect to the index page
    return redirect(url_for('index'))

# -----------------------------------------------------------------Export-------------------------------------------------------------------------------------


@app.route('/export_excel', methods=['GET'])
def export_excel():
    search_query = session.get('search_query', '')

    if search_query != '':
        # Perform a search query in your database
        conn, cursor = get_stores_db_connection()
        cursor.execute('''
            SELECT * FROM shop
            LEFT JOIN tenant ON shop.store_number = tenant.store_number
            LEFT JOIN occupant ON shop.store_number = occupant.store_number
            WHERE shop.store_number LIKE ? OR shop.store_size LIKE ? OR shop.sector LIKE ? OR shop.business LIKE ?
        ''', ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))
        results = cursor.fetchall()
        conn.close()

    else:
        conn, cursor = get_stores_db_connection()
        cursor.execute('''
            SELECT * FROM shop
            LEFT JOIN tenant ON shop.store_number = tenant.store_number
            LEFT JOIN occupant ON shop.store_number = occupant.store_number
        ''')

        results = cursor.fetchall()
        conn.close()

    # Convert the results to a pandas DataFrame
    df_columns = ['ID', 'Store Number', 'Store Size',
                  'Rent', 'Sector', 'Business', 'Staff', 'Tenant ID', 'Tenant Name', 'Tenant Gender', 'Tenant Phone Number', 'Tenant Date Of Birth', 'Tenant Image', 'Tenant House Number', 'Tenant Store Number', 'Tenant ID Number', 'Tenant ID Image', 'Occupant ID', 'Occupant Name', 'Occupant Gender', 'Occupant Phone Number', 'Occupant Date Of Birth', 'Occupant Image', 'Occupant House Number', 'Occupant Store Number', 'Occupant ID Number', 'Occupant ID Image']
    df = pd.DataFrame(results, columns=df_columns)

    # Drop columns from the DataFrame
    df = df.drop(['Tenant ID', 'Tenant Image', 'Tenant ID Image', 'Tenant Store Number',
                 'Occupant ID', 'Occupant Image', 'Occupant ID Image', 'Occupant Store Number'], axis=1)

    # Create a BytesIO buffer to save the Excel file
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, sheet_name='Search Results')

    # Set the buffer's position to the beginning
    excel_buffer.seek(0)

    # Return the Excel file as a downloadable attachment
    return send_file(
        excel_buffer,
        download_name='search_results.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.route('/export_excel_department', methods=['GET'])
def export_excel_department():
    search_query = session.get('search_query', '')

    if search_query != '':
        # Perform a search query in your database
        conn, cursor = get_stores_db_connection()
        cursor.execute('''
            SELECT * FROM shop
            LEFT JOIN tenant ON shop.store_number = tenant.store_number
            LEFT JOIN occupant ON shop.store_number = occupant.store_number
            WHERE shop.store_number LIKE ? OR shop.store_size LIKE ? OR shop.sector LIKE ? OR shop.business LIKE ?
        ''', ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))
        results = cursor.fetchall()
        conn.close()

    else:
        conn, cursor = get_stores_db_connection()
        cursor.execute('''
            SELECT * FROM shop
            LEFT JOIN tenant ON shop.store_number = tenant.store_number
            LEFT JOIN occupant ON shop.store_number = occupant.store_number
        ''')

        results = cursor.fetchall()
        conn.close()

    # Convert the results to a pandas DataFrame
    df_columns = ['ID', 'Store Number', 'Store Size',
                  'Rent', 'Sector', 'Business', 'Staff', 'Tenant ID', 'Tenant Name', 'Tenant Gender', 'Tenant Phone Number', 'Tenant Date Of Birth', 'Tenant Image', 'Tenant House Number', 'Tenant Store Number', 'Tenant ID Number', 'Tenant ID Image', 'Occupant ID', 'Occupant Name', 'Occupant Gender', 'Occupant Phone Number', 'Occupant Date Of Birth', 'Occupant Image', 'Occupant House Number', 'Occupant Store Number', 'Occupant ID Number', 'Occupant ID Image']
    df = pd.DataFrame(results, columns=df_columns)

    # Drop columns from the DataFrame
    df = df.drop(['Tenant ID', 'Tenant Image', 'Tenant ID Image', 'Tenant Store Number',
                 'Occupant ID', 'Occupant Image', 'Occupant ID Image', 'Occupant Store Number'], axis=1)

    # Create a BytesIO buffer to save the Excel file
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, sheet_name='Search Results')

    # Set the buffer's position to the beginning
    excel_buffer.seek(0)

    # Return the Excel file as a downloadable attachment
    return send_file(
        excel_buffer,
        download_name='search_results.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.route('/export_excel_asset', methods=['GET'])
def export_excel_asset():
    search_query = session.get('search_query', '')

    # Perform a search query in your database
    conn, cursor = get_asset_db_connection()
    cursor.execute('''
            SELECT * FROM asset
            WHERE department LIKE ? OR unit LIKE ? OR device_name LIKE ? OR division LIKE ? OR officer LIKE ?
    ''', ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))
    results = cursor.fetchall()
    conn.close()

    # Convert the results to a pandas DataFrame
    df_columns = ['ID', 'Department', 'Unit',
                  'Device Name', 'Device Brand', 'Device Serial Number', 'Device Embosenuit Number', 'Device Status', 'Division', 'Type Of Toner', 'Capacity', 'Date Purchased', 'Officer Incharge', 'Staff']
    df = pd.DataFrame(results, columns=df_columns)

    # Create a BytesIO buffer to save the Excel file
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, sheet_name='Search Results')

    # Set the buffer's position to the beginning
    excel_buffer.seek(0)

    # Return the Excel file as a downloadable attachment
    return send_file(
        excel_buffer,
        download_name='search_results.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.route('/export_excel_stores', methods=['GET'])
def export_excel_stores():
    search_query = session.get('search_query', '')

    # Perform a search query in your database
    conn, cursor = get_sms_db_connection()
    cursor.execute('''
            SELECT * FROM sms
            WHERE item LIKE ? 
        ''', ('%' + search_query + '%',))
    results = cursor.fetchall()
    conn.close()

    # Convert the results to a pandas DataFrame
    df_columns = ['ID', 'Item Purchased', 'Item S/N',
                  'Quantity', 'Date Purchased', 'Staff']
    df = pd.DataFrame(results, columns=df_columns)

    # Create a BytesIO buffer to save the Excel file
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, sheet_name='Search Results')

    # Set the buffer's position to the beginning
    excel_buffer.seek(0)

    # Return the Excel file as a downloadable attachment
    return send_file(
        excel_buffer,
        download_name='search_results.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=True)
