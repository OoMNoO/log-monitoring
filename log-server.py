import os
import subprocess
import json
from flask import Flask, render_template, jsonify, request
import threading
from datetime import datetime, timedelta

app = Flask(__name__)

# Server settings
LOG_SERVER_PORT = "5000"  # Port for the Flask server
LOG_FILE_PATH = '/mnt/D/Projects/log-monitoring/NetworkMon.log'  # Path to the log file
CACHE_FILE_PATH = './cache'  # Path to store cached data
CACHE_TIMEOUT = 300  # Cache timeout in seconds (5 minutes)

# Define the hour intervals for different modes
interval_map = {
    '1hr': 1,
    '3hr': 3,
    '12hr': 12,
    '24hr': 24,
    '72hr': 72
}

# Function to parse the log data from the log file
def parse_logs():
    """
    Reads the log file and extracts timestamp, packet loss, and ping information
    into a structured format.
    """
    logs = []
    with open(LOG_FILE_PATH, 'r') as f:
        lines = f.readlines()  # Read all lines from the log file
        for line in lines:
            try:
                # Split line based on 'Connection status : ' to separate timestamp and status
                parts = line.split('Connection status : ')
                if len(parts) > 1:
                    timestamp = parts[0].rsplit('-', 1)[0].strip().rsplit('.', 1)[0].strip()  # Extract timestamp
                    status = parts[1].strip().split('_')  # Split the status information
                    if status[0] == "TimeOut":
                        # If there is a timeout, set default values
                        packet_loss = 100
                        min_ping = 0
                        avg_ping = 0
                        max_ping = 0
                        mdev_ping = 0
                    else:
                        # Extract packet loss and ping statistics
                        packet_loss = int(status[0]) if int(status[0]) < 100 else 100
                        min_ping = int(status[1]) if int(status[1]) < 1000 else 1000
                        avg_ping = int(status[2]) if int(status[2]) < 1000 else 1000
                        max_ping = int(status[3]) if int(status[3]) < 1000 else 1000
                        mdev_ping = int(status[4]) if int(status[4]) < 1000 else 1000
                    
                    # Append the structured log entry to the logs list
                    logs.append({
                        'timestamp': timestamp,
                        'date': timestamp.split(" ")[0],
                        'time': timestamp.split(" ")[1],
                        'packet_loss': packet_loss,
                        'min_ping': min_ping,
                        'avg_ping': avg_ping,
                        'max_ping': max_ping,
                        'mdev_ping': mdev_ping
                    })
            except Exception as e:
                # Handle any parsing errors and continue processing the next log line
                print(f"Error parsing log line: {e}")
                continue
    return logs  # Return the list of parsed logs

# Cache functions to store and retrieve log data for different modes
def load_cache(mode):
    """
    Load cached log data for a specific mode from a file, if it exists.
    """
    if os.path.exists(f"{CACHE_FILE_PATH}_{mode}.json"):
        with open(f"{CACHE_FILE_PATH}_{mode}.json", 'r') as f:
            return json.load(f)
    return None

def save_cache(mode, data):
    """
    Save log data to a cache file for a specific mode.
    """
    with open(f"{CACHE_FILE_PATH}_{mode}.json", 'w') as f:
        json.dump(data, f)

def is_cache_valid(cache_time):
    """
    Check if the cached data is still valid by comparing the cache timestamp with the current time.
    """
    return (datetime.now() - datetime.fromtimestamp(cache_time)).total_seconds() < CACHE_TIMEOUT

def update_cache():
    """
    Updates the cache for all defined modes in the background.
    This function runs at intervals defined by CACHE_TIMEOUT.
    """
    
    print("Updating cache for all modes...\nit can take some time, please wait")
    
    # Schedule the next cache update
    UpdateCache_timer = threading.Timer(CACHE_TIMEOUT, update_cache)
    UpdateCache_timer.daemon = True
    UpdateCache_timer.start()
    
    logs = parse_logs()  # Parse logs from the log file

    now = datetime.now()

    # Update cache for each mode
    for mode, interval_hours in interval_map.items():
        print(f"-------------------------\nUpdating {mode} mode cache\n-------------------------")
        relevant_logs = [log for log in logs if datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M:%S') > now - timedelta(hours=interval_hours)]
        save_cache(mode, {'timestamp': now.timestamp(), 'data': relevant_logs})
    return

@app.route('/')
def index():
    """
    Render the main HTML page for the log monitoring system.
    """
    return render_template('index.html')

@app.route('/logs')
def get_logs():
    """
    Endpoint to retrieve logs based on the requested mode. 
    Modes supported: realtime, 1hr, 3hr, 12hr, 24hr, 72hr.
    - 'realtime': Returns the last 100 logs.
    - Other modes: Returns logs from the past 1, 3, 12, 24, or 72 hours, potentially using cached data.
    """
    mode = request.args.get('mode', 'realtime')  # Get mode from request (default: realtime)
    logs = parse_logs()  # Parse all logs from the file

    # Handle 'realtime' mode by returning the last 100 logs
    if mode == 'realtime':
        return jsonify(logs[-100:])

    # Handle historical modes (1hr, 3hr, 12hr, 24hr, 72hr)
    if mode in interval_map:
        cache = load_cache(mode)  # Load cached data for the mode
        return jsonify(cache['data'])

    # If mode is not recognized, return an empty list
    return jsonify([])

if __name__ == '__main__':
    
    # Start the background cache updater
    update_cache()
    
    # Start the Flask server as Development with no reloader to prevent file write issues
    app.run(host="0.0.0.0", port=LOG_SERVER_PORT, debug=True, use_reloader=False)
