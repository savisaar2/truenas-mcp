import os
import asyncio
import json
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

async def handle_request_error(e: Exception, method: str) -> str:
    """Handle common middleware errors, distinguishing between SCALE and Core."""
    err_str = str(e).lower()
    if "method not found" in err_str:
        if method == "chart.release.query":
            return "Error: This feature (Apps) is SCALE-only and not available on TrueNAS Core."
        if method == "jail.query":
            return "Error: This feature (Jails) is Core-only and not available on TrueNAS SCALE."
        return f"Error: Method '{method}' not found on this system."
    return f"Error communicating with TrueNAS: {str(e)}"

# --- META-DISCOVERY TOOLS (Dynamic Discovery) ---

@mcp.tool()
async def search_api_methods(query: str) -> str:
    """Search for API methods matching a keyword (e.g., 'iscsi', 'smb', 'ups'). 
    Use this to find niche commands that aren't explicitly listed as skills."""
    client = await get_client()
    try:
        response = await client.call("system.api_methods", [])
        all_methods = response.get("result", {})
        
        matches = [m for m in all_methods.keys() if query.lower() in m.lower()]
        if not matches:
            return f"No API methods found matching '{query}'."
        
        return f"API Methods matching '{query}':\n" + "\n".join(matches[:50]) # Limit for context
    except Exception as e:
        return f"Error searching API methods: {str(e)}"
    finally:
        await client.close()

@mcp.tool()
async def get_method_help(method: str) -> str:
    """Get detailed help text and parameter information for a specific API method."""
    client = await get_client()
    try:
        response = await client.call("system.api_query", [method])
        result = response.get("result", {})
        if not result:
            return f"No details found for method '{method}'."
        
        doc = result.get("description", "No description available.")
        params = result.get("accepts", [])
        return f"Method: {method}\n\nDescription:\n{doc}\n\nParameters:\n{json.dumps(params, indent=2)}"
    except Exception as e:
        return f"Error getting help for {method}: {str(e)}"
    finally:
        await client.close()

@mcp.tool()
async def execute_custom_api_call(method: str, params: list = None) -> str:
    """Execute ANY arbitrary TrueNAS API method. Use this for discovery or niche tasks.
    'params' should be a list of positional arguments as expected by the TrueNAS middleware."""
    if params is None:
        params = []
    
    client = await get_client()
    try:
        response = await client.call(method, params)
        return f"Response from {method}:\n" + json.dumps(response.get("result", {}), indent=2)
    except Exception as e:
        return f"Error executing {method}: {str(e)}"
    finally:
        await client.close()

# --- HIGH-SIGNAL ACTION TOOLS ---

@mcp.tool()
async def start_vm(vm_id: str) -> str:
    """Start a specific virtual machine by its ID or Name."""
    client = await get_client()
    try:
        # TrueNAS usually expects the integer ID for VM actions
        # We try to parse the id if it's numeric
        target_id = int(vm_id) if vm_id.isdigit() else vm_id
        await client.call("vm.start", [target_id])
        return f"Successfully sent start command to VM: {vm_id}"
    except Exception as e:
        return await handle_request_error(e, "vm.start")
    finally:
        await client.close()

@mcp.tool()
async def stop_vm(vm_id: str, force: bool = False) -> str:
    """Stop/Shutdown a specific virtual machine. Set 'force=True' for hard power-off."""
    client = await get_client()
    try:
        target_id = int(vm_id) if vm_id.isdigit() else vm_id
        method = "vm.poweroff" if force else "vm.stop"
        await client.call(method, [target_id])
        return f"Successfully sent stop/poweroff command to VM: {vm_id}"
    except Exception as e:
        return await handle_request_error(e, method)
    finally:
        await client.close()

@mcp.tool()
async def control_service(service: str, action: str) -> str:
    """Control system services (e.g., 'ssh', 'smb', 'nfs'). Action must be 'start', 'stop', or 'restart'."""
    if action not in ["start", "stop", "restart"]:
        return "Error: Action must be 'start', 'stop', or 'restart'."
    
    client = await get_client()
    try:
        await client.call(f"service.{action}", [service])
        return f"Successfully sent {action} command to service: {service}"
    except Exception as e:
        return await handle_request_error(e, f"service.{action}")
    finally:
        await client.close()

# --- HIGH-SIGNAL INFORMATION TOOLS (EXISTING) ---

@mcp.tool()
async def get_system_info() -> str:
    """Retrieve TrueNAS system information (version, hostname, status). Works on both SCALE and Core."""
    client = await get_client()
    try:
        response = await client.call("system.info", [])
        result = response.get("result", {})
        return (f"TrueNAS System Info:\n- Hostname: {result.get('hostname')}\n- Version: {result.get('version')}\n"
                f"- Build: {result.get('build_time')}\n- Platform: {result.get('platform')}")
    except Exception as e:
        return await handle_request_error(e, "system.info")
    finally:
        await client.close()

@mcp.tool()
async def list_vms() -> str:
    """List all virtual machines and their current state. Works on both SCALE and Core."""
    client = await get_client()
    try:
        response = await client.call("vm.query", [])
        vms = response.get("result", [])
        if not vms:
            return "No virtual machines found."
        
        vm_list = []
        for vm in vms:
            name = vm.get("name")
            vm_id = vm.get("id")
            status = vm.get("status", {}).get("state", "UNKNOWN")
            vcpus = vm.get("vcpus")
            memory = vm.get("memory")
            vm_list.append(f"- ID: {vm_id} | {name} ({status}): {vcpus} VCPUs, {memory}MB Memory")
        
        return "Virtual Machines:\n" + "\n".join(vm_list)
    except Exception as e:
        return await handle_request_error(e, "vm.query")
    finally:
        await client.close()

