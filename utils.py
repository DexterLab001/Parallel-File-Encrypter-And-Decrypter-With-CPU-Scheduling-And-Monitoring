import os
import time
from typing import Any, Dict, List
import hashlib

def format_bytes(bytes_value: int) -> str:
    """Format bytes into human readable format"""
    if bytes_value == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0
    size = float(bytes_value)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"

def format_time(seconds: float) -> str:
    """Format seconds into human readable time format"""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        remaining_seconds = seconds % 60
        return f"{hours}h {remaining_minutes}m {remaining_seconds:.1f}s"

def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """Calculate hash of a file"""
    hash_func = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except FileNotFoundError:
        return ""

def validate_file_integrity(original_file: str, processed_file: str) -> bool:
    """Validate file integrity by comparing hashes"""
    if not os.path.exists(original_file) or not os.path.exists(processed_file):
        return False
    
    original_hash = calculate_file_hash(original_file)
    processed_hash = calculate_file_hash(processed_file)
    
    return original_hash == processed_hash

def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get comprehensive file information"""
    if not os.path.exists(file_path):
        return {}
    
    stat_info = os.stat(file_path)
    
    return {
        'name': os.path.basename(file_path),
        'path': file_path,
        'size': stat_info.st_size,
        'size_formatted': format_bytes(stat_info.st_size),
        'created': stat_info.st_ctime,
        'modified': stat_info.st_mtime,
        'accessed': stat_info.st_atime,
        'extension': os.path.splitext(file_path)[1],
        'hash_sha256': calculate_file_hash(file_path, 'sha256'),
        'hash_md5': calculate_file_hash(file_path, 'md5')
    }

def estimate_processing_time(file_size: int, chunk_size: int, num_workers: int) -> float:
    """Estimate processing time based on file and system parameters"""
    # Base processing rate (bytes per second) - this is a rough estimate
    base_rate = 50 * 1024 * 1024  # 50 MB/s
    
    # Calculate number of chunks
    num_chunks = (file_size + chunk_size - 1) // chunk_size
    
    # Estimate time considering parallel processing
    sequential_time = file_size / base_rate
    parallel_efficiency = min(0.8, num_workers * 0.2)  # Diminishing returns
    estimated_time = sequential_time / (num_workers * parallel_efficiency)
    
    # Add overhead for task scheduling and coordination
    overhead = 0.1 * estimated_time + 0.001 * num_chunks
    
    return estimated_time + overhead

def chunk_file_info(file_size: int, chunk_size: int) -> Dict[str, Any]:
    """Calculate file chunking information"""
    num_chunks = (file_size + chunk_size - 1) // chunk_size
    last_chunk_size = file_size % chunk_size if file_size % chunk_size != 0 else chunk_size
    
    return {
        'total_chunks': num_chunks,
        'chunk_size': chunk_size,
        'last_chunk_size': last_chunk_size,
        'total_size': file_size,
        'estimated_memory_usage': num_chunks * chunk_size * 2,  # Approximate memory needed
        'chunks_per_worker': num_chunks // 4 if num_chunks >= 4 else 1  # Assuming 4 workers
    }

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to remove potentially problematic characters"""
    # Remove or replace problematic characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')
    
    # Ensure filename is not empty
    if not filename:
        filename = "file"
    
    # Limit filename length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        max_name_length = 255 - len(ext)
        filename = name[:max_name_length] + ext
    
    return filename

def create_temp_directory() -> str:
    """Create a temporary directory for processing"""
    import tempfile
    return tempfile.mkdtemp(prefix="file_encryption_")

def cleanup_temp_files(temp_dir: str):
    """Clean up temporary files and directory"""
    import shutil
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: Could not clean up temporary directory {temp_dir}: {e}")

def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength"""
    score = 0
    feedback = []
    
    # Length check
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Password should be at least 8 characters long")
    
    # Character variety checks
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    if has_lower:
        score += 1
    else:
        feedback.append("Include lowercase letters")
    
    if has_upper:
        score += 1
    else:
        feedback.append("Include uppercase letters")
    
    if has_digit:
        score += 1
    else:
        feedback.append("Include numbers")
    
    if has_special:
        score += 1
    else:
        feedback.append("Include special characters")
    
    # Determine strength level
    if score <= 2:
        strength = "Weak"
    elif score <= 3:
        strength = "Medium"
    elif score <= 4:
        strength = "Strong"
    else:
        strength = "Very Strong"
    
    return {
        'score': score,
        'max_score': 5,
        'strength': strength,
        'feedback': feedback,
        'is_valid': score >= 3  # Require at least medium strength
    }

def log_performance_metric(operation: str, duration: float, file_size: int, metadata: Dict[str, Any] = None):
    """Log performance metrics to a simple log format"""
    timestamp = time.time()
    throughput = file_size / duration if duration > 0 else 0
    
    log_entry = {
        'timestamp': timestamp,
        'operation': operation,
        'duration': duration,
        'file_size': file_size,
        'throughput': throughput,
        'metadata': metadata or {}
    }
    
    # In a real application, this would write to a log file
    # For now, we'll just return the formatted entry
    return log_entry

def calculate_parallel_efficiency(sequential_time: float, parallel_time: float, num_workers: int) -> Dict[str, float]:
    """Calculate parallel processing efficiency metrics"""
    if parallel_time <= 0 or num_workers <= 0:
        return {
            'speedup': 0,
            'efficiency': 0,
            'overhead': 0
        }
    
    speedup = sequential_time / parallel_time
    efficiency = speedup / num_workers
    
    # Calculate overhead (time lost due to parallelization)
    ideal_parallel_time = sequential_time / num_workers
    overhead = parallel_time - ideal_parallel_time
    
    return {
        'speedup': speedup,
        'efficiency': efficiency,
        'overhead': overhead,
        'parallel_fraction': min(1.0, speedup / num_workers)  # Amdahl's law consideration
    }
