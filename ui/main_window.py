import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from downloader import VideoDownloader
from ui.progress_dialog import ProgressDialog
from utils.thumbnail import load_thumbnail

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal Media Downloader")
        self.root.geometry("800x600")
        
        self.downloader = VideoDownloader()
        
        self.setup_ui()
    
    def setup_ui(self):
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill='x', padx=20, pady=10)
        ttk.Label(header_frame, text="Universal Media Downloader", font=('Segoe UI', 16, 'bold')).pack(side='left')
        
        # URL Input Area
        url_frame = ttk.LabelFrame(self.root, text="Video URL", padding=15)
        url_frame.pack(fill='x', padx=20, pady=5)
        
        self.url_entry = ttk.Entry(url_frame, font=('Segoe UI', 12))
        self.url_entry.pack(side='left', fill='x', expand=True, padx=(0,10))
        self.url_entry.bind('<Return>', lambda e: self.preview_video())
        
        btn_frame = ttk.Frame(url_frame)
        btn_frame.pack(side='right')
        
        ttk.Button(btn_frame, text="Paste", command=self.paste_url, width=10).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Preview", command=self.preview_video, width=10).pack(side='left', padx=2)
        
        # Preview Area
        self.preview_frame = ttk.LabelFrame(self.root, text="Video Information", padding=15)
        self.preview_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.info_label = ttk.Label(self.preview_frame, text="Enter a URL and click Preview", font=('Segoe UI', 10))
        self.info_label.pack(pady=20)
        
        self.thumb_label = ttk.Label(self.preview_frame)
        self.thumb_label.pack(pady=10)
        
        self.current_video_info = None

        # Download Controls
        control_frame = ttk.Frame(self.root, padding=20)
        control_frame.pack(fill='x', side='bottom')
        
        ttk.Label(control_frame, text="Quality:").pack(side='left', padx=(0,5))
        self.format_var = tk.StringVar(value="best")
        formats = ["best", "bestvideo+bestaudio/best", "best[height<=1080]", "best[height<=720]", "worst"]
        ttk.OptionMenu(control_frame, self.format_var, "best", *formats).pack(side='left')
        
        self.download_btn = ttk.Button(control_frame, text="Download Video", command=self.start_download, state='disabled', width=20)
        self.download_btn.pack(side='right')

    def paste_url(self):
        try:
            url = self.root.clipboard_get()
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)
            self.preview_video()
        except:
            pass

    def preview_video(self):
        url = self.url_entry.get().strip()
        if not url:
            return

        self.info_label.config(text="Fetching video info...")
        self.download_btn.config(state='disabled')
        
        def fetch():
            info = self.downloader.get_video_info(url)
            self.root.after(0, lambda: self.update_preview(info))
            
        threading.Thread(target=fetch, daemon=True).start()

    def update_preview(self, info):
        if not info:
            self.info_label.config(text="Error: Could not fetch video info. Check URL.")
            self.current_video_info = None
            return
            
        self.current_video_info = info
        
        # Update Text
        display_text = f"Title: {info['title']}\n"
        display_text += f"Duration: {int(info['duration'])}s\n"
        display_text += f"Uploader: {info['uploader']}"
        self.info_label.config(text=display_text)
        
        # Load Thumbnail
        if info.get('thumbnail'):
            # Run in separate thread to avoid UI freeze
            def load_thumb():
                photo = load_thumbnail(info['thumbnail'])
                if photo:
                    self.root.after(0, lambda p=photo: self._set_thumbnail(p))
            threading.Thread(target=load_thumb, daemon=True).start()
            
        self.download_btn.config(state='normal')

    def _set_thumbnail(self, photo):
        self.thumb_label.config(image=photo)
        self.thumb_label.image = photo # Keep reference

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url: 
            return
            
        # Create progress dialog
        progress_dialog = ProgressDialog(self.root)
        
        def download_thread():
            result = self.downloader.download_video(
                url, 
                format_selector=self.format_var.get(),
                progress_callback=lambda d: self.root.after(0, lambda: progress_dialog.update_progress(d))
            )
            
            if not result.get('success'):
                 self.root.after(0, lambda: progress_dialog.update_progress({'status': 'error', 'error': result.get('error')}))
            
        threading.Thread(target=download_thread, daemon=True).start()
