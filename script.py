import os 
import json 
import tkinter as tk
from tkinter import messagebox, ttk 
import platform 
from pathlib import Path
import glob
import time

class FOIDS:
    def __init__(self, root):
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
            self.delete()

    def delete(self):
        return
        
    def replace_placeholders(self, path):
        #function used to switch out placeholder usernames 
        current_user = os.environ.get("USERNAME") or os.getlogin()
            
        #holding dictionary for users
        placeholderDict = {
            "{user}" : current_user
        }

        for key, value in placeholderDict.items():
            path = path.replace(key, value)

        return path
    
    def expand_path(self, path):
        if "*" in path or "?" in path:
            return glob.glob(path)
        
        if os.path.exists(path):
            return [path]
        
        return []
    def get_category_targets (self, category):
         
         targets = []

         for raw_path in category.get("paths", []):
            resolved_path = self.replace_placeholders(raw_path)
            expanded_paths = self.expand_path(resolved_path)
            targets.extend(expanded_paths)

        return targets

    def age_check(self, file_path, category):
        max_age_days = category.get("max_age_days")

        if max_age_days is None:
            return True
        
        try:
        modified_time = os.path.getmtime(file_path)
        current_time = time.time()
        age_days = (current_time - modified_time) / 86400
        return age_days > max_age_days
    except Exception:
        return False

    def scan_category(self, category):
        matched_files = []
        targets = self.get_category_targets(category)
        patterns = category.get("patterns", ["*"])
        recursive = category.get("recursive", False)

        for target in targets:
            for pattern in patterns:
                try:
                    search_pattern = os.path.join(target, "**", pattern) if recursive else os.path.join(target, pattern)
                    found_paths = glob.glob(search_pattern, recursive=recursive)

                    for found_path in found_paths:
                        if os.path.isfile(found_path) and self.passes_age_rule(found_path, category):
                        matched_files.append({
                            "category_id": category.get("id"),
                            "category_name": category.get("name"),
                            "file_path": found_path,
                            "size": os.path.getsize(found_path)
                        })
                except Exception as e:
                    print(f"Error scanning target {target}: {e}")

    return matched_files


        
