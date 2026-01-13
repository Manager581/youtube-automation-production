# Quick Start Guide

## 🚀 Get Running in 5 Minutes

### Step 1: Set Up Virtual Environment (Already Done!)

```bash
# The virtual environment is already created
source venv/bin/activate
```

### Step 2: Configure Your Credentials

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

You need to fill in:
- `GENIUS_API_KEY` - From your Genius Link account
- `GENIUS_API_SECRET` - From your Genius Link account
- `GOOGLE_DRIVE_FOLDER_ID` - The folder where QR codes will be uploaded

### Step 3: Add Your Service Account File

1. Download your Google Cloud service account JSON file
2. Save it as `service-account.json` in this directory
3. Make sure the path in `.env` matches: `GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE=./service-account.json`

### Step 4: Create Your Links File (Optional)

```bash
# Copy the example
cp genius_links.txt.example genius_links.txt

# Edit with your actual links
nano genius_links.txt
```

Or skip this and use the hardcoded links in the script.

### Step 5: Run It!

```bash
python genius_qr_automation.py
```

## 📋 What the Script Does

1. **Loads your Genius Links** - From `genius_links.txt` or hardcoded list
2. **Resolves each link** - Follows the redirect to get the destination URL
3. **Creates a QR version** - Uses Genius API to create a new link with `-qr` suffix
4. **Generates QR code** - Creates a high-quality PNG image
5. **Uploads to Drive** - Saves the QR code to your Google Drive folder

## 📁 Where to Find Things

- **QR Codes**: `./qr_codes/` directory
- **Log File**: `genius_qr_automation.log`
- **Your Links**: `genius_links.txt`
- **Config**: `.env`

## 🔍 Example Run

```
2026-01-13 10:30:15 - INFO - ============================================================
2026-01-13 10:30:15 - INFO - Genius Link QR Code Automation - Starting
2026-01-13 10:30:15 - INFO - ============================================================
2026-01-13 10:30:15 - INFO - Processing 10 links

2026-01-13 10:30:15 - INFO - [1/10] Processing link...
2026-01-13 10:30:15 - INFO - Processing link: https://geni.us/yvyBS3
2026-01-13 10:30:16 - INFO - Resolved to: https://www.amazon.com/...
2026-01-13 10:30:17 - INFO - Created QR link: https://geni.us/yvyBS3-qr
2026-01-13 10:30:17 - INFO - Generated QR code: ./qr_codes/yvyBS3-qr.png
2026-01-13 10:30:18 - INFO - Uploaded to Google Drive - ID: 1abc...xyz
2026-01-13 10:30:18 - INFO - ✓ Successfully processed: https://geni.us/yvyBS3
...
```

## ⚠️ Troubleshooting

### "Missing required configuration" error
→ Check your `.env` file has all values filled in

### "Service account file not found"
→ Make sure `service-account.json` exists and path in `.env` is correct

### "Permission denied" on Google Drive
→ Share your Drive folder with the service account email (found in service-account.json)

### Rate limiting / API errors
→ The script includes 3-second delays between requests - this is normal

## 🎯 Pro Tips

1. **Start small** - Test with 2-3 links first
2. **Check the logs** - `genius_qr_automation.log` has detailed info
3. **Verify in Drive** - Check your folder after the first few uploads
4. **Keep credentials safe** - Never commit `.env` or `service-account.json` to git

## 📞 Need Help?

Check the main README.md for detailed troubleshooting and configuration options.
