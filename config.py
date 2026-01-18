"""
SkateHive Dashboard Configuration

Loads configuration from the monorepo's skatehive.config file,
or falls back to environment variables and defaults.
"""

import os
from pathlib import Path
from typing import Dict, Optional
import subprocess


def load_monorepo_config() -> Dict[str, str]:
    """Load configuration from skatehive.config in the monorepo root."""
    config = {}
    
    # Find monorepo root (parent of skatehive-dashboard)
    dashboard_dir = Path(__file__).parent
    monorepo_root = dashboard_dir.parent
    config_file = monorepo_root / "skatehive.config"
    
    if config_file.exists():
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                # Parse KEY="value" or KEY=value
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    config[key] = value
    
    return config


def get_tailscale_hostname() -> Optional[str]:
    """Try to detect Tailscale hostname automatically."""
    try:
        result = subprocess.run(
            ['tailscale', 'status', '--json'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            dns_name = data.get('Self', {}).get('DNSName', '')
            if dns_name:
                return dns_name.rstrip('.')
    except Exception:
        pass
    return None


# Load configuration
_config = load_monorepo_config()

# Node Configuration
NODE_NAME = _config.get('NODE_NAME', os.environ.get('NODE_NAME', 'skatehive-node'))
NODE_ROLE = _config.get('NODE_ROLE', os.environ.get('NODE_ROLE', 'primary'))

# Tailscale Configuration
TAILSCALE_HOSTNAME = _config.get(
    'TAILSCALE_HOSTNAME',
    os.environ.get('TAILSCALE_HOSTNAME', get_tailscale_hostname() or '')
)

# Service Ports
VIDEO_TRANSCODER_PORT = int(_config.get('VIDEO_TRANSCODER_PORT', os.environ.get('VIDEO_TRANSCODER_PORT', '8081')))
INSTAGRAM_DOWNLOADER_PORT = int(_config.get('INSTAGRAM_DOWNLOADER_PORT', os.environ.get('INSTAGRAM_DOWNLOADER_PORT', '6666')))
ACCOUNT_MANAGER_PORT = int(_config.get('ACCOUNT_MANAGER_PORT', os.environ.get('ACCOUNT_MANAGER_PORT', '3001')))

# Funnel Paths
VIDEO_FUNNEL_PATH = _config.get('VIDEO_FUNNEL_PATH', os.environ.get('VIDEO_FUNNEL_PATH', '/video'))
INSTAGRAM_FUNNEL_PATH = _config.get('INSTAGRAM_FUNNEL_PATH', os.environ.get('INSTAGRAM_FUNNEL_PATH', '/instagram'))

# Other Nodes (comma-separated list)
OTHER_NODES_STR = _config.get('OTHER_NODES', os.environ.get('OTHER_NODES', ''))
OTHER_NODES = [n.strip() for n in OTHER_NODES_STR.split(',') if n.strip()]

# Known SkateHive Nodes - load from config or use defaults
# These can be overridden by setting SKATEHIVE_NODES_JSON in skatehive.config
_nodes_json = _config.get('SKATEHIVE_NODES_JSON', '')
if _nodes_json:
    try:
        import json
        SKATEHIVE_NODES = json.loads(_nodes_json)
    except:
        SKATEHIVE_NODES = {}
else:
    # Default nodes - used as fallback when config doesn't specify
    SKATEHIVE_NODES = {}

# Build nodes from current config and OTHER_NODES
if NODE_NAME and TAILSCALE_HOSTNAME:
    SKATEHIVE_NODES[NODE_NAME] = {
        "name": _config.get('NODE_DISPLAY_NAME', NODE_NAME.replace('-', ' ').title()),
        "hostname": TAILSCALE_HOSTNAME,
        "role": NODE_ROLE,
    }

# Add other known nodes from OTHER_NODES list (format: "name:hostname:role" or "name:hostname:role:lan_ip:instagram_port")
for node_str in OTHER_NODES:
    parts = node_str.split(':')
    if len(parts) >= 2:
        node_id = parts[0]
        hostname = parts[1]
        role = parts[2] if len(parts) > 2 else 'secondary'
        lan_ip = parts[3] if len(parts) > 3 else None
        instagram_port = int(parts[4]) if len(parts) > 4 else INSTAGRAM_DOWNLOADER_PORT
        if node_id not in SKATEHIVE_NODES:
            SKATEHIVE_NODES[node_id] = {
                "name": node_id.replace('-', ' ').title(),
                "hostname": hostname,
                "role": role,
                "lan_ip": lan_ip,
                "instagram_port": instagram_port,
                "video_port": VIDEO_TRANSCODER_PORT,
            }

# Fallback defaults if no nodes configured at all
if not SKATEHIVE_NODES:
    SKATEHIVE_NODES = {
        "macmini": {
            "name": "Mac Mini M4",
            "hostname": "minivlad.tail83ea3e.ts.net",
            "role": "primary",
        },
        "raspberry": {
            "name": "Raspberry Pi",
            "hostname": "vladsberry.tail83ea3e.ts.net",
            "role": "secondary",
        },
    }

# Computed URLs
def get_local_url(service: str) -> str:
    """Get local URL for a service."""
    ports = {
        'video': VIDEO_TRANSCODER_PORT,
        'instagram': INSTAGRAM_DOWNLOADER_PORT,
        'account': ACCOUNT_MANAGER_PORT,
    }
    port = ports.get(service, 8080)
    return f"http://localhost:{port}"


def get_external_url(service: str, hostname: str = None) -> str:
    """Get external Tailscale URL for a service."""
    if hostname is None:
        hostname = TAILSCALE_HOSTNAME
    if not hostname:
        return ""
    
    paths = {
        'video': VIDEO_FUNNEL_PATH,
        'instagram': INSTAGRAM_FUNNEL_PATH,
    }
    path = paths.get(service, '')
    return f"https://{hostname}{path}"


def get_all_node_urls(service: str) -> Dict[str, str]:
    """Get URLs for a service across all known nodes."""
    urls = {}
    
    # Current node
    if TAILSCALE_HOSTNAME:
        urls[NODE_NAME] = get_external_url(service)
    
    # Other known nodes
    for node_id, node_info in SKATEHIVE_NODES.items():
        if node_info['hostname'] != TAILSCALE_HOSTNAME:
            urls[node_info['name']] = get_external_url(service, node_info['hostname'])
    
    return urls


# Service URLs for this node
VIDEO_LOCAL_URL = get_local_url('video')
INSTAGRAM_LOCAL_URL = get_local_url('instagram')
ACCOUNT_LOCAL_URL = get_local_url('account')

VIDEO_EXTERNAL_URL = get_external_url('video')
INSTAGRAM_EXTERNAL_URL = get_external_url('instagram')

# All nodes video URLs (for unified monitoring)
ALL_VIDEO_NODES = get_all_node_urls('video')
ALL_INSTAGRAM_NODES = get_all_node_urls('instagram')


# Debug: Print config on import if DEBUG is set
if os.environ.get('DEBUG_CONFIG'):
    print(f"Dashboard Config:")
    print(f"  NODE_NAME: {NODE_NAME}")
    print(f"  NODE_ROLE: {NODE_ROLE}")
    print(f"  TAILSCALE_HOSTNAME: {TAILSCALE_HOSTNAME}")
    print(f"  VIDEO_LOCAL_URL: {VIDEO_LOCAL_URL}")
    print(f"  VIDEO_EXTERNAL_URL: {VIDEO_EXTERNAL_URL}")
    print(f"  INSTAGRAM_LOCAL_URL: {INSTAGRAM_LOCAL_URL}")
    print(f"  INSTAGRAM_EXTERNAL_URL: {INSTAGRAM_EXTERNAL_URL}")
    print(f"  ALL_VIDEO_NODES: {ALL_VIDEO_NODES}")
