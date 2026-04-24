import fnmatch
import glob
import json
import os
import platform
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

CONFIG_FILE = 'rules.json'
PROTECTED_FILES = [r'C:\\Windows\\System32', r'C:\\Program Files', r'C:\\Program Files (x86)']
PROTECTED_EXTS = {'.dll', '.sys', '.exe', '.msi'}


class FOIDSApp:
    def __init__(self, root):
        self.root = root
        self.root.title('FOIDS Cleanup Tool')
        self.root.geometry('650x500')

        if platform.system() != 'Windows':
            messagebox.showerror('Unsupported OS', 'FOIDS is for Windows 11.')
            self.root.destroy()
            return

        self.rules = self.load_rules()
        self.vars = {}
        self.select_all = tk.BooleanVar(value=False)
        self.scan_results = []

        self.status = tk.StringVar(value='IDLE')
        self.space = tk.StringVar(value='Estimated space: 0.00 MB')
        self.count = tk.StringVar(value='Files found: 0')

        self.build_ui()

    def load_rules(self):
        path = Path(__file__).with_name(CONFIG_FILE)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror('Rules Error', f'Could not load {CONFIG_FILE}.\n\n{e}')
            self.root.destroy()
            raise
        return data

    def build_ui(self):
        tk.Label(self.root, text='File-Oriented Information Deletion System', font=('Segoe UI', 18, 'bold')).pack(pady=10)
        tk.Label(self.root, text='FOIDS').pack()

        frame = tk.LabelFrame(self.root, text='Cleanup Categories', padx=10, pady=10)
        frame.pack(fill='x', padx=10, pady=10)
        
        tk.Checkbutton(
            frame,
            text='Select All',
            variable = self.select_all,
            command=self.toggle_select_all,
            font=('Segoe UI', 10, 'bold')
            ).pack(anchor='w')

        for category in self.rules.get('foid_categories', []):
            cid = category['id']
            var = tk.BooleanVar(value=category.get('enabled_by_default', False))
            self.vars[cid] = var
            tk.Checkbutton(frame, text=category['name'], variable=var).pack(anchor='w')

        btns = tk.Frame(self.root)
        btns.pack(pady=5)
        tk.Button(btns, text='Scan', width=12, command=self.scan).pack(side='left', padx=5)
        tk.Button(btns, text='Delete', width=12, command=self.delete_files).pack(side='left', padx=5)
        tk.Button(btns, text='Clear', width=12, command=self.clear_results).pack(side='left', padx=5)
        

        tk.Label(self.root, textvariable=self.space, font=('Segoe UI', 11, 'bold')).pack()
        tk.Label(self.root, textvariable=self.count).pack(pady=(0, 8))
        tk.Label(self.root, textvariable=self.status).pack(pady=(0, 8))

        self.output = tk.Text(self.root, height=16, width=80)
        self.output.pack(fill='both', expand=True, padx=10, pady=10)

    def replace_user(self, path):
        return path.replace('{user}', os.environ.get('USERNAME', ''))

    def category_targets(self, category):
        targets = []
        for raw in category.get('paths', []):
            expanded = glob.glob(self.replace_user(raw))
            if expanded:
                targets.extend(expanded)
            elif os.path.exists(raw):
                targets.append(raw)
        return targets

    def scan_category(self, category):
        matches = []
        patterns = category.get('patterns', ['*'])
        recursive = category.get('recursive', False)

        for t in self.category_targets(category):
            if os.path.isfile(t):
                files = [t]
            else:
                files = []
                if recursive:
                    for root, _, names in os.walk(t):
                        for name in names:
                            files.append(os.path.join(root, name))
                else:
                    try:
                        for name in os.listdir(t):
                            p = os.path.join(t, name)
                            if os.path.isfile(p):
                                files.append(p)
                    except OSError:
                        continue

            for fileP in files:
                name = os.path.basename(fileP)
                if any(fnmatch.fnmatch(name, pat) for pat in patterns):
                    try:
                        matches.append({
                            'category_id': category['id'],
                            'category_name': category['name'],
                            'file_path': fileP,
                            'size': os.path.getsize(fileP),
                        })
                    except OSError:
                        pass
        return matches

    def scan(self):
        self.status.set('Scanning...')
        self.root.update()
        self.output.delete('1.0', 'end')
        self.scan_results = []
        seen = set()

        for category in self.rules.get('foid_categories', []):
            if not self.vars[category['id']].get():
                continue
            for item in self.scan_category(category):
                norm = os.path.normcase(os.path.abspath(item['file_path']))
                if norm not in seen:
                    seen.add(norm)
                    self.scan_results.append(item)

        total = sum(item['size'] for item in self.scan_results)
        self.space.set(f'Estimated space: {total / (1024 * 1024):.2f} MB')
        self.count.set(f'Files found: {len(self.scan_results)}')
        self.status.set('Scan complete')

        for item in self.scan_results[:200]:
            self.output.insert('end', f"{item['category_name']} -> {item['file_path']}\n")
        if len(self.scan_results) > 200:
            self.output.insert('end', f"\n...and {len(self.scan_results) - 200} more files\n")

    def is_safe_to_delete(self, file_path):
        full = os.path.normcase(os.path.abspath(file_path))
        if any(full.startswith(os.path.normcase(p)) for p in PROTECTED_FILES):
            return False
        if os.path.splitext(full)[1].lower() in PROTECTED_EXTS:
            return False
        return True

    def delete_files(self):
        if not self.scan_results:
            messagebox.showwarning('Nothing to delete', 'Run a scan first.')
            return

        total_mb = sum(item['size'] for item in self.scan_results) / (1024 * 1024)
        ok = messagebox.askyesno('Confirm Deletion', f'Delete {len(self.scan_results)} files and reclaim about {total_mb:.2f} MB?')
        if not ok:
            return

        deleted = skipped = 0
        for item in self.scan_results:
            path = item['file_path']
            try:
                if os.path.exists(path) and self.is_safe_to_delete(path):
                    os.remove(path)
                    deleted += 1
                else:
                    skipped += 1
            except OSError:
                skipped += 1

        messagebox.showinfo('Cleanup Summary', f'Deleted: {deleted}\nSkipped: {skipped}')
        self.clear_results()

    def clear_results(self):
        self.scan_results = []
        self.output.delete('1.0', 'end')
        self.space.set('Estimated space: 0.00 MB')
        self.count.set('Files found: 0')
        self.status.set('READY')
        
    def toggle_select_all(self):
        value = self.select_all.get()
        for var in self.vars.values():
            var.set(value)


if __name__ == '__main__':
    root = tk.Tk()
    app = FOIDSApp(root)
    if root.winfo_exists():
        root.mainloop()

