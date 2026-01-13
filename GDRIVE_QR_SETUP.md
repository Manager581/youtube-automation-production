# Google Drive QR Code Extractor - Setup Guide

## What This Script Does

This script scans your Google Drive folder, extracts malformed Genius links from filenames, fixes them, generates QR codes, and uploads them back to Drive.

**Example:**
- **Input file**: `2-in-1 Mixer httpsgeni.usxh2SUO.mp4`
- **Extracts**: `httpsgeni.usxh2SUO`
- **Fixes to**: `https://geni.us/xh2SUO`
- **Creates QR**: `2-in-1 Mixer httpsgeni.usxh2SUO.png` (QR code linking to `https://geni.us/xh2SUO`)
- **Uploads to**: `*GENERAL > QR Codes` folder

---

## Step-by-Step Setup

### ✅ Step 1: You've Already Done This!

You've already:
- Created a Google Cloud Service Account
- Downloaded the `service-account.json` file
- Shared your `*GENERAL` folder with the service account

Great! Now let's continue.

### Step 2: Get the QR Codes Folder ID

1. Open Google Drive and go to your `*GENERAL` folder
2. Find the `QR Codes` subfolder (I can see it in your screenshot)
3. **Click into the QR Codes folder**
4. Look at the URL in your browser:
   ```
   https://drive.google.com/drive/folders/SOME_LONG_ID_HERE
   ```
