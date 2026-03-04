import shutil
import os
from pathlib import Path

source = r"h:\DevWork\Win_Apps\Prive_Randomizer\Windows\dist\PriveRandomizer.exe"
destination = os.path.expanduser(r"~\Desktop\PriveRandomizer.exe")

try:
    if os.path.exists(source):
        shutil.copy2(source, destination)
        if os.path.exists(destination):
            print("SUCCESS: PriveRandomizer.exe copied to desktop")
        else:
            print("ERROR: Copy did not complete")
    else:
        print(f"ERROR: Source not found: {source}")
except Exception as e:
    print(f"ERROR: {e}")
