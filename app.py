from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, date
from pathlib import Path
from typing import Any

from flask import Flask, g, redirect, render_template, request, url_for, flash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'crm.db'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key'


# -----------------------------
# Database helpers
# -----------------------------
def get_db() -> sqlite3.Connection:
    if 'db' not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(_error: Exception | None) -> None:
    db = g.pop('db', None)
    if db is not None:
        db.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    business_name TEXT NOT NULL DEFAULT 'The Carpet Cleaning Company',
    phone TEXT NOT NULL DEFAULT '07802 563213',
    email TEXT NOT NULL DEFAULT 'info@example.com',
    website TEXT NOT NULL DEFAULT 'www.example.com',
    address TEXT NOT NULL DEFAULT 'Ludlow, Shropshire'
);

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    address1 TEXT,
    town TEXT,
    postcode TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    service_type TEXT NOT NULL,
    job_date TEXT NOT NULL,
    job_time TEXT,
    status TEXT NOT NULL DEFAULT 'Booked',
    rooms TEXT,
    total_price REAL NOT NULL DEFAULT 0,
    deposit REAL NOT NULL DEFAULT 0,
    balance_due REAL NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    quote_date TEXT NOT NULL,
    valid_until TEXT,
    status TEXT NOT NULL DEFAULT 'Open',
    description TEXT,
    amount REAL NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    job_id INTEGER,
    invoice_date TEXT NOT NULL,
    due_date TEXT,
    status TEXT NOT NULL DEFAULT 'Unpaid',
    description TEXT,
    amount REAL NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
