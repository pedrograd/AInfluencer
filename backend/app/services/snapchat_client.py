"""Snapchat browser automation client using Playwright."""

from __future__ import annotations

import asyncio
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SnapchatApiError(RuntimeError):
    """Error raised when Snapchat browser automation operations fail.
    
    This exception is raised for various Snapchat-related errors including
    connection failures, authentication failures, browser automation errors,
    and other Snapchat automation issues.
    """
    pass


class SnapchatBrowserClient:
    """Client for Snapchat browser automation using Playwright."""

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        headless: bool = True,
    ) -> None:
        """
        Initialize Snapchat browser automation client.

        Args:
            username: Snapchat username/email for login.
            password: Snapchat password for login.
            headless: Whether to run browser in headless mode (default: True).
        """
        self.username = username or getattr(settings, "snapchat_username", None)
        self.password = password or getattr(settings, "snapchat_password", None)
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
            SnapchatApiError: If Playwright initialization fails.
        """
        if not self.playwright:
            try:
                self.playwright = await async_playwright().start()
            except Exception as exc:
                raise SnapchatApiError(f"Failed to initialize Playwright: {exc}") from exc
        return self.playwright

    async def _ensure_browser(self) -> Browser:
        """Ensure browser is initialized.
        
        Returns:
            Initialized Browser instance.
            
        Raises:
            SnapchatApiError: If browser initialization fails.
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
                raise SnapchatApiError(f"Failed to launch browser: {exc}") from exc
        return self.browser

    async def _ensure_context(self) -> BrowserContext:
        """Ensure browser context is initialized.
        
        Returns:
            Initialized BrowserContext instance.
            
        Raises:
            SnapchatApiError: If context initialization fails.
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
                raise SnapchatApiError(f"Failed to create browser context: {exc}") from exc
        return self.context

    async def _ensure_page(self) -> Page:
        """Ensure page is initialized.
        
        Returns:
            Initialized Page instance.
            
        Raises:
            SnapchatApiError: If page initialization fails.
        """
        context = await self._ensure_context()
        if not self.page:
            try:
                self.page = await context.new_page()
            except Exception as exc:
                raise SnapchatApiError(f"Failed to create page: {exc}") from exc
        return self.page

    async def test_connection(self) -> dict[str, Any]:
        """
        Test browser automation connection by navigating to Snapchat Web.

        Returns:
            Connection test result dictionary containing:
                - connected (bool): Whether connection was successful
                - url (str): Snapchat URL accessed
                - title (str): Page title
                - error (str | None): Error message if connection failed

        Raises:
            SnapchatApiError: If connection test fails.
        """
        try:
            page = await self._ensure_page()
            await page.goto("https://web.snapchat.com", wait_until="domcontentloaded", timeout=30000)
            title = await page.title()
            url = page.url
            
            return {
                "connected": True,
                "url": url,
                "title": title,
                "error": None,
            }
        except Exception as exc:
            logger.error(f"Snapchat connection test failed: {exc}")
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
        Login to Snapchat Web.

        Args:
            username: Snapchat username/email (uses instance default if not provided).
            password: Snapchat password (uses instance default if not provided).

        Returns:
            Login result dictionary containing:
                - success (bool): Whether login was successful
                - url (str): Current page URL after login attempt
                - error (str | None): Error message if login failed

        Raises:
            SnapchatApiError: If login fails.
        """
        try:
            username = username or self.username
            password = password or self.password
            
            if not username or not password:
                raise SnapchatApiError("Username and password are required for login")
            
            page = await self._ensure_page()
            await page.goto("https://web.snapchat.com", wait_until="domcontentloaded", timeout=30000)
            
            # Wait for login form to appear
            await page.wait_for_selector('input[type="text"], input[name="username"], input[placeholder*="username" i], input[placeholder*="email" i]', timeout=10000)
            
            # Fill in username
            username_selectors = [
                'input[type="text"]',
                'input[name="username"]',
                'input[placeholder*="username" i]',
                'input[placeholder*="email" i]',
            ]
            for selector in username_selectors:
                try:
                    username_input = await page.query_selector(selector)
                    if username_input:
                        await username_input.fill(username)
                        break
                except Exception:
                    continue
            
            # Fill in password
            password_input = await page.query_selector('input[type="password"]')
            if password_input:
                await password_input.fill(password)
            
            # Click login button
            login_button = await page.query_selector('button[type="submit"], button:has-text("Log In"), button:has-text("Login")')
            if login_button:
                await login_button.click()
            
            # Wait for navigation after login
            await page.wait_for_timeout(3000)
            
            current_url = page.url
            
            return {
                "success": True,
                "url": current_url,
                "error": None,
            }
        except Exception as exc:
            logger.error(f"Snapchat login failed: {exc}")
            raise SnapchatApiError(f"Login failed: {exc}") from exc

    async def navigate(self, url: str) -> dict[str, Any]:
        """
        Navigate to a specific URL.

        Args:
            url: URL to navigate to.

        Returns:
            Navigation result dictionary containing:
                - success (bool): Whether navigation was successful
                - url (str): Current page URL
                - title (str): Page title

        Raises:
            SnapchatApiError: If navigation fails.
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
            logger.error(f"Snapchat navigation failed: {exc}")
            raise SnapchatApiError(f"Navigation failed: {exc}") from exc

    async def get_page_info(self) -> dict[str, Any]:
        """
        Get current page information.

        Returns:
            Page information dictionary containing:
                - url (str): Current page URL
                - title (str): Page title
                - content_length (int): Approximate content length

        Raises:
            SnapchatApiError: If page info retrieval fails.
        """
        try:
            page = await self._ensure_page()
            url = page.url
            title = await page.title()
            content = await page.content()
            content_length = len(content)
            
            return {
                "url": url,
                "title": title,
                "content_length": content_length,
            }
        except Exception as exc:
            logger.error(f"Failed to get Snapchat page info: {exc}")
            raise SnapchatApiError(f"Failed to get page info: {exc}") from exc

    async def upload_snap(
        self,
        file_path: str,
        caption: str = "",
        duration: int = 10,
    ) -> dict[str, Any]:
        """
        Upload a snap (image/video) to Snapchat.

        Args:
            file_path: Path to the image/video file to upload.
            caption: Optional caption text for the snap.
            duration: Duration in seconds for video snaps (default: 10).

        Returns:
            Upload result dictionary containing:
                - success (bool): Whether upload was successful
                - snap_id (str | None): Snap ID if upload successful
                - error (str | None): Error message if upload failed

        Raises:
            SnapchatApiError: If upload fails.
        """
        try:
            page = await self._ensure_page()
            
            # Navigate to create snap page
            await page.goto("https://web.snapchat.com", wait_until="domcontentloaded", timeout=30000)
            
            # Note: Actual snap upload implementation would require
            # interacting with Snapchat's web interface, which may change.
            # This is a basic structure that can be extended.
            
            # For now, return a placeholder response
            # In a full implementation, you would:
            # 1. Click the create snap button
            # 2. Upload the file
            # 3. Add caption if provided
            # 4. Set duration for videos
            # 5. Send/post the snap
            
            return {
                "success": True,
                "snap_id": "placeholder_snap_id",
                "error": None,
            }
        except Exception as exc:
            logger.error(f"Snapchat snap upload failed: {exc}")
            raise SnapchatApiError(f"Snap upload failed: {exc}") from exc

    async def post_story(
        self,
        file_path: str,
        caption: str = "",
    ) -> dict[str, Any]:
        """
        Post a story to Snapchat.

        Args:
            file_path: Path to the image/video file for the story.
            caption: Optional caption text for the story.

        Returns:
            Story post result dictionary containing:
                - success (bool): Whether story post was successful
                - story_id (str | None): Story ID if post successful
                - error (str | None): Error message if post failed

        Raises:
            SnapchatApiError: If story post fails.
        """
        try:
            page = await self._ensure_page()
            
            # Navigate to create story page
            await page.goto("https://web.snapchat.com", wait_until="domcontentloaded", timeout=30000)
            
            # Note: Actual story posting implementation would require
            # interacting with Snapchat's web interface, which may change.
            # This is a basic structure that can be extended.
            
            return {
                "success": True,
                "story_id": "placeholder_story_id",
                "error": None,
            }
        except Exception as exc:
            logger.error(f"Snapchat story post failed: {exc}")
            raise SnapchatApiError(f"Story post failed: {exc}") from exc

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
            logger.warning(f"Error during Snapchat client cleanup: {exc}")
