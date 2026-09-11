import socket
import subprocess
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
LOGS_DIR = ROOT / "logs"


def get_process_summary() -> list[str]:
    result = subprocess.run(
        ["ps", "-eo", "pid,ppid,comm,args", "--no-headers"],
        capture_output=True,
        text=True,
        check=False,
    )
    lines = []
    for line in result.stdout.splitlines():
        if "neuro_san_studio" in line or "nsflow" in line or "neuro_san_server_wrapper" in line:
            lines.append(line.strip())
    return lines


def port_is_open(host: str, port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        sock.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def read_recent_log(path: Path, lines: int = 40) -> str:
    if not path.exists():
        return "No log file found yet."
    content = path.read_text(errors="replace").splitlines()
    return "\n".join(content[-lines:]) if content else "Log file is empty."


st.set_page_config(page_title="Neuro SAN Studio Status", page_icon="🧠", layout="wide")

process_lines = get_process_summary()
server_running = any("python -m neuro_san_studio run" in line for line in process_lines)
nsflow_running = any("nsflow.backend.main" in line for line in process_lines)
server_wrapper_running = any("neuro_san_server_wrapper" in line for line in process_lines)
server_port_open = port_is_open("127.0.0.1", 8080)
nsflow_port_open = port_is_open("127.0.0.1", 4173)

status = "RUNNING" if server_running or nsflow_running or server_wrapper_running else "STOPPED"
status_color = "green" if status == "RUNNING" else "red"

st.title("Neuro SAN Studio Runtime Status")
st.markdown(f"<p><strong>Status:</strong> <span style='color:{status_color}; font-weight:bold;'>{status}</span></p>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Last run command", "python -m neuro_san_studio run", "")
col2.metric("Server process", "Online" if server_wrapper_running else "Offline")
col3.metric("nsflow UI", "Online" if nsflow_running else "Offline")
col4.metric("HTTP port 8080", "Open" if server_port_open else "Closed")

st.write("---")

st.subheader("Runtime checks")

checks = {
    "main launch command": server_running,
    "NSFlow client": nsflow_running,
    "Neuro SAN server wrapper": server_wrapper_running,
    "server port 8080": server_port_open,
    "nsflow port 4173": nsflow_port_open,
}

for name, ok in checks.items():
    st.write(f"- {name}: {'✅ up' if ok else '❌ down'}")

st.write("---")
left_col, right_col = st.columns(2)
with left_col:
    st.subheader("Server log")
    st.code(read_recent_log(LOGS_DIR / "server.log"), language="text")

with right_col:
    st.subheader("NSFlow log")
    st.code(read_recent_log(LOGS_DIR / "nsflow.log"), language="text")

st.write("---")

st.subheader("Process list")
if process_lines:
    st.code("\n".join(process_lines[:20]), language="text")
else:
    st.info("No matching Neuro SAN or nsflow processes were found.")
