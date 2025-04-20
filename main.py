from tkinter import * 
from tkinter import ttk
from tkinter import PhotoImage

#Dropdown
from tkinter import StringVar
from tkinter.ttk import Combobox

#Open Button
import subprocess

#Saving/Loading
import json
import os 

#Building
import sys

import psutil

appName = "ProcessPinner"
updateIntervall = 1 #in Seconds
activeProcessesList = []
monitoredProcessesLabels = {}
monitoredProcesses = []
monitorWidgets = []
monitoredProcessesFileLocation = "data/monitoredProcesses.json"

#Builds
def getResourcePath(relative_path: str) -> str:
    ### Get absolute path to resource (for PyInstaller or dev). 
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def getListOfActiveProcesses() -> list[tuple[str, int]]:
    activeProcesses = []
    for process in psutil.process_iter(["pid", "name"]):
        try:
            name = process.info['name'] or "Unknown"
            pid = process.info['pid']
            activeProcesses.append((name,pid))
        except(psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return activeProcesses

def checkIfProcessIsRunning(name: str) -> bool:
    filteredProcesses = [p for p in activeProcessesList if name.lower() in p[0].lower()]
    if not filteredProcesses:
        return 0
    return 1

def killProcessByName(name: str) -> None:
    filteredProcesses = [p for p in activeProcessesList if name.lower() in p[0].lower()]
    if not filteredProcesses:
        print(f"Process {name} was not running.")
        return
    for proc_name, pid in filteredProcesses:
        try:
            proc = psutil.Process(pid)
            proc.kill()
            print(f"Killed process: {proc_name} (PID {pid})")
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f"[-] Failed to kill {proc_name} (PID {pid}): {e}")

def getMainExecutablePath(process_name: str) -> str | None:
    #Returns the most likely path to the main executable of a process.
    candidates = []

    for proc in psutil.process_iter(['name', 'exe', 'pid']):
        try:
            if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                if proc.info['exe']:
                    candidates.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not candidates:
        return None

    # First priority: exact match to process_name.exe
    expected_exe_name = f"{process_name.lower()}.exe"
    for proc in candidates:
        exe_path = proc.info['exe']
        if exe_path and os.path.basename(exe_path).lower() == expected_exe_name:
            return exe_path  # highest confidence

    # Second: if all .exe paths are the same, return that
    unique_paths = set(p.info['exe'] for p in candidates)
    if len(unique_paths) == 1:
        return list(unique_paths)[0]

    # Third: fallback to lowest PID
    main_proc = min(candidates, key=lambda p: p.pid)
    return main_proc.info['exe']

def updateActiveProcesses() -> None:
    global activeProcessesList
    activeProcessesList = getListOfActiveProcesses()

def updateStatus() -> None:
    updateActiveProcesses()
    #Refresh Labels
    for name, label in monitoredProcessesLabels.items():
        is_running = checkIfProcessIsRunning(name)
        label['label'].config(image=icons["On"] if is_running else icons["Off"])
        label['label'].image = icons["On"] if is_running else icons["Off"]
    #Refresh Dropdown
    uniqueNames = sorted(set(name for name, _ in activeProcessesList), key=lambda s: s.lower())
    dropdown["values"] = uniqueNames
    #Intervall
    root.after(updateIntervall * 1000, updateStatus)

def getUserDataPath(relative: str = "") -> str:
    #Returns an absolute path under AppData/Local/AppName/.
    base = os.path.join(os.getenv("LOCALAPPDATA"), appName)
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, relative)

#Loading / Saving
def loadMonitoredProcessesFromFile() -> list[str]:
    #Try to open file location
    if not os.path.exists(monitoredProcessesFileLocation):
        default_list = [
            {"name": "opera", "path": None},
            {"name": "spotify", "path": None}
        ]
        with open(monitoredProcessesFileLocation, "w") as f:
            json.dump(default_list, f, indent=4)
        return default_list
    # Try to load Data
    try:
        with open(monitoredProcessesFileLocation, "r") as f:
            data = json.load(f)

        # Compatibility: Allow old format (list[str])
        if isinstance(data, list):
            formatted = []
            for entry in data:
                if isinstance(entry, str):
                    formatted.append({"name": entry, "path": None})
                elif isinstance(entry, list) and len(entry) == 2:
                    formatted.append({"name": entry[0], "path": entry[1]})
                elif isinstance(entry, dict) and "name" in entry:
                    formatted.append({
                        "name": entry["name"],
                        "path": entry.get("path")
                    })
            return formatted

        print("[!] Invalid monitored process format.")
        return []
    except Exception as e:
        print(f"[!] Failed to load monitored processes: {e}")
        return []

def saveCurrentMonitoredProcessesToFile() -> None:
    #Saves the current monitoredProcesses list to JSON file.
    with open(monitoredProcessesFileLocation, "w") as f:
        json.dump(monitoredProcesses, f, indent=4)

