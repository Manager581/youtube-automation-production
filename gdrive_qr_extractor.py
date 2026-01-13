#!/usr/bin/env python3
"""
Google Drive QR Code Extractor

This script extracts malformed Genius links from Google Drive filenames,
fixes the format, generates QR codes, and uploads them back to Drive.

Workflow:
1. Lists all files in the specified Google Drive folder (*GENERAL)
2. Extracts malformed Genius links from filenames (e.g., "httpsgeni.usXXXXX")
3. Fixes the format to proper URLs (e.g., "https://geni.us/XXXXX")
4. Generates QR codes for the corrected links
5. Uploads QR codes to the "QR Codes" subfolder with the same filename

Author: YouTube Automation
Date: 2026-01-13
"""

import os
import sys
import re
import csv
import time
import logging
import qrcode
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dotenv import load_dotenv

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Load environment variables
load_dotenv()

# --- Configuration ---
GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE")
GENERAL_FOLDER_ID = os.getenv("GENERAL_FOLDER_ID")  # The *GENERAL folder
QR_CODES_FOLDER_ID = os.getenv("QR_CODES_FOLDER_ID")  # The QR Codes subfolder
QR_CODE_DIR = os.getenv("QR_CODE_DIR", "./qr_codes/")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gdrive_qr_extractor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Regex pattern to extract malformed Genius links from filenames
# Pattern: httpsgeni.us[code] or httpsgeniusxx[code]
GENIUS_LINK_PATTERN = re.compile(r'https?geni\.?us(\w+)', re.IGNORECASE)


def validate_config() -> bool:
    """Validates that all required configuration is present."""
    required_vars = {
        "GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE": GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE,
        "GENERAL_FOLDER_ID": GENERAL_FOLDER_ID,
        "QR_CODES_FOLDER_ID": QR_CODES_FOLDER_ID,
    }

    missing = [key for key, value in required_vars.items() if not value]

    if missing:
        logger.error(f"Missing required configuration: {', '.join(missing)}")
        logger.error("Please set these in your .env file")
        return False

    if not os.path.exists(GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE):
        logger.error(f"Service account file not found: {GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE}")
        return False

    return True


def get_drive_service():
    """Creates and returns a Google Drive service instance."""
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)


def extract_genius_link(filename: str) -> Optional[str]:
    """
    Extracts and fixes a malformed Genius link from a filename.

    Args:
        filename: The filename containing the malformed link

    Returns:
        The corrected Genius link, or None if no link found

    Examples:
        "2-in-1 Mixer httpsgeni.usxh2SUO.mp4" -> "https://geni.us/xh2SUO"
        "Product httpsgeniusABC123.mp4" -> "https://geni.us/ABC123"
    """
    match = GENIUS_LINK_PATTERN.search(filename)
    if match:
        code = match.group(1)
        return f"https://geni.us/{code}"
    return None


def list_files_in_folder(drive_service, folder_id: str) -> List[Dict]:
    """
    Lists all files in the specified Google Drive folder.

    Args:
        drive_service: Google Drive API service instance
        folder_id: The folder ID to list files from

    Returns:
        List of file dictionaries with id, name, and mimeType
    """
    logger.info(f"Listing files in folder ID: {folder_id}")

    files = []
    page_token = None

    try:
        while True:
            query = f"'{folder_id}' in parents and trashed=false"
            results = drive_service.files().list(
                q=query,
                pageSize=1000,  # Max allowed
                fields="nextPageToken, files(id, name, mimeType)",
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            batch = results.get('files', [])
            files.extend(batch)

            page_token = results.get('nextPageToken')
            if not page_token:
                break

            logger.info(f"Retrieved {len(files)} files so far...")

        logger.info(f"Found {len(files)} total files in folder")
        return files

    except HttpError as e:
        logger.error(f"Error listing files: {e}")
        return []


def generate_qr_code(url: str, output_path: str) -> bool:
    """
    Generates a QR code for the given URL and saves it to a file.

    Args:
        url: The URL to encode in the QR code
        output_path: Path where to save the QR code image

    Returns:
        True if successful, False otherwise
    """
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        img.save(output_path)
        logger.debug(f"Generated QR code: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error generating QR code for {url}: {e}")
        return False


def upload_qr_code(drive_service, filepath: str, qr_folder_id: str, original_filename: str) -> Optional[str]:
    """
    Uploads a QR code to Google Drive.

    Args:
        drive_service: Google Drive API service instance
        filepath: Local path to the QR code file
        qr_folder_id: Folder ID where to upload the QR code
        original_filename: Original filename (will be used with .png extension)

    Returns:
        The file ID of the uploaded file, or None if upload fails
    """
    if DRY_RUN:
        logger.info(f"[DRY RUN] Would upload: {original_filename}.png")
        return "dry-run-id"

    try:
        # Remove original extension and add .png
        base_name = os.path.splitext(original_filename)[0]
        qr_filename = f"{base_name}.png"

        file_metadata = {
            "name": qr_filename,
            "parents": [qr_folder_id]
        }
        media = MediaFileUpload(filepath, mimetype="image/png")

        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id,name,webViewLink",
            supportsAllDrives=True
        ).execute()

        file_id = file.get("id")
        web_link = file.get("webViewLink")
        logger.info(f"✓ Uploaded: {qr_filename} (ID: {file_id})")
        return file_id

    except HttpError as e:
        logger.error(f"Error uploading {original_filename}: {e}")
        return None


