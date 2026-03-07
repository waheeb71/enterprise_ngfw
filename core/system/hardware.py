import psutil
import socket
from typing import Dict, Any
from ruamel.yaml import YAML

CONFIG_PATH = "m:/نسخ المشروع/enterprise_ngfw/config/defaults/base.yaml"

def get_network_interfaces() -> dict:
    """Scan OS hardware for physical network interface cards using psutil"""
    nics = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    
    interface_data = {}
    for nic_name, addrs in nics.items():
        # Exclude loopback interfaces
        if nic_name == 'lo' or nic_name.startswith('Loopback'):
            continue
            
        mac_addr = "N/A"
        ip_addr = "N/A"
        for addr in addrs:
            if addr.family == psutil.AF_LINK:
                mac_addr = addr.address
            elif addr.family == socket.AF_INET:
                ip_addr = addr.address
                
        nic_stats = stats.get(nic_name)
        status = "UP" if nic_stats and nic_stats.isup else "DOWN"
        speed = f"{nic_stats.speed} Mbps" if nic_stats and nic_stats.speed > 0 else "Unknown"
        
        interface_data[nic_name] = {
            "mac": mac_addr,
            "ip": ip_addr,
            "status": status,
            "speed": speed
        }
    return interface_data

def get_assigned_interfaces() -> dict:
    """Read the current interface roles from the YAML config"""
    try:
        yaml = YAML()
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.load(f)
            return config.get('interfaces', {})
    except Exception:
        return {}

def assign_interface_role(port: str, role: str) -> bool:
    """Assign a security role to a physical port and save to config"""
    hardware_nics = get_network_interfaces()
    if port not in hardware_nics:
        raise ValueError(f"Port '{port}' not found in hardware.")
        
    yaml = YAML()
    yaml.preserve_quotes = True
    
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.load(f)
        
    if 'interfaces' not in config:
        config['interfaces'] = {}
        
    config['interfaces'][port] = role.upper()
    
    with open(CONFIG_PATH, 'w') as f:
        yaml.dump(config, f)
        
    return True
