import subprocess
from bs4 import BeautifulSoup
from prometheus_client import start_http_server, Gauge, Counter
from socket import gethostname
import time

# Helper function to convert size strings (e.g., '12MB', '37KB') to bytes
def convert_to_bytes(size_str):
    size_str = size_str.strip().upper()
    if 'KB' in size_str:
        return int(float(size_str.replace('KB', '').strip()) * 1024)
    elif 'MB' in size_str:
        return int(float(size_str.replace('MB', '').strip()) * 1024 * 1024)
    elif 'GB' in size_str:
        return int(float(size_str.replace('GB', '').strip()) * 1024 * 1024 * 1024)
    else:
        return int(size_str)  # Assume bytes if no unit is specified

# Helper function to convert time ranges (e.g., 'Under 1m', '5m', '15m') to seconds
def convert_time_range_to_seconds(time_range):
    time_range = time_range.strip().lower()
    if time_range == 'under 1m':
        return 60
    elif time_range == 'over  1d':
        return 86400
    else:
        # Extract numeric value and unit
        if 'm' in time_range:
            return int(time_range.replace('m', '').strip()) * 60
        elif 'h' in time_range:
            return int(time_range.replace('h', '').strip()) * 3600
        elif 'd' in time_range:
            return int(time_range.replace('d', '').strip()) * 86400
        else:
            return int(time_range)  # Assume seconds if no unit is specified

# Define Prometheus metrics

# Queue metrics
exim_queue_count = Gauge('exim_queue_count', 'Total number of emails in the Exim queue')
exim_email_count = Gauge('exim_email_count', 'Number of emails in the queue per sender', ['email', 'hostname'])

# Grand total summary
messages_received = Gauge('exim_messages_received', 'Total messages received')
messages_delivered = Gauge('exim_messages_delivered', 'Total messages delivered')
messages_rejected = Gauge('exim_messages_rejected', 'Total messages rejected')
volume_received = Gauge('exim_volume_received_bytes', 'Total volume received in bytes')
volume_delivered = Gauge('exim_volume_delivered_bytes', 'Total volume delivered in bytes')

# Deliveries by Transport
transport_volume = Gauge('exim_transport_volume_bytes', 'Volume delivered by transport', ['transport'])
transport_messages = Gauge('exim_transport_messages', 'Messages delivered by transport', ['transport'])

# Messages received per hour
messages_received_per_hour = Gauge('exim_messages_received_per_hour', 'Messages received per hour', ['hour'])

# Deliveries per hour
deliveries_per_hour = Gauge('exim_deliveries_per_hour', 'Deliveries per hour', ['hour'])

# Time spent on the queue: all messages
queue_time_all = Gauge('exim_queue_time_all_messages', 'Time spent on the queue for all messages', ['time_range'])

# Time spent on the queue: messages with at least one remote delivery
queue_time_remote = Gauge('exim_queue_time_remote_messages', 'Time spent on the queue for messages with at least one remote delivery', ['time_range'])

# Relayed messages
relayed_messages = Gauge('exim_relayed_messages', 'Relayed messages', ['from', 'to'])

# Top 50 mail rejection reasons by message count
rejection_reasons = Counter('exim_rejection_reasons', 'Mail rejection reasons by message count', ['reason'])

# Top 50 sending hosts by message count
sending_hosts_message_count = Gauge('exim_sending_hosts_message_count', 'Sending hosts by message count', ['host'])

# Top 50 sending hosts by volume
sending_hosts_volume = Gauge('exim_sending_hosts_volume_bytes', 'Sending hosts by volume', ['host'])

# Top 50 local senders by message count
local_senders_message_count = Gauge('exim_local_senders_message_count', 'Local senders by message count', ['sender'])

# Top 50 local senders by volume
local_senders_volume = Gauge('exim_local_senders_volume_bytes', 'Local senders by volume', ['sender'])

# Top 50 host destinations by message count
host_destinations_message_count = Gauge('exim_host_destinations_message_count', 'Host destinations by message count', ['host'])

# Top 50 host destinations by volume
host_destinations_volume = Gauge('exim_host_destinations_volume_bytes', 'Host destinations by volume', ['host'])

# Top 50 local destinations by message count
local_destinations_message_count = Gauge('exim_local_destinations_message_count', 'Local destinations by message count', ['destination'])

