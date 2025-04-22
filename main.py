from tkinter import Tk
from src.ProcessMonitor import ProcessMonitor
from src.ProcessAppUI import ProcessAppUI

#Main
if __name__ == "__main__":
    monitor = ProcessMonitor()
    app = ProcessAppUI(Tk(), monitor)
    app.run()

    
    
    
    
    



