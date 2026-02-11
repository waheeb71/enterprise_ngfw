#!/usr/bin/env python3
"""
Enterprise NGFW - Command Line Interface
Comprehensive CLI tool for NGFW management using Click
"""

import click
import requests
import json
import sys
from typing import Optional
from datetime import datetime
from pathlib import Path
from tabulate import tabulate
import yaml

# Configuration
CONFIG_FILE = Path.home() / ".ngfw" / "config.yaml"
DEFAULT_API_URL = "http://localhost:8000/api/v1"


class NGFWClient:
    """NGFW API client"""
    
    def __init__(self, api_url: str, token: Optional[str] = None):
        self.api_url = api_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        
        if token:
            self.session.headers['Authorization'] = f'Bearer {token}'
    
    def login(self, username: str, password: str) -> str:
        """Authenticate and get token"""
        response = self.session.post(
            f"{self.api_url}/auth/login",
            json={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data['access_token']
            self.session.headers['Authorization'] = f'Bearer {self.token}'
            return self.token
        else:
            raise Exception(f"Login failed: {response.text}")
    
    def get(self, endpoint: str, **kwargs):
        """GET request"""
        response = self.session.get(f"{self.api_url}/{endpoint}", **kwargs)
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint: str, **kwargs):
        """POST request"""
        response = self.session.post(f"{self.api_url}/{endpoint}", **kwargs)
        response.raise_for_status()
        return response.json()
    
    def put(self, endpoint: str, **kwargs):
        """PUT request"""
        response = self.session.put(f"{self.api_url}/{endpoint}", **kwargs)
        response.raise_for_status()
        return response.json()
    
    def delete(self, endpoint: str, **kwargs):
        """DELETE request"""
        response = self.session.delete(f"{self.api_url}/{endpoint}", **kwargs)
        response.raise_for_status()


def load_config():
    """Load configuration from file"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f)
    return {}


def save_config(config: dict):
    """Save configuration to file"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config, f)


def get_client() -> NGFWClient:
    """Get configured API client"""
    config = load_config()
    api_url = config.get('api_url', DEFAULT_API_URL)
    token = config.get('token')
    return NGFWClient(api_url, token)


# ==================== CLI Commands ====================

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """
    Enterprise NGFW Command Line Interface
    
    Manage your Next-Generation Firewall from the terminal.
    """
    pass


# ==================== Authentication ====================

@cli.group()
def auth():
    """Authentication commands"""
    pass


@auth.command()
@click.option('--username', prompt=True, help='Username')
@click.option('--password', prompt=True, hide_input=True, help='Password')
@click.option('--api-url', default=DEFAULT_API_URL, help='API URL')
def login(username: str, password: str, api_url: str):
    """Login to NGFW API"""
    try:
        client = NGFWClient(api_url)
        token = client.login(username, password)
        
        # Save config
        save_config({
            'api_url': api_url,
            'token': token,
            'username': username
        })
        
        click.echo(click.style('✓ Login successful!', fg='green'))
    except Exception as e:
        click.echo(click.style(f'✗ Login failed: {e}', fg='red'), err=True)
        sys.exit(1)


@auth.command()
def logout():
    """Logout from NGFW API"""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
        click.echo(click.style('✓ Logged out successfully', fg='green'))
    else:
        click.echo('Not logged in')


@auth.command()
def whoami():
    """Show current user information"""
    config = load_config()
    if 'username' in config:
        click.echo(f"Logged in as: {config['username']}")
        click.echo(f"API URL: {config.get('api_url', DEFAULT_API_URL)}")
    else:
        click.echo('Not logged in')


# ==================== System Status ====================

@cli.group()
def status():
    """System status and health"""
    pass


@status.command()
def show():
    """Show system status"""
    try:
        client = get_client()
        data = client.get('status')
        
        click.echo(click.style('\n=== System Status ===\n', fg='cyan', bold=True))
        click.echo(f"Status: {click.style(data['status'].upper(), fg='green' if data['status'] == 'operational' else 'red')}")
        click.echo(f"Uptime: {data['uptime_seconds']:.0f} seconds")
        click.echo(f"CPU Usage: {data['cpu_usage']:.1f}%")
        click.echo(f"Memory Usage: {data['memory_usage']:.1f}%")
        click.echo(f"Active Connections: {data['active_connections']}")
        click.echo(f"Rules Count: {data['rules_count']}")
        click.echo(f"ML Models: {'Loaded' if data['ml_models_loaded'] else 'Not loaded'}")
    except Exception as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'), err=True)
        sys.exit(1)


@status.command()
def health():
    """Check API health"""
    try:
        client = get_client()
        response = client.session.get(f"{client.api_url.replace('/api/v1', '')}/api/v1/health")
        
        if response.status_code == 200:
            click.echo(click.style('✓ API is healthy', fg='green'))
        else:
            click.echo(click.style('✗ API is unhealthy', fg='red'), err=True)
            sys.exit(1)
    except Exception as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'), err=True)
        sys.exit(1)


# ==================== Statistics ====================

@cli.group()
def stats():
    """Traffic statistics"""
    pass


@stats.command()
@click.option('--window', default=300, help='Time window in seconds (default: 300)')
def show(window: int):
    """Show traffic statistics"""
    try:
        client = get_client()
        data = client.get('statistics', params={'time_window': window})
        
        click.echo(click.style('\n=== Traffic Statistics ===\n', fg='cyan', bold=True))
        click.echo(f"Timestamp: {data['timestamp']}")
        click.echo(f"\nTotal Packets: {data['total_packets']:,}")
        click.echo(f"Total Bytes: {data['total_bytes']:,}")
        click.echo(f"Blocked: {data['blocked_packets']:,}")
        click.echo(f"Allowed: {data['allowed_packets']:,}")
        click.echo(f"\nUnique Sources: {data['unique_sources']:,}")
        click.echo(f"Unique Destinations: {data['unique_destinations']:,}")
        
        click.echo(click.style('\nTop Protocols:', fg='cyan'))
        for proto, count in data['top_protocols'].items():
            click.echo(f"  {proto}: {count:,}")
    except Exception as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'), err=True)
        sys.exit(1)


# ==================== Rules Management ====================

@cli.group()
def rules():
    """Firewall rules management"""
    pass


@rules.command()
@click.option('--format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def list(format: str):
    """List all firewall rules"""
    try:
        client = get_client()
        data = client.get('rules')
        
        if format == 'json':
            click.echo(json.dumps(data, indent=2))
        else:
            if not data:
                click.echo('No rules found')
                return
            
            table_data = [
                [
                    rule['rule_id'],
                    rule.get('src_ip', '*'),
                    rule.get('dst_ip', '*'),
                    rule.get('dst_port', '*'),
                    rule.get('protocol', '*'),
                    rule['action'],
                    rule['priority'],
                    '✓' if rule['enabled'] else '✗'
                ]
                for rule in data
            ]
            
            click.echo(tabulate(
                table_data,
                headers=['Rule ID', 'Source IP', 'Dest IP', 'Port', 'Protocol', 'Action', 'Priority', 'Enabled'],
                tablefmt='grid'
            ))
    except Exception as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'), err=True)
        sys.exit(1)


@rules.command()
@click.option('--src-ip', help='Source IP (CIDR notation)')
@click.option('--dst-ip', help='Destination IP (CIDR notation)')
@click.option('--dst-port', type=int, help='Destination port')
@click.option('--protocol', type=click.Choice(['TCP', 'UDP', 'ICMP', 'ALL']), help='Protocol')
@click.option('--action', type=click.Choice(['ALLOW', 'BLOCK', 'THROTTLE']), required=True, help='Action')
@click.option('--priority', type=int, default=100, help='Priority (1-1000, default: 100)')
def add(src_ip: Optional[str], dst_ip: Optional[str], dst_port: Optional[int], 
        protocol: Optional[str], action: str, priority: int):
    """Add a new firewall rule"""
    try:
        if not any([src_ip, dst_ip, dst_port]):
            click.echo(click.style('✗ At least one of --src-ip, --dst-ip, or --dst-port must be specified', fg='red'), err=True)
            sys.exit(1)
        
        client = get_client()
        rule_data = {
            'action': action,
            'priority': priority,
            'enabled': True
        }
        
        if src_ip:
            rule_data['src_ip'] = src_ip
        if dst_ip:
            rule_data['dst_ip'] = dst_ip
        if dst_port:
            rule_data['dst_port'] = dst_port
        if protocol:
            rule_data['protocol'] = protocol
        
        result = client.post('rules', json=rule_data)
        
        click.echo(click.style(f'✓ Rule created: {result["rule_id"]}', fg='green'))
    except Exception as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'), err=True)
        sys.exit(1)


@rules.command()
@click.argument('rule_id')
def delete(rule_id: str):
    """Delete a firewall rule"""
    try:
        if not click.confirm(f'Delete rule {rule_id}?'):
            click.echo('Cancelled')
            return
        
        client = get_client()
        client.delete(f'rules/{rule_id}')
        
        click.echo(click.style(f'✓ Rule {rule_id} deleted', fg='green'))
    except Exception as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'), err=True)
        sys.exit(1)


# ==================== IP Blocking ====================

@cli.group()
def block():
    """IP blocking management"""
    pass


@block.command()
@click.argument('ip_address')
@click.option('--duration', type=int, default=3600, help='Block duration in seconds (default: 3600)')
def add(ip_address: str, duration: int):
    """Block an IP address"""
    try:
        client = get_client()
        result = client.post(f'block/{ip_address}', params={'duration': duration})
        
        click.echo(click.style(f'✓ IP {ip_address} blocked until {result["blocked_until"]}', fg='green'))
    except Exception as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'), err=True)
        sys.exit(1)


@block.command()
@click.argument('ip_address')
def remove(ip_address: str):
    """Unblock an IP address"""
    try:
        client = get_client()
        client.delete(f'block/{ip_address}')
        
        click.echo(click.style(f'✓ IP {ip_address} unblocked', fg='green'))
    except Exception as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'), err=True)
        sys.exit(1)


# ==================== Anomalies ====================

@cli.group()
def anomalies():
    """Anomaly detection"""
    pass


@anomalies.command()
@click.option('--limit', type=int, default=20, help='Maximum results (default: 20)')
def list(limit: int):
    """List recent anomalies"""
    try:
        client = get_client()
        data = client.get('anomalies', params={'limit': limit})
        
        if not data:
            click.echo('No anomalies detected')
            return
        
        table_data = [
            [
                anomaly['timestamp'],
                anomaly['src_ip'],
                f"{anomaly['anomaly_score']:.3f}",
                '✓' if anomaly['is_anomaly'] else '✗',
                anomaly['reason'][:50],
                f"{anomaly['confidence']:.2f}"
            ]
            for anomaly in data
        ]
        
        click.echo(tabulate(
            table_data,
            headers=['Timestamp', 'Source IP', 'Score', 'Anomaly', 'Reason', 'Confidence'],
            tablefmt='grid'
        ))
    except Exception as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'), err=True)
        sys.exit(1)


# ==================== Profiles ====================

@cli.group()
def profile():
    """IP profiling"""
    pass


@profile.command()
@click.argument('ip_address')
def show(ip_address: str):
    """Show IP profile"""
    try:
        client = get_client()
        data = client.get(f'profiles/{ip_address}')
        
        click.echo(click.style(f'\n=== Profile: {ip_address} ===\n', fg='cyan', bold=True))
        click.echo(f"Reputation Score: {data['reputation_score']:.1f}")
        click.echo(f"Total Connections: {data['total_connections']:,}")
        click.echo(f"First Seen: {data['first_seen']}")
        click.echo(f"Last Seen: {data['last_seen']}")
        
        if data['patterns_detected']:
            click.echo(click.style('\nPatterns Detected:', fg='cyan'))
            for pattern in data['patterns_detected']:
                click.echo(f"  - {pattern}")
    except Exception as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'), err=True)
        sys.exit(1)


# ==================== Main Entry Point ====================

if __name__ == '__main__':
    cli()