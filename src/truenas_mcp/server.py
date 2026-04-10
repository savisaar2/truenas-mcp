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
            status = vm.get("status", {}).get("state", "UNKNOWN")
            vcpus = vm.get("vcpus")
            memory = vm.get("memory")
            vm_list.append(f"- {name} ({status}): {vcpus} VCPUs, {memory}MB Memory")
        
        return "Virtual Machines:\n" + "\n".join(vm_list)
    except Exception as e:
        return await handle_request_error(e, "vm.query")
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
        for ds in datasets[:50]: # Limit to 50 for context safety
            name = ds.get("id")
            mount = ds.get("mountpoint")
            ds_list.append(f"- {name} at {mount}")
        
        output = "ZFS Datasets (Top 50):\n" + "\n".join(ds_list)
        if len(datasets) > 50:
            output += f"\n... and {len(datasets) - 50} more."
        return output
    except Exception as e:
        return await handle_request_error(e, "pool.dataset.query")
    finally:
        await client.close()

@mcp.tool()
async def list_disks() -> str:
    """List physical disks and their status. Works on both SCALE and Core."""
    client = await get_client()
    try:
        response = await client.call("disk.query", [])
        disks = response.get("result", [])
        if not disks:
            return "No physical disks found."
        
        disk_list = []
        for disk in disks:
            name = disk.get("name")
            model = disk.get("model")
            size = int(disk.get("size", 0)) / (1024**3) # Convert to GB
            type = disk.get("type", "UNKNOWN")
            disk_list.append(f"- {name} ({model}): {size:.2f}GB, {type}")
        
        return "Physical Disks:\n" + "\n".join(disk_list)
    except Exception as e:
        return await handle_request_error(e, "disk.query")
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
async def list_nfs_shares() -> str:
    """List configured NFS shares and their paths. Works on both SCALE and Core."""
    client = await get_client()
    try:
        response = await client.call("sharing.nfs.query", [])
        shares = response.get("result", [])
        if not shares:
            return "No NFS shares found."
        
        share_list = []
        for share in shares:
            comment = share.get("comment", "No comment")
            paths = ", ".join(share.get("paths", []))
            enabled = "Enabled" if share.get("enabled") else "Disabled"
            share_list.append(f"- {paths}: {comment} ({enabled})")
        
        return "NFS Shares:\n" + "\n".join(share_list)
    except Exception as e:
        return await handle_request_error(e, "sharing.nfs.query")
    finally:
        await client.close()

@mcp.tool()
async def list_snapshots(count: int = 20) -> str:
    """List recent ZFS snapshots. Works on both SCALE and Core."""
    client = await get_client()
    try:
        # Sort by creation time descending and limit
        response = await client.call("zfs.snapshot.query", [[], {"sort": [{"property": "creation", "direction": "desc"}], "limit": count}])
        snapshots = response.get("result", [])
        if not snapshots:
            return "No ZFS snapshots found."
        
        snap_list = []
        for snap in snapshots:
            name = snap.get("id")
            created = snap.get("properties", {}).get("creation", {}).get("value", "unknown")
            snap_list.append(f"- {name} (Created: {created})")
        
        return f"Recent ZFS Snapshots (Last {count}):\n" + "\n".join(snap_list)
    except Exception as e:
        return await handle_request_error(e, "zfs.snapshot.query")
    finally:
        await client.close()

@mcp.tool()
async def create_dataset_snapshot(dataset_id: str, name: str) -> str:
    """Create a new ZFS snapshot for a specific dataset. Works on both SCALE and Core."""
    client = await get_client()
    try:
        full_name = f"{dataset_id}@{name}"
        await client.call("zfs.snapshot.create", [{"dataset": dataset_id, "name": name}])
        return f"Successfully created snapshot: {full_name}"
    except Exception as e:
        return await handle_request_error(e, "zfs.snapshot.create")
    finally:
        await client.close()

