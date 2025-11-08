import time
import statistics
from typing import Dict, List, Any, Optional
import threading
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class PerformanceMetric:
    """Data class for performance metrics"""
    name: str
    value: float
    unit: str
    timestamp: float
    metadata: Dict[str, Any] = None

class PerformanceAnalyzer:
    """Performance analysis and benchmarking utilities"""
    
    def __init__(self):
        self.metrics = []
        self.benchmarks = {}
        self.baselines = {}
        
    def record_metric(self, name: str, value: float, unit: str, metadata: Dict[str, Any] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        self.metrics.append(metric)
    
    def benchmark_function(self, func, *args, **kwargs) -> Dict[str, Any]:
        """Benchmark a function execution"""
        start_memory = self._get_memory_usage()
        start_time = time.perf_counter()
        
        try:
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        end_time = time.perf_counter()
        end_memory = self._get_memory_usage()
        
        execution_time = end_time - start_time
        memory_delta = end_memory - start_memory
        
        benchmark_result = {
            'function_name': func.__name__ if hasattr(func, '__name__') else str(func),
            'execution_time': execution_time,
            'memory_delta': memory_delta,
            'start_memory': start_memory,
            'end_memory': end_memory,
            'success': success,
            'result': result,
            'error': error,
            'timestamp': time.time()
        }
        
        # Record metrics
        self.record_metric(f"{func.__name__}_execution_time", execution_time, "seconds")
        self.record_metric(f"{func.__name__}_memory_delta", memory_delta, "bytes")
        
        return benchmark_result
    
    def compare_algorithms(self, algorithms: Dict[str, callable], test_data: Any) -> Dict[str, Any]:
        """Compare performance of different algorithms"""
        results = {}
        
        for name, algorithm in algorithms.items():
            print(f"Benchmarking {name}...")
            
            # Run multiple iterations for better accuracy
            iterations = 5
            execution_times = []
            memory_deltas = []
            
            for i in range(iterations):
                benchmark = self.benchmark_function(algorithm, test_data)
                if benchmark['success']:
                    execution_times.append(benchmark['execution_time'])
                    memory_deltas.append(benchmark['memory_delta'])
            
            if execution_times:
                results[name] = {
                    'avg_execution_time': statistics.mean(execution_times),
                    'min_execution_time': min(execution_times),
                    'max_execution_time': max(execution_times),
                    'std_execution_time': statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
                    'avg_memory_delta': statistics.mean(memory_deltas),
                    'iterations': iterations,
                    'success_rate': len(execution_times) / iterations
                }
            else:
                results[name] = {
                    'error': 'All iterations failed',
                    'success_rate': 0
                }
        
        return results
    
    def analyze_parallel_performance(self, sequential_time: float, parallel_time: float, 
                                   num_workers: int) -> Dict[str, float]:
        """Analyze parallel processing performance"""
        speedup = sequential_time / parallel_time if parallel_time > 0 else 0
        efficiency = speedup / num_workers if num_workers > 0 else 0
        overhead = parallel_time - (sequential_time / num_workers) if num_workers > 0 else 0
        
        return {
            'sequential_time': sequential_time,
            'parallel_time': parallel_time,
            'speedup': speedup,
            'efficiency': efficiency,
            'overhead': overhead,
            'num_workers': num_workers,
            'theoretical_max_speedup': num_workers,
            'efficiency_percentage': efficiency * 100
        }
    
    def calculate_throughput(self, data_processed: int, time_taken: float, unit: str = "bytes") -> float:
        """Calculate throughput (data processed per second)"""
        if time_taken <= 0:
            return 0
        return data_processed / time_taken
    
    def analyze_scheduling_performance(self, scheduling_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze CPU scheduling algorithm performance"""
        if not scheduling_results:
            return {}
        
        algorithms = defaultdict(list)
        
        # Group results by algorithm
        for result in scheduling_results:
            algorithm = result.get('algorithm', 'unknown')
            algorithms[algorithm].append(result)
        
        analysis = {}
        
        for algorithm, results in algorithms.items():
            execution_times = [r.get('duration', 0) for r in results]
            file_sizes = [r.get('file_size', 0) for r in results]
            throughputs = [r.get('file_size', 0) / r.get('duration', 1) for r in results]
            
            if execution_times:
                analysis[algorithm] = {
                    'avg_execution_time': statistics.mean(execution_times),
                    'min_execution_time': min(execution_times),
                    'max_execution_time': max(execution_times),
                    'std_execution_time': statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
                    'avg_throughput': statistics.mean(throughputs),
                    'total_files_processed': len(results),
                    'total_data_processed': sum(file_sizes),
                    'algorithm_efficiency': self._calculate_algorithm_efficiency(results)
                }
        
        return analysis
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if not self.metrics:
            return {'error': 'No metrics recorded'}
        
        # Group metrics by name
        metric_groups = defaultdict(list)
        for metric in self.metrics:
            metric_groups[metric.name].append(metric)
        
        report = {
            'summary': {
                'total_metrics': len(self.metrics),
                'metric_types': len(metric_groups),
                'time_span': {
                    'start': min(m.timestamp for m in self.metrics),
                    'end': max(m.timestamp for m in self.metrics),
                    'duration': max(m.timestamp for m in self.metrics) - min(m.timestamp for m in self.metrics)
                }
            },
            'metrics': {}
        }
        
        # Analyze each metric group
        for name, metrics in metric_groups.items():
            values = [m.value for m in metrics]
            
            report['metrics'][name] = {
                'count': len(values),
                'unit': metrics[0].unit,
                'statistics': {
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'min': min(values),
                    'max': max(values),
                    'std': statistics.stdev(values) if len(values) > 1 else 0
                },
                'trend': self._calculate_trend(values),
                'latest_value': values[-1],
                'first_value': values[0]
            }
        
        return report
    
    def set_baseline(self, name: str, value: float):
        """Set a baseline value for comparison"""
        self.baselines[name] = value
    
    def compare_to_baseline(self, name: str, current_value: float) -> Dict[str, Any]:
        """Compare current value to baseline"""
        if name not in self.baselines:
            return {'error': f'No baseline set for {name}'}
        
        baseline = self.baselines[name]
        difference = current_value - baseline
        percentage_change = (difference / baseline * 100) if baseline != 0 else 0
        
        return {
            'baseline': baseline,
            'current': current_value,
            'difference': difference,
            'percentage_change': percentage_change,
            'improvement': difference < 0,  # Assuming lower is better for most metrics
            'status': 'improved' if difference < 0 else 'degraded' if difference > 0 else 'unchanged'
        }
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss
        except ImportError:
            # Fallback if psutil is not available
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024  # Convert KB to bytes
    
    def _calculate_algorithm_efficiency(self, results: List[Dict[str, Any]]) -> float:
        """Calculate algorithm efficiency based on results"""
        if not results:
            return 0.0
        
        # Simple efficiency calculation based on throughput consistency
        throughputs = [r.get('file_size', 0) / r.get('duration', 1) for r in results]
        
        if len(throughputs) < 2:
            return 1.0
        
        # Calculate coefficient of variation (lower is better)
        mean_throughput = statistics.mean(throughputs)
        std_throughput = statistics.stdev(throughputs)
        
        cv = std_throughput / mean_throughput if mean_throughput > 0 else 1.0
        
        # Convert to efficiency (0-1 scale, higher is better)
        efficiency = max(0, 1 - cv)
        
        return efficiency
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction for a series of values"""
        if len(values) < 2:
            return 'stable'
        
        # Simple linear trend calculation
        n = len(values)
        x = list(range(n))
        
        # Calculate slope using least squares
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 'stable'
        
        slope = numerator / denominator
        
        # Determine trend based on slope
        if abs(slope) < 0.1:  # Threshold for stability
            return 'stable'
        elif slope > 0:
            return 'increasing'
        else:
            return 'decreasing'
    
    def export_metrics(self, format: str = 'dict') -> Any:
        """Export metrics in specified format"""
        if format == 'dict':
            return [
                {
                    'name': m.name,
                    'value': m.value,
                    'unit': m.unit,
                    'timestamp': m.timestamp,
                    'metadata': m.metadata
                }
                for m in self.metrics
            ]
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['name', 'value', 'unit', 'timestamp'])
            
            # Write data
            for metric in self.metrics:
                writer.writerow([metric.name, metric.value, metric.unit, metric.timestamp])
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def clear_metrics(self):
        """Clear all recorded metrics"""
        self.metrics.clear()
