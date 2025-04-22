from tkinter import * 
from tkinter import ttk
from tkinter import PhotoImage

#Dropdown
from tkinter import StringVar
from tkinter.ttk import Combobox

#Open Button
import subprocess

from src.config import * 
from src.utils import *

from src.ProcessMonitor import ProcessMonitor

class ProcessAppUI:
    def __init__(self, root: Tk, monitor: ProcessMonitor):
        self.root = root
        self.monitor = monitor
        self.monitoredProcessesLabels = {}
        self.monitoredProcesses = self.monitor.loadMonitoredProcessesFromFile()
        self.monitorWidgets = []
        self.initRootWindowAndFrame()
        self.initPermanentButtons()

        self.monitor.updateActiveProcessesList()
    
    def initRootWindowAndFrame(self) -> None:
        #Tk init 
        self.root.title(APP_NAME)
        #App icon
        icon = PhotoImage(file = getResourcePath("assets/ico.png"))
        self.root.wm_iconphoto(False, icon)
        #Status icons need existing root window
        self.icons = {
        "On": PhotoImage(file=getResourcePath("assets/On.png")),
        "Off": PhotoImage(file=getResourcePath("assets/Off.png")),
        "Neutral": PhotoImage(file=getResourcePath("assets/Neutral.png"))
        }
        self.frame = ttk.Frame(self.root, padding=5) #padding = Rand
        self.frame.grid()
    
    def initPermanentButtons(self) -> None:
        #Dropdown "Combobox"
        self.uniqueNames = sorted(set(name for name, _ in self.monitor.activeProcessesList), key=lambda s: s.lower())
        self.dropdown_var = StringVar()
        self.dropdown = Combobox(self.frame, textvariable=self.dropdown_var, state="readonly")
        #Add/Quit Buttons
        self.add_button = ttk.Button(self.frame, text="Add", command=self.addSelectedProcessToMonitor)
        self.quit_button = ttk.Button(self.frame, text="Quit", command=self.root.destroy)
    
    #Combobox
    def addSelectedProcessToMonitor(self) -> None:
        #Adds the selected process (from dropdown) to the monitored list.
        name = self.dropdown_var.get().strip()

        if not name:
            print("[!] No process selected.")
            return

        # Remove .exe if present
        if name.lower().endswith(".exe"):
            name = name[:-4]

        # Check for duplicate (case-insensitive)
        if any(entry["name"].lower() == name.lower() for entry in self.monitoredProcesses):
            print(f"[i] '{name}' is already monitored.")
            return

        # Try to detect path if process is running
        path = self.monitor.getMainExecutablePath(name)

        self.monitoredProcesses.append({"name": name, "path": path})
        self.monitor.saveMonitoredProcessesToFile(self.monitoredProcesses)
        print(f"[+] Added '{name}' with path: {path}")

        self.rebuildMonitoredProcessWidgets()
    
    #Remove Button
    def removeProcessFromList(self, processName: str) -> None:
        #Removes the given process from the monitored list and refreshes the UI.
        self.monitoredProcesses = [p for p in self.monitoredProcesses if p["name"].lower() != processName.lower()]
        self.monitor.saveMonitoredProcessesToFile(self.monitoredProcesses)
        self.rebuildMonitoredProcessWidgets()
    
    #Open Button
    def openProcessByName(self, name: str, path: str | None) -> None:
        if self.monitor.checkIfProcessIsRunning(name):
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

    def rebuildMonitoredProcessWidgets(self) ->None:
        # Remove existing process widgets
        for widget in self.monitorWidgets:
            widget.destroy()

        self.monitorWidgets.clear()
        self.monitoredProcessesLabels.clear()

        # Rebuild from current monitoredProcesses
        for i, entry in enumerate(self.monitoredProcesses):
            name = entry["name"]
            path = entry.get("path")
            
            #Name label
            name_label = ttk.Label(self.frame, text=name.capitalize())
            name_label.grid(column=0, row=i)
            self.monitorWidgets.append(name_label)

            #Status Symbol
            status_label = Label(self.frame, image=self.icons["Neutral"])
            status_label.grid(column=1, row=i)
            self.monitorWidgets.append(status_label)

            #Kill/Close Button
            kill_button = ttk.Button(self.frame, text="Close", command=lambda n=name: self.monitor.killProcessByName(n))
            kill_button.grid(column=2, row=i)
            self.monitorWidgets.append(kill_button)

            #Remove Button
            remove_button = ttk.Button(self.frame, text="Remove", command=lambda n=name: self.removeProcessFromList(n))
            remove_button.grid(column=3, row=i)
            self.monitorWidgets.append(remove_button)

            #Open Button
            open_button = ttk.Button(self.frame, text="Open", command=lambda n=name, p=path: self.openProcessByName(n, p))
            open_button.grid(column=4, row=i)
            self.monitorWidgets.append(open_button)

            self.monitoredProcessesLabels[name] = {'label': status_label}

        
        #Reposition Combobox / Add / Quit Button
        # Add dropdown and buttons BELOW the process rows
        last_row = len(self.monitoredProcesses) + 1

        unique_names = sorted(set(name for name, _ in self.monitor.activeProcessesList), key=lambda s: s.lower())
        self.dropdown_var.set("")  # reset selection
        self.dropdown["values"] = unique_names
        self.dropdown.grid(column=0, row=last_row, columnspan=2)

        self.add_button.grid(column=2, row=last_row)
        self.quit_button.grid(column=5, row=last_row)
    
    #Update
    def updateStatus(self) -> None:
        self.monitor.updateActiveProcessesList()
        #Refresh Labels
        for name, label in self.monitoredProcessesLabels.items():
            is_running = self.monitor.checkIfProcessIsRunning(name)
            label['label'].config(image=self.icons["On"] if is_running else self.icons["Off"])
            label['label'].image = self.icons["On"] if is_running else self.icons["Off"]
        
        #Refresh Dropdown
        self.uniqueNames = sorted(set(name for name, _ in self.monitor.activeProcessesList), key=lambda s: s.lower())
        self.dropdown["values"] = self.uniqueNames
        #Intervall
        self.root.after(UPDATE_INTERVAL, self.updateStatus)

    def run(self) -> None:
        self.rebuildMonitoredProcessWidgets()
        self.updateStatus()
        self.root.mainloop()
    
