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

    # URL Input Form
    with st.form(key='url_form'):
        c1, c2 = st.columns([4, 1])
        with c1:
            url = st.text_input("Paste Video URL:", placeholder="https://www.youtube.com/watch?v=...", label_visibility="visible")
        with c2:
            st.write("") # Spacer for alignment
            st.write("")
            submit_btn = st.form_submit_button("🔍 Preview")
            
    # Logic handles 'url' variable which is updated upon form submission

    # Logic handles 'url' variable which is updated upon form submission

    if url:
        if 'video_info' not in st.session_state or st.session_state.get('last_url') != url:
            with st.spinner("Fetching video info..."):
                # Pass cookies to get_video_info
                info = downloader.get_video_info(url)
                if info:
                    st.session_state['video_info'] = info
                    st.session_state['last_url'] = url
                else:
                    st.error("Could not fetch video info. Please check the URL.")

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
                # Pass cookies to download_wrapper
                download_wrapper(downloader, url, selected_format_id)
            
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

    # Footer
    st.markdown("---")
    # Footer
    st.markdown("---")
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
