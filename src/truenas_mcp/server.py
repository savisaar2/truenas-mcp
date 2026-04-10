import os
import asyncio
from mcp.server.fastmcp import FastMCP
from .client import TrueNASClient

# Initialize FastMCP server
mcp = FastMCP("truenas-mcp")

# Environment variables for TrueNAS connection
TRUENAS_URL = os.getenv("TRUENAS_URL")
TRUENAS_API_KEY = os.getenv("TRUENAS_API_KEY")

async def get_client() -> TrueNASClient:
    """Helper to get an authenticated TrueNAS client."""
    if not TRUENAS_URL or not TRUENAS_API_KEY:
        raise ValueError("TRUENAS_URL and TRUENAS_API_KEY environment variables must be set.")
    
    client = TrueNASClient(TRUENAS_URL, TRUENAS_API_KEY)
    await client.connect()
    return client

@mcp.tool()
async def get_system_info() -> str:
    """Retrieve TrueNAS system information (version, hostname, status)."""
    client = await get_client()
    try:
        response = await client.call("system.info", [])
        result = response.get("result", {})
        return f"TrueNAS System Info:\n- Hostname: {result.get('hostname')}\n- Version: {result.get('version')}\n- Build: {result.get('build_time')}\n- Platform: {result.get('platform')}"
    finally:
        await client.close()

@mcp.tool()
async def list_vms() -> str:
    """List all virtual machines and their current state."""
    client = await get_client()
    try:
        response = await client.call("vm.query", [])
        vms = response.get("result", [])
        if not vms:
            return "No virtual machines found."
        
        vm_list = []
        for vm in vms:
            name = vm.get("name")
            status = vm.get("status", {}).get("state", "UNKNOWN")
            vcpus = vm.get("vcpus")
            memory = vm.get("memory")
            vm_list.append(f"- {name} ({status}): {vcpus} VCPUs, {memory}MB Memory")
        
        return "Virtual Machines:\n" + "\n".join(vm_list)
    finally:
        await client.close()

@mcp.tool()
async def list_apps() -> str:
    """List installed chart releases (Applications) and their statuses."""
    client = await get_client()
    try:
        response = await client.call("chart.release.query", [])
        apps = response.get("result", [])
        if not apps:
            return "No applications found."
        
        app_list = []
        for app in apps:
            name = app.get("name")
            status = app.get("status")
            namespace = app.get("namespace")
            app_list.append(f"- {name} [{namespace}] ({status})")
        
        return "Installed Applications:\n" + "\n".join(app_list)
    finally:
        await client.close()

@mcp.tool()
async def list_users() -> str:
    """List non-system user accounts on the TrueNAS system."""
    client = await get_client()
    try:
        # Filter for non-builtin users
        response = await client.call("user.query", [[["builtin", "=", False]]])
        users = response.get("result", [])
        if not users:
            return "No non-system users found."
        
        user_list = []
        for user in users:
            username = user.get("username")
            full_name = user.get("full_name")
            locked = "LOCKED" if user.get("locked") else "ACTIVE"
            user_list.append(f"- {username} ({full_name}): {locked}")
        
        return "User Accounts:\n" + "\n".join(user_list)
    finally:
        await client.close()

def main():
    """Main entry point for the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()