# Top 50 local destinations by volume
local_destinations_volume = Gauge('exim_local_destinations_volume_bytes', 'Local destinations by volume', ['destination'])

# Top 50 rejected ips by message count
rejected_ips_message_count = Counter('exim_rejected_ips_message_count', 'Rejected IPs by message count', ['ip'])


# Function to get the count of emails in the Exim queue
def get_queue_count():
    try:
        result = subprocess.check_output(['exim', '-bpc'], text=True)
        return int(result.strip())
    except Exception as e:
        print(f"Error getting queue count: {e}")
        return 0
    
def get_email_counts():
    try:
        result = subprocess.check_output(['exim', '-bp'], text=True)
        lines = result.strip().split('\n')
        email_counts = {}
        for line in lines:
            parts = line.split()
            if len(parts) > 0 and '@' in parts[-1]:
                email = parts[-1]
                email_counts[email] = email_counts.get(email, 0) + 1
        return email_counts
    except Exception as e:
        print(f"Error getting email counts: {e}")
        return {}


# Exporter update loop
def update_queue_metrics():
    hostname = gethostname()

    # Update the exim_queue_count metric
    queue_count = get_queue_count()
    exim_queue_count.set(queue_count)

    # Update the exim_email_count metric
    email_counts = get_email_counts()
    for email, count in email_counts.items():
        exim_email_count.labels(email=email, hostname=hostname).set(count)



