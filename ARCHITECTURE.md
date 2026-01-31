# 🏗️ System Architecture - Universal Media Downloader

## High-Level Data Flow

```mermaid
flowchart TB
    subgraph USER["👤 User Interface"]
        URL[Paste URL]
        COOKIES[Upload Cookies]
        QUALITY[Select Quality]
        DOWNLOAD[Download Button]
    end

    subgraph STREAMLIT["☁️ Streamlit Cloud"]
        APP[app.py]
        DOWNLOADER[downloader.py]
        COOKIE_FILE[Temp Cookie File]
    end

    subgraph PROXY["🏠 Residential Proxy Layer"]
        WEBSHARE[Webshare 10 IPs]
        ROTATION[Random Rotation]
    end

    subgraph PLATFORMS["🌐 Platform APIs"]
        YT[YouTube]
        IG[Instagram]
        FB[Facebook]
        TH[Threads]
    end

    subgraph RESPONSE["📦 Response"]
        INFO[Video Metadata]
        FORMATS[Available Formats]
        STREAM[Video Stream]
    end

    URL --> APP
    COOKIES --> COOKIE_FILE
    APP --> DOWNLOADER
    DOWNLOADER --> ROTATION
    ROTATION --> WEBSHARE
    WEBSHARE --> YT
    WEBSHARE --> IG
    WEBSHARE --> FB
    WEBSHARE --> TH
    YT --> INFO
    IG --> INFO
    FB --> INFO
    TH --> INFO
    INFO --> FORMATS
    QUALITY --> DOWNLOADER
    DOWNLOADER --> STREAM
    STREAM --> DOWNLOAD
```

---

## Detailed Component Diagram

```mermaid
flowchart LR
    subgraph INPUT["📥 Input Layer"]
        U_URL["URL Input"]
        U_COOK["Cookie Secret"]
    end

    subgraph PROCESS["⚙️ Processing Layer"]
        SANITIZE["_sanitize_url()"]
        YT_BRUTE["Brute Force Configs"]
        PROXY_SEL["_get_working_proxy()"]
    end

    subgraph YTDLP["🎬 yt-dlp Engine"]
        EXTRACT["extract_info()"]
        DOWNLOAD_V["download()"]
    end

    subgraph NETWORK["🌐 Network Layer"]
        DIRECT["Direct Connection"]
        RESID["Residential Proxy"]
    end

    subgraph OUTPUT["📤 Output Layer"]
        META["Video Metadata"]
        FILE["Downloaded File"]
    end

    U_URL --> SANITIZE
    U_COOK --> YTDLP
    SANITIZE --> YT_BRUTE
    YT_BRUTE --> PROXY_SEL
    PROXY_SEL --> RESID
    SANITIZE --> DIRECT
    RESID --> EXTRACT
    DIRECT --> EXTRACT
    EXTRACT --> META
    META --> DOWNLOAD_V
    DOWNLOAD_V --> FILE
```

---

## Proxy Rotation Strategy

```mermaid
sequenceDiagram
    participant App as Streamlit App
    participant DL as Downloader
    participant Proxy as Proxy Pool
    participant YT as YouTube

    App->>DL: Download Request (URL)
    DL->>DL: Detect YouTube URL
    DL->>Proxy: Get Random Proxy
    Proxy-->>DL: http://user:pass@ip:port
    DL->>YT: Request via Proxy
    alt Success
        YT-->>DL: Video Stream
        DL-->>App: Download Complete
    else 403 Forbidden
        DL->>Proxy: Get Next Proxy
        DL->>YT: Retry with New Proxy
    end
```

---

## Client Simulation Order

| Priority | Client | Use Case |
|----------|--------|----------|
| 1 | `android_creator` | Bypasses most cloud blocks |
| 2 | `ios_creator` | Alternative creator client |
| 3 | `tv_embedded` | TV app simulation |
| 4 | `android` | Standard mobile |
| 5 | `ios` | Apple devices |
| 6 | `mweb` | Mobile web |
| 7 | `web` | Desktop fallback |

---

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit UI, session state, download triggers |
| `downloader.py` | Core yt-dlp wrapper, proxy rotation, format processing |
| `cookies.txt` | Local cookie storage |
| `COPY_THIS_TO_STREAMLIT.toml` | Streamlit Secrets template |
