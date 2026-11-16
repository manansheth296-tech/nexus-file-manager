"""Drive and system partition detection across Windows, Linux, and macOS."""

import os
import sys
import psutil
from pathlib import Path
from typing import List, Dict, Any


def get_system_drives() -> List[Dict[str, Any]]:
    """Retrieve all mounted partitions/drives with total and free space."""
    drives = []
    try:
        partitions = psutil.disk_partitions(all=False)
        for part in partitions:
            mountpoint = part.mountpoint
            try:
                usage = psutil.disk_usage(mountpoint)
                name = part.device
                if sys.platform.startswith("win"):
                    # On Windows, device is e.g. "C:\\"
                    name = mountpoint
                drives.append({
                    "device": part.device,
                    "mountpoint": mountpoint,
                    "fstype": part.fstype,
                    "opts": part.opts,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent,
                    "name": name,
                    "icon": "fa5s.hdd",
                })
            except (PermissionError, OSError):
                # Drive might not be ready (e.g. empty CD-ROM / disconnected network share)
                drives.append({
                    "device": part.device,
                    "mountpoint": mountpoint,
                    "fstype": part.fstype,
                    "opts": part.opts,
                    "total": 0,
                    "used": 0,
                    "free": 0,
                    "percent": 0.0,
                    "name": mountpoint,
                    "icon": "fa5s.hdd",
                })
    except Exception as e:
        print(f"Error querying partitions: {e}", file=sys.stderr)
        # Fallback to root or home
        drives.append({
            "device": "/",
            "mountpoint": str(Path.home()),
            "fstype": "unknown",
            "opts": "",
            "total": 0,
            "used": 0,
            "free": 0,
            "percent": 0.0,
            "name": "Home",
            "icon": "fa5s.hdd",
        })

    return drives
