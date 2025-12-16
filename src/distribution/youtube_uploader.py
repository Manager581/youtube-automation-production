"""
YouTube Uploader
Uploads videos to YouTube using the YouTube Data API v3

SETUP REQUIRED:
1. Go to https://console.cloud.google.com/
2. Create a new project
3. Enable YouTube Data API v3
4. Create OAuth 2.0 credentials
5. Download client_secrets.json to config/
6. Run this script to authenticate (one-time)
"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime

# YouTube API imports (install: pip install google-api-python-client google-auth-oauthlib)
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False


class YouTubeUploader:
    """Uploads videos to YouTube"""

    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

    def __init__(self, config_path="config/config.yaml"):
        if not YOUTUBE_API_AVAILABLE:
            print("⚠️  YouTube API libraries not installed")
            print("   Run: pip install google-api-python-client google-auth-oauthlib")
            return

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.credentials_file = Path("config/youtube_credentials.json")
        self.client_secrets = Path("config/client_secrets.json")

    def authenticate(self):
        """Authenticate with YouTube API (one-time setup)"""

        if not self.client_secrets.exists():
            print("❌ client_secrets.json not found!")
            print("\nSETUP INSTRUCTIONS:")
            print("1. Go to https://console.cloud.google.com/")
            print("2. Create a new project")
            print("3. Enable 'YouTube Data API v3'")
            print("4. Create OAuth 2.0 Client ID credentials")
            print("5. Download JSON and save as: config/client_secrets.json")
            return None

        creds = None

        # Load existing credentials
        if self.credentials_file.exists():
            creds = Credentials.from_authorized_user_file(str(self.credentials_file), self.SCOPES)

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.client_secrets),
                self.SCOPES
            )
            creds = flow.run_local_server(port=8080)

            # Save credentials
            with open(self.credentials_file, 'w') as f:
                f.write(creds.to_json())

            print("✅ Authentication successful!")

        return creds

    def upload_video(self, video_file, metadata_file):
        """Upload video to YouTube"""

        if not YOUTUBE_API_AVAILABLE:
            print("❌ YouTube API not available")
            return None

        # Authenticate
        creds = self.authenticate()
        if not creds:
            return None

        # Load metadata
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        # Build YouTube service
        youtube = build('youtube', 'v3', credentials=creds)

        # Prepare video metadata
        body = {
            'snippet': {
                'title': metadata['primary_title'],
                'description': metadata['description'],
                'tags': metadata['tags'],
                'categoryId': str(metadata['category_id'])
            },
            'status': {
                'privacyStatus': metadata['privacy_status'],
                'selfDeclaredMadeForKids': False
            }
        }

        # Create MediaFileUpload
        media = MediaFileUpload(
            video_file,
            chunksize=1024*1024,  # 1MB chunks
            resumable=True
        )

        print(f"\n📤 UPLOADING TO YOUTUBE")
        print(f"{'='*60}")
        print(f"Title: {metadata['primary_title']}")
        print(f"File: {video_file}")
        print(f"Privacy: {metadata['privacy_status']}")

        try:
            # Execute upload
            request = youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"Upload progress: {progress}%", end='\r')

            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            print(f"\n\n✅ UPLOAD SUCCESSFUL!")
            print(f"{'='*60}")
            print(f"Video ID: {video_id}")
            print(f"URL: {video_url}")
            print(f"\n📋 NEXT STEPS:")
            print(f"1. Add thumbnail: https://studio.youtube.com/video/{video_id}/edit")
            print(f"2. Add chapters in description")
            print(f"3. Set as 'Public' when ready")

            # Save upload record
            upload_record = {
                "video_id": video_id,
                "url": video_url,
                "uploaded_at": datetime.now().isoformat(),
                "title": metadata['primary_title'],
                "video_file": str(video_file),
                "metadata_file": str(metadata_file)
            }

            record_file = Path("output/uploads") / f"upload_{video_id}.json"
            record_file.parent.mkdir(exist_ok=True)

            with open(record_file, 'w') as f:
                json.dump(upload_record, f, indent=2)

            return video_url

        except HttpError as e:
            print(f"\n❌ Upload failed: {e}")
            return None


def main():
    """CLI interface"""
    import sys

    if not YOUTUBE_API_AVAILABLE:
        print("❌ Required packages not installed")
        print("   Run: pip install google-api-python-client google-auth-oauthlib")
        return

    uploader = YouTubeUploader()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "auth":
            uploader.authenticate()

        elif command == "upload":
            if len(sys.argv) < 4:
                print("❌ Usage: python src/distribution/youtube_uploader.py upload <video_file> <metadata_file>")
                return
            video_file = sys.argv[2]
            metadata_file = sys.argv[3]
            uploader.upload_video(video_file, metadata_file)

        else:
            print("❌ Unknown command. Use: auth or upload")

    else:
        print("📤 YouTube Uploader")
        print("\nCommands:")
        print("  python src/distribution/youtube_uploader.py auth")
        print("  python src/distribution/youtube_uploader.py upload <video_file> <metadata_file>")
        print("\nExamples:")
        print("  python src/distribution/youtube_uploader.py auth")
        print("  python src/distribution/youtube_uploader.py upload output/videos/video.mp4 output/metadata/metadata.json")


if __name__ == "__main__":
    main()