"""


def init_db() -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.executescript(SCHEMA)
        conn.execute(
            """
            INSERT INTO settings (id, business_name, phone, email, website, address)
            VALUES (1, 'The Carpet Cleaning Company', '07802 563213', 'info@example.com', 'www.thecarpetcleaningcrew.co.uk', 'Ludlow, Shropshire')
            ON CONFLICT(id) DO NOTHING
            """
        )
        conn.commit()


# -----------------------------
# Utility helpers
# -----------------------------
def query_all(sql: str, params: tuple[Any, ...] = ()):
    return get_db().execute(sql, params).fetchall()


def query_one(sql: str, params: tuple[Any, ...] = ()):
    return get_db().execute(sql, params).fetchone()


def execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    db = get_db()
    cur = db.execute(sql, params)
    db.commit()
    return cur.lastrowid


def get_settings():
    return query_one('SELECT * FROM settings WHERE id = 1')


def customer_options():
    return query_all('SELECT id, name, town FROM customers ORDER BY name')


def job_options():
    return query_all('''
        SELECT jobs.id, customers.name, jobs.service_type, jobs.job_date
        FROM jobs
        JOIN customers ON customers.id = jobs.customer_id
        ORDER BY jobs.job_date DESC
    ''')


@app.context_processor
def inject_globals():
    return {
        'today': date.today().isoformat(),
        'business': get_settings(),
    }


# -----------------------------
# Routes
# -----------------------------
@app.route('/')
def dashboard():
    stats = {
        'customers': query_one('SELECT COUNT(*) AS c FROM customers')['c'],
        'jobs': query_one('SELECT COUNT(*) AS c FROM jobs')['c'],
        'quotes_open': query_one("SELECT COUNT(*) AS c FROM quotes WHERE status = 'Open'")['c'],
        'invoices_unpaid': query_one("SELECT COUNT(*) AS c FROM invoices WHERE status != 'Paid'")['c'],
        'revenue': query_one("SELECT COALESCE(SUM(amount), 0) AS total FROM invoices WHERE status = 'Paid'")['total'],
    }

    upcoming_jobs = query_all('''
        SELECT jobs.*, customers.name AS customer_name, customers.town, customers.phone
        FROM jobs
        JOIN customers ON customers.id = jobs.customer_id
        ORDER BY jobs.job_date ASC, COALESCE(jobs.job_time, '') ASC
        LIMIT 8
    ''')

    recent_customers = query_all('SELECT * FROM customers ORDER BY created_at DESC LIMIT 5')
    recent_quotes = query_all('''
        SELECT quotes.*, customers.name AS customer_name
        FROM quotes JOIN customers ON customers.id = quotes.customer_id
        ORDER BY quotes.created_at DESC LIMIT 5
    ''')
    return render_template('dashboard.html', stats=stats, upcoming_jobs=upcoming_jobs, recent_customers=recent_customers, recent_quotes=recent_quotes)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        execute(
            '''UPDATE settings SET business_name=?, phone=?, email=?, website=?, address=? WHERE id=1''',
            (
                request.form['business_name'],
                request.form['phone'],
                request.form['email'],
                request.form['website'],
                request.form['address'],
            ),
        )
        flash('Business settings updated.')
        return redirect(url_for('settings'))
    return render_template('settings.html', settings=get_settings())


@app.route('/customers')
def customers():
    q = request.args.get('q', '').strip()
    if q:
        items = query_all(
            '''
            SELECT * FROM customers
            WHERE name LIKE ? OR phone LIKE ? OR email LIKE ? OR town LIKE ? OR postcode LIKE ?
            ORDER BY name
            ''',
            tuple(f'%{q}%' for _ in range(5)),
        )
    else:
        items = query_all('SELECT * FROM customers ORDER BY name')
    return render_template('customers.html', customers=items, q=q)


@app.route('/customers/new', methods=['GET', 'POST'])
def new_customer():
    if request.method == 'POST':
        execute(
            '''INSERT INTO customers (name, phone, email, address1, town, postcode, notes) VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (
                request.form['name'],
                request.form.get('phone', ''),
                request.form.get('email', ''),
                request.form.get('address1', ''),
                request.form.get('town', ''),
                request.form.get('postcode', ''),
                request.form.get('notes', ''),
            ),
        )
        flash('Customer added.')
        return redirect(url_for('customers'))
    return render_template('customer_form.html', customer=None)


@app.route('/customers/<int:customer_id>/edit', methods=['GET', 'POST'])
def edit_customer(customer_id: int):
    customer = query_one('SELECT * FROM customers WHERE id = ?', (customer_id,))
    if not customer:
        return redirect(url_for('customers'))
    if request.method == 'POST':
        execute(
            '''UPDATE customers SET name=?, phone=?, email=?, address1=?, town=?, postcode=?, notes=? WHERE id=?''',
            (
                request.form['name'],
                request.form.get('phone', ''),
                request.form.get('email', ''),
                request.form.get('address1', ''),
                request.form.get('town', ''),
                request.form.get('postcode', ''),
                request.form.get('notes', ''),
                customer_id,
            ),
        )
        flash('Customer updated.')
        return redirect(url_for('customers'))
    return render_template('customer_form.html', customer=customer)


@app.route('/customers/<int:customer_id>/delete', methods=['POST'])
def delete_customer(customer_id: int):
    execute('DELETE FROM customers WHERE id = ?', (customer_id,))
    flash('Customer deleted.')
    return redirect(url_for('customers'))


@app.route('/jobs')
def jobs():
    items = query_all('''
        SELECT jobs.*, customers.name AS customer_name, customers.town, customers.phone
        FROM jobs
        JOIN customers ON customers.id = jobs.customer_id
        ORDER BY jobs.job_date DESC, COALESCE(jobs.job_time, '') DESC
    ''')
    return render_template('jobs.html', jobs=items)


@app.route('/jobs/new', methods=['GET', 'POST'])
def new_job():
    if request.method == 'POST':
        total = float(request.form.get('total_price') or 0)
        deposit = float(request.form.get('deposit') or 0)
        balance = total - deposit
        execute(
            '''INSERT INTO jobs (customer_id, service_type, job_date, job_time, status, rooms, total_price, deposit, balance_due, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                request.form['customer_id'],
                request.form['service_type'],
                request.form['job_date'],
                request.form.get('job_time', ''),
                request.form['status'],
                request.form.get('rooms', ''),
                total,
                deposit,
                balance,
                request.form.get('notes', ''),
            ),
        )
        flash('Job created.')
        return redirect(url_for('jobs'))
    return render_template('job_form.html', job=None, customers=customer_options())


@app.route('/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
def edit_job(job_id: int):
    job = query_one('SELECT * FROM jobs WHERE id = ?', (job_id,))
    if not job:
        return redirect(url_for('jobs'))
    if request.method == 'POST':
        total = float(request.form.get('total_price') or 0)
        deposit = float(request.form.get('deposit') or 0)
        balance = total - deposit
        execute(
            '''UPDATE jobs SET customer_id=?, service_type=?, job_date=?, job_time=?, status=?, rooms=?, total_price=?, deposit=?, balance_due=?, notes=? WHERE id=?''',
            (
                request.form['customer_id'],
                request.form['service_type'],
                request.form['job_date'],
                request.form.get('job_time', ''),
                request.form['status'],
                request.form.get('rooms', ''),
                total,
                deposit,
                balance,
                request.form.get('notes', ''),
                job_id,
            ),
        )
        flash('Job updated.')
        return redirect(url_for('jobs'))
    return render_template('job_form.html', job=job, customers=customer_options())


@app.route('/jobs/<int:job_id>/delete', methods=['POST'])
def delete_job(job_id: int):
    execute('DELETE FROM jobs WHERE id = ?', (job_id,))
    flash('Job deleted.')
    return redirect(url_for('jobs'))


@app.route('/quotes')
def quotes():
    items = query_all('''
        SELECT quotes.*, customers.name AS customer_name, customers.town
        FROM quotes
        JOIN customers ON customers.id = quotes.customer_id
        ORDER BY quotes.quote_date DESC
    ''')
    return render_template('quotes.html', quotes=items)


@app.route('/quotes/new', methods=['GET', 'POST'])
def new_quote():
    if request.method == 'POST':
        execute(
            '''INSERT INTO quotes (customer_id, quote_date, valid_until, status, description, amount, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (
                request.form['customer_id'],
                request.form['quote_date'],
                request.form.get('valid_until', ''),
                request.form['status'],
                request.form.get('description', ''),
                float(request.form.get('amount') or 0),
                request.form.get('notes', ''),
            ),
        )
        flash('Quote created.')
        return redirect(url_for('quotes'))
    return render_template('quote_form.html', quote=None, customers=customer_options())


@app.route('/quotes/<int:quote_id>/edit', methods=['GET', 'POST'])
def edit_quote(quote_id: int):
    quote = query_one('SELECT * FROM quotes WHERE id = ?', (quote_id,))
    if not quote:
        return redirect(url_for('quotes'))
    if request.method == 'POST':
        execute(
            '''UPDATE quotes SET customer_id=?, quote_date=?, valid_until=?, status=?, description=?, amount=?, notes=? WHERE id=?''',
            (
                request.form['customer_id'],
                request.form['quote_date'],
                request.form.get('valid_until', ''),
                request.form['status'],
                request.form.get('description', ''),
                float(request.form.get('amount') or 0),
                request.form.get('notes', ''),
                quote_id,
            ),
        )
        flash('Quote updated.')
        return redirect(url_for('quotes'))
    return render_template('quote_form.html', quote=quote, customers=customer_options())


@app.route('/quotes/<int:quote_id>/delete', methods=['POST'])
def delete_quote(quote_id: int):
    execute('DELETE FROM quotes WHERE id = ?', (quote_id,))
    flash('Quote deleted.')
    return redirect(url_for('quotes'))


@app.route('/quotes/<int:quote_id>/view')
def view_quote(quote_id: int):
    quote = query_one('''
        SELECT quotes.*, customers.name AS customer_name, customers.address1, customers.town, customers.postcode, customers.phone, customers.email
        FROM quotes
        JOIN customers ON customers.id = quotes.customer_id
        WHERE quotes.id = ?
    ''', (quote_id,))
    return render_template('quote_view.html', quote=quote)


@app.route('/invoices')
def invoices():
    items = query_all('''
        SELECT invoices.*, customers.name AS customer_name, jobs.service_type
        FROM invoices
        JOIN customers ON customers.id = invoices.customer_id
        LEFT JOIN jobs ON jobs.id = invoices.job_id
        ORDER BY invoices.invoice_date DESC
    ''')
    return render_template('invoices.html', invoices=items)


@app.route('/invoices/new', methods=['GET', 'POST'])
def new_invoice():
    if request.method == 'POST':
        execute(
            '''INSERT INTO invoices (customer_id, job_id, invoice_date, due_date, status, description, amount, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                request.form['customer_id'],
                request.form.get('job_id') or None,
                request.form['invoice_date'],
                request.form.get('due_date', ''),
                request.form['status'],
                request.form.get('description', ''),
                float(request.form.get('amount') or 0),
                request.form.get('notes', ''),
            ),
        )
        flash('Invoice created.')
        return redirect(url_for('invoices'))
    return render_template('invoice_form.html', invoice=None, customers=customer_options(), jobs=job_options())


@app.route('/invoices/<int:invoice_id>/edit', methods=['GET', 'POST'])
def edit_invoice(invoice_id: int):
    invoice = query_one('SELECT * FROM invoices WHERE id = ?', (invoice_id,))
    if not invoice:
        return redirect(url_for('invoices'))
    if request.method == 'POST':
        execute(
            '''UPDATE invoices SET customer_id=?, job_id=?, invoice_date=?, due_date=?, status=?, description=?, amount=?, notes=? WHERE id=?''',
            (
                request.form['customer_id'],
                request.form.get('job_id') or None,
                request.form['invoice_date'],
                request.form.get('due_date', ''),
                request.form['status'],
                request.form.get('description', ''),
                float(request.form.get('amount') or 0),
                request.form.get('notes', ''),
                invoice_id,
            ),
        )
        flash('Invoice updated.')
        return redirect(url_for('invoices'))
    return render_template('invoice_form.html', invoice=invoice, customers=customer_options(), jobs=job_options())


@app.route('/invoices/<int:invoice_id>/delete', methods=['POST'])
def delete_invoice(invoice_id: int):
    execute('DELETE FROM invoices WHERE id = ?', (invoice_id,))
    flash('Invoice deleted.')
    return redirect(url_for('invoices'))


@app.route('/invoices/<int:invoice_id>/view')
def view_invoice(invoice_id: int):
    invoice = query_one('''
        SELECT invoices.*, customers.name AS customer_name, customers.address1, customers.town, customers.postcode, customers.phone, customers.email,
               jobs.service_type, jobs.job_date
        FROM invoices
        JOIN customers ON customers.id = invoices.customer_id
        LEFT JOIN jobs ON jobs.id = invoices.job_id
        WHERE invoices.id = ?
    ''', (invoice_id,))
    return render_template('invoice_view.html', invoice=invoice)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
