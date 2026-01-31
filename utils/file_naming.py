import re
from pathlib import Path

def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename"""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'\s+', ' ', filename).strip()
    return filename[:200]  # Truncate if too long

def get_platform_from_url(url: str) -> str:
    """Detect platform from URL"""
    platforms = {
        'facebook.com': 'facebook',
        'instagram.com': 'instagram', 
        'twitter.com': 'twitter',
        'x.com': 'twitter',
        'linkedin.com': 'linkedin',
        'tiktok.com': 'tiktok',
        'youtube.com': 'youtube',
        'tomorrow.com': 'unknown',
        'threads.net': 'threads',
        'threads.com': 'threads',
        'pinterest.com': 'pinterest'

    }
    
    for domain, platform in platforms.items():
        if domain in url:
            return platform
    return 'unknown'
