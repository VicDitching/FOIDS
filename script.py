import os 
import json 
import tkinter import messagebox, ttk 
import platform 
from pathlib import Path

class FOIDS:
    def __initialization__(self, root):
        #Initialize the main application window
        #Trace Tags: FR-04, IR-02
        self.root = root
        self.root.title("FOIDS Cleanup Tool")
        self.root.geometry("")

        #Checks if tool is being used in Windows 11
        if platform.system() != "Windows":
            messagebox.showerror("OS Error", "This tool is specifically for Windows 11")
            self.root.destroy()
            return
        
        #loads the data from the external JSON file
        self.rules = self.load_configuration()
        #to store file data found during scanning for the deletion engine
        self.scan_results = []
        #to store the state of GUI checkboxes
        self.category = {}
        #build user inteface components
        self.create_components()

    def load_configuration(self): 
        
    
    def create_components(self):

    
    def scanner(self):

    
    def confirmation(self):
        
    
    def deletion(self):

    