def process_files(drive_service, files: List[Dict], qr_folder_id: str) -> Tuple[int, int, List[Dict]]:
    """
    Processes all files: extracts links, generates QR codes, uploads to Drive.

    Args:
        drive_service: Google Drive API service instance
        files: List of file dictionaries from Drive
        qr_folder_id: Folder ID where to upload QR codes

    Returns:
        Tuple of (successful_count, failed_count, processed_records)
    """
    successful = 0
    failed = 0
    skipped = 0
    processed_records = []

    # Ensure QR code directory exists
    Path(QR_CODE_DIR).mkdir(parents=True, exist_ok=True)

    total = len(files)
    logger.info(f"\nProcessing {total} files...")
    logger.info("=" * 60)

    for i, file in enumerate(files, 1):
        filename = file.get('name', '')
        file_id = file.get('id', '')

        logger.info(f"\n[{i}/{total}] Processing: {filename}")

        # Extract Genius link
        genius_link = extract_genius_link(filename)

        if not genius_link:
            logger.warning(f"  ⚠ No Genius link found in filename, skipping")
            skipped += 1
            processed_records.append({
                'filename': filename,
                'file_id': file_id,
                'genius_link': 'NOT_FOUND',
                'status': 'SKIPPED'
            })
            continue

        logger.info(f"  → Extracted link: {genius_link}")

        # Generate QR code
        qr_filename = f"{os.path.splitext(filename)[0]}.png"
        qr_filepath = os.path.join(QR_CODE_DIR, qr_filename)

        if not generate_qr_code(genius_link, qr_filepath):
            logger.error(f"  ✗ Failed to generate QR code")
            failed += 1
            processed_records.append({
                'filename': filename,
                'file_id': file_id,
                'genius_link': genius_link,
                'status': 'QR_GENERATION_FAILED'
            })
            continue

        logger.info(f"  → Generated QR code: {qr_filename}")

        # Upload to Drive
        uploaded_id = upload_qr_code(drive_service, qr_filepath, qr_folder_id, filename)

        if uploaded_id:
            successful += 1
            processed_records.append({
                'filename': filename,
                'file_id': file_id,
                'genius_link': genius_link,
                'qr_file_id': uploaded_id,
                'status': 'SUCCESS'
            })
        else:
            failed += 1
            processed_records.append({
                'filename': filename,
                'file_id': file_id,
                'genius_link': genius_link,
                'status': 'UPLOAD_FAILED'
            })

        # Rate limiting - small delay to avoid API limits
        if i < total:
            time.sleep(0.5)

    logger.info("\n" + "=" * 60)
    logger.info("Processing Complete!")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Skipped (no link): {skipped}")
    logger.info(f"Total: {total}")
    logger.info("=" * 60)

    return successful, failed, processed_records


def save_report(records: List[Dict], output_file: str = "qr_extraction_report.csv"):
    """
    Saves a CSV report of all processed files.

    Args:
        records: List of processed file records
        output_file: Path to save the CSV report
    """
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if records:
                writer = csv.DictWriter(f, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)

        logger.info(f"\n📄 Report saved to: {output_file}")

    except Exception as e:
        logger.error(f"Error saving report: {e}")


def main():
    """Main function to run the extraction workflow."""
    logger.info("=" * 60)
    logger.info("Google Drive QR Code Extractor - Starting")
    if DRY_RUN:
        logger.info("🧪 DRY RUN MODE - No files will be uploaded")
    logger.info("=" * 60)

    # Validate configuration
    if not validate_config():
        logger.error("Configuration validation failed. Exiting.")
        sys.exit(1)

    # Create Drive service
    logger.info("Connecting to Google Drive...")
    try:
        drive_service = get_drive_service()
    except Exception as e:
        logger.error(f"Failed to connect to Google Drive: {e}")
        sys.exit(1)

    # List files in *GENERAL folder
    files = list_files_in_folder(drive_service, GENERAL_FOLDER_ID)

    if not files:
        logger.warning("No files found in the folder. Exiting.")
        sys.exit(0)

    # Process all files
    successful, failed, records = process_files(drive_service, files, QR_CODES_FOLDER_ID)

    # Save report
    save_report(records)

    logger.info("\n✅ Done!")


if __name__ == "__main__":
    main()
