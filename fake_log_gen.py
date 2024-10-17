from datetime import datetime, timedelta
import random

# Function to generate log data
def generate_log_data(filename):
    start_time = datetime.now() - timedelta(days=7)  # Start from 7 days ago
    logs = []

    for _ in range(7 * 24 * 60 * 20):  # 7 days * 24 hours * 20 logs per hour
        log_time = start_time.strftime('%Y-%m-%d %H:%M:%S.%f')
        ip_address = "8.8.8.8"  # Example IP address
        status = "_".join(str(random.randint(0, 255)) for _ in range(5))  # Random status
        log_entry = f"{log_time} - {ip_address} Connection status : {status}"
        logs.append(log_entry)
        start_time += timedelta(seconds=3)  # Increment time by 3 seconds

    # Write to log file
    with open(filename, 'w') as f:
        f.write("\n".join(logs))

# Generate the log data
generate_log_data('NetworkMon.log')
