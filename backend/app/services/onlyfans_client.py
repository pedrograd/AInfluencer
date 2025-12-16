"""OnlyFans browser automation client using Playwright."""

from __future__ import annotations

import asyncio
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OnlyFansApiError(RuntimeError):
    """Error raised when OnlyFans browser automation operations fail.
    
    This exception is raised for various OnlyFans-related errors including
    connection failures, authentication failures, browser automation errors,
    and other OnlyFans automation issues.
    """
    pass


class OnlyFansBrowserClient:
    """Client for OnlyFans browser automation using Playwright."""

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        headless: bool = True,
    ) -> None:
        """
        Initialize OnlyFans browser automation client.

        Args:
            username: OnlyFans username/email for login.
            password: OnlyFans password for login.
            headless: Whether to run browser in headless mode (default: True).
        """
        self.username = username or getattr(settings, "onlyfans_username", None)
        self.password = password or getattr(settings, "onlyfans_password", None)
        self.headless = headless
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    async def _ensure_playwright(self) -> Playwright:
        """Ensure Playwright is initialized.
        
        Returns:
            Initialized Playwright instance.
            
        Raises:
            OnlyFansApiError: If Playwright initialization fails.
        """
        if not self.playwright:
            try:
                self.playwright = await async_playwright().start()
            except Exception as exc:
                raise OnlyFansApiError(f"Failed to initialize Playwright: {exc}") from exc
        return self.playwright

    async def _ensure_browser(self) -> Browser:
        """Ensure browser is initialized.
        
        Returns:
            Initialized Browser instance.
            
        Raises:
            OnlyFansApiError: If browser initialization fails.
        """
        playwright = await self._ensure_playwright()
        if not self.browser:
            try:
                # Launch browser with stealth settings
                self.browser = await playwright.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                    ],
                )
            except Exception as exc:
                raise OnlyFansApiError(f"Failed to launch browser: {exc}") from exc
        return self.browser

    async def _ensure_context(self) -> BrowserContext:
        """Ensure browser context is initialized.
        
        Returns:
            Initialized BrowserContext instance.
            
        Raises:
            OnlyFansApiError: If context initialization fails.
        """
        browser = await self._ensure_browser()
        if not self.context:
            try:
                # Create context with stealth settings
                self.context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="en-US",
                    timezone_id="America/New_York",
                )
                # Add stealth script to hide automation
                await self.context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
            except Exception as exc:
                raise OnlyFansApiError(f"Failed to create browser context: {exc}") from exc
        return self.context

    async def _ensure_page(self) -> Page:
        """Ensure page is initialized.
        
        Returns:
            Initialized Page instance.
            
        Raises:
            OnlyFansApiError: If page initialization fails.
        """
        context = await self._ensure_context()
        if not self.page:
            try:
                self.page = await context.new_page()
            except Exception as exc:
                raise OnlyFansApiError(f"Failed to create page: {exc}") from exc
        return self.page

    async def test_connection(self) -> dict[str, Any]:
        """
        Test browser automation connection by navigating to OnlyFans.

        Returns:
            Connection test result dictionary containing:
                - connected (bool): Whether connection was successful
                - url (str): OnlyFans URL accessed
                - title (str): Page title
                - error (str | None): Error message if connection failed

        Raises:
            OnlyFansApiError: If connection test fails.
        """
        try:
            page = await self._ensure_page()
            await page.goto("https://onlyfans.com", wait_until="domcontentloaded", timeout=30000)
            title = await page.title()
            url = page.url
            
            return {
                "connected": True,
                "url": url,
                "title": title,
                "error": None,
            }
        except Exception as exc:
            error_msg = f"OnlyFans connection test failed: {exc}"
            logger.error(error_msg)
            return {
                "connected": False,
                "url": None,
                "title": None,
                "error": str(exc),
            }

    async def login(
        self,
        username: str | None = None,
        password: str | None = None,
    ) -> dict[str, Any]:
        """
        Login to OnlyFans account.

        Args:
            username: OnlyFans username/email (uses instance username if not provided).
            password: OnlyFans password (uses instance password if not provided).

        Returns:
            Login result dictionary containing:
                - success (bool): Whether login was successful
                - url (str): Current page URL after login attempt
                - error (str | None): Error message if login failed

        Raises:
            OnlyFansApiError: If login fails.
        """
        login_username = username or self.username
        login_password = password or self.password

        if not login_username or not login_password:
            raise OnlyFansApiError("Username and password are required for login")

        try:
            page = await self._ensure_page()
            await page.goto("https://onlyfans.com", wait_until="domcontentloaded", timeout=30000)
            
            # Wait for login form to appear
            await page.wait_for_selector("input[type='email'], input[name='email'], input[placeholder*='email' i], input[placeholder*='username' i]", timeout=10000)
            
            # Find and fill username field
            username_selectors = [
                "input[type='email']",
                "input[name='email']",
                "input[placeholder*='email' i]",
                "input[placeholder*='username' i]",
            ]
            username_filled = False
            for selector in username_selectors:
                try:
                    username_input = page.locator(selector).first
                    if await username_input.is_visible():
                        await username_input.fill(login_username)
                        username_filled = True
                        break
                except Exception:
                    continue
            
            if not username_filled:
                raise OnlyFansApiError("Could not find username/email input field")

            # Find and fill password field
            password_selectors = [
                "input[type='password']",
                "input[name='password']",
            ]
            password_filled = False
            for selector in password_selectors:
                try:
                    password_input = page.locator(selector).first
                    if await password_input.is_visible():
                        await password_input.fill(login_password)
                        password_filled = True
                        break
                except Exception:
                    continue
            
            if not password_filled:
                raise OnlyFansApiError("Could not find password input field")

            # Submit login form
            submit_selectors = [
                "button[type='submit']",
                "button:has-text('Sign in')",
                "button:has-text('Log in')",
                "button:has-text('Login')",
            ]
            submitted = False
            for selector in submit_selectors:
                try:
                    submit_button = page.locator(selector).first
                    if await submit_button.is_visible():
                        await submit_button.click()
                        submitted = True
                        break
                except Exception:
                    continue
            
            if not submitted:
                # Try pressing Enter on password field
                password_input = page.locator("input[type='password']").first
                await password_input.press("Enter")

            # Wait for navigation after login (or 2FA prompt)
            await asyncio.sleep(3)
            current_url = page.url
            
            # Check if login was successful (URL should change from login page)
            # Note: OnlyFans may require 2FA, so we check if we're still on login page
            is_logged_in = "login" not in current_url.lower() and "signin" not in current_url.lower()
            
            return {
                "success": is_logged_in,
                "url": current_url,
                "error": None if is_logged_in else "Login may require 2FA or verification",
            }
        except Exception as exc:
            error_msg = f"OnlyFans login failed: {exc}"
            logger.error(error_msg)
            raise OnlyFansApiError(error_msg) from exc

    async def navigate(self, url: str) -> dict[str, Any]:
        """
        Navigate to a URL in the browser.

        Args:
            url: URL to navigate to.

        Returns:
            Navigation result dictionary containing:
                - success (bool): Whether navigation was successful
                - url (str): Current page URL
                - title (str): Page title

        Raises:
            OnlyFansApiError: If navigation fails.
        """
        try:
            page = await self._ensure_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            title = await page.title()
            current_url = page.url
            
            return {
                "success": True,
                "url": current_url,
                "title": title,
            }
        except Exception as exc:
            error_msg = f"Navigation failed: {exc}"
            logger.error(error_msg)
            raise OnlyFansApiError(error_msg) from exc

    async def get_page_info(self) -> dict[str, Any]:
        """
        Get current page information.

        Returns:
            Page information dictionary containing:
                - url (str): Current page URL
                - title (str): Page title
                - content_length (int): Page content length

        Raises:
            OnlyFansApiError: If page info retrieval fails.
        """
        try:
            page = await self._ensure_page()
            url = page.url
            title = await page.title()
            content = await page.content()
            
            return {
                "url": url,
                "title": title,
                "content_length": len(content),
            }
        except Exception as exc:
            error_msg = f"Failed to get page info: {exc}"
            logger.error(error_msg)
            raise OnlyFansApiError(error_msg) from exc

    async def upload_content(
        self,
        file_path: str,
        caption: str = "",
        price: float | None = None,
        is_free: bool = False,
    ) -> dict[str, Any]:
        """
        Upload content (image or video) to OnlyFans.

        Args:
            file_path: Path to the image or video file to upload.
            caption: Caption/description for the content.
            price: Price for the content (required if is_free is False).
            is_free: Whether the content should be free (default: False).

        Returns:
            Upload result dictionary containing:
                - success (bool): Whether upload was successful
                - content_id (str | None): OnlyFans content ID if successful
                - content_url (str | None): URL to the uploaded content
                - error (str | None): Error message if upload failed

        Raises:
            OnlyFansApiError: If upload fails.
        """
        from pathlib import Path

        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise OnlyFansApiError(f"File not found: {file_path}")

        if not is_free and price is None:
            raise OnlyFansApiError("Price is required for paid content")

        try:
            page = await self._ensure_page()
            
            # Navigate to content creation page
            # OnlyFans typically uses /posts/new or similar URL
            await page.goto("https://onlyfans.com/posts/new", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)  # Wait for page to load

            # Wait for file upload input
            # OnlyFans typically uses input[type="file"] for uploads
            file_input_selectors = [
                'input[type="file"]',
                'input[accept*="image"]',
                'input[accept*="video"]',
                '[data-testid*="upload"]',
            ]
            
            file_input = None
            for selector in file_input_selectors:
                try:
                    file_input = page.locator(selector).first
                    if await file_input.is_visible(timeout=5000):
                        break
                except Exception:
                    continue

            if not file_input:
                # Try to find any file input on the page
                file_input = page.locator('input[type="file"]').first
                if not await file_input.is_visible(timeout=5000):
                    raise OnlyFansApiError("Could not find file upload input")

            # Upload file
            await file_input.set_input_files(str(file_path_obj))
            logger.info(f"File uploaded: {file_path}")
            await asyncio.sleep(3)  # Wait for file to process

            # Fill caption if provided
            if caption:
                caption_selectors = [
                    'textarea[placeholder*="caption" i]',
                    'textarea[placeholder*="description" i]',
                    'textarea[placeholder*="what" i]',
                    'textarea',
                ]
                
                caption_filled = False
                for selector in caption_selectors:
                    try:
                        caption_input = page.locator(selector).first
                        if await caption_input.is_visible(timeout=5000):
                            await caption_input.fill(caption)
                            caption_filled = True
                            logger.info("Caption filled")
                            break
                    except Exception:
                        continue

            # Set price if needed
            if not is_free and price is not None:
                price_selectors = [
                    'input[type="number"][placeholder*="price" i]',
                    'input[name*="price" i]',
                    'input[type="number"]',
                ]
                
                price_filled = False
                for selector in price_selectors:
                    try:
                        price_input = page.locator(selector).first
                        if await price_input.is_visible(timeout=5000):
                            await price_input.fill(str(price))
                            price_filled = True
                            logger.info(f"Price set: {price}")
                            break
                    except Exception:
                        continue

            # Find and click publish/submit button
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Publish")',
                'button:has-text("Post")',
                'button:has-text("Upload")',
                'button:has-text("Submit")',
                '[data-testid*="publish"]',
                '[data-testid*="submit"]',
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    submit_button = page.locator(selector).first
                    if await submit_button.is_visible(timeout=5000):
                        await submit_button.click()
                        submitted = True
                        logger.info("Submit button clicked")
                        break
                except Exception:
                    continue

            if not submitted:
                raise OnlyFansApiError("Could not find submit/publish button")

            # Wait for upload to complete
            await asyncio.sleep(5)  # Wait for upload processing

            # Check if upload was successful (URL should change or show success message)
            current_url = page.url
            is_success = "posts/new" not in current_url.lower()

            # Try to extract content ID from URL or page
            content_id = None
            content_url = None
            
            if is_success:
                # Try to extract post ID from URL
                if "/posts/" in current_url:
                    parts = current_url.split("/posts/")
                    if len(parts) > 1:
                        content_id = parts[1].split("/")[0].split("?")[0]
                        content_url = current_url

            return {
                "success": is_success,
                "content_id": content_id,
                "content_url": content_url,
                "error": None if is_success else "Upload may have failed - check OnlyFans",
            }
        except Exception as exc:
            error_msg = f"OnlyFans content upload failed: {exc}"
            logger.error(error_msg)
            raise OnlyFansApiError(error_msg) from exc

    async def send_message(
        self,
        recipient_username: str,
        message: str,
    ) -> dict[str, Any]:
        """
        Send a message to a recipient on OnlyFans.

        Args:
            recipient_username: Username of the recipient to send message to.
            message: Message text to send.

        Returns:
            Send message result dictionary containing:
                - success (bool): Whether message was sent successfully
                - message_id (str | None): Message ID if available
                - error (str | None): Error message if sending failed

        Raises:
            OnlyFansApiError: If message sending fails.
        """
        if not recipient_username:
            raise OnlyFansApiError("Recipient username is required")
        if not message:
            raise OnlyFansApiError("Message text is required")

        try:
            page = await self._ensure_page()
            
            # Ensure logged in before sending messages
            login_result = await self.login()
            if not login_result.get("success"):
                raise OnlyFansApiError("Must be logged in to send messages. Please login first.")
            
            # Navigate to messages page
            # OnlyFans typically uses /messages or /chats URL
            await page.goto("https://onlyfans.com/messages", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)  # Wait for page to load

            # Search for recipient or find existing conversation
            # OnlyFans may have a search box or list of conversations
            search_selectors = [
                'input[placeholder*="search" i]',
                'input[placeholder*="find" i]',
                'input[type="search"]',
                'input[name*="search" i]',
            ]
            
            search_filled = False
            for selector in search_selectors:
                try:
                    search_input = page.locator(selector).first
                    if await search_input.is_visible(timeout=5000):
                        await search_input.fill(recipient_username)
                        search_filled = True
                        logger.info(f"Searching for recipient: {recipient_username}")
                        await asyncio.sleep(2)  # Wait for search results
                        break
                except Exception:
                    continue

            # If no search box found, try to find conversation in list
            if not search_filled:
                # Try to find conversation by username in conversation list
                conversation_selectors = [
                    f'a[href*="{recipient_username}"]',
                    f'div:has-text("{recipient_username}")',
                    f'span:has-text("{recipient_username}")',
                ]
                
                conversation_clicked = False
                for selector in conversation_selectors:
                    try:
                        conversation = page.locator(selector).first
                        if await conversation.is_visible(timeout=5000):
                            await conversation.click()
                            conversation_clicked = True
                            logger.info(f"Found conversation with {recipient_username}")
                            await asyncio.sleep(2)
                            break
                    except Exception:
                        continue
                
                if not conversation_clicked:
                    # Try navigating directly to conversation URL
                    await page.goto(f"https://onlyfans.com/messages/{recipient_username}", wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(2)

            # Find message input field
            message_input_selectors = [
                'textarea[placeholder*="message" i]',
                'textarea[placeholder*="type" i]',
                'textarea[placeholder*="write" i]',
                'textarea',
                'input[type="text"][placeholder*="message" i]',
            ]
            
            message_input = None
            for selector in message_input_selectors:
                try:
                    message_input = page.locator(selector).first
                    if await message_input.is_visible(timeout=5000):
                        break
                except Exception:
                    continue

            if not message_input or not await message_input.is_visible(timeout=5000):
                raise OnlyFansApiError("Could not find message input field")

            # Type message
            await message_input.fill(message)
            logger.info("Message text filled")
            await asyncio.sleep(1)

            # Find and click send button
            send_selectors = [
                'button[type="submit"]',
                'button:has-text("Send")',
                'button:has-text("Send message")',
                'button[aria-label*="send" i]',
                '[data-testid*="send"]',
                'button[class*="send"]',
            ]
            
            sent = False
            for selector in send_selectors:
                try:
                    send_button = page.locator(selector).first
                    if await send_button.is_visible(timeout=5000):
                        await send_button.click()
                        sent = True
                        logger.info("Send button clicked")
                        break
                except Exception:
                    continue

            if not sent:
                # Try pressing Enter on message input
                await message_input.press("Enter")
                logger.info("Sent message using Enter key")

            # Wait for message to be sent
            await asyncio.sleep(3)

            # Check if message was sent successfully
            # OnlyFans may show a success indicator or the message appears in chat
            current_url = page.url
            is_success = True  # Assume success if no error occurred

            # Try to extract message ID if available (from URL or page content)
            message_id = None
            if "/messages/" in current_url:
                # Message ID might be in URL or page
                parts = current_url.split("/messages/")
                if len(parts) > 1:
                    # Could extract conversation ID or message ID
                    pass

            return {
                "success": is_success,
                "message_id": message_id,
                "error": None if is_success else "Message may not have been sent - check OnlyFans",
            }
        except Exception as exc:
            error_msg = f"OnlyFans message sending failed: {exc}"
            logger.error(error_msg)
            raise OnlyFansApiError(error_msg) from exc

    async def close(self) -> None:
        """Close browser and cleanup resources."""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            if self.context:
                await self.context.close()
                self.context = None
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
        except Exception as exc:
            logger.warning(f"Error during browser cleanup: {exc}")

    async def __aenter__(self) -> OnlyFansBrowserClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