5. Copy the `SOME_LONG_ID_HERE` part (that's your QR Codes folder ID)

### Step 3: Configure the Script

```bash
# Create your .env file
cp .env.example .env

# Edit it
nano .env  # or use your preferred editor
```

Fill in these values in `.env`:

```env
# Google Drive Configuration (required for this script)
GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE=./service-account.json

# The *GENERAL folder ID (already filled in!)
GENERAL_FOLDER_ID=1PyoofGC1rY6PHq0aGURVw9afK0AA6Gzr

# The QR Codes subfolder ID (YOU NEED TO ADD THIS)
QR_CODES_FOLDER_ID=paste_your_qr_codes_folder_id_here

# Local storage for QR codes
QR_CODE_DIR=./qr_codes/

# Dry run mode (test without uploading)
DRY_RUN=false
```

**Important:**
- You already have `GENERAL_FOLDER_ID` from your screenshot: `1PyoofGC1rY6PHq0aGURVw9afK0AA6Gzr`
- You need to add your `QR_CODES_FOLDER_ID` from Step 2

### Step 4: Make Sure Your Service Account JSON is in Place

```bash
# Check if the file exists
ls -la service-account.json

# If it's not there, download it again from Google Cloud Console
# and save it as service-account.json in this directory
```

---

## Running the Script

### Test Run First (Recommended!)

Run in **dry-run mode** to see what will happen without actually uploading:

```bash
# Activate virtual environment
source venv/bin/activate

# Set dry-run mode
# Edit .env and change: DRY_RUN=true

# Run the script
python gdrive_qr_extractor.py
```

This will:
- ✅ List all files in `*GENERAL`
- ✅ Show which links it found
- ✅ Generate QR codes locally (in `./qr_codes/`)
- ✅ Show what would be uploaded
- ❌ NOT upload anything to Drive

### Real Run

Once you're happy with the dry-run results:

```bash
# Edit .env and change: DRY_RUN=false

# Run the script
python gdrive_qr_extractor.py
```

---

## What to Expect

### Console Output:

```
============================================================
Google Drive QR Code Extractor - Starting
============================================================
Connecting to Google Drive...
Listing files in folder ID: 1PyoofGC1rY6PHq0aGURVw9afK0AA6Gzr
Found 1247 total files in folder

Processing 1247 files...
============================================================

[1/1247] Processing: 2-in-1 Mixer httpsgeni.usxh2SUO.mp4
  → Extracted link: https://geni.us/xh2SUO
  → Generated QR code: 2-in-1 Mixer httpsgeni.usxh2SUO.png
  ✓ Uploaded: 2-in-1 Mixer httpsgeni.usxh2SUO.png (ID: 1abc...xyz)

[2/1247] Processing: 3-in-1 Vacuum httpsgeni.usABC123.mp4
  → Extracted link: https://geni.us/ABC123
  → Generated QR code: 3-in-1 Vacuum httpsgeni.usABC123.png
  ✓ Uploaded: 3-in-1 Vacuum httpsgeni.usABC123.png (ID: 1def...xyz)

...

============================================================
Processing Complete!
Successful: 1240
Failed: 2
Skipped (no link): 5
Total: 1247
============================================================

📄 Report saved to: qr_extraction_report.csv

✅ Done!
```

### Files Created:

1. **Local QR codes**: `./qr_codes/*.png` (can be deleted after upload)
2. **Log file**: `gdrive_qr_extractor.log` (detailed processing log)
3. **CSV report**: `qr_extraction_report.csv` (summary of all files processed)

### Google Drive:

All QR codes will be uploaded to: `*GENERAL > QR Codes/`

Each QR code will have the same name as the original file, but with `.png` extension.

---

## CSV Report

The script generates `qr_extraction_report.csv` with details:

| filename | file_id | genius_link | qr_file_id | status |
|----------|---------|-------------|------------|--------|
| 2-in-1 Mixer httpsgeni.usxh2SUO.mp4 | 1abc... | https://geni.us/xh2SUO | 1xyz... | SUCCESS |
| 3-in-1 Vacuum httpsgeni.usABC123.mp4 | 1def... | https://geni.us/ABC123 | 1uvw... | SUCCESS |
| SomeFile.mp4 | 1ghi... | NOT_FOUND | - | SKIPPED |

Use this to:
- See which files were processed successfully
- Identify files that failed or were skipped
- Track the mapping between original files and QR codes

---

## Troubleshooting

### "Missing required configuration" error
- Make sure you've created `.env` from `.env.example`
- Verify all three IDs are filled in:
  - `GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE`
  - `GENERAL_FOLDER_ID`
  - `QR_CODES_FOLDER_ID`

### "Service account file not found"
- Check that `service-account.json` exists in the project directory
- Verify the path in `.env` is correct

### "Error listing files" / "Permission denied"
- Make sure you've shared the `*GENERAL` folder with the service account email
- The email is in your `service-account.json` file, look for `"client_email"`
- Give it "Editor" or "Content Manager" permission

### "No files found in the folder"
- Double-check the `GENERAL_FOLDER_ID` in your `.env`
- Make sure you're using the folder ID, not a file ID

### Files are being skipped
- The script looks for patterns like `httpsgeni.us` or `httpsgeniusxx` in filenames
- If your filenames have a different pattern, the regex may need adjustment
- Check the log file for details on why files were skipped

### Rate limiting / API errors
- The script includes small delays (0.5s) between uploads
- If you have thousands of files, the script may take a while
- Google Drive API limit: 10,000 requests per 100 seconds (you should be fine!)

---

## Advanced Usage

### Process Only a Few Files (Testing)

To test on just a few files before processing thousands:

1. Create a test subfolder in `*GENERAL`
2. Move a few files into it
3. Update `GENERAL_FOLDER_ID` in `.env` to point to the test folder
4. Run the script
5. Once satisfied, change back to the main folder ID

### Resume After Interruption

If the script is interrupted:
- Check `qr_extraction_report.csv` to see what was processed
- The script will process ALL files again, but Drive will handle duplicates
- OR manually remove successfully processed files from the source folder

### Change QR Code Settings

Edit `gdrive_qr_extractor.py` around line 173 to customize:

```python
qr = qrcode.QRCode(
    version=1,           # Size (1-40, higher = bigger)
    error_correction=qrcode.constants.ERROR_CORRECT_L,  # Error correction level
    box_size=10,         # Pixels per box
    border=4,            # Border width in boxes
)
```

---

## API Limits & Costs

### Google Drive API (Free Tier):
- ✅ **10,000 requests per 100 seconds** per project
- ✅ **1,000 requests per 100 seconds** per user
- ✅ **Completely FREE** (no charges)

### For 1,000 files:
- ~1 request to list all files
- ~1,000 requests to upload QR codes
- **Total: ~1,001 requests**
- **Time: ~8-10 minutes** (with built-in delays)

### For 10,000 files:
- **Total: ~10,001 requests**
- **Time: ~1.5-2 hours**
- Still well within free limits!

---

## Next Steps

1. ✅ Get your QR Codes folder ID (Step 2 above)
2. ✅ Create your `.env` file (Step 3 above)
3. ✅ Run a dry-run test
4. ✅ Check the output and CSV report
5. ✅ Run the real upload
6. ✅ Verify QR codes in your Drive folder

---

## Questions?

If something's not working, check:
1. `gdrive_qr_extractor.log` - detailed error messages
2. `qr_extraction_report.csv` - see which files failed
3. The troubleshooting section above

Good luck! 🚀
