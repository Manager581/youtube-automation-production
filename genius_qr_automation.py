#!/usr/bin/env python3
"""
Genius Link QR Code Automation Script

This script automates the following workflow:
1. Takes a list of Genius Links (from file or hardcoded list)
2. For each link, resolves it to its destination URL
3. Creates a new "-qr" version of the link using the Genius Link API
4. Generates a QR code for the new "-qr" link
5. Uploads the generated QR code to Google Drive

Author: YouTube Automation
Date: 2026-01-13
"""

import os
import sys
import time
import logging
import requests
import qrcode
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Load environment variables
load_dotenv()

# --- Configuration ---
GENIUS_API_KEY = os.getenv("GENIUS_API_KEY")
GENIUS_API_SECRET = os.getenv("GENIUS_API_SECRET")
GENIUS_GROUP_ID = int(os.getenv("GENIUS_GROUP_ID", "416519"))
TSID = os.getenv("TSID", "20320")

GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
QR_CODE_DIR = os.getenv("QR_CODE_DIR", "./qr_codes/")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('genius_qr_automation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# --- Helper Functions ---

def validate_config() -> bool:
    """Validates that all required configuration is present."""
    required_vars = {
        "GENIUS_API_KEY": GENIUS_API_KEY,
        "GENIUS_API_SECRET": GENIUS_API_SECRET,
        "GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE": GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE,
        "GOOGLE_DRIVE_FOLDER_ID": GOOGLE_DRIVE_FOLDER_ID,
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


def resolve_genius_link(genius_url: str) -> Optional[str]:
    """
    Resolves a Genius Link to its destination URL.

    Args:
        genius_url: The Genius Link URL to resolve

    Returns:
        The resolved destination URL, or None if resolution fails
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        with requests.get(
            genius_url,
            headers=headers,
            stream=True,
            allow_redirects=True,
            timeout=10
        ) as response:
            response.raise_for_status()
            return response.url
    except requests.exceptions.RequestException as e:
        logger.error(f"Error resolving {genius_url}: {e}")
        return None


def create_genius_link(destination_url: str, original_genius_link: str) -> Optional[str]:
    """
    Creates a new Genius Link with a "-qr" suffix.

    Args:
        destination_url: The URL the new link should point to
        original_genius_link: The original Genius Link (used to create the name)

    Returns:
        The new Genius Link URL, or None if creation fails
    """
    headers = {
        "X-Api-Key": GENIUS_API_KEY,
        "X-Api-Secret": GENIUS_API_SECRET,
        "Content-Type": "application/json",
    }

    # Extract the short code from the original link
    original_code = original_genius_link.split("/")[-1]
    new_name = f"{original_code}-qr"

    payload = {
        "GroupId": GENIUS_GROUP_ID,
        "Domain": "geni.us",
        "Url": destination_url,
        "Name": new_name,
    }

    url = f"https://api.geni.us/v3/shorturls?tsid={TSID}"

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        response_data = response.json()
        short_url_data = response_data.get('shortUrl', {})
        domain = short_url_data.get('domain')
        code = short_url_data.get('code')

        if domain and code:
            return f"https://{domain}/{code}"
        else:
            logger.error(f"Invalid response from Genius API: {response_data}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating link for {destination_url}: {e}")
        if hasattr(e.response, 'text'):
            logger.error(f"Response: {e.response.text}")
        return None


def generate_qr_code(url: str, filename: str) -> Optional[str]:
    """
    Generates a QR code and saves it as a PNG file.

    Args:
        url: The URL to encode in the QR code
        filename: The filename for the QR code image

    Returns:
        The full filepath of the generated QR code, or None if generation fails
    """
    try:
        # Create QR code with higher quality settings
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
        Path(QR_CODE_DIR).mkdir(parents=True, exist_ok=True)

        filepath = os.path.join(QR_CODE_DIR, filename)
        img.save(filepath)
        logger.info(f"Generated QR code: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Error generating QR code for {url}: {e}")
        return None


def upload_to_google_drive(filepath: str, folder_id: str) -> Optional[str]:
    """
    Uploads a file to the specified Google Drive folder.

    Args:
        filepath: Path to the file to upload
        folder_id: Google Drive folder ID

    Returns:
        The file ID of the uploaded file, or None if upload fails
    """
    try:
        creds = service_account.Credentials.from_service_account_file(
            GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        drive_service = build("drive", "v3", credentials=creds)

        file_metadata = {
            "name": os.path.basename(filepath),
            "parents": [folder_id]
        }
        media = MediaFileUpload(filepath, mimetype="image/png")

        file = (
            drive_service.files()
            .create(body=file_metadata, media_body=media, fields="id,name,webViewLink")
            .execute()
        )

        file_id = file.get("id")
        web_link = file.get("webViewLink")
        logger.info(f"Uploaded to Google Drive - ID: {file_id}, Link: {web_link}")
        return file_id

    except HttpError as e:
        logger.error(f"Google Drive API error uploading {filepath}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error uploading {filepath} to Google Drive: {e}")
        return None


def load_links_from_file(filepath: str) -> List[str]:
    """
    Loads Genius Links from a text file (one per line).

    Args:
        filepath: Path to the file containing links

    Returns:
        List of Genius Link URLs
    """
    try:
        with open(filepath, 'r') as f:
            links = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        logger.info(f"Loaded {len(links)} links from {filepath}")
        return links
    except Exception as e:
        logger.error(f"Error loading links from {filepath}: {e}")
        return []


def process_link(link: str) -> bool:
    """
    Processes a single Genius Link through the complete workflow.

    Args:
        link: The Genius Link to process

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Processing link: {link}")

    # 1. Resolve the original Genius Link
    destination_url = resolve_genius_link(link)
    if not destination_url:
        logger.error(f"Failed to resolve link: {link}")
        return False
    logger.info(f"Resolved to: {destination_url}")

    # 2. Create -qr link
    qr_link_url = create_genius_link(destination_url, link)
    if not qr_link_url:
        logger.error(f"Failed to create QR link for: {link}")
        return False
    logger.info(f"Created QR link: {qr_link_url}")

    # 3. Generate QR code
    qr_code_filename = f'{link.split("/")[-1]}-qr.png'
    qr_code_filepath = generate_qr_code(qr_link_url, qr_code_filename)
    if not qr_code_filepath:
        logger.error(f"Failed to generate QR code for: {link}")
        return False

    # 4. Upload to Google Drive
    file_id = upload_to_google_drive(qr_code_filepath, GOOGLE_DRIVE_FOLDER_ID)
    if not file_id:
        logger.error(f"Failed to upload QR code for: {link}")
        return False

    logger.info(f"✓ Successfully processed: {link}")
    return True


# --- Main Workflow ---

def main():
    """Main function to run the automation workflow."""
    logger.info("=" * 60)
    logger.info("Genius Link QR Code Automation - Starting")
    logger.info("=" * 60)

    # Validate configuration
    if not validate_config():
        logger.error("Configuration validation failed. Exiting.")
        sys.exit(1)

    # Load links (try from file first, then use hardcoded list)
    links = []
    links_file = "genius_links.txt"

    if os.path.exists(links_file):
        links = load_links_from_file(links_file)

    # Fallback to hardcoded list if no file found
    if not links:
        logger.info("No links file found, using hardcoded list")
        links = [
            "https://geni.us/yvyBS3",
            "https://geni.us/AXM8T",
            "https://geni.us/GaTn",
            "https://geni.us/R8n2",
            "https://geni.us/N012",
            "https://geni.us/Oa34",
            "https://geni.us/P567",
            "https://geni.us/Q890",
            "https://geni.us/R123",
            "https://geni.us/S456",
        ]

    logger.info(f"Processing {len(links)} links")

    # Process each link
    successful = 0
    failed = 0

    for i, link in enumerate(links, 1):
        logger.info(f"\n[{i}/{len(links)}] Processing link...")

        try:
            if process_link(link):
                successful += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Unexpected error processing {link}: {e}")
            failed += 1

        # Rate limiting - be nice to the APIs
        if i < len(links):  # Don't sleep after the last one
            time.sleep(3)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Processing Complete!")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total: {len(links)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
