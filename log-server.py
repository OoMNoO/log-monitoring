from flask import Flask, render_template, jsonify
import os

app = Flask(__name__)
LOG_FILE_PATH = './NetworkMon.log'

# Function to parse the log data and return structured data
def parse_logs():
    logs = []
    with open(LOG_FILE_PATH, 'r') as f:
        lines = f.readlines()
        for line in lines:
            try:
                # Extract connection status data from each line
                parts = line.split('Connection status : ')
                if len(parts) > 1:
                    timestamp = parts[0].rsplit('-', 1)[0].strip().rsplit('.', 1)[0].strip()
                    status = parts[1].strip().split('_')
                    packet_loss = int(status[0])
                    min_ping = int(status[1])
                    avg_ping = int(status[2])
                    max_ping = int(status[3])
                    mdev_ping = int(status[4])
                    logs.append({
                        'timestamp': timestamp,
                        'packet_loss': packet_loss,
                        'min_ping': min_ping,
                        'avg_ping': avg_ping,
                        'max_ping': max_ping,
                        'mdev_ping': mdev_ping
                    })
            except:
                continue
    return logs

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logs')
def get_logs():
    logs = parse_logs()[-10:]  # Return the last 10 logs
    return jsonify(logs)

if __name__ == '__main__':
    app.run(debug=True)