def parse_exim_stats(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Parse Grand Total Summary
    grand_total_table = soup.find('a', {'name': 'Grandtotal'}).find_next('table')
    rows = grand_total_table.find_all('tr')
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) > 0:
            if cols[0].text.strip() == 'Received':
                messages_received.set(int(cols[2].text.strip()))
                volume_received.set(convert_to_bytes(cols[1].text.strip()))
            elif cols[0].text.strip() == 'Delivered':
                messages_delivered.set(int(cols[2].text.strip()))
                volume_delivered.set(convert_to_bytes(cols[1].text.strip()))
            elif cols[0].text.strip() == 'Rejects':
                messages_rejected.set(int(cols[2].text.strip()))

    # Parse Deliveries by Transport
    transport_table = soup.find('a', {'name': 'Transport'}).find_next('table')
    rows = transport_table.find_all('tr')
    
    for row in rows[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) > 0:
            transport = cols[0].text.strip()
            transport_volume.labels(transport).set(convert_to_bytes(cols[1].text.strip()))
            transport_messages.labels(transport).set(int(cols[2].text.strip()))

    # Parse Messages received per hour
    messages_received_table = soup.find('a', {'name': 'Messages received'}).find_next('table')
    rows = messages_received_table.find_all('tr')
    
    for row in rows[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) > 0:
            hour = cols[0].text.strip()
            messages_received_per_hour.labels(hour).set(int(cols[1].text.strip()))

    # Parse Deliveries per hour
    deliveries_table = soup.find('a', {'name': 'Deliveries'}).find_next('table')
    rows = deliveries_table.find_all('tr')
    
    for row in rows[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) > 0:
            hour = cols[0].text.strip()
            deliveries_per_hour.labels(hour).set(int(cols[1].text.strip()))

    # Parse Time spent on the queue: all messages
    queue_time_all_table = soup.find('a', {'name': 'Time spent on the queue all messages'}).find_next('table')
    rows = queue_time_all_table.find_all('tr')
    
    for row in rows[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) > 0:
            time_range = cols[0].text.strip()
            messages = int(cols[1].text.strip())
            queue_time_all.labels(time_range).set(messages)

    # Parse Time spent on the queue: messages with at least one remote delivery
    queue_time_remote_table = soup.find('a', {'name': 'Time spent on the queue messages with at least one remote delivery'}).find_next('table')
    rows = queue_time_remote_table.find_all('tr')
    
    for row in rows[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) > 0:
            time_range = cols[0].text.strip()
            messages = int(cols[1].text.strip())
            queue_time_remote.labels(time_range).set(messages)

    # Parse Relayed messages
    relayed_messages_table = soup.find('a', {'name': 'Relayed messages'}).find_next('table')
    rows = relayed_messages_table.find_all('tr')
    
    # Reset the relayed_messages metric before updating it
    relayed_messages.clear()
    
    for row in rows[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) > 0:
            from_host = cols[1].text.strip()
            to_host = cols[2].text.strip()
            relayed_messages.labels(from_host, to_host).set(int(cols[0].text.strip()))

    # Parse Top 50 mail rejection reasons by message count
    rejection_reasons_table = soup.find('a', {'name': 'Mail rejection reason count'}).find_next('table')
    rows = rejection_reasons_table.find_all('tr')
    
    for row in rows[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) > 0:
            reason = cols[1].text.strip()
            rejection_reasons.labels(reason).inc(int(cols[0].text.strip()))

    # Parse Top 50 sending hosts by message count
    sending_hosts_message_count_table = soup.find('a', {'name': 'Sending host count'}).find_next('table')
    rows = sending_hosts_message_count_table.find_all('tr')
    
    for row in rows[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) > 0:
            host = cols[3].text.strip()
            sending_hosts_message_count.labels(host).set(int(cols[0].text.strip()))

    # Parse Top 50 sending hosts by volume
    sending_hosts_volume_table = soup.find('a', {'name': 'Sending host volume'}).find_next('table')
    rows = sending_hosts_volume_table.find_all('tr')
    
    for row in rows[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) > 0:
            host = cols[3].text.strip()
            sending_hosts_volume.labels(host).set(convert_to_bytes(cols[1].text.strip()))

    # Parse Top 50 local senders by message count
    local_senders_message_count_table = soup.find('a', {'name': 'Local sender count'}).find_next('table')
    rows = local_senders_message_count_table.find_all('tr')
    
    for row in rows[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) > 0:
            sender = cols[3].text.strip()
            local_senders_message_count.labels(sender).set(int(cols[0].text.strip()))

    # Parse Top 50 local senders by volume
    local_senders_volume_table = soup.find('a', {'name': 'Local sender volume'}).find_next('table')
    rows = local_senders_volume_table.find_all('tr')
    
    for row in rows[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) > 0:
            sender = cols[3].text.strip()
            local_senders_volume.labels(sender).set(convert_to_bytes(cols[1].text.strip()))

    # Parse Top 50 host destinations by message count
    host_destinations_message_count_table = soup.find('a', {'name': 'Host destination count'}).find_next('table')
    rows = host_destinations_message_count_table.find_all('tr')
    
    for row in rows[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) > 0:
            host = cols[4].text.strip()
            host_destinations_message_count.labels(host).set(int(cols[0].text.strip()))

    # Parse Top 50 host destinations by volume
    host_destinations_volume_table = soup.find('a', {'name': 'Host destination volume'}).find_next('table')
    rows = host_destinations_volume_table.find_all('tr')
    
    for row in rows[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) > 0:
            host = cols[4].text.strip()
            host_destinations_volume.labels(host).set(convert_to_bytes(cols[2].text.strip()))

    # Parse Top 50 local destinations by message count
    local_destinations_message_count_table = soup.find('a', {'name': 'Local destination count'}).find_next('table')
    rows = local_destinations_message_count_table.find_all('tr')
    
    for row in rows[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) > 0:
            destination = cols[4].text.strip()
            local_destinations_message_count.labels(destination).set(int(cols[0].text.strip()))

    # Parse Top 50 local destinations by volume
    local_destinations_volume_table = soup.find('a', {'name': 'Local destination volume'}).find_next('table')
    rows = local_destinations_volume_table.find_all('tr')
    
    for row in rows[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) > 0:
            destination = cols[4].text.strip()
            local_destinations_volume.labels(destination).set(convert_to_bytes(cols[2].text.strip()))

    # Parse Top 50 rejected ips by message count
    rejected_ips_message_count_table = soup.find('a', {'name': 'Rejected ip count'}).find_next('table')
    rows = rejected_ips_message_count_table.find_all('tr')
    
    for row in rows[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) > 0:
            ip = cols[1].text.strip()
            rejected_ips_message_count.labels(ip).inc(int(cols[0].text.strip()))


def get_exim_stats():
    # Run eximstats command and capture the output
    result = subprocess.run(['eximstats', '-html', '/var/log/exim4/mainlog'], capture_output=True, text=True)
    return result.stdout

def main():
    # Start the Prometheus HTTP server
    start_http_server(8000)
    
    while True:
        # Get the eximstats output
        html_content = get_exim_stats()
        
        # Parse the HTML content and update Prometheus metrics
        parse_exim_stats(html_content)

        # update queue metrics
        update_queue_metrics()
        
        # Wait for a while before updating the metrics again
        time.sleep(60)

if __name__ == '__main__':
    main()
