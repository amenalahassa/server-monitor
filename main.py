import streamlit as st
import socket
import datetime
import os

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

# Initialize session state
if 'monitoring' not in st.session_state:
    st.session_state.monitoring = False
if 'server_info' not in st.session_state:
    st.session_state.server_info = None

st.title("Server Monitoring Dashboard")

if not st.session_state.monitoring:
    with st.form("server_config"):
        st.subheader("Server Configuration")
        ip = st.text_input("Server IP Address")
        port = st.number_input("Port", min_value=1, max_value=65535, value=22)
        username = st.text_input("Username (optional)")

        if st.form_submit_button("Start Monitoring"):
            if ip and port:
                st.session_state.server_info = {
                    'ip': ip,
                    'port': port,
                    'username': username
                }
                st.session_state.monitoring = True
                st.rerun()
            else:
                st.error("Please provide both IP address and port number")

else:
    # Add auto-refresh meta tag
    st.markdown("""<meta http-equiv="refresh" content="10">""", unsafe_allow_html=True)

    # Perform server check
    server = st.session_state.server_info
    status, error = check_server(server['ip'], server['port'])
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Log result
    log_entry = f"{timestamp} - {server['ip']}:{server['port']} - Status: {status}"
    if error:
        log_entry += f" - Error: {error}"
    log_entry += "\n"

    with open("server_monitor.log", "a") as f:
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

    if os.path.exists("server_monitor.log"):
        with open("server_monitor.log", "r") as f:
            logs = f.readlines()

        # Show last 10 entries
        st.text_area("Recent log entries", value="".join(logs[-10:]), height=200)

        # Download full log
        st.download_button(
            label="Download Full Log",
            data="".join(logs),
            file_name="server_monitor.log",
            mime="text/plain"
        )
    else:
        st.info("No log entries yet")

    # Stop monitoring button
    if st.button("Stop Monitoring"):
        st.session_state.monitoring = False
        st.session_state.server_info = None
        st.rerun()

st.write("---")
st.write("Monitoring checks occur every 10 seconds. Keep this page open to continue monitoring.")