from src.utils import * 
from src.config import * 

import psutil
import json

class ProcessMonitor:
    def __init__(self):
        self.monitoredProcessesFileLocation = getUserDataPath() + PROCESS_MONITOR_NAME_JSON
        self.activeProcessesList: list[dict] = []
        self.updateActiveProcessesList()

    #Management
    def updateActiveProcessesList(self) -> None:
        self.activeProcessesList.clear()
        for process in psutil.process_iter(["pid", "name"]):
            try:
                name = process.info['name'] or "Unknown"
                pid = process.info['pid']
                self.activeProcessesList.append((name,pid))
            except(psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    def checkIfProcessIsRunning(self, name: str) -> bool:
        filteredProcesses = [p for p in self.activeProcessesList if name.lower() in p[0].lower()]
        if not filteredProcesses:
            return 0
        return 1
    
    def killProcessByName(self, name: str) -> None:
        filteredProcesses = [p for p in self.activeProcessesList if name.lower() in p[0].lower()]
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

    def getMainExecutablePath(self, process_name: str) -> str | None:
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
    
    #Loading / Saving

    def loadMonitoredProcessesFromFile(self) -> list[str]:
        #Try to open file location
        if not os.path.exists(self.monitoredProcessesFileLocation):
            default_list = [
                {"name": DEFAULT_MONITORED_PROCESSES[0], "path": None},
                {"name": DEFAULT_MONITORED_PROCESSES[1], "path": None}
            ]
            with open(self.monitoredProcessesFileLocation, "w") as f:
                json.dump(default_list, f, indent=4)
            return default_list
        # Try to load Data
        try:
            with open(self.monitoredProcessesFileLocation, "r") as f:
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

    def saveMonitoredProcessesToFile(self, monitoredProcesses) -> None:
        #Saves the current monitoredProcesses list to JSON file.
        with open(self.monitoredProcessesFileLocation, "w") as f:
            json.dump(monitoredProcesses, f, indent=4)