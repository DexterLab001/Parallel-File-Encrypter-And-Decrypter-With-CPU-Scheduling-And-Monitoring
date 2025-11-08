import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
import threading
import queue
import os
from datetime import datetime

from encryption import FileEncryption
from scheduler import TaskScheduler
from monitor import SystemMonitor
from performance import PerformanceAnalyzer
from utils import format_bytes, format_time

# Page configuration
st.set_page_config(
    page_title="Parallel File Encryption System",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'encryption_results' not in st.session_state:
    st.session_state.encryption_results = []
if 'monitoring_data' not in st.session_state:
    st.session_state.monitoring_data = []
if 'gantt_data' not in st.session_state:
    st.session_state.gantt_data = []
if 'performance_data' not in st.session_state:
    st.session_state.performance_data = []

def main():
    st.title("🔐 Parallel File Encryption/Decryption System")
    st.markdown("Advanced file processing with CPU scheduling algorithms and real-time monitoring")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Operation selection
        operation = st.selectbox(
            "Operation",
            ["Encrypt", "Decrypt"],
            help="Select whether to encrypt or decrypt files"
        )
        
        # Scheduling algorithm selection
        algorithm = st.selectbox(
            "Scheduling Algorithm",
            ["FCFS", "SJF", "Round Robin"],
            help="Select the CPU scheduling algorithm for task execution"
        )
        
        # Round Robin time quantum (only shown for Round Robin)
        time_quantum = None
        if algorithm == "Round Robin":
            time_quantum = st.slider(
                "Time Quantum (ms)",
                min_value=10,
                max_value=1000,
                value=100,
                step=10,
                help="Time slice for Round Robin scheduling"
            )
        
        # Parallel processing settings
        st.subheader("Parallel Processing")
        chunk_size = st.slider(
            "Chunk Size (KB)",
            min_value=64,
            max_value=2048,
            value=512,
            step=64,
            help="Size of each file chunk for parallel processing"
        )
        
        max_workers = st.slider(
            "Max Workers",
            min_value=1,
            max_value=16,
            value=4,
            help="Maximum number of worker threads"
        )
        
        # Monitoring settings
        st.subheader("Monitoring")
        enable_monitoring = st.checkbox("Enable Real-time Monitoring", value=True)
        monitor_interval = st.slider(
            "Monitor Interval (ms)",
            min_value=100,
            max_value=2000,
            value=500,
            step=100,
            help="Frequency of system monitoring updates"
        )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("File Processing")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose a file to process",
            type=None,
            help="Upload any file type for encryption/decryption"
        )
        
        # Password input for encryption/decryption
        password = st.text_input(
            "Password",
            type="password",
            help="Enter password for encryption/decryption"
        )
        
        # Process button
        if st.button("Process File", type="primary", disabled=not (uploaded_file and password)):
            process_file(uploaded_file, password, operation, algorithm, time_quantum, 
                        chunk_size, max_workers, enable_monitoring, monitor_interval)
    
    with col2:
        st.header("Quick Stats")
        if st.session_state.encryption_results:
            latest_result = st.session_state.encryption_results[-1]
            st.metric("Last Operation", latest_result['operation'])
            st.metric("Processing Time", f"{latest_result['duration']:.2f}s")
            st.metric("File Size", format_bytes(latest_result['file_size']))
            st.metric("Chunks Processed", latest_result['chunks'])
    
    # Real-time monitoring section
    if enable_monitoring and st.session_state.monitoring_data:
        st.header("📊 Real-time System Monitoring")
        display_monitoring_dashboard()
    
    # Gantt chart section
    if st.session_state.gantt_data:
        st.header("📅 Task Scheduling Visualization")
        display_gantt_chart()
    
    # Performance analysis section
    if len(st.session_state.performance_data) > 1:
        st.header("📈 Performance Analysis")
        display_performance_analysis()

