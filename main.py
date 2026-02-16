import subprocess
import shutil
import os
import time
import ctypes
import sys
from pathlib import Path
from colorama import init, Fore
import re

# just file paths 
init(autoreset=True)
basedir = Path(__file__).resolve().parent
offsetfinder = basedir / "RDPWrapOffsetFinder-0.9" / "64bit" / "RDPWrapOffsetFinder.exe"
templateini = basedir / "rdpwrap.ini"
rdpwrapper = Path(r"C:\Program Files\RDP Wrapper")
finalini = rdpwrapper / "rdpwrap.ini"
rbtray = basedir / "RBTRAY" / "rbtray.exe"

# admin check stuff
def admincheck():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def elevate():
    script = sys.executable
    params = " ".join([f'"{arg}"' for arg in sys.argv])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", script, params, None, 1)

# rbtray start

def startrbtray():
    print(f"{Fore.YELLOW}Starting RBTray...")
    subprocess.Popen([str(f"./{rbtray}")], cwd=rbtray.parent, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"{Fore.GREEN}RBTray started successfully, exitting now.")

# termservice start/stop

def stopservice():
    print(f"{Fore.YELLOW}Stopping dependant rdp service...")
    subprocess.run(["sc", "stop", "umrdpservice"], capture_output=True)
    print(f"{Fore.YELLOW}Stopping Rdp Service...")
    subprocess.run(["sc", "stop", "TermService"], capture_output=True)
    time.sleep(.25)
    copyini()

def startservice():
    print(f"{Fore.YELLOW}Starting TermService...")
    subprocess.run(["sc", "start", "TermService"], capture_output=True)
    print(f"{Fore.GREEN}TermService started successfully.")
    startrbtray()

# ini file stuff

def backupini():
    if os.path.exists(finalini):
        backup_name = f"rdpwrap_backup_{int(time.time())}.ini"
        backup_path = os.path.join(rdpwrapper, backup_name)
        shutil.copy2(finalini, backup_path)
        print(f"{Fore.GREEN}Backup created: {backup_path}")

def copyini():
    if not os.path.exists(templateini):
        raise FileNotFoundError("rdpwrap.ini not found.")

    if not os.path.exists(rdpwrapper):
        raise FileNotFoundError("RDP Wrapper directory not found.")

    backupini()

    print(f"{Fore.YELLOW}Adding rdpwrap.ini...")
    shutil.copy2(templateini, finalini)
    print(f"{Fore.GREEN}Added rdpwrap.ini successfully.")
    startservice()

def getoffsets():
    print(f"{Fore.YELLOW}Getting offsets.")

    process = subprocess.Popen(
        [str(offsetfinder)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=offsetfinder.parent
    )

    output, _ = process.communicate()

    if not output or not output.strip():
        print(f"{Fore.RED} Unable to get offsets, aborting.")
        return

    match = re.search(r"^\[(.+?)\]", output, re.MULTILINE)
    if not match:
        print(f"{Fore.RED}Invalid output, aborting.")
        return

    version = match.group(1)   

    if templateini.exists():
        existing_text = templateini.read_text(encoding="utf-8", errors="ignore")

        if f"[{version}]" in existing_text:
            print(f"{Fore.GREEN}Offsets for {version} already exist")
            stopservice()
            return

    with templateini.open("a", encoding="utf-8") as f:
        f.write("\n" + output.strip() + "\n")

    print(f"{Fore.GREEN}Added new offsets for {version}")

    stopservice()

def main():
    print(f"{Fore.CYAN}===Rdp updater or something===")

    if not admincheck():
        print(f"{Fore.RED} Not running as admin")
        elevate()
        sys.exit(0)

    getoffsets()


if __name__ == "__main__":
    main()