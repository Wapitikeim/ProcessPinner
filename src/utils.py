import os
import sys

from src.config import APP_NAME


def getResourcePath(relative_path: str) -> str:
    ### Get absolute path to resource (for PyInstaller or dev). 
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def getUserDataPath(relative: str = "") -> str:
    #Returns an absolute path under AppData/Local/AppName/.
    base = os.path.join(os.getenv("LOCALAPPDATA"), APP_NAME)
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, relative)