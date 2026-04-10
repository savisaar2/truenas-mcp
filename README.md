# TrueNAS MCP Server

A professional [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for interacting with TrueNAS Middleware via WebSocket.

## 🚀 Overview
This MCP server provides a comprehensive set of "skills" (tools) to manage and monitor TrueNAS systems. It is designed to work seamlessly with both **TrueNAS SCALE** and **TrueNAS Core**.

## ✨ Features & Skills

### 📂 Storage & Data Management
- **List Pools**: Monitor ZFS storage pools, health, and scrub status.
- **List Datasets**: List ZFS datasets and their mount points.
- **List Disks**: Retrieve physical disk information (model, size, type).
- **List Snapshots**: List recent ZFS snapshots.
- **Create Snapshot**: Create a new ZFS snapshot for a specific dataset.

### 🌐 Networking & Sharing
- **List Network Interfaces**: View network configuration and link states.
- **List SMB Shares**: List configured SMB shares and their paths.
- **List NFS Shares**: List configured NFS shares and their paths.

### 🛡️ Data Protection & Sync
- **List Replication Tasks**: List ZFS replication tasks and their status.
- **List Cloud Sync Tasks**: List Cloud Sync tasks and their last run status.

### ⚙️ System Monitoring & Maintenance
- **Get System Info**: Retrieve TrueNAS version, hostname, and platform details.
- **Get Alerts**: Retrieve active system alerts and warnings.
- **List Services**: Check the status of system services (SMB, SSH, etc.).
- **List Users**: List non-system user accounts and their status.
- **List Cron Jobs**: List scheduled cron jobs.
- **Check Updates**: Check for available system updates.

### 🖥️ Virtualization & Containers
- **List VMs**: List all virtual machines and their current state.
- **List Apps (SCALE Only)**: List installed chart releases and namespaces.
- **List Jails (Core Only)**: List FreeBSD Jails and their release versions.

### ⚠️ System Control
- **Reboot System**: Initiate a system reboot (requires `confirm=True`).
- **Shutdown System**: Initiate a system shutdown (requires `confirm=True`).

## 🛠️ Configuration
The following environment variables are required:
- `TRUENAS_URL`: The WebSocket URL of your TrueNAS instance (e.g., `wss://192.168.1.100/websocket`).
- `TRUENAS_API_KEY`: A valid TrueNAS API Key.

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
