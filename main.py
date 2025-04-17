from tkinter import * 
from tkinter import ttk
from tkinter import PhotoImage

#Saving/Loading
import json
import os 

import psutil

updateIntervall = 1 #in Seconds
activeProcessesList = []
monitoredProcesses = []
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
    for name, label in monitoredProcessesLabels.items():
        is_running = checkIfProcessIsRunning(name)
        if is_running:
            label['label'].config(image=icons["On"])
            label['label'].image = icons["On"]
        else:
            label['label'].config(image=icons["Off"])
            label['label'].image = icons["Off"]
    
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

#Main
if __name__ == "__main__":
    root = Tk()
    root.title("Process Killer")
    #Icon
    icon = PhotoImage(file = "assets/ico.png")
    root.wm_iconphoto(False, icon)

    #Icons brauchen root window
    icons = {
    "On": PhotoImage(file="assets/On.png"),
    "Off": PhotoImage(file="assets/Off.png"),
    "Neutral": PhotoImage(file="assets/Neutral.png")
    }

    frame = ttk.Frame(root, padding=5) #padding = Rand
    frame.grid()

    updateActiveProcesses()

    monitoredProcesses = loadMonitoredProcessesFromFile()
    
    monitoredProcessesLabels = {}
    
    for i,processName in enumerate(monitoredProcesses):
        #Name and Label
        ttk.Label(frame,text=processName.capitalize()).grid(column=0, row=i)

        #Status Label
        statusLabel = Label(frame, image=icons["Neutral"])
        statusLabel.grid(column=1, row=i)

        #Close Button
        ttk.Button(frame, text="Close", command=lambda name=processName: killProcessByName(name)).grid(column=2, row=i)

        #Dict for Update
        monitoredProcessesLabels[processName] = {'label' : statusLabel}

    ttk.Button(frame, text="Quit", command=root.destroy).grid(column=5, row=len(monitoredProcesses))

    updateStatus()
    root.mainloop()
    
    