def process_file(uploaded_file, password, operation, algorithm, time_quantum, 
                chunk_size, max_workers, enable_monitoring, monitor_interval):
    """Process the uploaded file with the specified parameters"""
    
    # Create progress containers
    progress_container = st.container()
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
    # Initialize components
    encryptor = FileEncryption()
    scheduler = TaskScheduler(algorithm, time_quantum)
    monitor = SystemMonitor() if enable_monitoring else None
    
    try:
        # Save uploaded file temporarily
        temp_filename = f"temp_{uploaded_file.name}"
        with open(temp_filename, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        file_size = os.path.getsize(temp_filename)
        
        # Start monitoring if enabled
        monitoring_queue = queue.Queue()
        monitor_thread = None
        
        if enable_monitoring:
            monitor_thread = threading.Thread(
                target=monitor_system_performance,
                args=(monitor, monitoring_queue, monitor_interval)
            )
            monitor_thread.daemon = True
            monitor_thread.start()
        
        status_text.text("Preparing file chunks...")
        
        # Process file
        start_time = time.time()
        
        if operation == "Encrypt":
            result_filename, gantt_data, chunk_count = encryptor.encrypt_file_parallel(
                temp_filename, password, chunk_size * 1024, max_workers, scheduler, progress_bar
            )
        else:
            result_filename, gantt_data, chunk_count = encryptor.decrypt_file_parallel(
                temp_filename, password, chunk_size * 1024, max_workers, scheduler, progress_bar
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Stop monitoring
        if monitor_thread:
            monitor.stop()
            monitor_thread.join(timeout=1)
        
        # Store results
        result_data = {
            'timestamp': datetime.now(),
            'operation': operation,
            'algorithm': algorithm,
            'file_size': file_size,
            'chunks': chunk_count,
            'duration': duration,
            'workers': max_workers,
            'chunk_size': chunk_size * 1024
        }
        
        st.session_state.encryption_results.append(result_data)
        st.session_state.gantt_data = gantt_data
        st.session_state.performance_data.append(result_data)
        
        # Collect monitoring data
        monitoring_data = []
        while not monitoring_queue.empty():
            monitoring_data.append(monitoring_queue.get())
        
        if monitoring_data:
            st.session_state.monitoring_data = monitoring_data
        
        # Clean up temporary files
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        
        # Success message and download
        status_text.text("✅ Processing completed successfully!")
        progress_bar.progress(1.0)
        
        if os.path.exists(result_filename):
            with open(result_filename, "rb") as f:
                st.download_button(
                    label=f"Download {operation}ed File",
                    data=f.read(),
                    file_name=result_filename,
                    mime="application/octet-stream"
                )
            os.remove(result_filename)
        
        # Display summary
        st.success(f"""
        **Processing Summary:**
        - Operation: {operation}
        - Algorithm: {algorithm}
        - File Size: {format_bytes(file_size)}
        - Chunks: {chunk_count}
        - Duration: {format_time(duration)}
        - Workers: {max_workers}
        """)
        
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        status_text.text("❌ Processing failed!")
        
        # Clean up on error
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

def monitor_system_performance(monitor, monitoring_queue, interval_ms):
    """Monitor system performance in a separate thread"""
    interval = interval_ms / 1000.0
    
    while not monitor.should_stop():
        data = monitor.get_system_stats()
        monitoring_queue.put(data)
        time.sleep(interval)

def display_monitoring_dashboard():
    """Display real-time monitoring dashboard"""
    if not st.session_state.monitoring_data:
        return
    
    # Convert monitoring data to DataFrame
    df = pd.DataFrame(st.session_state.monitoring_data)
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('CPU Usage (%)', 'Memory Usage (%)', 'CPU Per Core (%)', 'Active Threads'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # CPU Usage
    fig.add_trace(
        go.Scatter(x=df.index, y=df['cpu_percent'], name='CPU %', line=dict(color='red')),
        row=1, col=1
    )
    
    # Memory Usage
    fig.add_trace(
        go.Scatter(x=df.index, y=df['memory_percent'], name='Memory %', line=dict(color='blue')),
        row=1, col=2
    )
    
    # CPU per core (if available)
    if 'cpu_per_core' in df.columns and df['cpu_per_core'].iloc[0]:
        for i, core_data in enumerate(df['cpu_per_core']):
            if isinstance(core_data, list) and len(core_data) > 0:
                fig.add_trace(
                    go.Scatter(x=df.index, y=[c[i] if i < len(c) else 0 for c in df['cpu_per_core']], 
                              name=f'Core {i}', showlegend=False),
                    row=2, col=1
                )
    
    # Active threads
    fig.add_trace(
        go.Scatter(x=df.index, y=df['active_threads'], name='Threads', line=dict(color='green')),
        row=2, col=2
    )
    
    fig.update_layout(height=600, showlegend=True, title_text="System Performance Monitoring")
    st.plotly_chart(fig, use_container_width=True)

def display_gantt_chart():
    """Display Gantt chart for task scheduling"""
    if not st.session_state.gantt_data:
        return
    
    # Create Gantt chart
    fig = go.Figure()
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF']
    
    for i, task in enumerate(st.session_state.gantt_data):
        fig.add_trace(go.Scatter(
            x=[task['start'], task['end']],
            y=[f"Worker {task['worker']}", f"Worker {task['worker']}"],
            mode='lines',
            line=dict(color=colors[i % len(colors)], width=20),
            name=f"Chunk {task['chunk_id']}",
            hovertemplate=f"<b>Chunk {task['chunk_id']}</b><br>" +
                         f"Worker: {task['worker']}<br>" +
                         f"Start: {task['start']:.3f}s<br>" +
                         f"End: {task['end']:.3f}s<br>" +
                         f"Duration: {task['end'] - task['start']:.3f}s<extra></extra>"
        ))
    
    fig.update_layout(
        title="Task Execution Gantt Chart",
        xaxis_title="Time (seconds)",
        yaxis_title="Workers",
        height=400,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_performance_analysis():
    """Display performance analysis dashboard"""
    df = pd.DataFrame(st.session_state.performance_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Execution time vs file size
        fig1 = px.scatter(
            df, x='file_size', y='duration', color='algorithm',
            title='Execution Time vs File Size',
            labels={'file_size': 'File Size (bytes)', 'duration': 'Duration (seconds)'},
            hover_data=['chunks', 'workers']
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Algorithm comparison
        if len(df['algorithm'].unique()) > 1:
            fig2 = px.box(
                df, x='algorithm', y='duration',
                title='Algorithm Performance Comparison',
                labels={'algorithm': 'Scheduling Algorithm', 'duration': 'Duration (seconds)'}
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            # Workers vs performance
            fig2 = px.scatter(
                df, x='workers', y='duration', size='file_size',
                title='Workers vs Performance',
                labels={'workers': 'Number of Workers', 'duration': 'Duration (seconds)'},
                hover_data=['algorithm', 'chunks']
            )
            st.plotly_chart(fig2, use_container_width=True)
    
    # Performance metrics table
    st.subheader("Performance Metrics")
    
    # Calculate throughput and efficiency metrics
    df_display = df.copy()
    df_display['throughput'] = df_display['file_size'] / df_display['duration']  # bytes per second
    df_display['chunks_per_second'] = df_display['chunks'] / df_display['duration']
    df_display['efficiency'] = df_display['file_size'] / (df_display['duration'] * df_display['workers'])
    
    # Format display values
    df_display['file_size_mb'] = df_display['file_size'] / (1024 * 1024)
    df_display['throughput_mbps'] = df_display['throughput'] / (1024 * 1024)
    
    display_cols = ['timestamp', 'operation', 'algorithm', 'file_size_mb', 'duration', 
                   'throughput_mbps', 'chunks_per_second', 'workers']
    
    st.dataframe(
        df_display[display_cols],
        column_config={
            'timestamp': 'Time',
            'operation': 'Operation',
            'algorithm': 'Algorithm',
            'file_size_mb': st.column_config.NumberColumn('File Size (MB)', format="%.2f"),
            'duration': st.column_config.NumberColumn('Duration (s)', format="%.3f"),
            'throughput_mbps': st.column_config.NumberColumn('Throughput (MB/s)', format="%.2f"),
            'chunks_per_second': st.column_config.NumberColumn('Chunks/s', format="%.2f"),
            'workers': 'Workers'
        },
        use_container_width=True
    )

if __name__ == "__main__":
    main()
