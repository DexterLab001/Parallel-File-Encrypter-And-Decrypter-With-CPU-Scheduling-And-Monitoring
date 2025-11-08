import psutil
import threading
import time
from typing import Dict, List, Any

class SystemMonitor:
    """Real-time system monitoring for CPU, memory, and process information"""
    
    def __init__(self):
        self._stop_flag = threading.Event()
        self._monitoring_data = []
        
    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_per_core = psutil.cpu_percent(percpu=True, interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used
            memory_total = memory.total
            
            # Process information
            current_process = psutil.Process()
            process_cpu = current_process.cpu_percent()
            process_memory = current_process.memory_info()
            
            # Thread count
            active_threads = threading.active_count()
            
            # Disk I/O (if available)
            disk_io = psutil.disk_io_counters()
            
            # Network I/O (if available)
            network_io = psutil.net_io_counters()
            
            stats = {
                'timestamp': time.time(),
                'cpu_percent': cpu_percent,
                'cpu_per_core': cpu_per_core,
                'memory_percent': memory_percent,
                'memory_used': memory_used,
                'memory_total': memory_total,
                'process_cpu_percent': process_cpu,
                'process_memory_rss': process_memory.rss,
                'process_memory_vms': process_memory.vms,
                'active_threads': active_threads
            }
            
            # Add disk I/O if available
            if disk_io:
                stats.update({
                    'disk_read_bytes': disk_io.read_bytes,
                    'disk_write_bytes': disk_io.write_bytes,
                    'disk_read_count': disk_io.read_count,
                    'disk_write_count': disk_io.write_count
                })
            
            # Add network I/O if available
            if network_io:
                stats.update({
                    'network_bytes_sent': network_io.bytes_sent,
                    'network_bytes_recv': network_io.bytes_recv,
                    'network_packets_sent': network_io.packets_sent,
                    'network_packets_recv': network_io.packets_recv
                })
            
            return stats
            
        except Exception as e:
            # Return minimal stats if there's an error
            return {
                'timestamp': time.time(),
                'cpu_percent': 0.0,
                'cpu_per_core': [],
                'memory_percent': 0.0,
                'memory_used': 0,
                'memory_total': 0,
                'process_cpu_percent': 0.0,
                'process_memory_rss': 0,
                'process_memory_vms': 0,
                'active_threads': threading.active_count(),
                'error': str(e)
            }
    
    def start_monitoring(self, interval: float = 0.5) -> threading.Thread:
        """Start continuous monitoring in a separate thread"""
        def monitor_loop():
            while not self._stop_flag.is_set():
                stats = self.get_system_stats()
                self._monitoring_data.append(stats)
                time.sleep(interval)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        return monitor_thread
    
    def stop(self):
        """Stop monitoring"""
        self._stop_flag.set()
    
    def should_stop(self) -> bool:
        """Check if monitoring should stop"""
        return self._stop_flag.is_set()
    
    def get_monitoring_data(self) -> List[Dict[str, Any]]:
        """Get collected monitoring data"""
        return self._monitoring_data.copy()
    
    def clear_data(self):
        """Clear collected monitoring data"""
        self._monitoring_data.clear()
    
    def get_process_info(self, pid: int = None) -> Dict[str, Any]:
        """Get detailed information about a specific process"""
        try:
            if pid is None:
                process = psutil.Process()
            else:
                process = psutil.Process(pid)
            
            return {
                'pid': process.pid,
                'name': process.name(),
                'status': process.status(),
                'cpu_percent': process.cpu_percent(),
                'memory_info': process.memory_info()._asdict(),
                'memory_percent': process.memory_percent(),
                'num_threads': process.num_threads(),
                'create_time': process.create_time(),
                'cmdline': process.cmdline() if hasattr(process, 'cmdline') else []
            }
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            return {'error': str(e)}
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get general system information"""
        try:
            cpu_count_logical = psutil.cpu_count(logical=True)
            cpu_count_physical = psutil.cpu_count(logical=False)
            
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            boot_time = psutil.boot_time()
            
            # CPU frequency
            cpu_freq = psutil.cpu_freq()
            
            return {
                'cpu_count_logical': cpu_count_logical,
                'cpu_count_physical': cpu_count_physical,
                'cpu_freq_current': cpu_freq.current if cpu_freq else None,
                'cpu_freq_min': cpu_freq.min if cpu_freq else None,
                'cpu_freq_max': cpu_freq.max if cpu_freq else None,
                'memory_total': memory.total,
                'memory_available': memory.available,
                'swap_total': swap.total,
                'swap_used': swap.used,
                'boot_time': boot_time,
                'platform': psutil.WINDOWS if hasattr(psutil, 'WINDOWS') else 'Unix-like'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_top_processes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top processes by CPU usage"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            
            return processes[:limit]
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def monitor_file_operations(self) -> Dict[str, Any]:
        """Monitor file I/O operations"""
        try:
            # Get current process I/O counters
            current_process = psutil.Process()
            io_counters = current_process.io_counters()
            
            return {
                'read_count': io_counters.read_count,
                'write_count': io_counters.write_count,
                'read_bytes': io_counters.read_bytes,
                'write_bytes': io_counters.write_bytes
            }
            
        except (AttributeError, psutil.AccessDenied):
            # I/O counters might not be available on all platforms
            return {
                'read_count': 0,
                'write_count': 0,
                'read_bytes': 0,
                'write_bytes': 0,
                'note': 'I/O monitoring not available on this platform'
            }
    
    def get_resource_limits(self) -> Dict[str, Any]:
        """Get resource limits for the current process"""
        try:
            current_process = psutil.Process()
            
            # Get memory and CPU limits if available
            limits = {}
            
            # Try to get memory limit
            try:
                memory_info = current_process.memory_info()
                limits['memory_rss'] = memory_info.rss
                limits['memory_vms'] = memory_info.vms
            except AttributeError:
                pass
            
            # Try to get CPU affinity
            try:
                cpu_affinity = current_process.cpu_affinity()
                limits['cpu_affinity'] = cpu_affinity
            except (AttributeError, psutil.AccessDenied):
                pass
            
            # Try to get nice value
            try:
                nice = current_process.nice()
                limits['nice'] = nice
            except (AttributeError, psutil.AccessDenied):
                pass
            
            return limits
            
        except Exception as e:
            return {'error': str(e)}
