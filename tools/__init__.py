from .system import get_current_time, get_filesystem
from .browser import navigate_webpage

# Single point to import all tools
ALL_TOOLS = [
    get_current_time,
    get_filesystem,
    #navigate_webpage
]

# Organize by namespace
SYSTEM_TOOLS = [get_current_time, get_filesystem]
#BROWSER_TOOLS = [navigate_webpage]

# Export for easy imports
__all__ = [
    'ALL_TOOLS', 
    'SYSTEM_TOOLS', 
    #'BROWSER_TOOLS',
    'get_current_time', 
    'get_filesystem',
    #'navigate_webpage'
]