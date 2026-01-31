import requests
from PIL import Image
from io import BytesIO

def load_thumbnail(url: str, size=(320, 180)):
    """Load and resize image from URL for Tkinter"""
    try:
        # Lazy import to avoid crashing on headless systems (Streamlit Cloud)
        from PIL import ImageTk
        
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        img_data = response.content
        img = Image.open(BytesIO(img_data))
        img.thumbnail(size)
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"Error loading thumbnail: {e}")
        return None
