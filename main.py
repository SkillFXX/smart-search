import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import queue
import concurrent.futures
import platform
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import subprocess
from tkinter import font as tkfont
import time
import webbrowser


class FileSearch:
    def __init__(self, master):
        self.master = master
        master.title("SmartSearch")
        master.geometry("900x700")
        master.configure(bg='#f0f0f0')
        
        # Police personnalisée
        self.custom_font = tkfont.Font(family="Segoe UI", size=10)
        self.title_font = tkfont.Font(family="Segoe UI", size=12, weight="bold")
        
        self.create_ui()
        self.search_queue = queue.Queue()
        self.results_queue = queue.Queue()
        
    

        self.system_dirs_to_exclude = [
            'Windows', 'Program Files', 'Program Files (x86)', 'ProgramData', 
            '$Recycle.Bin', 'System32', 'WinNT', 'Temp', 'AppData',
            
            'proc', 'sys', 'dev',
            
            'Library', 'private',
            
            '.git', '.cache', 'node_modules'
        ]
        
        self.system_extensions_to_exclude = [
            '.sys', '.dll', '.exe', '.msi', '.bat', '.cmd', 
            '.log', '.tmp', '.temp'
        ]

    def system_dirs(self):
        if self.ignore_system_dir.get():  # Si coché (1)
            self.system_dirs_to_exclude = [
                'Windows', 'Program Files', 'Program Files (x86)', 'ProgramData', 
                '$Recycle.Bin', 'System32', 'WinNT', 'Temp', 'AppData',
                
                'proc', 'sys', 'dev',
                
                'Library', 'private',
                
                '.git', '.cache', 'node_modules'
            ]
        else:  # Si décoché (0)
            self.system_dirs_to_exclude = []

    def is_system_path(self, path):
        path_lower = path.lower()
        
        for sys_dir in self.system_dirs_to_exclude:
            if sys_dir.lower() in path_lower:
                return True
        
        return False

    def open_github(self, event):
        webbrowser.open("https://github.com/SkillFXX")
        
    def open_help(self):
        webbrowser.open("https://github.com/SkillFXX/smart-search")

    def create_ui(self):
        self.master = self.master
        self.master.title("SmartSearch")
        self.master.geometry("700x500")
        
        ctk.set_appearance_mode("light")  # "dark" ou "light"
        ctk.set_default_color_theme("blue")

        # --- Barre de menu ---
        menu_bar = tk.Menu(self.master)
        
        # Menu "File"
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open a folder", command=self.choose_directory)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        # Menu "Options"
        self.ignore_system_dir = tk.IntVar(value=1)
        options_menu = tk.Menu(menu_bar, tearoff=0)
        options_menu.add_checkbutton(label="Ignore system folders", variable=self.ignore_system_dir, command=self.system_dirs)
        menu_bar.add_cascade(label="Settings", menu=options_menu)

        # Menu "Aide"
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.open_help)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        # Ajout de la barre de menu à la fenêtre principale
        self.master.config(menu=menu_bar)
        
        # --- Interface principale ---
        self.frame = ctk.CTkFrame(self.master, corner_radius=15)
        self.frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        self.title_label = ctk.CTkLabel(self.frame, text="SmartSearch", font=("Arial", 20, "bold"))
        self.title_label.pack(pady=10)

        # --- Directory Selection ---
        self.dir_frame = ctk.CTkFrame(self.frame, corner_radius=10)
        self.dir_frame.pack(fill="x", pady=10, padx=10)
        
        self.directory_entry = ctk.CTkEntry(self.dir_frame, placeholder_text="Choose a folder", width=400)
        self.directory_entry.pack(side="left", padx=10, pady=10, expand=True, fill="x")
        
        self.browse_btn = ctk.CTkButton(self.dir_frame, text="Browse", command=self.choose_directory)
        self.browse_btn.pack(side="right", padx=10)

        # --- Search and Extension Fields ---
        self.options_frame = ctk.CTkFrame(self.frame, corner_radius=10)
        self.options_frame.pack(fill="x", pady=10, padx=10)
        
        self.search_entry = ctk.CTkEntry(self.options_frame, placeholder_text="Search...", width=250)
        self.search_entry.pack(side="left", padx=10, pady=10, expand=True, fill="x")
        
        self.extension_entry = ctk.CTkEntry(self.options_frame, placeholder_text="Extension", width=100)
        self.extension_entry.pack(side="left", padx=10)
        
        self.search_button = ctk.CTkButton(self.options_frame, text="Search", command=self.launch_search)
        self.search_button.pack(side="right", padx=10)

        # --- Results Frame ---
        self.results_frame = ctk.CTkFrame(self.frame, corner_radius=10)
        self.results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.results_tree = ttk.Treeview(self.results_frame, columns=("File",), show="headings")
        self.results_tree.heading("File", text="Found files")
        self.results_tree.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Progress Bar (Barre de chargement) ---
        self.progress = ttk.Progressbar(self.frame, mode="indeterminate")
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.pack_forget()  # Cachée par défaut

        # --- Footer ---
        self.footer_label = ctk.CTkLabel(self.frame, text="Made by SkillFX", cursor="hand2")
        self.footer_label.pack(pady=10)
        self.footer_label.bind("<Button-1>", self.open_github)

        self.search_entry.bind("<Return>", lambda event: self.launch_search())


    def show_context_menu(self, event):
        item = self.results_tree.identify_row(event.y)
        if item:
            self.results_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)


    def launch_search(self):
        for i in self.results_tree.get_children():
            self.results_tree.delete(i)

        directory = self.directory_entry.get()
        search_term = self.search_entry.get().lower()
        extension = self.extension_entry.get().lower()

        if not directory:
            directory = "C:/"
            # messagebox.showwarning("Warning", "Please select a directory")
            # return

        if not os.path.isdir(directory):
            messagebox.showerror("Error", "The specified directory is invalid")
            return

        self.search_in_progress = True  # Indique que la recherche commence
        self.progress.pack()  # Affiche la barre de chargement
        self.progress.start()

        threading.Thread(target=lambda: self.perform_fast_search(directory, search_term, extension), daemon=True).start()
        self.check_search_results()




    def should_exclude_file(self, filename):
            for ext in self.system_extensions_to_exclude:
                if filename.lower().endswith(ext):
                    return True
            
            return False

    def perform_fast_search(self, directory, search_term, extension):
        start_time = time.time()
        results = []

        try:
            for root, dirs, files in os.walk(directory):
                dirs[:] = [d for d in dirs if not self.is_system_path(os.path.join(root, d))]
                
                for file in files:
                    if self.should_exclude_file(file):
                        continue
                    
                    name_match = search_term in file.lower()
                    ext_match = not extension or file.lower().endswith(extension)
                    
                    if name_match and ext_match:
                        full_path = os.path.join(root, file)
                        results.append(full_path)

                        if len(results) >= 500:
                            break
                
                if len(results) >= 500:
                    break
        except PermissionError:
            messagebox.showerror("Error", "Unauthorized access to certain files/directories")
        except Exception as e:
            messagebox.showerror("Error", f"An error has occurred : {e}")

        print(f"Search performed in {time.time() - start_time:.4f} seconds")

        for result in results:
            self.results_queue.put(result)

        self.search_in_progress = False  # Signale que la recherche est terminée


    def check_search_results(self):
        try:
            while True:
                result = self.results_queue.get_nowait()
                self.results_tree.insert('', 'end', values=(os.path.basename(result),), tags=(result,))
        except queue.Empty:
            if self.search_in_progress:  # Continue tant que la recherche est en cours
                self.master.after(100, self.check_search_results)
            else:  # Recherche terminée, on cache la barre de chargement
                self.progress.stop()
                self.progress.pack_forget()

        


    def choose_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.directory_entry.delete(0, tk.END)
            self.directory_entry.insert(0, directory)

    def open_directory(self):
        selected_item = self.results_tree.selection()
        if selected_item:
            full_path = self.results_tree.item(selected_item[0], 'tags')[0]
            directory = os.path.dirname(full_path)
            
            self._open_path(directory)

    def _open_path(self, path):
        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(path)
            elif system == "Darwin":  # macOS
                subprocess.Popen(["open", path])
            else:  # linux variants
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", f"Impossible to open the path: {e}")

    def _select_file_in_explorer(self, file_path):
        system = platform.system()
        try:
            if system == "Windows":
                subprocess.run(['explorer', '/select,', file_path])
            elif system == "Darwin":  # macOS
                subprocess.run(['open', '-R', file_path])
            else:  # Linux (avec xdg-open)
                subprocess.run(['xdg-open', os.path.dirname(file_path)])
        except Exception as e:
            print(f"Error of file selection: {e}")

    def open_file(self):
        selected_item = self.results_tree.selection()
        if selected_item:
            full_path = self.results_tree.item(selected_item[0], 'tags')[0]
            self._open_path(full_path)

def main():
    root = tk.Tk()
    app = FileSearch(root)
    root.mainloop()

if __name__ == "__main__":
    main()
