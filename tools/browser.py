from langchain_core.tools import BaseTool
from playwright.async_api import async_playwright, Browser, BrowserContext
from typing import Optional, Type
from pydantic import BaseModel, Field


class PlaywrightNavigateInput(BaseModel):
    """Input schema for the Playwright navigation tool."""
    url: str = Field(description="The URL to navigate to")


class PlaywrightNavigateTool(BaseTool):
    """Tool for navigating web pages using Playwright with persistent context."""
    
    name: str = "navigate_webpage"
    description: str = (
        "Navigate to a URL and return the text content of the page. "
        "Maintains browser context across calls to preserve login state."
    )
    args_schema: Type[BaseModel] = PlaywrightNavigateInput
    
    _playwright: Optional[object] = None
    _browser: Optional[Browser] = None
    _context: Optional[object] = None
    _storage_state_path: Optional[str] = None
    
    def __init__(self, storage_state_path: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self._storage_state_path = storage_state_path
    
    async def _arun(self, url: str) -> str:
        try:
            if self._browser is None:
                await self._initialize_browser()
            
            page = await self._context.new_page()
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                content = await page.evaluate("() => document.body.innerText")
                return content
            finally:
                await page.close()
                
        except Exception as e:
            return f"Error navigating to {url}: {str(e)}"
    
    async def _initialize_browser(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.firefox.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        context_options = {}
        if self._storage_state_path:
            context_options['storage_state'] = self._storage_state_path
            
        self._context = await self._browser.new_context(**context_options)
    
    async def save_storage_state(self, path: str):
        if self._context is None:
            raise RuntimeError("Browser context not initialized")
        await self._context.storage_state(path=path)
    
    async def cleanup(self):
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
    
    def _run(self, url: str) -> str:
        raise NotImplementedError("Use async version (_arun) instead")


# Create a singleton instance for import
navigate_webpage = PlaywrightNavigateTool()