@mcp.tool()
async def list_pools() -> str:
    """List ZFS storage pools, their health, and capacity. Works on both SCALE and Core."""
    client = await get_client()
    try:
        response = await client.call("pool.query", [])
        pools = response.get("result", [])
        if not pools:
            return "No pools found."
        
        pool_list = []
        for pool in pools:
            name = pool.get("name")
            status = pool.get("status")
            healthy = pool.get("healthy", False)
            scan = pool.get("scan", {}).get("state", "NONE")
            pool_list.append(f"- {name} ({status}): Healthy={healthy}, Scrub State={scan}")
        
        return "Storage Pools:\n" + "\n".join(pool_list)
    except Exception as e:
        return await handle_request_error(e, "pool.query")
    finally:
        await client.close()

@mcp.tool()
async def list_datasets() -> str:
    """List ZFS datasets and their mount points. Works on both SCALE and Core."""
    client = await get_client()
    try:
        response = await client.call("pool.dataset.query", [])
        datasets = response.get("result", [])
        if not datasets:
            return "No datasets found."
        
        ds_list = []
        for ds in datasets[:50]: # Limit for context
            name = ds.get("id")
            mount = ds.get("mountpoint")
            ds_list.append(f"- {name} at {mount}")
        
        return "ZFS Datasets (Top 50):\n" + "\n".join(ds_list)
    except Exception as e:
        return await handle_request_error(e, "pool.dataset.query")
    finally:
        await client.close()

@mcp.tool()
async def get_alerts() -> str:
    """Retrieve active system alerts. Works on both SCALE and Core."""
    client = await get_client()
    try:
        response = await client.call("alert.list", [])
        alerts = response.get("result", [])
        if not alerts:
            return "No active alerts."
        
        alert_list = []
        for alert in alerts:
            level = alert.get("level")
            message = alert.get("formatted")
            time = alert.get("datetime", {}).get("$date", "unknown time")
            alert_list.append(f"[{level}] {message} ({time})")
        
        return "Active Alerts:\n" + "\n".join(alert_list)
    except Exception as e:
        return await handle_request_error(e, "alert.list")
    finally:
        await client.close()

@mcp.tool()
async def list_smb_shares() -> str:
    """List configured SMB shares and their paths. Works on both SCALE and Core."""
    client = await get_client()
    try:
        response = await client.call("sharing.smb.query", [])
        shares = response.get("result", [])
        if not shares:
            return "No SMB shares found."
        
        share_list = []
        for share in shares:
            name = share.get("name")
            path = share.get("path")
            enabled = "Enabled" if share.get("enabled") else "Disabled"
            share_list.append(f"- {name}: {path} ({enabled})")
        
        return "SMB Shares:\n" + "\n".join(share_list)
    except Exception as e:
        return await handle_request_error(e, "sharing.smb.query")
    finally:
        await client.close()

@mcp.tool()
async def list_users() -> str:
    """List non-system user accounts on the TrueNAS system. Works on both SCALE and Core."""
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
    except Exception as e:
        return await handle_request_error(e, "user.query")
    finally:
        await client.close()

@mcp.tool()
async def list_apps() -> str:
    """List SCALE chart releases (Applications) and their statuses. (TrueNAS SCALE ONLY)"""
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
        
        return "Installed Applications (SCALE):\n" + "\n".join(app_list)
    except Exception as e:
        return await handle_request_error(e, "chart.release.query")
    finally:
        await client.close()

@mcp.tool()
async def list_jails() -> str:
    """List FreeBSD Jails and their statuses. (TrueNAS CORE ONLY)"""
    client = await get_client()
    try:
        response = await client.call("jail.query", [])
        jails = response.get("result", [])
        if not jails:
            return "No jails found."
        
        jail_list = []
        for jail in jails:
            name = jail.get("id")
            state = jail.get("state")
            release = jail.get("release")
            jail_list.append(f"- {name} ({state}): {release}")
        
        return "FreeBSD Jails (Core):\n" + "\n".join(jail_list)
    except Exception as e:
        return await handle_request_error(e, "jail.query")
    finally:
        await client.close()

@mcp.tool()
async def reboot_system(confirm: bool = False) -> str:
    """Initiate a system reboot. (REQUIRES CONFIRMATION)"""
    if not confirm:
        return "Error: System reboot requires 'confirm=True' to be passed."
    
    client = await get_client()
    try:
        await client.call("system.reboot", [])
        return "Reboot command sent successfully."
    except Exception as e:
        return await handle_request_error(e, "system.reboot")
    finally:
        await client.close()

@mcp.tool()
async def shutdown_system(confirm: bool = False) -> str:
    """Initiate a system shutdown. (REQUIRES CONFIRMATION)"""
    if not confirm:
        return "Error: System shutdown requires 'confirm=True' to be passed."
    
    client = await get_client()
    try:
        await client.call("system.shutdown", [])
        return "Shutdown command sent successfully."
    except Exception as e:
        return await handle_request_error(e, "system.shutdown")
    finally:
        await client.close()

def main():
    """Main entry point for the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()
