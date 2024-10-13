from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
from collections import defaultdict

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

# Function to parse the log data for 24 hours format
def parse_24_hours_logs(logs):
    hourly_data = defaultdict(lambda: {
        'packet_loss': 0,
        'min_ping': float('inf'),
        'avg_ping': 0,
        'max_ping': float('-inf'),
        'count': 0
    })

    for log in logs:
        timestamp = log['timestamp']
        packet_loss = log['packet_loss']
        min_ping = log['min_ping']
        avg_ping = log['avg_ping']
        max_ping = log['max_ping']

        # Get the hour key (timestamp without minutes and seconds)
        hour_key = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').replace(minute=0, second=0, microsecond=0)

        # Aggregate the data
        hourly_data[hour_key]['packet_loss'] += packet_loss
        hourly_data[hour_key]['min_ping'] = min(hourly_data[hour_key]['min_ping'], min_ping)
        hourly_data[hour_key]['avg_ping'] += avg_ping  # Sum for averaging later
        hourly_data[hour_key]['max_ping'] = max(hourly_data[hour_key]['max_ping'], max_ping)
        hourly_data[hour_key]['count'] += 1

    # Prepare the final averaged log data
    parsed_logs = []
    for hour_key, values in hourly_data.items():
        if values['count'] > 0:
            parsed_logs.append({
                'timestamp': hour_key.strftime('%Y-%m-%d %H:%M:%S'),
                'packet_loss': values['packet_loss'] / values['count'],
                'min_ping': values['min_ping'],
                'avg_ping': values['avg_ping'] / values['count'],  # Calculate average
                'max_ping': values['max_ping'],
                'mdev_ping': None  # You can handle this as needed
            })

    return parsed_logs

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logs')
def get_logs():
    mode = request.args.get('mode', 'realtime')
    logs = parse_logs()

    # Real-time: Return the last 100 logs
    if mode == 'realtime':
        return jsonify(logs[-100:])

    # Daily: Return logs from the last 24 hours
    elif mode == 'daily':
        now = datetime.now()
        last_24_hours = [log for log in logs if datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M:%S') > now - timedelta(days=1)]
        parsed_last_24_hours = parse_24_hours_logs(last_24_hours)
        return jsonify(parsed_last_24_hours)

    # Weekly: Return logs from the last 7 days
    elif mode == 'weekly':
        now = datetime.now()
        last_7_days = [log for log in logs if datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M:%S') > now - timedelta(days=7)]
        return jsonify(last_7_days)

    return jsonify([])

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