#Process logic for Combobox
def addSelectedProcessToMonitor() -> None:
    #Adds the selected process (from dropdown) to the monitored list.
    name = dropdown_var.get().strip()

    if not name:
        print("[!] No process selected.")
        return

    # Remove .exe if present
    if name.lower().endswith(".exe"):
        name = name[:-4]

    # Check for duplicate (case-insensitive)
    if any(entry["name"].lower() == name.lower() for entry in monitoredProcesses):
        print(f"[i] '{name}' is already monitored.")
        return

    # Try to detect path if process is running
    path = getMainExecutablePath(name)

    monitoredProcesses.append({"name": name, "path": path})
    saveCurrentMonitoredProcessesToFile()
    print(f"[+] Added '{name}' with path: {path}")

    rebuildMonitoredProcessWidgets()

#Process logic for Remove Button
def removeProcessFromList(processName: str) -> None:
    #Removes the given process from the monitored list and refreshes the UI.
    global monitoredProcesses
    monitoredProcesses = [p for p in monitoredProcesses if p["name"].lower() != processName.lower()]
    saveCurrentMonitoredProcessesToFile()
    rebuildMonitoredProcessWidgets()

#Process logic for Open Button
def openProcessByName(name: str, path: str | None) -> None:
    if checkIfProcessIsRunning(name):
        print(f"[i] '{name}' is already running.")
        return

    if not path or not os.path.isfile(path):
        print(f"[!] No valid path found for '{name}' – cannot launch.")
        return

    try:
        subprocess.Popen([path])
        print(f"[+] Started '{name}' from '{path}'")
    except Exception as e:
        print(f"[!] Failed to start '{name}': {e}")

#Rebuild GUI
def rebuildMonitoredProcessWidgets() -> None:
    global monitoredProcessesLabels, monitorWidgets

    # Remove existing process widgets
    for widget in monitorWidgets:
        widget.destroy()

    monitorWidgets.clear()
    monitoredProcessesLabels.clear()

    # Rebuild from current monitoredProcesses
    for i, entry in enumerate(monitoredProcesses):
        name = entry["name"]
        path = entry.get("path")
        
        #Name label
        name_label = ttk.Label(frame, text=name.capitalize())
        name_label.grid(column=0, row=i)
        monitorWidgets.append(name_label)

        #Status Symbol
        status_label = Label(frame, image=icons["Neutral"])
        status_label.grid(column=1, row=i)
        monitorWidgets.append(status_label)

        #Kill/Close Button
        kill_button = ttk.Button(frame, text="Close", command=lambda n=name: killProcessByName(n))
        kill_button.grid(column=2, row=i)
        monitorWidgets.append(kill_button)

        #Remove Button
        remove_button = ttk.Button(frame, text="Remove", command=lambda n=name: removeProcessFromList(n))
        remove_button.grid(column=3, row=i)
        monitorWidgets.append(remove_button)

        #Open Button
        open_button = ttk.Button(frame, text="Open", command=lambda n=name, p=path: openProcessByName(n, p))
        open_button.grid(column=4, row=i)
        monitorWidgets.append(open_button)

        monitoredProcessesLabels[name] = {'label': status_label}

    
    #Reposition Combobox / Add / Quit Button
    # Add dropdown and buttons BELOW the process rows
    last_row = len(monitoredProcesses) + 1

    unique_names = sorted(set(name for name, _ in activeProcessesList), key=lambda s: s.lower())
    dropdown_var.set("")  # reset selection
    dropdown["values"] = unique_names
    dropdown.grid(column=0, row=last_row, columnspan=2)

    add_button.grid(column=2, row=last_row)
    quit_button.grid(column=5, row=last_row)

#Main
if __name__ == "__main__":
    root = Tk()
    root.title(appName)
    #Icon
    icon = PhotoImage(file = getResourcePath("assets/ico.png"))
    root.wm_iconphoto(False, icon)

    #For Builds
    monitoredProcessesFileLocation  = getUserDataPath() + "monitoredProcesses.json"
    
    #Icons need existing root window
    icons = {
    "On": PhotoImage(file=getResourcePath("assets/On.png")),
    "Off": PhotoImage(file=getResourcePath("assets/Off.png")),
    "Neutral": PhotoImage(file=getResourcePath("assets/Neutral.png"))
    }

    frame = ttk.Frame(root, padding=5) #padding = Rand
    frame.grid()

    updateActiveProcesses()

    monitoredProcesses = loadMonitoredProcessesFromFile()
    
    #Dropdown "Combobox"
    uniqueNames = sorted(set(name for name, _ in activeProcessesList), key=lambda s: s.lower())
    dropdown_var = StringVar()
    dropdown = Combobox(frame, textvariable=dropdown_var, state="readonly")
    #Add/Quit Buttons
    add_button = ttk.Button(frame, text="Add", command=addSelectedProcessToMonitor)
    quit_button = ttk.Button(frame, text="Quit", command=root.destroy)

    rebuildMonitoredProcessWidgets()

    updateStatus()

    root.mainloop()
    
    



