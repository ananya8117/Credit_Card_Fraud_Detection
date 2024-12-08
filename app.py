from flask import Flask, render_template, request, redirect, url_for
import os
from flask_mysqldb import MySQL

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db_config = {
    'MYSQL_HOST': 'localhost',
    'MYSQL_USER': 'root',
    'MYSQL_PASSWORD': 'babygirl',
    'MYSQL_DB': 'Credit'
}

app.config.update(db_config)
mysql = MySQL(app)
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/form', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            full_name = request.form.get('full_name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            address = request.form.get('address')
            card_number = request.form.get('card_number')
            card_holder = request.form.get('card_holder')
            card_expiry = request.form.get('card_expiry')
            cvv = request.form.get('cvv')

            fraud_result = detect_fraud(filepath)

            cursor = mysql.connection.cursor()
            query = """INSERT INTO History (full_name, email, phone, address, card_number, card_holder, card_expiry, cvv, prediction) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(query, (full_name, email, phone, address, card_number, card_holder, card_expiry, cvv, fraud_result))
            mysql.connection.commit()
            cursor.close()

            return render_template('result.html', fraud=fraud_result)
    return render_template('form.html')

@app.route('/result', methods=['POST'])
def result():
    return render_template('result.html', fraud="Yes") 

@app.route('/history')
def history():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM History")
    transactions = cursor.fetchall()
    cursor.close()

    return render_template('history.html', transactions=transactions)

def detect_fraud(file_path):
    return "Yes"

if __name__ == '__main__':
    app.run(debug=True)