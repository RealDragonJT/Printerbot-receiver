# PrintsAlot V2 Receiver

The desktop receiver application for PrinterBot V2. This app connects your local thermal printer to the PrinterBot Relay server, allowing you to print from Discord.

## Prerequisites

*   **Python 3.10+**
*   **Thermal Printer** (USB)
*   **Zadig** (for installing WinUSB driver)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <your-repo-url>
    cd PrintsAlotV2
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Driver Setup (Zadig)**:
    *   Download and run [Zadig](https://zadig.akeo.ie/).
    *   Options > List All Devices.
    *   Select your printer from the dropdown.
    *   Ensure the target driver is **WinUSB**.
    *   Click "Replace Driver" or "Install Driver".

## Configuration

1.  **Environment Variables**:
    Create a `.env` file in the root directory:
    ```env
    RELAY_URL=https://printerbot.dragnai.dev
    ```

2.  **Run the App**:
    ```bash
    python -m src.main
    ```

## Usage

1.  The app will launch in a window.
2.  If not linked, copy the **Pairing Code**.
3.  In your Discord server, run:
    ```
    /printer link <code>
    ```
4.  The app will confirm the link and save the token to `config.json`.
5.  Configure your printer settings (width, auto-cut) in the app.

## Troubleshooting

*   **"Printer not found"**: Ensure the printer is on, connected via USB, and the WinUSB driver is installed via Zadig.
*   **"Connection failed"**: Check your internet connection and ensure `RELAY_URL` in `.env` is correct.
