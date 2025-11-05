"""
Resource Monitoring Script

Monitors CPU, memory, and network during performance tests.
"""

import psutil
import time
import csv
from datetime import datetime
from pathlib import Path


def monitor_resources(duration_seconds=300, interval=1):
    """
    Monitor system resources.
    
    Args:
        duration_seconds: How long to monitor
        interval: Sampling interval in seconds
    """
    print(f"Monitoring resources for {duration_seconds} seconds...")
    
    # Create results directory
    Path("performance/results").mkdir(parents=True, exist_ok=True)
    
    # Output file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"performance/results/resources_{timestamp}.csv"
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'timestamp',
            'cpu_percent',
            'memory_percent',
            'memory_mb',
            'disk_read_mb',
            'disk_write_mb',
            'network_sent_mb',
            'network_recv_mb'
        ])
        
        start_time = time.time()
        disk_io_start = psutil.disk_io_counters()
        net_io_start = psutil.net_io_counters()
        
        while time.time() - start_time < duration_seconds:
            # Get current stats
            cpu = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            net_io = psutil.net_io_counters()
            
            # Calculate deltas
            disk_read_mb = (disk_io.read_bytes - disk_io_start.read_bytes) / 1024 / 1024
            disk_write_mb = (disk_io.write_bytes - disk_io_start.write_bytes) / 1024 / 1024
            net_sent_mb = (net_io.bytes_sent - net_io_start.bytes_sent) / 1024 / 1024
            net_recv_mb = (net_io.bytes_recv - net_io_start.bytes_recv) / 1024 / 1024
            
            # Write row
            writer.writerow([
                datetime.now().isoformat(),
                cpu,
                memory.percent,
                memory.used / 1024 / 1024,
                disk_read_mb,
                disk_write_mb,
                net_sent_mb,
                net_recv_mb
            ])
            
            # Print current stats
            print(f"CPU: {cpu:5.1f}% | Memory: {memory.percent:5.1f}% | "
                  f"Disk R/W: {disk_read_mb:6.1f}/{disk_write_mb:6.1f} MB | "
                  f"Net S/R: {net_sent_mb:6.1f}/{net_recv_mb:6.1f} MB", end='\r')
            
            time.sleep(interval)
    
    print(f"\nResource monitoring complete. Results saved to {output_file}")


if __name__ == "__main__":
    import sys
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    monitor_resources(duration)
