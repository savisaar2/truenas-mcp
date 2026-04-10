# TrueNAS MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for interacting with TrueNAS Middleware via WebSocket.

## Features
- **Get System Info**: Retrieve TrueNAS version, hostname, and basic status.
- **List VMs**: List all virtual machines and their current state.
- **List Apps**: List installed chart releases and their statuses.
- **List Users**: List non-system user accounts.

## Configuration
The following environment variables are required:
- `TRUENAS_URL`: The WebSocket URL of your TrueNAS instance (e.g., `wss://192.168.1.100/websocket`).
- `TRUENAS_API_KEY`: A valid TrueNAS API Key with appropriate permissions.

## Installation & Usage

### Using Docker
```bash
docker run -e TRUENAS_URL=... -e TRUENAS_API_KEY=... mcp/truenas
```

### Local Development
```bash
uv pip install -e .
truenas-mcp
```
