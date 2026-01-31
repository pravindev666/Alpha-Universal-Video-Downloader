import streamlit as st
import threading
import queue
import time
import os
from downloader import VideoDownloader

st.set_page_config(page_title="Universal Media Downloader", page_icon="⬇️")

def main():
    st.title("⬇️ Universal Media Downloader")
    st.markdown("Download videos from YouTube, Instagram, Facebook, and more.")

    # Initialize downloader
    downloader = VideoDownloader()

    # CRITICAL: Clear session if URL changes to avoid "ghost" metadata
    if 'last_url' not in st.session_state:
        st.session_state['last_url'] = ""

    # URL Input (Removed form for reactivity)
    c1, c2 = st.columns([4, 1])
    with c1:
        # We use a key for the text input to ensure it's tracked properly
        url = st.text_input("Paste Video URL:", placeholder="https://www.youtube.com/watch?v=...", key="url_input").strip()
    
    with c2:
        st.write("") # Spacer
        st.write("")
        if st.button("🔄 Clear", help="Click to reset the app"):
            for key in ['video_info', 'last_file', 'last_url', 'last_url_downloaded']:
                if key in st.session_state: del st.session_state[key]
            st.rerun()

    # Detect URL change and wipe old state immediately
    if url != st.session_state['last_url']:
        for key in ['video_info', 'last_file']:
            if key in st.session_state: del st.session_state[key]
        st.session_state['last_url'] = url
        st.rerun() # Force fresh state for the new URL

    # Logic handles 'url' variable which is updated upon form submission
    
    # Cookie Upload (Optional)
    cookies = st.file_uploader("🍪 Cookies (Optional - for private/age-restricted videos)", type=['txt', 'cookies'], help="Upload Netscape cookies.txt file")
    
    # 🍪 AUTOMATIC COOKIE LOADING (The "No Headache" Fix)
    # Check for server-side cookies so users don't have to upload anything
    server_cookies = None
    
    # Priority 1: Check Streamlit Secrets (Best for Cloud)
    if not server_cookies:
        try:
            if "cookies" in st.secrets:
                server_cookies = st.secrets["cookies"]
                st.toast("✅ Using Server Credentials", icon="🍪")
        except:
            pass
            
    # Priority 2: Check local file (Best for Local Development)
    if not server_cookies and os.path.exists("cookies.txt"):
        try:
            with open("cookies.txt", "r") as f:
                server_cookies = f.read()
            st.toast("✅ Using Local Cookies File", icon="🍪")
        except:
            pass

    if url:
        # Create a container for the status/error area
        status_area = st.container()
        
        # Auto-fetch if info is missing or URL changed
        if 'video_info' not in st.session_state:
            with st.spinner("Fetching video info..."):
                # Handle cookies: User Upload > Server Default > None
                user_cookies = cookies.getvalue().decode("utf-8") if cookies else None
                final_cookies = user_cookies if user_cookies else server_cookies
                
                # Pass cookies to get_video_info
                info = downloader.get_video_info(url, cookies_content=final_cookies)
                
                if info and 'error' not in info:
                    st.session_state['video_info'] = info
                    st.session_state['last_url'] = url
                else:
                    error_msg = info.get('error') if info else "Unknown error"
                    with status_area:
                        st.error(f"❌ Error fetching video: {error_msg}")
                        if "403" in error_msg:
                            st.warning("⚠️ YouTube is blocking the connection. This is common with Cloud Servers.")
                        elif "Sign in" in error_msg or "login required" in error_msg.lower():
                            st.warning("⚠️ This video requires a login (Instagram/Age Restricted). Please upload cookies to fix this.")
                    return # Stop here if error

        if 'video_info' in st.session_state and st.session_state.get('last_url') == url:
            info = st.session_state['video_info']
            
            # Display Info
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if info.get('thumbnail'):
                    st.image(info['thumbnail'], use_container_width=True)
            
            with col2:
                st.subheader(info['title'])
                st.write(f"**Duration:** {int(info['duration'])}s")
                st.write(f"**Uploader:** {info['uploader']}")
            
            # Options
            quality_options = info.get('quality_options', [])
            # Create a simple list of labels for the selectbox
            format_labels = [q['label'] for q in quality_options]
            selected_label = st.selectbox("Select Quality", format_labels)
            
            # Find the corresponding format ID
            selected_format_id = "best" # default
            for q in quality_options:
                if q['label'] == selected_label:
                    selected_format_id = q['id']
                    break
            
            # Download Action
            if st.button("Fetch Video", type="primary"):
                # Resolve cookies again for the download action (User > Server > None)
                # Note: We duplicate logic briefly here or rely on session state if we refactored, 
                # but simplest is to just re-read since variables are local scope.
                
                user_c = cookies.getvalue().decode("utf-8") if cookies else None
                
                # Re-fetch server cookies if needed (conceptually cleaner to store in session, but this is fast)
                server_c = None
                try: 
                    if "cookies" in st.secrets: server_c = st.secrets["cookies"]
                except: pass
                if not server_c and os.path.exists("cookies.txt"):
                    try: server_c = open("cookies.txt", "r").read()
                    except: pass
                
                final_c = user_c if user_c else server_c
                
                download_wrapper(downloader, url, selected_format_id, final_c)
            
            # Show download button if file exists in session
            if 'last_file' in st.session_state and st.session_state.get('last_url_downloaded') == url:
                file_path = st.session_state['last_file']
                if os.path.exists(file_path):
                    try:
                        mime_type = "audio/mpeg" if file_path.endswith(".mp3") else "video/mp4"
                        with open(file_path, "rb") as file:
                            btn = st.download_button(
                                label="⬇️ Download to Device",
                                data=file,
                                file_name=os.path.basename(file_path),
                                mime=mime_type
                            )
                    except Exception as e:
                        st.error(f"Error opening file: {e}")

    # Footer - Supported Sites & Disclaimer
    st.markdown("---")
    
    with st.expander("🌐 View Supported Sites & Requirements"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **Full Support (Public & Private*):**
            - 📸 **Instagram** (Posts, Reels, Stories)
            - 👥 **Facebook** (Public & Private)
            - 🧵 **Threads** (New!)
            - 🎞️ **YouTube** (Regular & Shorts)
            
            *\*Requires cookies.txt for Private content.*
            """)
        with col2:
            st.markdown("""
            **Global Support:**
            - ✖️ **X / Twitter**
            - 📌 **Pinterest**
            - 🎵 **TikTok**
            - 🎥 **1000+ Others** (Vimeo, Dailymotion, etc.)
            """)
            
        st.info("💡 **Pro Tip:** If a video fails or says 'Login Required', simply upload your `cookies.txt` file or add it to the server secrets to bypass the block.")
        
        # Debug Version Info
        import yt_dlp
        st.caption(f"Engine Version: `yt-dlp {yt_dlp.version.__version__}`")

    st.markdown(
        """
<div style='text-align: center; color: #666;'>
    <h3 style='margin-bottom: 5px; font-size: 24px;'>App by Pravin A Mathew</h3>
    <p style='font-size: 0.8em; margin: 0;'>Property of Zeta Aztra Technologies</p>
    <p style='font-size: 0.8em; margin: 0;'>Operated by Zeta Aztra Technologies (Individual Proprietorship, India)</p>
    <p style='font-size: 0.8em; margin-top: 5px; margin-bottom: 15px;'>© 2026 Zeta Aztra Technologies. All Rights Reserved.</p>
    <p style='color: #ff4b4b; font-weight: bold; margin-bottom: 5px;'>⚠️ DISCLAIMER: FOR PERSONAL USE ONLY</p>
    <p style='font-size: 0.75em; line-height: 1.4; max-width: 800px; margin: 0 auto;'>
        This tool is designed for educational purposes and personal archiving only. 
        Users are responsible for ensuring they have the right to download and use the content. 
        Running this tool to infringe on copyright or violate terms of service of any platform is strictly prohibited. 
        The author accepts no liability for misuse of this application.
    </p>
</div>
        """,
        unsafe_allow_html=True
    )



def download_wrapper(downloader, url, format_selector, cookies_content=None):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Queue for communicating between thread and streamlit
    q = queue.Queue()
    
    def progress_callback(d):
        q.put(d)
        
    def worker():
        result = downloader.download_video(
            url, 
            format_selector=format_selector,
            progress_callback=progress_callback,
            cookies_content=cookies_content
        )
        q.put({'done': True, 'result': result})

    # Start download in a separate thread
    t = threading.Thread(target=worker)
    t.start()
    
    # Process queue
    while True:
        try:
            msg = q.get(timeout=0.1)
            
            if 'done' in msg:
                result = msg['result']
                if result.get('success'):
                    progress_bar.progress(100)
                    filename = result.get('filename')
                    status_text.success(f"Processing Complete! File ready.")
                    
                    # Store in session state to show download button
                    st.session_state['last_file'] = filename
                    st.session_state['last_url_downloaded'] = url
                    st.rerun() # Rerun to show the button
                else:
                    status_text.error(f"Error: {result.get('error')}")
                break
                
            status = msg.get('status')
            if status == 'downloading':
                percent_str = msg.get('percent', '0%').replace('%','')
                try:
                    percent = float(percent_str) / 100
                    progress_bar.progress(min(percent, 1.0))
                    status_text.text(f"Downloading... {msg.get('percent')} ({msg.get('speed')})")
                except:
                    pass
            elif status == 'finished':
                progress_bar.progress(100)
                status_text.text("Processing file...")
                
        except queue.Empty:
            if not t.is_alive():
                break
            time.sleep(0.1)

if __name__ == "__main__":
    main()
