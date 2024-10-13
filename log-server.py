from flask import Flask, render_template, jsonify
import os

app = Flask(__name__)
LOG_FILE_PATH = './NetworkMon.log'

# Read the last N lines of the log file
def tail_log(n=10):
    with open(LOG_FILE_PATH, 'r') as f:
        lines = f.readlines()
    return lines[-n:]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logs')
def get_logs():
    logs = tail_log()  # Fetch the last N lines from the log
    return jsonify(logs)

if __name__ == '__main__':
    app.run(debug=True)
