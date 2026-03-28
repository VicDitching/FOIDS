import os 
import json 
import tkinter as tk
from tkinter import messagebox, ttk 
import platform 
from pathlib import Path

class FOIDS:
    def __initialization__(self, root):
        #SDD_LDD_PY_GUI_001: Initialize the main application window
        #Trace Tags: FR-04, IR-02
        self.root = root
        self.root.title("FOIDS Cleanup Tool")
        self.root.geometry("450x500")

        #Checks if tool is being used in Windows 11
        #Trace Tags: ESR-01, NFR-01
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
        #DC-02: uses the python 'json' module to parse the rules.json file 
        #Trace Tags: [SDD_HLD_CONFIG_001]
        try: 
            with open('rules.json', 'r') as f: 
                return json.load(f)
        except Exception as e: 
                #error handling if JSON is missing or malformed 
                print(f"Error loading configuration: {e}")
                return {}
    
    def create_components(self):
        return
    
    def scanner(self):
        return
    
    def confirmation(self):
        #safety check to ensure user intent before permanently deleting the selected files
        #Trace Tags: FR-05, SR-03
        if messagebox.askyesno("Confirm Deletion", "Are you sure? This will permanently delete the selected files."):
            self.run_deletion()

    def deletion(self):
        return
