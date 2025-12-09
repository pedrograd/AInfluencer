# Platform Integration Detailed
## Complete Platform Integration Guides

**Version:** 1.0  
**Date:** January 2025  
**Last Updated:** January 2025  
**Status:** Production Ready  
**Document Owner:** Engineering Team

---

## 📋 Document Metadata

### Purpose
Detailed guides for integrating with Instagram, Twitter/X, Facebook, Telegram, OnlyFans, and YouTube. Covers API usage, browser automation, rate limiting, error handling, authentication, and best practices.

### Reading Order
**Read After:** [05-AUTOMATION-STRATEGY.md](./05-AUTOMATION-STRATEGY.md), [25-AUTOMATION-WORKFLOWS.md](./25-AUTOMATION-WORKFLOWS.md)  
**Read Before:** [29-PRODUCTION-DEPLOYMENT.md](./29-PRODUCTION-DEPLOYMENT.md), [30-TROUBLESHOOTING-COMPLETE.md](./30-TROUBLESHOOTING-COMPLETE.md)

### Related Documents
- [05-AUTOMATION-STRATEGY.md](./05-AUTOMATION-STRATEGY.md) - Automation strategy
- [25-AUTOMATION-WORKFLOWS.md](./25-AUTOMATION-WORKFLOWS.md) - Automation workflows

---

## Table of Contents

