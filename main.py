import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import queue
import concurrent.futures
import platform
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

    def is_system_path(self, path):
        path_lower = path.lower()
        
        for sys_dir in self.system_dirs_to_exclude:
            if sys_dir.lower() in path_lower:
                return True
        
        return False

    def open_github(self, event):
        webbrowser.open("https://github.com/SkillFXX")

    def create_ui(self):
        main_frame = tk.Frame(self.master, bg='#f0f0f0', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = tk.Label(main_frame, text="SmartSearch", 
                                font=self.title_font, 
                                bg='#f0f0f0', 
                                fg='#333333')
        title_label.pack(pady=(0,20))

        search_frame = tk.Frame(main_frame, bg='#f0f0f0')
        search_frame.pack(fill=tk.X, pady=10)

        dir_label = tk.Label(search_frame, text="Directory:", 
                              font=self.custom_font, 
                              bg='#f0f0f0')
        dir_label.pack(side=tk.LEFT, padx=(0,10))

        self.directory_entry = tk.Entry(search_frame, 
                                        font=self.custom_font, 
                                        width=50, 
                                        relief=tk.FLAT,
                                        bg='white', 
                                        highlightthickness=1, 
                                        highlightcolor='#4A90E2', 
                                        highlightbackground='#cccccc')
        self.directory_entry.pack(side=tk.LEFT, padx=(0,10), fill=tk.X, expand=True)

        browse_btn = tk.Button(search_frame, text="Browse", 
                                command=self.choose_directory,
                                font=self.custom_font,
                                bg='#4A90E2', 
                                fg='white', 
                                relief=tk.FLAT,
                                activebackground='#357ABD')
        browse_btn.pack(side=tk.LEFT, padx=(0,10))

        options_frame = tk.Frame(main_frame, bg='#f0f0f0')
        options_frame.pack(fill=tk.X, pady=10)

        search_label = tk.Label(options_frame, text="Search:", 
                                 font=self.custom_font, 
                                 bg='#f0f0f0')
        search_label.pack(side=tk.LEFT, padx=(0,10))

        self.search_entry = tk.Entry(options_frame, 
                                     font=self.custom_font, 
                                     width=30, 
                                     relief=tk.FLAT,
                                     bg='white', 
                                     highlightthickness=1, 
                                     highlightcolor='#4A90E2', 
                                     highlightbackground='#cccccc')
        self.search_entry.pack(side=tk.LEFT, padx=(0,10), fill=tk.X, expand=True)

        ext_label = tk.Label(options_frame, text="Extension:", 
                              font=self.custom_font, 
                              bg='#f0f0f0')
        ext_label.pack(side=tk.LEFT, padx=(10,10))

        self.extension_entry = tk.Entry(options_frame, 
                                        font=self.custom_font, 
                                        width=10, 
                                        relief=tk.FLAT,
                                        bg='white', 
                                        highlightthickness=1, 
                                        highlightcolor='#4A90E2', 
                                        highlightbackground='#cccccc')
        self.extension_entry.pack(side=tk.LEFT, padx=(0,10))

        search_button = tk.Button(options_frame, text="Start search", 
                                  command=self.launch_search,
                                  font=self.custom_font,
                                  bg='#2ECC71', 
                                  fg='white', 
                                  relief=tk.FLAT,
                                  activebackground='#27AE60')
        search_button.pack(side=tk.LEFT, padx=(10,0))

        results_frame = tk.Frame(main_frame, bg='#f0f0f0')
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.results_tree = ttk.Treeview(results_frame, 
                                         columns=('File',), 
                                         show='headings', 
                                         style='Custom.Treeview')
        self.results_tree.heading('File', text='Found files')
        self.results_tree.column('File', width=500)
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.configure(yscroll=scrollbar.set)

        style = ttk.Style()
        style.configure('Custom.Treeview', rowheight=25, font=self.custom_font)
        style.map('Custom.Treeview', 
                  background=[('selected', '#4A90E2')], 
                  foreground=[('selected', 'white')])

        self.context_menu = tk.Menu(self.master, tearoff=0, font=self.custom_font)
        self.context_menu.add_command(label="Open file", command=self.open_file)
        self.context_menu.add_command(label="Open directory", command=self.open_directory)
        
        self.results_tree.bind('<Button-3>', self.show_context_menu)

        footer_label = tk.Label(main_frame, text="Made by SkillFX", 
                            font=self.custom_font, 
                            bg='#f0f0f0', 
                            fg='#333333', 
                            cursor="hand2")  # Change le curseur pour montrer qu'il est cliquable
        footer_label.pack(side=tk.BOTTOM, anchor='w', padx=10, pady=10)

        # Ajout de l'événement pour ouvrir GitHub au clic
        footer_label.bind("<Button-1>", self.open_github)
        pass 

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
            messagebox.showwarning("Warning", "Please select a directory")
            return

        if not os.path.isdir(directory):
            messagebox.showerror("Error", "LThe specified directory is invalid")
            return

        if search_term:
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

        is_windows = platform.system() == "Windows"

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

    def check_search_results(self):
        try:
            while True:
                result = self.results_queue.get_nowait()
                self.results_tree.insert('', 'end', values=(os.path.basename(result),), tags=(result,))
        except queue.Empty:
            self.master.after(100, self.check_search_results)

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
