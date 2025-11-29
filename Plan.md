# Project Plan: Discord Printer Relay V2

## 1\. Architectural Shift

**Goal:** Eliminate port forwarding and static IP requirements.
**Method:** Switch from **Server-Push (HTTP)** to **Client-Pull (WebSocket)**.

| Component | Technology | Role |
| :--- | :--- | :--- |
| **User Interface** | Discord | User sends commands (`/link`, `/print`). |
| **The Relay (VPS)** | Python (aiohttp + socket.io) | The central hub. Hosting the Bot and the WebSocket Server. |
| **Gateway** | Nginx | Reverse Proxy. Handles SSL termination and WSS upgrades. |
| **The Receiver (PC)** | Python (NiceGUI + Pystray) | Client app. Runs in background. Connects outbound to Relay. |
| **Hardware** | ESC/POS Printer | Connected via USB. |

-----

## 2\. Server-Side Implementation (The Relay)

**Host:** VPS (Ubuntu/Debian recommended)
**Domain:** `printerbot.dragnai.dev`

### A. The Database (Storage)

A simple JSON or SQLite database to store permanent links.

```json
// db.json schema
{
  "permanent_token_uuid": {
    "user_id": "discord_user_id_123",
    "created_at": "timestamp",
    "settings": {"width": "58mm"}
  }
}
```

### B. The Logic (Python)

The script must run the Discord Bot and the Socket.IO server on the same asyncio loop.

  * **Guest Mode:** If a socket connects without a token, assign it a temporary 6-digit code (e.g., `X9P2`).
  * **User Mode:** If a socket connects *with* a token, validate against DB and mark as "Online".
  * **Linking:** When user types `/link X9P2`, finding the matching Guest socket, generate a UUID, save to DB, and emit it to the socket.

### C. Nginx Configuration

Required to forward WebSocket headers correctly.

```nginx
server {
    server_name printerbot.dragnai.dev;
    location /socket.io/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

-----

## 3\. Client-Side Implementation (The Receiver)

**Target OS:** Windows 10/11 (Primary), Linux/Raspberry Pi (Secondary)

### A. The UI Stack

  * **GUI:** `NiceGUI` (Runs a local web-engine wrapped in a native window).
  * **System Tray:** `pystray` (Allows app to minimize to tray and run background).
  * **Network:** `python-socketio[client]`.
  * **Printer:** `python-escpos`.

### B. Startup Logic

1.  **Check `config.json`**:
      * *Exists?* Connect to WSS with `auth={'token': '...'}`.
      * *Missing?* Connect to WSS as Guest.
2.  **State Management**:
      * **Unlinked:** Display huge code (e.g., `X9P2`) and instructions.
      * **Linked:** Minimize to tray immediately. Show "Online" in Tray Tooltip.

### C. Driver Management (Zadig)

  * **Strategy:** "Guided Manual Setup".
  * **Bundle:** Include `zadig.exe` in the application `resources/` folder.
  * **UI Integration:** If `python-escpos` throws a "Driver Not Found" or "Backend Error", the GUI displays a "Driver Setup Required" button.
  * **Action:** Clicking the button launches the bundled `zadig.exe`.

### D. Autostart

  * **Method:** Registry Key (Windows).
  * **Logic:** A checkbox in Settings "Run on Startup". If checked, add executable path to `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.

-----

## 4\. The Workflows

### Workflow A: First Time Setup (The "Smart TV" Flow)

1.  User installs and runs **Receiver**.
2.  App connects to VPS. No token found.
3.  VPS sends `{'code': 'A1B2'}`.
4.  App shows: *"Type `/link A1B2` in Discord"*.
5.  User types command in Discord.
6.  Bot validates code, generates Token `UUID-555`.
7.  Bot sends Token to App via WebSocket.
8.  App saves Token to `config.json` and turns Green (Online).

### Workflow B: Printing

1.  User types `/print [Image/Text]` in Discord.
2.  Bot converts content to a **1-bit Dithered Monochromatic Image**.
3.  Bot looks up the WebSocket ID associated with that User ID.
4.  Bot emits `print_job` event with base64 image data.
5.  Receiver gets event, decodes base64.
6.  Receiver passes image to `python-escpos` -\> USB Printer.

-----

## 5\. Development Phase Checklist

### Phase 1: Infrastructure (VPS)

  - [ ] Set up `printerbot.dragnai.dev` DNS.
  - [ ] Install Nginx and Certbot (SSL).
  - [ ] Configure Nginx for WebSocket forwarding.
  - [ ] Create `systemd` service for the Relay.

### Phase 2: The Relay Code

  - [ ] Create basic Discord Bot + Socket.IO skeleton.
  - [ ] Implement "Pending Code" logic (In-memory dict).
  - [ ] Implement "Permanent Token" logic (DB persistence).
  - [ ] Implement Image Processing (Resize/Dither).

### Phase 3: The Receiver App

  - [ ] Create NiceGUI layout (Unlinked vs Linked states).
  - [ ] Integrate `pystray` for background minimizing.
  - [ ] Implement `config.json` load/save.
  - [ ] Implement `python-escpos` printing logic.
  - [ ] Add "Launch Zadig" button and bundle the .exe.

### Phase 4: Packaging

  - [ ] Use `PyInstaller` to compile Receiver to `.exe`.
  - [ ] Test on a fresh Windows PC (ensure Zadig path resolution works).
  - [ ] (Optional) Create an Installer using Inno Setup for "Add to Desktop" support.