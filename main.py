from tkinter import * 
from tkinter import ttk
from tkinter import PhotoImage

import psutil

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
    filteredProcesses = [p for p in getListOfActiveProcesses() if name in p[0].lower()]
    if not filteredProcesses:
        return 0
    return 1

def killProcessByName(name: str) -> None:
    filteredProcesses = [p for p in getListOfActiveProcesses() if name in p[0].lower()]
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

def updateStatus() -> None:
    if checkIfProcessIsRunning("steam"):
        onOffLabel.config(image=icons["On"])
        onOffLabel.image = icons["On"]
    else:
        onOffLabel.config(image=icons["Off"])
        onOffLabel.image = icons["Off"]
    
    if checkIfProcessIsRunning("spotify"):
        onOffLabel2.config(image=icons["On"])
        onOffLabel2.image = icons["On"]
    else:
        onOffLabel2.config(image=icons["Off"])
        onOffLabel2.image = icons["Off"]


    root.after(1000, updateStatus)



#Main
if __name__ == "__main__":
    root = Tk()
    
    #Icons brauchen root window
    icons = {
    "On": PhotoImage(file="assets/On.png"),
    "Off": PhotoImage(file="assets/Off.png"),
    "Neutral": PhotoImage(file="assets/Neutral.png")
    }

    frame = ttk.Frame(root, padding=5) #padding = Rand
    frame.grid()
    ttk.Label(frame, text="Steam").grid(column=0, row=0)
    ttk.Label(frame, text="Spotify").grid(column=0, row=1)

    onOffLabel = Label(frame, image=icons["Neutral"])
    onOffLabel.grid(column=1,row=0)

    onOffLabel2 = Label(frame, image=icons["Neutral"])
    onOffLabel2.grid(column=1,row=1)

    ttk.Button(frame, text="Kill", command=lambda:killProcessByName("steam")).grid(column=2,row=0)
    ttk.Button(frame, text="Kill", command=lambda:killProcessByName("spotify")).grid(column=2,row=1)
    ttk.Button(frame, text="Quit", command=root.destroy).grid(column=5, row=3)

    updateStatus()
    root.mainloop()
    
    



