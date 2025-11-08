import os
import threading
import time
import queue
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import secrets

class FileEncryption:
    """File encryption/decryption with AES and parallel processing support"""
    
    def __init__(self):
        self.backend = default_backend()
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256-bit key
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        return kdf.derive(password.encode())
    
    def _encrypt_chunk(self, chunk_data: bytes, key: bytes) -> bytes:
        """Encrypt a single chunk of data"""
        # Generate random IV for each chunk
        iv = secrets.token_bytes(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        
        # Pad the chunk to be multiple of 16 bytes (AES block size)
        padding_length = 16 - (len(chunk_data) % 16)
        padded_data = chunk_data + bytes([padding_length] * padding_length)
        
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # Return IV + encrypted data
        return iv + encrypted_data
    
    def _decrypt_chunk(self, chunk_data: bytes, key: bytes) -> bytes:
        """Decrypt a single chunk of data"""
        # Extract IV and encrypted data
        iv = chunk_data[:16]
        encrypted_data = chunk_data[16:]
        
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=self.backend)
        decryptor = cipher.decryptor()
        
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # Remove padding
        padding_length = decrypted_data[-1]
        return decrypted_data[:-padding_length]
    
    def _worker_process(self, task_queue: queue.Queue, result_queue: queue.Queue, 
                       key: bytes, operation: str, worker_id: int):
        """Worker thread for processing encryption/decryption tasks"""
        while True:
            try:
                task = task_queue.get(timeout=1)
                if task is None:  # Shutdown signal
                    break
                
                chunk_id, chunk_data, start_time = task
                
                # Record actual start time
                actual_start = time.time()
                
                try:
                    if operation == "encrypt":
                        result_data = self._encrypt_chunk(chunk_data, key)
                    else:
                        result_data = self._decrypt_chunk(chunk_data, key)
                    
                    # Record completion time
                    end_time = time.time()
                    
                    result_queue.put({
                        'chunk_id': chunk_id,
                        'data': result_data,
                        'worker_id': worker_id,
                        'start_time': actual_start,
                        'end_time': end_time,
                        'success': True
                    })
                
                except Exception as e:
                    result_queue.put({
                        'chunk_id': chunk_id,
                        'error': str(e),
                        'worker_id': worker_id,
                        'success': False
                    })
                
                task_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
                break
    
    def encrypt_file_parallel(self, input_file: str, password: str, chunk_size: int, 
                            max_workers: int, scheduler, progress_bar=None) -> tuple:
        """Encrypt file using parallel processing with scheduling"""
        
        # Generate salt and derive key
        salt = secrets.token_bytes(16)
        key = self._derive_key(password, salt)
        
        # Read and split file into chunks
        chunks = []
        with open(input_file, 'rb') as f:
            chunk_id = 0
            while True:
                chunk_data = f.read(chunk_size)
                if not chunk_data:
                    break
                chunks.append((chunk_id, chunk_data))
                chunk_id += 1
        
        if not chunks:
            raise ValueError("File is empty")
        
        # Schedule tasks
        task_queue = queue.Queue()
        result_queue = queue.Queue()
        
        # Add tasks to scheduler
        for chunk_id, chunk_data in chunks:
            task_size = len(chunk_data)  # Use data size as task size for SJF
            scheduler.add_task(chunk_id, task_size)
        
        # Start worker threads
        workers = []
        for i in range(max_workers):
            worker = threading.Thread(
                target=self._worker_process,
                args=(task_queue, result_queue, key, "encrypt", i)
            )
            worker.start()
            workers.append(worker)
        
        # Execute tasks using scheduler
        scheduled_tasks = scheduler.schedule_tasks()
        gantt_data = []
        
        start_time = time.time()
        completed_chunks = 0
        
        for task_info in scheduled_tasks:
            chunk_id = task_info['task_id']
            chunk_data = chunks[chunk_id][1]
            
            # Add task to queue with timing info
            task_queue.put((chunk_id, chunk_data, time.time()))
            
        # Collect results
        results = {}
        for _ in range(len(chunks)):
            result = result_queue.get()
            if result['success']:
                results[result['chunk_id']] = result['data']
                
                # Record Gantt chart data
                gantt_data.append({
                    'chunk_id': result['chunk_id'],
                    'worker': result['worker_id'],
                    'start': result['start_time'] - start_time,
                    'end': result['end_time'] - start_time
                })
                
                completed_chunks += 1
                if progress_bar:
                    progress_bar.progress(completed_chunks / len(chunks))
        
        # Shutdown workers
        for _ in workers:
            task_queue.put(None)
        
        for worker in workers:
            worker.join()
        
        # Write encrypted file
        output_file = input_file + ".enc"
        with open(output_file, 'wb') as f:
            # Write salt first
            f.write(salt)
            
            # Write chunk count
            f.write(len(chunks).to_bytes(4, byteorder='big'))
            
            # Write chunks in order
            for i in range(len(chunks)):
                if i in results:
                    chunk_data = results[i]
                    f.write(len(chunk_data).to_bytes(4, byteorder='big'))
                    f.write(chunk_data)
        
        return output_file, gantt_data, len(chunks)
    
    def decrypt_file_parallel(self, input_file: str, password: str, chunk_size: int, 
                            max_workers: int, scheduler, progress_bar=None) -> tuple:
        """Decrypt file using parallel processing with scheduling"""
        
        # Read encrypted file structure
        with open(input_file, 'rb') as f:
            # Read salt
            salt = f.read(16)
            
            # Derive key
            key = self._derive_key(password, salt)
            
            # Read chunk count
            chunk_count = int.from_bytes(f.read(4), byteorder='big')
            
            # Read encrypted chunks
            chunks = []
            for i in range(chunk_count):
                chunk_length = int.from_bytes(f.read(4), byteorder='big')
                chunk_data = f.read(chunk_length)
                chunks.append((i, chunk_data))
        
        # Schedule tasks
        task_queue = queue.Queue()
        result_queue = queue.Queue()
        
        # Add tasks to scheduler
        for chunk_id, chunk_data in chunks:
            task_size = len(chunk_data)
            scheduler.add_task(chunk_id, task_size)
        
        # Start worker threads
        workers = []
        for i in range(max_workers):
            worker = threading.Thread(
                target=self._worker_process,
                args=(task_queue, result_queue, key, "decrypt", i)
            )
            worker.start()
            workers.append(worker)
        
        # Execute tasks using scheduler
        scheduled_tasks = scheduler.schedule_tasks()
        gantt_data = []
        
        start_time = time.time()
        completed_chunks = 0
        
        for task_info in scheduled_tasks:
            chunk_id = task_info['task_id']
            chunk_data = chunks[chunk_id][1]
            
            task_queue.put((chunk_id, chunk_data, time.time()))
        
        # Collect results
        results = {}
        for _ in range(len(chunks)):
            result = result_queue.get()
            if result['success']:
                results[result['chunk_id']] = result['data']
                
                gantt_data.append({
                    'chunk_id': result['chunk_id'],
                    'worker': result['worker_id'],
                    'start': result['start_time'] - start_time,
                    'end': result['end_time'] - start_time
                })
                
                completed_chunks += 1
                if progress_bar:
                    progress_bar.progress(completed_chunks / len(chunks))
        
        # Shutdown workers
        for _ in workers:
            task_queue.put(None)
        
        for worker in workers:
            worker.join()
        
        # Write decrypted file
        if input_file.endswith('.enc'):
            output_file = input_file[:-4]  # Remove .enc extension
        else:
            output_file = input_file + ".dec"
        
        with open(output_file, 'wb') as f:
            for i in range(len(chunks)):
                if i in results:
                    f.write(results[i])
        
        return output_file, gantt_data, len(chunks)