1. [Introduction to Platform Integration](#introduction)
2. [Instagram Integration](#instagram)
3. [Twitter/X Integration](#twitter)
4. [Facebook Integration](#facebook)
5. [Telegram Integration](#telegram)
6. [OnlyFans Integration](#onlyfans)
7. [YouTube Integration](#youtube)
8. [Rate Limiting Strategies](#rate-limiting)
9. [Error Handling Per Platform](#error-handling)
10. [Authentication Methods](#authentication)
11. [Best Practices Summary](#best-practices)

---

## Introduction to Platform Integration {#introduction}

Platform integration enables automated content publishing across social media platforms. This guide covers detailed integration methods for each platform.

### Integration Approaches

1. **API Integration:** Official or unofficial APIs
2. **Browser Automation:** Selenium, Playwright, Puppeteer
3. **Hybrid:** Combine API and browser automation

### Common Challenges

- Rate limiting
- Authentication
- Platform changes
- Detection
- Error handling

---

## Instagram Integration {#instagram}

### API Approach (instagrapi)

**Installation:**
```bash
pip install instagrapi
```

**Authentication:**
```python
from instagrapi import Client

cl = Client()
cl.login("username", "password")

# Or use session
cl.load_settings("session.json")
```

**Posting Images:**
```python
# Post photo
cl.photo_upload(
    path="image.jpg",
    caption="Your caption here #hashtag"
)

# Post reel
cl.clip_upload(
    path="video.mp4",
    caption="Your caption"
)
```

**Rate Limits:**
- Posts: 3-5 per day
- Likes: 100-200 per day
- Comments: 20-30 per day
- Follows: 50-100 per day

### Browser Automation (Playwright)

**Setup:**
```python
from playwright.sync_api import sync_playwright

def post_to_instagram(image_path, caption):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Login
        page.goto("https://www.instagram.com")
        page.fill('input[name="username"]', "username")
        page.fill('input[name="password"]', "password")
        page.click('button[type="submit"]')
        
        # Post
        page.click('svg[aria-label="New post"]')
        page.set_input_files('input[type="file"]', image_path)
        page.fill('textarea[aria-label="Write a caption"]', caption)
        page.click('button:has-text("Share")')
        
        browser.close()
```

---

## Twitter/X Integration {#twitter}

### API Approach (tweepy)

**Installation:**
```bash
pip install tweepy
```

**Authentication:**
```python
import tweepy

auth = tweepy.OAuthHandler(api_key, api_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
```

**Posting:**
```python
# Post tweet
api.update_status("Your tweet text")

# Post with image
api.update_status_with_media("Caption", "image.jpg")

# Post video
api.update_status_with_media("Caption", "video.mp4")
```

**Rate Limits:**
- Tweets: 300 per 3 hours
- Media uploads: Limited
- Follows: 400 per day

### Browser Automation

```python
from playwright.sync_api import sync_playwright

def post_to_twitter(text, media_path=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Login and post
        # Similar to Instagram approach
        pass
```

---

## Facebook Integration {#facebook}

### API Approach (Graph API)

**Installation:**
```bash
pip install facebook-sdk
```

**Authentication:**
```python
import facebook

graph = facebook.GraphAPI(access_token)
```

**Posting:**
```python
# Post to page
graph.put_object(
    parent_object="page_id",
    connection_name="feed",
    message="Your post text",
    link="https://example.com"
)

# Post with image
graph.put_photo(
    image=open("image.jpg", "rb"),
    message="Your caption"
)
```

---

## Telegram Integration {#telegram}

### API Approach (python-telegram-bot)

**Installation:**
```bash
pip install python-telegram-bot
```

**Usage:**
```python
from telegram import Bot

bot = Bot(token="your_token")

# Send message
bot.send_message(chat_id="channel_id", text="Your message")

# Send photo
bot.send_photo(chat_id="channel_id", photo=open("image.jpg", "rb"))

# Send video
bot.send_video(chat_id="channel_id", video=open("video.mp4", "rb"))
```

---

## OnlyFans Integration {#onlyfans}

### Browser Automation (Primary Method)

**Note:** OnlyFans doesn't have a public API, so browser automation is required.

**Setup:**
```python
from playwright.sync_api import sync_playwright

def post_to_onlyfans(content_path, caption, content_type="photo"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Login
        page.goto("https://onlyfans.com")
        # Login steps...
        
        # Navigate to post creation
        page.click('button:has-text("Post")')
        
        # Upload content
        if content_type == "photo":
            page.set_input_files('input[type="file"]', content_path)
        elif content_type == "video":
            page.set_input_files('input[type="file"]', content_path)
        
        # Add caption
        page.fill('textarea', caption)
        
        # Post
        page.click('button:has-text("Publish")')
        
        browser.close()
```

**Best Practices:**
- Use stealth browser settings
- Human-like delays
- Rotate user agents
- Handle CAPTCHAs

---

## YouTube Integration {#youtube}

### API Approach (YouTube Data API)

**Installation:**
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

**Authentication:**
```python
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

flow = InstalledAppFlow.from_client_secrets_file(
    'client_secrets.json', SCOPES)
credentials = flow.run_local_server()

youtube = build('youtube', 'v3', credentials=credentials)
```

**Upload Video:**
```python
def upload_video(video_path, title, description):
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': ['tag1', 'tag2'],
            'categoryId': '22'
        },
        'status': {
            'privacyStatus': 'public'
        }
    }
    
    youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=video_path
    ).execute()
```

---

## Rate Limiting Strategies {#rate-limiting}

### Rate Limit Management

**Implementation:**
```python
import time
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests, time_window):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    def wait_if_needed(self):
        now = datetime.now()
        # Remove old requests
        self.requests = [
            r for r in self.requests
            if now - r < timedelta(seconds=self.time_window)
        ]
        
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0]).seconds
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.requests.append(now)
```

### Platform-Specific Limits

**Instagram:**
- Posts: 3-5/day
- Actions: Space out by hours

**Twitter:**
- Tweets: 300/3 hours
- Space out posts

**Facebook:**
- Posts: Varies by account
- Monitor limits

---

## Error Handling Per Platform {#error-handling}

### Common Errors

**Authentication Errors:**
- Invalid credentials
- Expired tokens
- Session expired

**Rate Limit Errors:**
- Too many requests
- Temporary bans
- Permanent restrictions

**Content Errors:**
- Invalid format
- Size limits
- Policy violations

### Error Handling

```python
def safe_post(platform, content, max_retries=3):
    for attempt in range(max_retries):
        try:
            return platform.post(content)
        except RateLimitError as e:
            wait_time = calculate_wait_time(e)
            time.sleep(wait_time)
        except AuthenticationError as e:
            platform.reauthenticate()
        except Exception as e:
            log_error(e)
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

---

## Authentication Methods {#authentication}

### OAuth 2.0

**Standard Flow:**
1. Redirect to authorization URL
2. User authorizes
3. Receive authorization code
4. Exchange for access token
5. Use access token for API calls

### Session-Based

**Cookies/Sessions:**
- Login via browser
- Save session cookies
- Reuse for requests

### API Keys

**Direct Keys:**
- Some platforms use API keys
- Include in requests
- Rotate regularly

---

## Best Practices Summary {#best-practices}

### Do's

✅ **Respect Rate Limits:** Never exceed limits  
✅ **Handle Errors Gracefully:** Implement retry logic  
✅ **Use Stealth Techniques:** Avoid detection  
✅ **Monitor Activity:** Track all actions  
✅ **Backup Authentication:** Keep tokens safe  

### Don'ts

❌ **Don't Spam:** Space out actions  
❌ **Don't Ignore Errors:** Handle all errors  
❌ **Don't Hardcode Credentials:** Use environment variables  
❌ **Don't Skip Rate Limiting:** Always implement limits  

---

## Conclusion

Platform integration requires careful attention to authentication, rate limiting, and error handling. By following platform-specific guidelines and best practices, you can create reliable integrations.

**Key Takeaways:**
1. Use appropriate integration method per platform
2. Implement rate limiting
3. Handle errors gracefully
4. Use stealth techniques
5. Monitor and maintain integrations

**Next Steps:**
- Review [29-PRODUCTION-DEPLOYMENT.md](./29-PRODUCTION-DEPLOYMENT.md) for deployment
- Review [30-TROUBLESHOOTING-COMPLETE.md](./30-TROUBLESHOOTING-COMPLETE.md) for troubleshooting
- Implement platform integrations
- Test thoroughly

---

**Document Status:** ✅ Complete  
**Last Updated:** January 2025  
**Version:** 1.0
