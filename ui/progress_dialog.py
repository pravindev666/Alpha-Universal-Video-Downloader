import tkinter as tk
from tkinter import ttk

class ProgressDialog(tk.Toplevel):
    def __init__(self, parent, callback=None):
        super().__init__(parent)
        self.title("Download Progress")
        self.geometry("400x150")
        self.transient(parent)
        self.grab_set()
        
        self.callback = callback
        
        # UI Elements
        self.status_label = ttk.Label(self, text="Starting download...")
        self.status_label.pack(pady=(20, 5))
        
        self.progress = ttk.Progressbar(self, mode='indeterminate')
        self.progress.pack(fill='x', padx=20, pady=10)
        self.progress.start()
        
        self.percent_label = ttk.Label(self, text="Preparing...")
        self.percent_label.pack(pady=5)
        
        # Center window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def update_progress(self, data):
        """Update progress bar and labels"""
        status = data.get('status')
        if status == 'downloading':
            percent = data.get('percent', '0%')
            speed = data.get('speed', '0')
            filename = data.get('filename', '')
            
            # Switch to determinate mode if we have a percentage
            if '%' in percent:
                try:
                    p_val = float(percent.replace('%', ''))
                    self.progress.configure(mode='determinate', value=p_val)
                    self.progress.stop()
                except ValueError:
                    pass
            
            self.status_label.config(text=f"Downloading: {filename}")
            self.percent_label.config(text=f"{percent} ({speed})")
            
        elif status == 'finished':
            self.status_label.config(text="Download Complete!")
            self.percent_label.config(text="Processing...")
            self.progress.configure(mode='indeterminate')
            self.progress.start()
            self.after(1000, self.destroy)
        
        elif status == 'error':
             self.status_label.config(text="Error occurred")
             self.percent_label.config(text=data.get('error', 'Unknown Error'))
             self.progress.stop()

    def close(self):
        self.destroy()
