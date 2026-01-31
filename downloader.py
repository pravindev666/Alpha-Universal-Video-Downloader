import yt_dlp
import os
import tempfile
import requests
from pathlib import Path
from typing import Optional, Dict, List

# Free proxies provided by user (Auto-rotation)
PROXIES = [
    'http://103.153.39.19:80',
    'http://47.74.135.104:8888',
    'http://20.206.106.192:80',
]

class VideoDownloader:
    def __init__(self, output_dir: str = "downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        # Point to local ffmpeg if it exists
        self.ffmpeg_location = os.path.join(os.getcwd(), 'ffmpeg.exe') if os.path.exists('ffmpeg.exe') else None
        
    def _format_bytes(self, size):
        if not size:
            return "Unknown size"
        power = 2**10
        n = 0
        power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
        while size > power:
            size /= power
            n += 1
        return f"{size:.1f}{power_labels[n]}B"

    def _get_working_proxy(self):
        """Find a working proxy from the list"""
        print("Searching for working proxy...")
        for proxy in PROXIES:
            try:
                # Test connectivity to YouTube
                requests.get('https://www.youtube.com', proxies={'http': proxy, 'https': proxy}, timeout=3)
                print(f"Found working proxy: {proxy}")
                return proxy
            except:
                continue
        return None

    def _sanitize_url(self, url: str) -> str:
        """Clean URL and handle domain hotfixes"""
        url = url.strip()
        # Threads hotfix: Meta acquired threads.com, but yt-dlp might only match threads.net
        if 'threads.com' in url:
            url = url.replace('threads.com', 'threads.net')
        
        # Threads format normalization: @user/post/ID -> t/ID (Better for generic extraction)
        if 'threads.net/@' in url and '/post/' in url:
            import re
            match = re.search(r'/post/([^/?#\s]+)', url)
            if match:
                post_id = match.group(1)
                url = f"https://www.threads.net/t/{post_id}"
                
        return url

    def get_video_info(self, url: str, cookies_content: str = None) -> Optional[Dict]:
        """Extract video metadata using robust anti-bot settings, optional cookies, and proxy fallback"""
        url = self._sanitize_url(url)
        
        cookie_file = None
        if cookies_content:
            fd, cookie_file = tempfile.mkstemp(suffix='.txt', text=True)
            with os.fdopen(fd, 'w') as f:
                f.write(cookies_content)

        # Base options
        base_opts = {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.google.com/',
            'socket_timeout': 30,
            'retries': 20,
            'source_address': '0.0.0.0',
            'cachedir': False,
            'extractor_args': {
                'youtube': {
                    'player_client': 'android',
                    'player_skip': 'webpage,configs,js',
                    'include_ssl_logs': False
                }
            }
        }
        
        if cookie_file:
            base_opts['cookiefile'] = cookie_file

        # Strategy 1: Direct Connection
        try:
            with yt_dlp.YoutubeDL(base_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return self._process_info(info)
        except Exception as e:
            print(f"Direct fetch failed: {e}")
            
            # Strategy 2: Try Proxy
            proxy = self._get_working_proxy()
            if proxy:
                print(f"Retrying with proxy: {proxy}")
                base_opts['proxy'] = proxy
                try:
                    with yt_dlp.YoutubeDL(base_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        return self._process_info(info)
                except Exception as proxy_e:
                     print(f"Proxy fetch failed: {proxy_e}")
                     return {'error': f"Direct & Proxy failed. Last error: {str(proxy_e)}"}
            
            return {'error': str(e)}
        finally:
            if cookie_file and os.path.exists(cookie_file):
                os.remove(cookie_file)

    def _process_info(self, info):
        """Helper to process raw info into app format"""
        formats_summary = []
        seen_resolutions = set()
        best_audio_size = 0
        
        for f in info.get('formats', []):
            if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    size = f.get('filesize') or f.get('filesize_approx') or 0
                    if size > best_audio_size:
                        best_audio_size = size

        for f in info.get('formats', []):
            height = f.get('height')
            if not height: continue
            
            if height not in seen_resolutions:
                seen_resolutions.add(height)
                v_size = f.get('filesize') or f.get('filesize_approx') or 0
                total_estimate = v_size + best_audio_size if v_size else 0
                ext = 'mp4' 
                formats_summary.append({
                    'label': f"{height}p",
                    'size': total_estimate,
                    'height': height,
                    'type': 'video',
                    'ext': ext
                })
        
        formats_summary.sort(key=lambda x: x['height'], reverse=True)
        
        options = []
        for fmt in formats_summary:
            size_str = self._format_bytes(fmt['size'])
            options.append({
                'label': f"Video: {fmt['label']} - {fmt['ext'].upper()} (~{size_str})",
                'id': f"bestvideo[height={fmt['height']}]+bestaudio/best[height={fmt['height']}]",
                'type': 'video'
            })
        
        audio_size_str = self._format_bytes(best_audio_size)
        options.append({
            'label': f"Audio Only - MP3 (~{audio_size_str})",
            'id': 'audio_only',
            'type': 'audio'
        })

        return {
            'title': info.get('title', 'Unknown'),
            'duration': info.get('duration', 0),
            'thumbnail': info.get('thumbnail'),
            'uploader': info.get('uploader', ''),
            'quality_options': options
        }
    
    def download_video(self, 
                      url: str, 
                      format_selector: str = 'best',
                      progress_callback=None,
                      cookies_content: str = None) -> Dict:
        """Download video with robust fallback strategy and proxies"""
        url = self._sanitize_url(url)
        
        cookie_file = None
        if cookies_content:
            fd, cookie_file = tempfile.mkstemp(suffix='.txt', text=True)
            with os.fdopen(fd, 'w') as f:
                f.write(cookies_content)

        def progress_hook(d):
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', '0%')
                speed = d.get('_speed_str', '0')
                if progress_callback:
                    progress_callback({
                        'status': 'downloading',
                        'percent': percent,
                        'speed': speed,
                        'filename': d.get('filename', '')
                    })
            elif d['status'] == 'finished':
                if progress_callback:
                    progress_callback({
                        'status': 'finished',
                        'filename': d.get('filename', '')
                    })

        strategies = [format_selector]
        if format_selector != 'audio_only':
            strategies.extend(['best[ext=mp4]', 'best[height<=720]', 'best', 'worst[ext=mp4]'])

        last_error = None
        
        # Try strategies (Direct)
        for fmt in strategies:
            ydl_opts = self._get_download_opts(fmt, progress_hook, cookie_file, None)
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    return self._success_result(filename, info, format_selector)
            except Exception as e:
                last_error = str(e)
                continue
        
        # If direct failed: Try Proxy with best strategy only (to save time)
        print("Direct download failed. Trying proxies...")
        proxy = self._get_working_proxy()
        if proxy:
            ydl_opts = self._get_download_opts(format_selector, progress_hook, cookie_file, proxy) # Try requested format first
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    return self._success_result(filename, info, format_selector)
            except Exception as e:
                return {'success': False, 'error': f"Proxy failed: {e}"}

        return {'success': False, 'error': f"All attempts failed. Last error: {last_error}"}

    def _get_download_opts(self, fmt, hook, cookie_file, proxy):
        opts = {
            'outtmpl': str(self.output_dir / '%(title)s_%(id)s.%(ext)s'),
            'progress_hooks': [hook],
            'restrictfilenames': True,
            'merge_output_format': 'mp4',
            'ffmpeg_location': self.ffmpeg_location,
            'source_address': '0.0.0.0',
            'extractor_args': {
                'youtube': {'player_client': 'android', 'player_skip': 'webpage,configs,js', 'include_ssl_logs': False}
            }
        }
        if fmt == 'audio_only':
            opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            })
        else:
            opts['format'] = fmt
            
        if cookie_file: opts['cookiefile'] = cookie_file
        if proxy: opts['proxy'] = proxy
        return opts

    def _success_result(self, filename, info, fmt):
        if fmt == 'audio_only':
            filename = str(Path(filename).with_suffix('.mp3'))
        return {
            'success': True,
            'filename': filename,
            'title': info.get('title'),
            'duration': info.get('duration', 0)
        }
        
    def _cleanup(self, cookie_file):
         if cookie_file and os.path.exists(cookie_file):
            try: os.remove(cookie_file)
            except: pass
