import os
import subprocess
import json
from flask import Flask, render_template, jsonify, request
import threading
from datetime import datetime, timedelta
from collections import defaultdict

app = Flask(__name__)

# Log server variables
LOG_SERVER_PORT = "5000"
LOG_FILE_PATH = '/mnt/D/Projects/log-monitoring/NetworkMon.log'
CACHE_FILE_PATH = './cache'
CACHE_TIMEOUT = 300  # Cache timeout in seconds (5 minutes)

# # Ping test variables
# ThreadTimerInterval = 3.0
# interval= '0.3'
# count='10'
# TestSource= '8.8.8.8'

# def PingTest():
#     PingTest_timer = threading.Timer(ThreadTimerInterval, PingTest)
#     PingTest_timer.daemon = True
#     PingTest_timer.start()
#     CommandOutput, err=subprocess.Popen(["ping", TestSource, "-c", count, "-i", interval], stdout=subprocess.PIPE).communicate()
#     if 'ttl=' in str(CommandOutput):
#         for line in str(CommandOutput).split('\\n'):
#             if line.find('received,') != -1:
#                 PacketLoss= int(line[line.find('received,') + 10 : line.find('% packet loss')])
#             elif line.find('mdev = ') != -1:
#                 NetworkData= line[line.find('mdev = ') + 7 : line.find(' ms')].split('/')
#                 MinPing=int(float(NetworkData[0]))
#                 AvgPing=int(float(NetworkData[1]))
#                 MaxPing=int(float(NetworkData[2]))
#                 MdevPing=int(float(NetworkData[3]))
#                 log=str(PacketLoss) + '_' + str(MinPing) + '_' + str(AvgPing) + '_' + str(MaxPing) + '_' + str(MdevPing)
#     else:
#         log= "TimeOut"
#        
#     subprocess.Popen('echo ' + str(datetime.now()) + ' - ' + TestSource + ' Connection status : ' + log  + ' >> ' + LOG_FILE_PATH, shell= True, env= os.environ)
#     return

# PingTest()

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
                    if status[0] == "TimeOut":
                        packet_loss = 100
                        min_ping = 0
                        avg_ping = 0
                        max_ping = 0
                        mdev_ping = 0
                    else:
                        packet_loss = int(status[0])
                        min_ping = int(status[1])
                        avg_ping = int(status[2])
                        max_ping = int(status[3])
                        mdev_ping = int(status[4])
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
                print(f"Error parsing log line: {e}")
                continue
    return logs

def load_cache(mode):
    """Load the cache from a file."""
    if os.path.exists(f"{CACHE_FILE_PATH}_{mode}.json"):
        with open(f"{CACHE_FILE_PATH}_{mode}.json", 'r') as f:
            return json.load(f)
    return None

def save_cache(mode, data):
    """Save the cache to a file."""
    with open(f"{CACHE_FILE_PATH}_{mode}.json", 'w') as f:
        json.dump(data, f)

def is_cache_valid(cache_time):
    """Check if the cache is valid based on the timeout."""
    return (datetime.now() - datetime.fromtimestamp(cache_time)).total_seconds() < CACHE_TIMEOUT

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

    interval_map = {
        '1hr': 1,
        '3hr': 3,
        '12hr': 12,
        '24hr': 24,
        '72hr': 72
    }

    if mode in interval_map:

        # Load cached data
        cache = load_cache(mode)
        now = datetime.now()
        
        interval_hours = interval_map[mode]
        
        if cache and is_cache_valid(cache['timestamp']):
            print(f"{mode} found in cache")
            return jsonify(cache['data'])
        print(f"{mode} not found in cache")
        relevant_logs = [log for log in logs if datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M:%S') > now - timedelta(hours=interval_hours)]
        
        # Update cache
        if cache is None:
            cache = {}
        cache = {'timestamp': now.timestamp(), 'data': relevant_logs}
        save_cache(mode, cache)
        
        return jsonify(relevant_logs)

    return jsonify([])

if __name__ == '__main__':
    # Run the Flask server
    app.run(host="0.0.0.0", port=LOG_SERVER_PORT, debug=True)

# TODO:
# websocket for realtime
# modes: realtime, 1hr, 6hr, 12hr, 24hr
# remove average
# remove weekly
# responsive