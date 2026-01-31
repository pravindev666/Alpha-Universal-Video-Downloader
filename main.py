import tkinter as tk
import ctypes
from ui.main_window import MainWindow

def set_dpi_awareness():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

def main():
    set_dpi_awareness()
    
    root = tk.Tk()
    
    # Set default theme/style if possible
    try:
        style = tk.ttk.Style()
        style.theme_use('clam')
    except:
        pass
        
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