@mcp.tool()
async def list_replication_tasks() -> str:
    """List ZFS replication tasks and their status. Works on both SCALE and Core."""
    client = await get_client()
    try:
        response = await client.call("replication.query", [])
        tasks = response.get("result", [])
        if not tasks:
            return "No replication tasks found."
        
        task_list = []
        for task in tasks:
            name = task.get("name")
            state = task.get("state", {}).get("state", "UNKNOWN")
            enabled = "Enabled" if task.get("enabled") else "Disabled"
            task_list.append(f"- {name}: {state} ({enabled})")
        
        return "Replication Tasks:\n" + "\n".join(task_list)
    except Exception as e:
        return await handle_request_error(e, "replication.query")
    finally:
        await client.close()

@mcp.tool()
async def list_cloud_sync_tasks() -> str:
    """List Cloud Sync tasks and their last run status. Works on both SCALE and Core."""
    client = await get_client()
    try:
        response = await client.call("cloudsync.query", [])
        tasks = response.get("result", [])
        if not tasks:
            return "No cloud sync tasks found."
        
        task_list = []
        for task in tasks:
            description = task.get("description", "No description")
            provider = task.get("credentials", {}).get("provider", "UNKNOWN")
            status = task.get("job", {}).get("state", "UNKNOWN")
            task_list.append(f"- {description} ({provider}): {status}")
        
        return "Cloud Sync Tasks:\n" + "\n".join(task_list)
    except Exception as e:
        return await handle_request_error(e, "cloudsync.query")
    finally:
        await client.close()

@mcp.tool()
async def list_cron_jobs() -> str:
    """List scheduled cron jobs. Works on both SCALE and Core."""
    client = await get_client()
    try:
        response = await client.call("cronjob.query", [])
        jobs = response.get("result", [])
        if not jobs:
            return "No cron jobs found."
        
        job_list = []
        for job in jobs:
            user = job.get("user")
            command = job.get("command")
            schedule = f"{job.get('schedule', {}).get('minute')} {job.get('schedule', {}).get('hour')} {job.get('schedule', {}).get('dom')} {job.get('schedule', {}).get('month')} {job.get('schedule', {}).get('dow')}"
            enabled = "Enabled" if job.get("enabled") else "Disabled"
            job_list.append(f"- {user}: {command} (Schedule: {schedule}, {enabled})")
        
        return "Cron Jobs:\n" + "\n".join(job_list)
    except Exception as e:
        return await handle_request_error(e, "cronjob.query")
    finally:
        await client.close()

@mcp.tool()
async def check_system_updates() -> str:
    """Check if TrueNAS updates are available. Works on both SCALE and Core."""
    client = await get_client()
    try:
        response = await client.call("update.check_available", [])
        result = response.get("result", {})
        status = result.get("status")
        if status == "AVAILABLE":
            version = result.get("version", "unknown")
            return f"Update AVAILABLE: {version}"
        return f"System status: {status}"
    except Exception as e:
        return await handle_request_error(e, "update.check_available")
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
async def list_services() -> str:
    """List TrueNAS services and their statuses (e.g., SMB, SSH). Works on both SCALE and Core."""
    client = await get_client()
    try:
        response = await client.call("service.query", [])
        services = response.get("result", [])
        if not services:
            return "No services found."
        
        svc_list = []
        for svc in services:
            name = svc.get("service")
            state = svc.get("state")
            enable = "Enabled" if svc.get("enable") else "Disabled"
            svc_list.append(f"- {name}: {state} ({enable})")
        
        return "System Services:\n" + "\n".join(svc_list)
    except Exception as e:
        return await handle_request_error(e, "service.query")
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
async def list_network_interfaces() -> str:
    """List network interfaces and their configuration. Works on both SCALE and Core."""
    client = await get_client()
    try:
        response = await client.call("interface.query", [])
        interfaces = response.get("result", [])
        if not interfaces:
            return "No interfaces found."
        
        int_list = []
        for interface in interfaces:
            name = interface.get("name")
            type = interface.get("type")
            state = interface.get("state", {})
            link_state = state.get("link_state", "UNKNOWN")
            ips = [addr.get("address") for addr in state.get("aliases", [])]
            int_list.append(f"- {name} ({type}): Link={link_state}, IPs={', '.join(ips)}")
        
        return "Network Interfaces:\n" + "\n".join(int_list)
    except Exception as e:
        return await handle_request_error(e, "interface.query")
    finally:
        await client.close()

def main():
    """Main entry point for the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()
