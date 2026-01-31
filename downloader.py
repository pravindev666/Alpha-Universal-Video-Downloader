import yt_dlp
import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, List

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

    def get_video_info(self, url: str, cookies_content: str = None) -> Optional[Dict]:
        """Extract video metadata using robust anti-bot settings and optional cookies"""
        
        cookie_file = None
        if cookies_content:
            # Create a temporary cookie file
            fd, cookie_file = tempfile.mkstemp(suffix='.txt', text=True)
            with os.fdopen(fd, 'w') as f:
                f.write(cookies_content)

        self.ydl_opts_base = {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            # Anti-bot options (Standard Android Client)
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'referer': 'https://www.youtube.com/',
            'socket_timeout': 30,
            'retries': 20,
            'extractor_args': {
                'youtube': {
                    'player_client': 'android',
                    'player_skip': 'webpage,configs,js',
                    'include_ssl_logs': False
                }
            }
        }
        
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts_base) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Process formats
                formats_summary = []
                seen_resolutions = set()
                
                # audio size estimate (take the best audio)
                best_audio_size = 0
                for f in info.get('formats', []):
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                         # It's audio only
                         size = f.get('filesize') or f.get('filesize_approx') or 0
                         if size > best_audio_size:
                             best_audio_size = size

                # Video formats
                for f in info.get('formats', []):
                    # Skip audio-only or video-only if we serve mixed, but usually we want to see available resolutions
                    height = f.get('height')
                    if not height: continue
                    
                    if height not in seen_resolutions:
                        seen_resolutions.add(height)
                        # Estimate size: video stream + audio stream
                        v_size = f.get('filesize') or f.get('filesize_approx') or 0
                        total_estimate = v_size + best_audio_size if v_size else 0
                        
                        # Determine ext (default to mp4 if we merge)
                        ext = 'mp4' 
                        
                        formats_summary.append({
                            'label': f"{height}p",
                            'size': total_estimate,
                            'height': height,
                            'type': 'video',
                            'ext': ext
                        })
                
                # Sort by resolution desc
                formats_summary.sort(key=lambda x: x['height'], reverse=True)
                
                # Add human readable strings
                options = []
                for fmt in formats_summary:
                    size_str = self._format_bytes(fmt['size'])
                    options.append({
                        'label': f"Video: {fmt['label']} - {fmt['ext'].upper()} (~{size_str})",
                        'id': f"bestvideo[height={fmt['height']}]+bestaudio/best[height={fmt['height']}]",
                        'type': 'video'
                    })
                
                # Add Audio Only option
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
        except Exception as e:
            print(f"Error getting info: {e}")
            return {'error': str(e)}
        finally:
            # Cleanup cookie file
            if cookie_file and os.path.exists(cookie_file):
                os.remove(cookie_file)
    
    def download_video(self, 
                      url: str, 
                      format_selector: str = 'best',
                      progress_callback=None,
                      cookies_content: str = None) -> Dict:
        """Download video with progress callback and optional cookies"""
        
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
        
        ydl_opts = {
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'restrictfilenames': True,
            'merge_output_format': 'mp4',
            'format_sort': ['res', 'ext:mp4:m4a'],
            'ffmpeg_location': self.ffmpeg_location,
            # Add stronger client options for download too
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'android', 'web'],
                    'player_skip': ['webpage', 'configs', 'js'],
                    'include_ssl_logs': [False]
                }
            }
        }

        if cookie_file:
            ydl_opts['cookiefile'] = cookie_file

        if format_selector == 'audio_only':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            ydl_opts['format'] = format_selector
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                if format_selector == 'audio_only':
                    filename = str(Path(filename).with_suffix('.mp3'))
                    
                return {
                    'success': True,
                    'filename': filename,
                    'title': info.get('title'),
                    'duration': info.get('duration', 0)
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cookie_file and os.path.exists(cookie_file):
                os.remove(cookie_file)
