# Standard library imports for file system operations
import os

# Used to load and parse JSON rules
import json

# GUI framework (used only when GUI is enabled by Jay)
import tkinter as tk
from tkinter import messagebox

# Used to check operating system compatibility
import platform

# Used for wildcard path expansion (e.g., * and ?)
import glob

# Used for time calculations (file age filtering)
import time


class FOIDS:
    def __init__(self, root=None):
        # SDD_LDD_PY_GUI_001: Initialize the main application window
        # Trace Tags: FR-04, IR-02
        self.root = root

        if self.root is not None:
            self.root.title("FOIDS Cleanup Tool")
            self.root.geometry("450x500")

        # ESR-01: Ensure application runs only on Windows systems
        if platform.system() != "Windows":
            if self.root is not None:
                messagebox.showerror("OS Error", "This tool is specifically for Windows 11")
                self.root.destroy()
            else:
                print("OS Error: This tool is specifically for Windows 11")
            return

        # SDD_HLD_CONFIG_001: Load rules from external JSON config
        self.rules = self.load_configuration()

        # Data structure to store scan results
        self.scan_results = []

        # IR-03: Stores checkbox state for each category (used by GUI)
        self.category_states = {}

        if self.root is not None:
            self.create_components()

    def log(self, message):
        # Utility logging function (can be redirected to GUI later)
        print(message)

    def load_configuration(self):
        # DC-02: Parse JSON configuration file
        # Trace Tags: SDD_HLD_CONFIG_001
        try:
            with open("foidRules.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.log(f"Error loading configuration: {e}")
            return {}

    def create_components(self):
        # GUI construction handled by Jay
        return

    def scanner(self, selected_category_ids=None):
        #Scan system based on selected categories
        self.scan_results = []
        seen_paths = set()

        for category in self.rules.get("foid_categories", []):
            category_id = category.get("id")

            if selected_category_ids is not None and category_id not in selected_category_ids:
                continue

            category_results = self.scan_category(category)

            # Deduplicate files across categories
            for item in category_results:
                normalized = os.path.normcase(os.path.abspath(item["file_path"]))
                if normalized not in seen_paths:
                    seen_paths.add(normalized)
                    self.scan_results.append(item)

        return self.scan_results

    def confirmation(self, dry_run=True):
        # FR-05, SR-03: Confirm deletion before execution
        if dry_run:
            return self.delete(dry_run=True, limit=20)

        if self.root is None:
            return self.delete(dry_run=False)

        if messagebox.askyesno(
            "Confirm Deletion",
            "Are you sure? This will permanently delete the selected files?"
        ):
            return self.delete(dry_run=False)

        return {
            "deleted": 0,
            "failed": 0,
            "skipped": 0,
            "protected": 0,
            "processed": 0
        }

    def replace_placeholders(self, path):
        # Replace placeholders like {user} with actual system values
        current_user = os.environ.get("USERNAME") or os.getlogin()

        placeholder_dict = {
            "{user}": current_user
        }

        for key, value in placeholder_dict.items():
            path = path.replace(key, value)

        return path

    def expand_path(self, path):
        # Expand wildcard paths (*, ?) or validate direct paths
        if "*" in path or "?" in path:
            return glob.glob(path)

        if os.path.exists(path):
            return [path]

        return []

    def get_category_by_id(self, category_id):
        # Retrieve category config by ID
        for category in self.rules.get("foid_categories", []):
            if category.get("id") == category_id:
                return category
        return None

    def get_category_targets(self, category):
        # Resolve and expand all paths for a category
        targets = []

        for raw_path in category.get("paths", []):
            resolved_path = self.replace_placeholders(raw_path)
            expanded_paths = self.expand_path(resolved_path)
            targets.extend(expanded_paths)

        return targets

    def is_path_within(self, child_path, parent_path):
        # Check if file is within allowed directory
        try:
            child_abs = os.path.normcase(os.path.abspath(child_path))
            parent_abs = os.path.normcase(os.path.abspath(parent_path))
            return os.path.commonpath([child_abs, parent_abs]) == parent_abs
        except ValueError:
            return False

    def is_safe_to_delete(self, file_path, category_id=None):
        # SR-02: Prevent deletion of critical system files
        file_path = os.path.abspath(file_path)

        protected_extensions = [".dll", ".sys", ".exe", ".msi"]
        protected_names = ["ntoskrnl.exe", "explorer.exe"]

        _, ext = os.path.splitext(file_path)
        if ext.lower() in protected_extensions:
            return False

        if os.path.basename(file_path).lower() in protected_names:
            return False

        # Only allow deletion if file belongs to FOIDS rule paths
        allowed_targets = []

        if category_id is not None:
            category = self.get_category_by_id(category_id)
            if category:
                allowed_targets.extend(self.get_category_targets(category))
        else:
            for category in self.rules.get("foid_categories", []):
                allowed_targets.extend(self.get_category_targets(category))

        for target in allowed_targets:
            if self.is_path_within(file_path, target):
                return True

        return False

    def age_check(self, file_path, category):
        #Apply max age filtering if specified
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
        # FR-02: Scan files for a single category
        self.log(f"Scanning: {category.get('name')}")
        matched_files = []
        seen_paths = set()

        targets = self.get_category_targets(category)
        patterns = category.get("patterns", ["*"])
        recursive = category.get("recursive", False)

        for target in targets:
            for pattern in patterns:
                try:
                    search_pattern = (
                        os.path.join(target, "**", pattern)
                        if recursive else os.path.join(target, pattern)
                    )

                    found_paths = glob.glob(search_pattern, recursive=recursive)

                    for found_path in found_paths:
                        if os.path.isfile(found_path) and self.age_check(found_path, category):
                            normalized = os.path.normcase(os.path.abspath(found_path))
                            if normalized in seen_paths:
                                continue

                            seen_paths.add(normalized)
                            matched_files.append({
                                "category_id": category.get("id"),
                                "category_name": category.get("name"),
                                "file_path": found_path,
                                "size": os.path.getsize(found_path)
                            })

                except Exception as e:
                    self.log(f"Error scanning target {target}: {e}")

        return matched_files

    def summarize_results(self):
        # FR-06: Summarize scan results by category
        summary = {}

        for item in self.scan_results:
            category_name = item["category_name"]

            if category_name not in summary:
                summary[category_name] = {"count": 0, "size": 0}

            summary[category_name]["count"] += 1
            summary[category_name]["size"] += item["size"]

        return summary

    def get_summary_rows(self):
        # Format summary data for GUI table display
        summary = self.summarize_results()
        rows = []

        for category, data in summary.items():
            rows.append({
                "category": category,
                "count": data["count"],
                "size_bytes": data["size"],
                "size_display": self.format_size(data["size"])
            })

        return rows

    def format_size(self, size):
        # Convert bytes to human-readable format
        for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

    def get_selected_category_ids(self):
        # IR-03: Return selected categories from GUI
        selected = []

        for category in self.rules.get("foid_categories", []):
            category_id = category.get("id")
            if self.category_states.get(category_id):
                selected.append(category_id)

        return selected

    def select_all_categories(self, value=True):
        # IR-03: Select/deselect all categories
        for category in self.rules.get("foid_categories", []):
            self.category_states[category.get("id")] = value

    def delete(self, dry_run=True, limit=None):
        # FR-05: Delete files (with safety checks and dry-run support)
        deleted_count = 0
        failed_count = 0
        skipped_count = 0
        protected_count = 0

        items_to_process = self.scan_results if limit is None else self.scan_results[:limit]

        for item in items_to_process:
            file_path = item["file_path"]
            category_id = item.get("category_id")

            try:
                if not self.is_safe_to_delete(file_path, category_id):
                    self.log(f"[SKIPPED - PROTECTED] {file_path}")
                    protected_count += 1
                    continue

                if dry_run:
                    self.log(f"[DRY RUN] Would delete: {file_path}")
                    skipped_count += 1
                else:
                    os.remove(file_path)
                    self.log(f"Deleted: {file_path}")
                    deleted_count += 1

            except Exception as e:
                self.log(f"Failed to delete {file_path}: {e}")
                failed_count += 1

        return {
            "deleted": deleted_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "protected": protected_count,
            "processed": len(items_to_process)
        }


if __name__ == "__main__":
    app = FOIDS()

    print("Starting scan...\n")
    results = app.scanner()
    summary_rows = app.get_summary_rows()

    print(f"Total files found: {len(results)}\n")

    for row in summary_rows:
        print(f"{row['category']}: {row['count']} files, {row['size_display']}")

    print("\n--- DRY RUN DELETE TEST ---\n")
    print(app.delete(dry_run=True, limit=20))
