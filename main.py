import streamlit as st
import socket
import datetime
import os
import json

SESSION_FILE = "session_state.json"
LOG_FILE = "server_monitor.log"
REFRESH_TIME = 20

def save_session_state():
    """Save session state to a file"""
    with open(SESSION_FILE, "w") as f:
        json.dump({
            'monitoring': st.session_state.monitoring,
            'server_info': st.session_state.server_info,
            'confirm_reset': st.session_state.confirm_reset,
            'refresh_time': st.session_state.refresh_time
        }, f)

def load_session_state():
    """Load session state from file if exists"""
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    return None

def remove_log_file():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

def check_server(ip, port, timeout=5):
    """Attempt to connect to the server's port to check if it's reachable."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((ip, port))
        return "Up", None
    except socket.error as e:
        return "Down", str(e)
    except Exception as e:
        return "Down", str(e)

# Initialize session state with persistence
loaded_state = load_session_state()
if loaded_state:
    st.session_state.update(loaded_state)
else:
    if 'monitoring' not in st.session_state:
        st.session_state.monitoring = False
    if 'server_info' not in st.session_state:
        st.session_state.server_info = None
    if 'confirm_reset' not in st.session_state:
        st.session_state.confirm_reset = False
    if 'refresh_time' not in st.session_state:
        st.session_state.refresh_time = REFRESH_TIME


st.title("Server Monitoring Dashboard")

# Always show configuration form
with st.form("server_config"):
    st.subheader("Server Configuration")
    ip = st.text_input("Server IP Address",
                       value=st.session_state.server_info['ip'] if st.session_state.server_info else "")
    port = st.number_input("Port", min_value=1, max_value=65535,
                           value=st.session_state.server_info['port'] if st.session_state.server_info else 22)
    username = st.text_input("Username (optional)",
                             value=st.session_state.server_info.get('username', '') if st.session_state.server_info else "")
    refresh_time = st.slider("Refresh Time (seconds)", min_value=15, max_value=60, value=REFRESH_TIME)

    submitted = st.form_submit_button("Apply Configuration")
    if submitted:
        if ip and port:
            if st.session_state.monitoring:
                st.session_state.confirm_reset = True
            else:
                st.session_state.server_info = {
                    'ip': ip,
                    'port': port,
                    'username': username,
                }
                st.session_state.refresh_time = refresh_time
                remove_log_file()
                save_session_state()
                st.rerun()
        else:
            st.error("Please provide both IP address and port number")

# Confirmation dialog for configuration change during monitoring
if st.session_state.confirm_reset:
    st.warning("Changing configuration will stop current monitoring and clear existing logs. Are you sure?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Confirm"):
            st.session_state.monitoring = False
            st.session_state.server_info = {
                'ip': ip,
                'port': port,
                'username': username
            }
            st.session_state.confirm_reset = False
            st.session_state.refresh_time = refresh_time
            remove_log_file()
            save_session_state()
            st.rerun()
    with col2:
        if st.button("Cancel"):
            st.session_state.confirm_reset = False
            st.rerun()

if st.session_state.monitoring:
    # Add auto-refresh meta tag
    st.markdown(f"""<meta http-equiv="refresh" content="{st.session_state.refresh_time}">""", unsafe_allow_html=True)

    # Perform server check
    server = st.session_state.server_info
    status, error = check_server(server['ip'], server['port'])
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Log result
    log_entry = f"{timestamp} - {server['ip']}:{server['port']} - Status: {status}"
    if error:
        log_entry += f" - Error: {error}"
    log_entry += "\n"

    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

    # Display current status
    st.subheader("Current Server Status")
    if status == "Up":
        st.success("🟢 Server is reachable")
    else:
        st.error(f"🔴 Server is unreachable - {error}")

    # Display monitoring information
    st.write(f"**IP Address:** {server['ip']}")
    st.write(f"**Port:** {server['port']}")
    if server['username']:
        st.write(f"**Username:** {server['username']}")

    # Show log file
    st.subheader("Monitoring Log")

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            logs = f.readlines()

        # Show last 10 entries
        st.text_area("Recent log entries", value="".join(logs[-10:]), height=200)

        # Download full log
        st.download_button(
            label="Download Full Log",
            data="".join(logs),
            file_name=LOG_FILE,
            mime="text/plain"
        )
    else:
        st.info("No log entries yet")

    # Stop monitoring button
    if st.button("Stop Monitoring"):
        st.session_state.monitoring = False
        st.markdown("""<meta http-equiv="refresh" content="0">""", unsafe_allow_html=True)
        save_session_state()
        st.rerun()

elif st.session_state.server_info and not st.session_state.confirm_reset:
    if st.button("Start Monitoring"):
        st.session_state.monitoring = True
        save_session_state()
        st.rerun()

st.write("---")
st.write(f"Monitoring checks occur every {st.session_state.refresh_time} seconds. Keep this page open to continue monitoring.")