import os
import time 
import subprocess
import socket
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy import event


# --- SYSTEM DIRECTORY PATH NAVIGATION ---
current_path = Path(__file__).resolve()
while current_path.name != "evaluating-sycophancy" and current_path.parent != current_path:
    current_path = current_path.parent
PROJECT_ROOT = str(current_path)

BIN_DIR = os.path.join(PROJECT_ROOT, ".postgres_bin", "bin")
DATA_DIR = os.path.join(PROJECT_ROOT, "postgres_database")
LOG_FILE = os.path.join(PROJECT_ROOT, "postgres_server.log")
PG_CTL_EXE = os.path.join(BIN_DIR, "pg_ctl")
INITDB_EXE = os.path.join(BIN_DIR, "initdb")

env = os.environ.copy()
env["PATH"] = f"{BIN_DIR}:{env.get('PATH', '')}"

PORT = env.get("DB_PORT") or "54332"
DB_NAME = "sycophancy_db"
USER = env.get("USER") or env.get("LOGNAME") or "postgres"
DATABASE_URL = f"postgresql://{USER}@localhost:{PORT}/{DB_NAME}"

# THE AUTO-RETRY ALIGNMENT LAYOUT:
# pool_pre_ping=True forces SQLAlchemy to test the connection before issuing any query.
# If Postgres drops the connection, it silently recreates it without raising an OperationalError!
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800
)

base_server_engine = create_engine(
    f"postgresql://{USER}@localhost:{PORT}/postgres",
    pool_pre_ping=True
)

# PIGGYBACK RETRY LISTENER:
# Intercepts raw connections at the driver level to catch trailing startup drops safely.
@event.listens_for(Engine, "connect")
def provide_initialization_buffer(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        # Pings a basic lightweight select statement to verify pg_catalog is stable
        cursor.execute("SELECT 1;")
        cursor.close()
    except Exception:
        # If it drops, give it a moment to finish its background startup and try one more time
        time.sleep(0.5)
        cursor.execute("SELECT 1;")
        cursor.close()
        
        
engine = create_engine(DATABASE_URL)
base_server_engine = create_engine(f"postgresql://{USER}@localhost:{PORT}/postgres")

def is_postgres_running():
    """Checks if the basic system pid signature is structurally detectable."""
    if not os.path.exists(DATA_DIR) or not os.path.exists(PG_CTL_EXE):
        return False
    cmd = [PG_CTL_EXE, "-D", DATA_DIR, "status"]
    result = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.returncode == 0

def check_port_open():
    """Actively tests if port 54332 is accepting live network connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex(("localhost", int(PORT))) == 0

def start_postgres():
    """Boots up the engine using a direct background worker to prevent socket drops."""
    if not os.path.exists(INITDB_EXE) or not os.path.exists(PG_CTL_EXE):
        raise FileNotFoundError(f"PostgreSQL binaries missing from: {BIN_DIR}")

    # 1. Clear out any hanging ports or ghost processes
    try:
        subprocess.run(f"fuser -k {PORT}/tcp", shell=True, capture_output=True)
        time.sleep(0.4)
    except Exception:
        pass

    # 2. Re-initialize a clean database cluster structure if missing
    if not os.path.exists(DATA_DIR):
        subprocess.run([INITDB_EXE, "-D", DATA_DIR], env=env, check=True)
        time.sleep(0.4)
    
    # 3. Direct Server Invocation with absolute local system constraints
    if not is_postgres_running():
        # We invoke postgres directly with dynamic shared memory limits suited for cluster nodes
        postgres_exe = os.path.join(BIN_DIR, "postgres")
        
        # Build direct start command flags bypassing pg_ctl wrapper bugs
        start_cmd = [
            postgres_exe, 
            "-D", DATA_DIR, 
            "-p", PORT, 
            "-h", "localhost",
            "-c", "shared_buffers=16MB",      # Low footprint to prevent node memory panics
            "-c", "max_connections=20"        # Lower connection limit for user-space safety
        ]
        
        # Open a log handler to safely pipe background logs away from standard out
        log_file_obj = open(LOG_FILE, "a")
        
        # Launch as a completely separated background daemon process
        subprocess.Popen(start_cmd, env=env, stdout=log_file_obj, stderr=log_file_obj)
        
        # 4. Rigorous Active Network Verification Loop
        max_wait = 6
        start_time = time.time()
        db_ready = False
        
        while time.time() - start_time < max_wait:
            if check_port_open():
                # The port is listening! Now run a lightweight check to ensure catalogs are active
                try:
                    with base_server_engine.connect() as test_conn:
                        test_conn.execute(text("SELECT 1;"))
                        db_ready = True
                        break
                except Exception:
                    # Port is open but inner engine is still reading catalog pages, loop again
                    pass
            time.sleep(0.2)
            
        log_file_obj.close()
        
        if not db_ready:
            raise RuntimeError("PostgreSQL cluster process failed to stabilize network connection sockets.")
        
    # 5. Seamlessly provision catalog targets if missing
    try:
        with base_server_engine.connect() as conn:
            conn.execute(text("COMMIT;"))
            conn.execute(text(f"CREATE DATABASE {DB_NAME};"))
    except Exception:
        pass

def stop_postgres():
    """Signals background worker processes to terminate safely."""
    if os.path.exists(PG_CTL_EXE) and os.path.exists(DATA_DIR):
        # Trigger an immediate fast shutdown signal sequence
        stop_cmd = [PG_CTL_EXE, "-D", DATA_DIR, "-m", "fast", "stop"]
        subprocess.run(stop_cmd, env=env, capture_output=True)
        
    # Force kill anything remaining on the socket to ensure a clean slate for the next run
    try:
        subprocess.run(f"fuser -k {PORT}/tcp", shell=True, capture_output=True)
        time.sleep(0.5)
    except Exception:
        pass