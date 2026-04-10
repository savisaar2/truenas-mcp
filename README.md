# TrueNAS MCP Server

A professional [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for interacting with TrueNAS Middleware via WebSocket.

## 🚀 Overview
This MCP server uses a **Hybrid Model** to provide exhaustive coverage of the TrueNAS API (1,000+ methods) while maintaining a lean, high-signal toolset for common operations.

1.  **High-Signal Skills**: Explicitly defined tools for the most common tasks (Storage, VMs, Sharing, Users).
2.  **Dynamic Discovery**: Meta-tools that allow the LLM to search, learn, and execute *any* TrueNAS middleware method dynamically.

## ✨ Features & Skills

### 📂 Storage & Data Management
- **List Pools**: Monitor ZFS storage pools, health, and scrub status.
- **List Datasets**: List ZFS datasets and their mount points.
- **Get Alerts**: Retrieve active system alerts and warnings.

### 🖥️ Virtualization & Services
- **List VMs**: List all virtual machines and their current state.
- **Start/Stop VM**: Control power states for specific VMs.
- **Control Service**: Start, stop, or restart system services (SMB, SSH, etc.).
- **List Apps (SCALE Only)**: List installed chart releases.
- **List Jails (Core Only)**: List FreeBSD Jails.

### ⚙️ System & Identity
- **Get System Info**: Retrieve TrueNAS version, hostname, and platform details.
- **List Users**: List non-system user accounts and their status.
- **List SMB Shares**: View configured Windows shares.

### 🔍 Dynamic Discovery (Exhaustive API Access)
When a specific skill isn't listed above, the LLM can use these tools to access the full TrueNAS API:
- **Search API Methods**: Search the 1,000+ available methods by keyword (e.g., "iscsi", "ups", "cloudsync").
- **Get Method Help**: Get the exact documentation and parameter requirements for any method.
- **Execute Custom Call**: Run any discovered API method with a JSON payload.

### ⚠️ System Control
- **Reboot System**: Initiate a system reboot (requires `confirm=True`).
- **Shutdown System**: Initiate a system shutdown (requires `confirm=True`).

## 🛠️ Configuration

### Environment Variables
The following environment variables are supported:
- `TRUENAS_URL`: The WebSocket URL of your TrueNAS instance (e.g., `ws://192.168.1.100/websocket`).
- `TRUENAS_API_KEY`: A valid TrueNAS API Key.
- `TRUENAS_USER`: (Optional) TrueNAS username for session-based auth.
- `TRUENAS_PASS`: (Optional) TrueNAS password for session-based auth.

### ⚠️ Important Security Caveats
To ensure a successful connection, please note the following TrueNAS middleware behaviors:

1.  **API Key Security**: TrueNAS requires **Encrypted Transport (`wss://`)** for all API Key authentication. If you attempt to use an API Key over an unencrypted connection (`ws://`), TrueNAS will **instantly revoke the key** for security reasons.
2.  **Insecure Transport Fallback**: If your environment requires an unencrypted connection (`ws://`), you **must** use the `TRUENAS_USER` and `TRUENAS_PASS` variables instead of an API Key. TrueNAS allows session-based authentication over insecure local connections.
3.  **Self-Signed Certificates**: This server is configured to bypass SSL verification by default, making it compatible with TrueNAS instances using default self-signed certificates over `wss://`.

## 📦 Installation & Usage

### Using Docker
```bash
docker run -e TRUENAS_URL=... -e TRUENAS_API_KEY=... mcp/truenas
```

### Local Development
```bash
# Install dependencies
pip install -e .

# Run the server
truenas-mcp
```

## ⚖️ License
MIT
