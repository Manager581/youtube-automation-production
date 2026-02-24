# How to Download Fern Videos for Analysis

YouTube is blocking automated downloads (403 errors). Here's how to get the videos manually:

## Top 5 Videos to Download (by views):

1. **How an FBI Agent Infiltrated the KKK** (11.2M views)
   - https://www.youtube.com/watch?v=wLFY_Zu_O08

2. **The Kid Who Hacked the Pentagon** (5.4M views)
   - https://www.youtube.com/watch?v=I1rzcZWTIjo

3. **The Most Secret Building in Manhattan** (5.1M views)
   - https://www.youtube.com/watch?v=qqJSXoa5ZtQ

4. **Why Otto Warmbier Didn't Survive North Korea** (4.7M views)
   - https://www.youtube.com/watch?v=yXdzKqhEA9M

5. **Camp 14: The Most Horrible Place in North Korea** (4.5M views)
   - https://www.youtube.com/watch?v=8Gm7kSUkBAk

## Download Steps:

### Option 1: Using yt-dlp on your Mac (recommended)
```bash
# Install yt-dlp if you haven't
brew install yt-dlp

# Download all 5 videos
yt-dlp -f best https://www.youtube.com/watch?v=wLFY_Zu_O08
yt-dlp -f best https://www.youtube.com/watch?v=I1rzcZWTIjo
yt-dlp -f best https://www.youtube.com/watch?v=qqJSXoa5ZtQ
yt-dlp -f best https://www.youtube.com/watch?v=yXdzKqhEA9M
yt-dlp -f best https://www.youtube.com/watch?v=8Gm7kSUkBAk
```

### Option 2: Browser Extension
1. Install "Video DownloadHelper" (Firefox/Chrome)
2. Go to each video URL
3. Click the extension icon and download

## Transfer to Analysis Environment:

Once downloaded, upload to `analysis/fern/[video-id]/` matching the structure:
```
analysis/fern/wLFY_Zu_O08/video.mp4
analysis/fern/I1rzcZWTIjo/video.mp4
analysis/fern/qqJSXoa5ZtQ/video.mp4
analysis/fern/yXdzKqhEA9M/video.mp4
analysis/fern/8Gm7kSUkBAk/video.mp4
```

We already have the transcripts, thumbnails, and metadata for these - we just need the actual video files.

## Why These 5?

- Top performers = proven formulas
- Different topics = variety of patterns
- Recent uploads = current style
- Enough data to extract patterns without downloading 30+ GB
