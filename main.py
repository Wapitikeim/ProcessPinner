from tkinter import * 
from tkinter import ttk
from tkinter import PhotoImage

#Dropdown
from tkinter import StringVar
from tkinter.ttk import Combobox

#Saving/Loading
import json
import os 

import psutil

updateIntervall = 1 #in Seconds
activeProcessesList = []
monitoredProcessesLabels = {}
monitoredProcesses = []
monitorWidgets = []
monitoredProcessesFileLocation = "data/monitoredProcesses.json"



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
    filteredProcesses = [p for p in activeProcessesList if name in p[0].lower()]
    if not filteredProcesses:
        return 0
    return 1

def killProcessByName(name: str) -> None:
    filteredProcesses = [p for p in activeProcessesList if name in p[0].lower()]
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

def updateActiveProcesses() -> None:
    global activeProcessesList
    activeProcessesList = getListOfActiveProcesses()

def updateStatus() -> None:
    updateActiveProcesses()
    #Refresh Labels
    for name, label in monitoredProcessesLabels.items():
        is_running = checkIfProcessIsRunning(name)
        if is_running:
            label['label'].config(image=icons["On"])
            label['label'].image = icons["On"]
        else:
            label['label'].config(image=icons["Off"])
            label['label'].image = icons["Off"]
    #Refresh Dropdown
    uniqueNames = sorted(set(name for name, _ in activeProcessesList), key=lambda s: s.lower())
    dropdown["values"] = uniqueNames
    #Intervall
    root.after(updateIntervall * 1000, updateStatus)

#Loading / Saving
def loadMonitoredProcessesFromFile() -> list[str]:
    #Try to open file location
    if not os.path.exists(monitoredProcessesFileLocation):
        default_list = ["opera", "spotify"]
        with open(monitoredProcessesFileLocation, "w") as f:
            json.dump(default_list, f, indent=4)
        return default_list
    # Try to load Data
    try:
        with open(monitoredProcessesFileLocation, "r") as f:
            data = json.load(f)
            # Check if structure contains only Strings
            if isinstance(data, list) and all(isinstance(item, str) for item in data):
                return data
            else:
                print("[!] Structure of monitored processes json faulty – fallback to default list")
                return ["opera", "spotify"]
    except Exception as e:
        print(f"[!] Cannot load monitored process file: {e}")
        return ["opera", "spotify"]

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

    # Check for duplicates
    if name.lower() in (p.lower() for p in monitoredProcesses):
        print(f"[i] '{name}' is already monitored.")
        return

    # Add, save, refresh
    monitoredProcesses.append(name.lower())
    saveCurrentMonitoredProcessesToFile()
    print(f"[+] Added '{name}' to monitored list.")

    #Rebuild Labels
    rebuildMonitoredProcessWidgets()

    # Update display (Status-Labels, Buttons, etc.)
    updateStatus()

#Process logic for Remove Button
def removeProcessFromList(processName: str) -> None:
    #Removes the given process from the monitored list and refreshes the UI.
    if processName in monitoredProcesses:
        monitoredProcesses.remove(processName)
        saveCurrentMonitoredProcessesToFile()
        rebuildMonitoredProcessWidgets()
        print(f"[-] Removed '{processName}' from monitored list.")
    else:
        print(f"[!] '{processName}' is not in the monitored list.")

#Rebuild GUI
def rebuildMonitoredProcessWidgets() -> None:
    global monitoredProcessesLabels, monitorWidgets

    # Remove existing process widgets
    for widget in monitorWidgets:
        widget.destroy()

    monitorWidgets.clear()
    monitoredProcessesLabels.clear()

    # Rebuild from current monitoredProcesses
    for i, processName in enumerate(monitoredProcesses):
        # Name label
        name_label = ttk.Label(frame, text=processName.capitalize())
        name_label.grid(column=0, row=i)
        monitorWidgets.append(name_label)

        # Status label
        status_label = Label(frame, image=icons["Neutral"])
        status_label.grid(column=1, row=i)
        monitorWidgets.append(status_label)

        # Kill button
        kill_button = ttk.Button(frame, text="Close", command=lambda name=processName: killProcessByName(name))
        kill_button.grid(column=2, row=i)
        monitorWidgets.append(kill_button)

        # Remove button
        remove_button = ttk.Button(frame, text="Remove", command=lambda name=processName: removeProcessFromList(name))
        remove_button.grid(column=3, row=i)
        monitorWidgets.append(remove_button)

        # Store reference for status updates
        monitoredProcessesLabels[processName] = {'label': status_label}
    
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
    root.title("Process Killer")
    #Icon
    icon = PhotoImage(file = "assets/ico.png")
    root.wm_iconphoto(False, icon)

    #Icons need existing root window
    icons = {
    "On": PhotoImage(file="assets/On.png"),
    "Off": PhotoImage(file="assets/Off.png"),
    "Neutral": PhotoImage(file="assets/Neutral.png")
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
    
    



