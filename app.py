from flask import Flask, render_template, request, redirect, url_for
import os
from flask_mysqldb import MySQL
import pandas as pd
import numpy as np
import joblib

app = Flask(__name__)

model = joblib.load('fraud_detection.pkl')

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

            fraud_result = detect_fraud(filepath, model)

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

def detect_fraud(file_path, model):
    try:
        data = pd.read_csv(file_path)
        data.columns = data.columns.str.strip() 
        if data.shape[1] > 31:
            data = data.iloc[:, :31]  

        print("Columns after cleaning:", data.columns.tolist())
        if 'Class' not in data.columns:
            return "Target column 'Class' not found."
        features = data.drop(columns=['Class'])
        features = features.apply(pd.to_numeric, errors='coerce').dropna()

        if features.shape[1] != 30:
            return f"Expected 28 numeric feature columns, but found {features.shape[1]}."

        if 'Time' not in features.columns:
            return "Feature 'Time' is missing from input data."

        predictions = model.predict(features)
        fraud_count = np.sum(predictions)

    except Exception as e:
        return f"Error during processing: {e}"

    return "Fraud" if fraud_count > 0 else "Valid"


if __name__ == '__main__':
    app.run(debug=True)