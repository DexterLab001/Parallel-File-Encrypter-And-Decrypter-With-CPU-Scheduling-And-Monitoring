import time
import heapq
from typing import List, Dict, Any
from collections import deque

class Task:
    """Represents a task to be scheduled"""
    
    def __init__(self, task_id: int, size: int, arrival_time: float = None):
        self.task_id = task_id
        self.size = size  # Used for SJF scheduling
        self.arrival_time = arrival_time or time.time()
        self.start_time = None
        self.end_time = None
        self.remaining_time = size  # For Round Robin
        
    def __lt__(self, other):
        # For heapq comparison in SJF
        return self.size < other.size

class TaskScheduler:
    """CPU scheduling algorithms for task management"""
    
    def __init__(self, algorithm: str = "FCFS", time_quantum: int = None):
        self.algorithm = algorithm
        self.time_quantum = time_quantum  # in milliseconds
        self.tasks = []
        self.completed_tasks = []
        
    def add_task(self, task_id: int, size: int):
        """Add a task to the scheduler"""
        task = Task(task_id, size)
        self.tasks.append(task)
    
    def schedule_tasks(self) -> List[Dict[str, Any]]:
        """Schedule tasks based on the selected algorithm"""
        if self.algorithm == "FCFS":
            return self._schedule_fcfs()
        elif self.algorithm == "SJF":
            return self._schedule_sjf()
        elif self.algorithm == "Round Robin":
            return self._schedule_round_robin()
        else:
            raise ValueError(f"Unknown scheduling algorithm: {self.algorithm}")
    
    def _schedule_fcfs(self) -> List[Dict[str, Any]]:
        """First Come First Serve scheduling"""
        scheduled_tasks = []
        
        # Sort by arrival time (FCFS)
        sorted_tasks = sorted(self.tasks, key=lambda t: t.arrival_time)
        
        for task in sorted_tasks:
            scheduled_tasks.append({
                'task_id': task.task_id,
                'size': task.size,
                'algorithm': 'FCFS',
                'scheduled_at': time.time()
            })
        
        return scheduled_tasks
    
    def _schedule_sjf(self) -> List[Dict[str, Any]]:
        """Shortest Job First scheduling"""
        scheduled_tasks = []
        
        # Sort by task size (shortest first)
        sorted_tasks = sorted(self.tasks, key=lambda t: t.size)
        
        for task in sorted_tasks:
            scheduled_tasks.append({
                'task_id': task.task_id,
                'size': task.size,
                'algorithm': 'SJF',
                'scheduled_at': time.time()
            })
        
        return scheduled_tasks
    
    def _schedule_round_robin(self) -> List[Dict[str, Any]]:
        """Round Robin scheduling with time quantum"""
        if not self.time_quantum:
            raise ValueError("Time quantum must be specified for Round Robin scheduling")
        
        scheduled_tasks = []
        ready_queue = deque(self.tasks.copy())
        current_time = 0
        
        while ready_queue:
            task = ready_queue.popleft()
            
            # Calculate execution time for this quantum
            execution_time = min(self.time_quantum / 1000.0, task.remaining_time / 1000.0)
            
            # Schedule the task
            scheduled_tasks.append({
                'task_id': task.task_id,
                'size': int(execution_time * 1000),  # Convert back to ms
                'algorithm': 'Round Robin',
                'quantum': self.time_quantum,
                'remaining': task.remaining_time,
                'scheduled_at': time.time()
            })
            
            # Update remaining time
            task.remaining_time -= execution_time * 1000  # Convert to ms
            current_time += execution_time
            
            # If task is not complete, add it back to the queue
            if task.remaining_time > 0:
                ready_queue.append(task)
        
        return scheduled_tasks
    
    def get_scheduling_stats(self) -> Dict[str, Any]:
        """Get statistics about the scheduling process"""
        if not self.tasks:
            return {}
        
        total_tasks = len(self.tasks)
        total_size = sum(task.size for task in self.tasks)
        avg_size = total_size / total_tasks if total_tasks > 0 else 0
        
        min_size = min(task.size for task in self.tasks) if self.tasks else 0
        max_size = max(task.size for task in self.tasks) if self.tasks else 0
        
        return {
            'algorithm': self.algorithm,
            'total_tasks': total_tasks,
            'total_size': total_size,
            'average_size': avg_size,
            'min_size': min_size,
            'max_size': max_size,
            'time_quantum': self.time_quantum
        }
    
    def simulate_execution(self) -> List[Dict[str, Any]]:
        """Simulate task execution with timing information"""
        scheduled_tasks = self.schedule_tasks()
        execution_timeline = []
        
        current_time = 0.0
        
        for task_info in scheduled_tasks:
            task_id = task_info['task_id']
            
            # Find the original task
            original_task = next(t for t in self.tasks if t.task_id == task_id)
            
            # Simulate execution time (proportional to size)
            execution_time = original_task.size / 1000.0  # Convert to seconds
            
            start_time = current_time
            end_time = current_time + execution_time
            
            execution_timeline.append({
                'task_id': task_id,
                'start_time': start_time,
                'end_time': end_time,
                'duration': execution_time,
                'size': original_task.size,
                'algorithm': self.algorithm
            })
            
            current_time = end_time
        
        return execution_timeline
    
    def calculate_metrics(self, execution_timeline: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate scheduling performance metrics"""
        if not execution_timeline:
            return {}
        
        # Calculate turnaround time, waiting time, etc.
        total_turnaround_time = 0
        total_waiting_time = 0
        total_response_time = 0
        
        for task_exec in execution_timeline:
            # Turnaround time = completion time - arrival time
            # For simplicity, assume all tasks arrive at time 0
            turnaround_time = task_exec['end_time']
            total_turnaround_time += turnaround_time
            
            # Waiting time = turnaround time - execution time
            waiting_time = turnaround_time - task_exec['duration']
            total_waiting_time += waiting_time
            
            # Response time = first execution - arrival time
            response_time = task_exec['start_time']
            total_response_time += response_time
        
        num_tasks = len(execution_timeline)
        
        return {
            'average_turnaround_time': total_turnaround_time / num_tasks,
            'average_waiting_time': total_waiting_time / num_tasks,
            'average_response_time': total_response_time / num_tasks,
            'throughput': num_tasks / execution_timeline[-1]['end_time'] if execution_timeline else 0,
            'total_execution_time': execution_timeline[-1]['end_time'] if execution_timeline else 0
        }
    
    def reset(self):
        """Reset the scheduler for a new set of tasks"""
        self.tasks = []
        self.completed_tasks = []
