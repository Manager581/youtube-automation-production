# YouTube Automation + Genius Link QR Code Generator

Master Project - YouTube Automation + Video Creation + Google Drive QR Code Automation

## Overview

This repository contains automation scripts for:
1. YouTube video creation and automation
2. Genius Link QR code generation and Google Drive upload

## Projects

### 1. Genius Link QR Code Automation

Automates the workflow of creating QR codes from Genius affiliate links and uploading them to Google Drive.

**Workflow:**
1. Takes a list of Genius Links (from file or hardcoded)
2. Resolves each link to its destination URL
3. Creates a new "-qr" version via Genius Link API
4. Generates a QR code image for the new link
5. Uploads the QR code to Google Drive

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Google Cloud Project with Drive API enabled
- Genius Link account with API access
- Service account credentials for Google Drive

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd youtube-automation
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

5. **Set up Google Drive Service Account:**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select existing one
   - Enable Google Drive API
   - Create a Service Account
   - Download the JSON key file
   - Save it as `service-account.json` in the project root
   - Share your target Google Drive folder with the service account email

6. **Get your Genius Link API credentials:**
   - Log in to [Genius Link](https://geni.us)
   - Go to API settings
   - Copy your API Key and Secret
   - Add them to your `.env` file

7. **Get your Google Drive Folder ID:**
   - Open the folder in Google Drive
   - The URL will look like: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`
   - Copy the `FOLDER_ID_HERE` part
   - Add it to your `.env` file

### Configuration

Edit `.env` file with your credentials:

```env
# Genius Link API Credentials
GENIUS_API_KEY=your_actual_api_key
GENIUS_API_SECRET=your_actual_api_secret
GENIUS_GROUP_ID=416519
TSID=20320

# Google Drive Configuration
GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE=./service-account.json
GOOGLE_DRIVE_FOLDER_ID=your_actual_folder_id

# Local Storage
QR_CODE_DIR=./qr_codes/
```

### Usage

#### Option 1: Use a links file (recommended)

1. Create a file called `genius_links.txt`:
   ```bash
   cp genius_links.txt.example genius_links.txt
   ```

2. Edit the file and add your Genius Links (one per line):
   ```
   https://geni.us/link1
   https://geni.us/link2
   https://geni.us/link3
   ```

3. Run the script:
   ```bash
   python genius_qr_automation.py
   ```

#### Option 2: Use hardcoded links

If no `genius_links.txt` file exists, the script will use the hardcoded list in the script.

### Running the Script

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the automation
python genius_qr_automation.py
```

### Output

- QR code images are saved to `./qr_codes/` directory
- Logs are written to `genius_qr_automation.log`
- Console output shows real-time progress
- Google Drive links are logged for each uploaded file

## Features

✅ Environment-based configuration (no hardcoded credentials)
✅ Comprehensive error handling and logging
✅ Rate limiting to respect API limits
✅ Support for loading links from file or hardcoded list
✅ High-quality QR code generation
✅ Automatic Google Drive upload
✅ Progress tracking and summary statistics
✅ Detailed logging to file and console

## Troubleshooting

### "Missing required configuration" error
- Make sure your `.env` file exists and has all required values
- Check that you've copied `.env.example` to `.env` and filled in the values

### "Service account file not found" error
- Ensure `service-account.json` exists in the project root
- Verify the path in your `.env` file

### Google Drive upload fails
- Make sure you've shared the target folder with the service account email
- The service account email looks like: `account-name@project-id.iam.gserviceaccount.com`
- Verify the folder ID is correct

### Genius Link API errors
- Check your API key and secret are correct
- Ensure your Genius Link account is active
- Verify you're not hitting rate limits (script includes delays)

## Project Structure

```
youtube-automation/
├── genius_qr_automation.py    # Main automation script
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .env                       # Your actual configuration (not in git)
├── genius_links.txt.example   # Example links file
├── genius_links.txt           # Your actual links (not in git)
├── service-account.json       # Google credentials (not in git)
├── qr_codes/                  # Generated QR codes (not in git)
└── README.md                  # This file
```

## License

MIT
