# Exim Metrics Exporter

This project is a Prometheus exporter designed to collect and expose various metrics related to Exim, a popular mail transfer agent (MTA). The exporter collects data on the Exim queue, mail delivery, message rejection, and other mail-related statistics, then exposes these metrics for Prometheus monitoring.

## Metrics

Here is a summary of the metrics exposed by this exporter:

### Queue Metrics
- **exim_queue_count**: Total number of emails in the Exim queue (Gauge).
- **exim_queue_email_count**: Number of emails in the queue per sender, labeled by email and hostname (Counter).

### Grand Total Summary
- **exim_messages_received**: Total number of messages received by Exim (Gauge).
- **exim_messages_delivered**: Total number of messages delivered by Exim (Gauge).
- **exim_messages_rejected**: Total number of messages rejected by Exim (Gauge).
- **exim_volume_received_bytes**: Total volume of messages received by Exim, in bytes (Gauge).
- **exim_volume_delivered_bytes**: Total volume of messages delivered by Exim, in bytes (Gauge).

### Deliveries by Transport
- **exim_transport_volume_bytes**: Volume delivered by each transport, labeled by transport type (Gauge).
- **exim_transport_messages**: Messages delivered by each transport, labeled by transport type (Gauge).

### Per Hour Metrics
- **exim_messages_received_per_hour**: Messages received per hour, labeled by hour (Gauge).
- **exim_deliveries_per_hour**: Deliveries per hour, labeled by hour (Gauge).

### Queue Time Metrics
- **exim_queue_time_all_messages**: Time spent on the queue for all messages, labeled by time range (Gauge).
- **exim_queue_time_remote_messages**: Time spent on the queue for messages with at least one remote delivery, labeled by time range (Gauge).

### Relayed Messages
- **exim_relayed_messages**: Relayed messages, labeled by source host, source email, destination host, and destination email (Counter).

### Rejection Reasons
- **exim_rejection_reasons**: Mail rejection reasons by message count, labeled by reason (Counter).

### Top 50 Hosts and Senders
- **exim_sending_hosts_message_count**: Number of messages sent by each host, labeled by host (Gauge).
- **exim_sending_hosts_volume_bytes**: Volume of messages sent by each host, in bytes, labeled by host (Gauge).
- **exim_local_senders_message_count**: Number of messages sent by local senders, labeled by sender (Gauge).
- **exim_local_senders_volume_bytes**: Volume of messages sent by local senders, in bytes, labeled by sender (Gauge).
- **exim_host_destinations_message_count**: Number of messages received by each destination host, labeled by host (Counter).
- **exim_host_destinations_volume_bytes**: Volume of messages received by each destination host, in bytes, labeled by host (Gauge).
- **exim_local_destinations_message_count**: Number of messages received by each local destination, labeled by destination (Gauge).
- **exim_local_destinations_volume_bytes**: Volume of messages received by each local destination, in bytes, labeled by destination (Gauge).

### Rejected IPs
- **exim_rejected_ips_message_count**: Number of messages rejected by IP, labeled by IP address (Counter).

## How to Install

### Prerequisites
- Python 3.7 or later
- Prometheus installed for metric scraping
- Exim installed and configured on the host machine

### Steps to Install

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/exim-metrics-exporter.git
   cd exim-metrics-exporter
2. **Install the required Python packages You can install the dependencies using pip:**
   ```bash
   pip install -r requirements.txt
3. **Run the exporter** Run the exporter script to start collecting and exposing metrics:
4.   ```bash
     python exim_metrics_exporter.py

## Configuration
The exporter uses the exim and eximstats commands, which should be available on the system. Ensure that these commands are accessible and correctly configured.
Exim Configuration

You will need to ensure that the following Exim commands are available and accessible:

    exim -bpc to get the queue count.
    exim -bp to get a list of messages in the queue.
    eximstats -html to generate HTML-based statistics output.

Make sure Exim is installed and properly configured for your system.
Prometheus Configuration

To scrape metrics from the exporter, you need to add the following job to your Prometheus configuration file (prometheus.yml):
```bash
scrape_configs:
  - job_name: 'exim'
    static_configs:
      - targets: ['<EXIM_EXPORTER_HOST>:9103']
```

## Metrics Update

The exporter will update the metrics every minute. The metrics are updated based on the output from Exim commands, parsed HTML statistics, and the queue status. Make sure your Exim server is actively processing emails to get accurate and up-to-date metrics.
