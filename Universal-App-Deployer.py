import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import platform
import webbrowser
import shutil
import urllib.request
import time
import json
import sys
import socket
import hashlib
import platform

# macOS PATH Fix: GUI apps don't inherit shell PATH. 
# We must manually inject common binary locations.
if platform.system() == "Darwin":
    common_paths = ["/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin", "/usr/sbin", "/sbin"]
    current_path = os.environ.get("PATH", "")
    new_paths = [p for p in common_paths if p not in current_path]
    if new_paths:
        os.environ["PATH"] = ":".join(new_paths) + ":" + current_path

__version__ = "1.0.2"
GITHUB_REPO = "shaibal-tiller/Universal-Node-Deployer-Engine"

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def ensure_dependencies():
    if getattr(sys, 'frozen', False):
        return # Cannot auto-install in a bundled app
    try:
        import psutil
        import tkhtmlview
        import markdown2
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil", "tkhtmlview", "markdown2"])
        except:
            pass

ensure_dependencies()
import psutil
from tkhtmlview import HTMLScrolledText
import markdown2

class UpdateManager:
    def __init__(self, current_version, repo):
        self.current_version = current_version
        self.repo = repo
        self.api_url = f"https://api.github.com/repos/{repo}/releases/latest"
        self.update_available = False
        self.latest_version = ""
        self.download_url = ""

    def check_for_updates(self):
        try:
            req = urllib.request.Request(self.api_url)
            req.add_header('User-Agent', 'Universal-App-Deployer-Updater')
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                self.latest_version = data.get("tag_name", "").replace("v", "")
                if self.latest_version and self._is_newer(self.latest_version, self.current_version):
                    self.update_available = True
                    # Find asset for current platform
                    assets = data.get("assets", [])
                    ext = ".exe" if platform.system() == "Windows" else ".dmg"
                    for asset in assets:
                        if asset["name"].endswith(ext):
                            self.download_url = asset["browser_download_url"]
                            break
                    return True
        except Exception:
            pass
        return False

    def _is_newer(self, latest, current):
        try:
            l_parts = [int(p) for p in latest.split(".")]
            c_parts = [int(p) for p in current.split(".")]
            return l_parts > c_parts
        except:
            return latest != current

class UniversalAppDeployer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Universal App Deployer - Professional Edition")
        self.geometry("1100x800")
        self.configure(bg="#1e1e2e")
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        
        # Set App Icon
        try:
            icon_path = resource_path("assets/icon.png")
            if os.path.exists(icon_path):
                self.app_icon = tk.PhotoImage(file=icon_path)
                self.iconphoto(False, self.app_icon)
        except Exception:
            pass
        
        self.recents_file = os.path.expanduser("~/.universal_deployer_recents.json")
        self.recent_projects = self.load_recents()
        
        self.project_dir = tk.StringVar(value=os.getcwd())
        if self.project_dir.get() not in self.recent_projects:
            self.recent_projects.insert(0, self.project_dir.get())
            self.save_recents()
            
        self.local_proc = None
        self.tunnel_proc = None
        self.tunnel_url = ""
        self.current_step = 1
        self.active_port = 5555
        
        self.npm_cmd = shutil.which("npm") or ("npm.cmd" if platform.system() == "Windows" else "npm")
        self.npx_cmd = shutil.which("npx") or ("npx.cmd" if platform.system() == "Windows" else "npx")
        
        self._setup_styles()
        self._create_layout()
        
        self.log("System initialized. Welcome to Universal App Deployer.")
        self.update_network_status()
        self.update_system_stats()
        self.run_step(1)
        
        # Async Update Check
        threading.Thread(target=self.check_updates_async, daemon=True).start()

    def check_updates_async(self):
        updater = UpdateManager(__version__, GITHUB_REPO)
        if updater.check_for_updates():
            self.after(0, lambda: self.show_update_dialog(updater))

    def show_update_dialog(self, updater):
        if messagebox.askyesno("Update Available", 
                               f"A new version ({updater.latest_version}) is available!\n"
                               f"Current version: {__version__}\n\n"
                               "Would you like to install it now? The app will restart automatically."):
            self.perform_hot_update(updater)

    def perform_hot_update(self, updater):
        if not updater.download_url:
            webbrowser.open(f"https://github.com/{GITHUB_REPO}/releases/latest")
            return
            
        import tempfile
        
        # Show progress
        top = tk.Toplevel(self)
        top.title("Updating...")
        top.geometry("300x150")
        top.configure(bg="#1e1e2e")
        ttk.Label(top, text="Downloading update...", foreground="#89b4fa", font=("Segoe UI", 11)).pack(pady=20)
        progress = ttk.Progressbar(top, mode="indeterminate")
        progress.pack(fill=tk.X, padx=20)
        progress.start()
        
        def download_and_swap():
            try:
                temp_dir = tempfile.gettempdir()
                ext = ".exe" if platform.system() == "Windows" else ".dmg"
                download_path = os.path.join(temp_dir, f"UniversalAppDeployer_Update{ext}")
                
                urllib.request.urlretrieve(updater.download_url, download_path)
                
                # Executable location
                exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
                
                if platform.system() == "Windows":
                    # Create a batch script to wait for exit, swap, and restart
                    bat_path = os.path.join(temp_dir, "updater.bat")
                    with open(bat_path, "w") as f:
                        f.write(f'''@echo off
timeout /t 2 /nobreak > NUL
move /Y "{download_path}" "{exe_path}"
start "" "{exe_path}"
del "%~f0"
''')
                    subprocess.Popen(bat_path, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
                    self.after(0, self.destroy) # Close current app
                elif platform.system() == "Darwin":
                    # Mount DMG and close app
                    subprocess.Popen(["open", download_path])
                    self.after(0, self.destroy)
                else:
                    webbrowser.open(f"https://github.com/{GITHUB_REPO}/releases/latest")
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Update Failed", f"Could not perform update: {e}"))
                self.after(0, top.destroy)
                
        threading.Thread(target=download_and_swap, daemon=True).start()

    def _setup_styles(self):
        # Modern App Font Stack
        app_font = ("Segoe UI", 10)
        header_font = ("Segoe UI", 16, "bold")
        step_font = ("Segoe UI", 11)
        step_active_font = ("Segoe UI", 11, "bold")
        btn_font = ("Segoe UI", 10, "bold")
        mono_font = ("Consolas", 11)

        self.style.configure(".", background="#1e1e2e", foreground="#cdd6f4", font=app_font)
        self.style.configure("TFrame", background="#1e1e2e")
        self.style.configure("Sidebar.TFrame", background="#11111b")
        self.style.configure("Header.TLabel", font=header_font, background="#1e1e2e", foreground="#b4befe")
        self.style.configure("StepStatus.TLabel", font=step_font, background="#11111b", foreground="#6c7086")
        self.style.configure("StepActive.TLabel", font=step_active_font, background="#11111b", foreground="#89b4fa")
        
        # Modern Button Styling
        self.style.configure("Action.TButton", font=btn_font, padding=10, background="#89b4fa", foreground="#11111b", borderwidth=0)
        self.style.map("Action.TButton", background=[("active", "#b4befe")])
        
        self.style.configure("Custom.Vertical.TScrollbar", background="#313244", troughcolor="#1e1e2e", bordercolor="#1e1e2e", arrowcolor="#cdd6f4")
        self.style.map("Custom.Vertical.TScrollbar", background=[('active', '#45475a')])
        
        self.style.configure("TCombobox", fieldbackground="#313244", background="#1e1e2e", foreground="#a6e3a1", font=app_font)
        self.style.map("TCombobox", fieldbackground=[("readonly", "#313244")])
        
        # LabelFrame modern look
        self.style.configure("TLabelframe", background="#1e1e2e", borderwidth=1, bordercolor="#313244")
        self.style.configure("TLabelframe.Label", background="#1e1e2e", foreground="#89dceb", font=("Segoe UI", 10, "bold"))

    def _create_layout(self):
        # Header
        header = ttk.Frame(self, padding=(20, 10))
        header.pack(fill=tk.X)
        
        title_frame = ttk.Frame(header)
        title_frame.pack(side=tk.LEFT)
        ttk.Label(title_frame, text="◆ Universal App Deployer - Builder Engine", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(title_frame, text=f"v{__version__} | Author: Sharif Shaibal | shaibalsharif@gmail.com", foreground="#a6adc8", font=("Helvetica", 9)).pack(anchor=tk.W, pady=(2, 0))
        
        self.lbl_network = ttk.Label(header, text="Net: Checking...", foreground="#89b4fa", font=("Helvetica", 10, "bold"))
        self.lbl_network.pack(side=tk.RIGHT, padx=5)

        # System Metrics Dashboard (Prominent)
        metrics_frame = ttk.LabelFrame(self, text=" System Real-Time Metrics ", padding=10)
        metrics_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.lbl_cpu = ttk.Label(metrics_frame, text="CPU Usage: --%", foreground="#a6e3a1", font=("Helvetica", 11, "bold"), width=20)
        self.lbl_cpu.pack(side=tk.LEFT, padx=10)
        
        self.lbl_ram = ttk.Label(metrics_frame, text="RAM Usage: --%", foreground="#f9e2af", font=("Helvetica", 11, "bold"), width=20)
        self.lbl_ram.pack(side=tk.LEFT, padx=10)
        
        self.lbl_disk = ttk.Label(metrics_frame, text="Disk Usage: --%", foreground="#fab387", font=("Helvetica", 11, "bold"), width=20)
        self.lbl_disk.pack(side=tk.LEFT, padx=10)

        # Project Selector
        proj_frame = ttk.Frame(self, padding=(20, 0, 20, 10))
        proj_frame.pack(fill=tk.X)
        ttk.Label(proj_frame, text="Project: ", foreground="#bac2de").pack(side=tk.LEFT)
        
        self.cb_projects = ttk.Combobox(proj_frame, values=self.recent_projects, textvariable=self.project_dir, state="readonly", width=60)
        self.cb_projects.pack(side=tk.LEFT, padx=10)
        self.cb_projects.bind("<<ComboboxSelected>>", self.on_project_changed)
        
        ttk.Button(proj_frame, text="Browse Folder...", command=self.browse_project).pack(side=tk.LEFT)

        # Main Body
        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Sidebar (Steps)
        sidebar = ttk.Frame(body, style="Sidebar.TFrame", width=250)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        sidebar.pack_propagate(False)

        ttk.Label(sidebar, text="Deployment Process", font=("Helvetica", 12, "bold"), background="#181825", foreground="#cdd6f4").pack(pady=(20, 15), padx=15, anchor=tk.W)
        
        self.step_labels = {}
        steps = [
            (1, "1. Project Overview"),
            (2, "2. System Check"),
            (3, "3. Dependencies"),
            (4, "4. Build Application"),
            (5, "5. Local Server"),
            (6, "6. Global Tunnel")
        ]
        
        for num, text in steps:
            lbl = ttk.Label(sidebar, text=text, style="StepStatus.TLabel")
            lbl.pack(anchor=tk.W, padx=20, pady=8)
            self.step_labels[num] = lbl

        # Action Area
        right_panel = ttk.Frame(body)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.action_frame = ttk.LabelFrame(right_panel, text=" Current Action ", padding=20)
        self.action_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.progress = ttk.Progressbar(self.action_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        self.action_content = ttk.Frame(self.action_frame)
        self.action_content.pack(fill=tk.BOTH, expand=True)

        # Terminal Area
        term_frame = ttk.Frame(right_panel)
        term_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(term_frame, text="Terminal Output:", font=("Segoe UI", 10, "bold"), foreground="#89dceb").pack(anchor=tk.W, pady=(0,5))
        
        # Custom Scrollbar and ScrolledText alternative
        self.term = tk.Text(term_frame, bg="#11111b", fg="#a6e3a1", font=("Consolas", 11), borderwidth=1, relief="flat", highlightthickness=1, highlightbackground="#313244", highlightcolor="#89b4fa", wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(term_frame, orient=tk.VERTICAL, command=self.term.yview, style="Custom.Vertical.TScrollbar")
        self.term.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.term.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def load_recents(self):
        try:
            if os.path.exists(self.recents_file):
                with open(self.recents_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def save_recents(self):
        try:
            with open(self.recents_file, 'w') as f:
                json.dump(self.recent_projects, f)
        except Exception:
            pass

    def add_recent(self, path):
        if path in self.recent_projects:
            self.recent_projects.remove(path)
        self.recent_projects.insert(0, path)
        self.recent_projects = self.recent_projects[:10]
        self.save_recents()
        if hasattr(self, 'cb_projects'):
            self.cb_projects['values'] = self.recent_projects
            self.cb_projects.current(0)
    
    def on_project_changed(self, event=None):
        new_path = self.project_dir.get()
        if os.path.isdir(new_path):
            self.add_recent(new_path)
            self.log(f"Switched project to: {new_path}")
            self.do_stop_local()
            self.do_stop_tunnel()
            self.term.delete(1.0, tk.END)
            self.run_step(1)
        else:
            messagebox.showerror("Error", "Selected project directory does not exist.")

    def browse_project(self):
        directory = filedialog.askdirectory(initialdir=self.project_dir.get(), title="Select Project Folder")
        if directory:
            self.project_dir.set(directory)
            self.on_project_changed()

    def start_loading(self):
        self.progress.start(15)
        
    def stop_loading(self):
        self.progress.stop()

    def log(self, text, color=None):
        timestamp = datetime.now().strftime("[%H:%M:%S] ")
        self.term.insert(tk.END, timestamp + text + "\n")
        self.term.see(tk.END)
        self.update_idletasks()

    def update_network_status(self):
        def check():
            try:
                start = time.time()
                urllib.request.urlopen('https://8.8.8.8', timeout=2)
                ms = int((time.time() - start) * 1000)
                self.lbl_network.config(text=f"Net: {ms}ms", foreground="#a6e3a1")
            except:
                self.lbl_network.config(text="Net: Offline", foreground="#f38ba8")
            self.after(10000, self.update_network_status)
        threading.Thread(target=check, daemon=True).start()

    def update_system_stats(self):
        def check():
            try:
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent
                disk = psutil.disk_usage('/').percent
                
                self.lbl_cpu.config(text=f"CPU: {cpu:.1f}%")
                self.lbl_ram.config(text=f"RAM: {ram:.1f}%")
                self.lbl_disk.config(text=f"Disk: {disk:.1f}%")
            except Exception as e:
                pass
            self.after(2000, self.update_system_stats)
        threading.Thread(target=check, daemon=True).start()

    def set_active_step(self, step_num):
        self.current_step = step_num
        for num, lbl in self.step_labels.items():
            current_text = lbl.cget("text").replace("➜ ", "").replace("✓ ", "")
            if num < step_num:
                lbl.config(style="StepStatus.TLabel", foreground="#a6e3a1", text="✓ " + current_text)
            elif num == step_num:
                lbl.config(style="StepActive.TLabel", foreground="#89b4fa", text="➜ " + current_text)
            else:
                lbl.config(style="StepStatus.TLabel", foreground="#6c7086", text=current_text)

    def clear_action_frame(self):
        for widget in self.action_content.winfo_children():
            widget.destroy()

    def run_step(self, step_num):
        self.set_active_step(step_num)
        self.clear_action_frame()
        
        if step_num == 1:
            self.step_project_overview()
        elif step_num == 2:
            self.step_system_check()
        elif step_num == 3:
            self.step_dependencies()
        elif step_num == 4:
            self.step_build()
        elif step_num == 5:
            self.step_local_server()
        elif step_num == 6:
            self.step_global_tunnel()

    # --- STEPS IMPLEMENTATION ---

    def step_project_overview(self):
        ttk.Label(self.action_content, text="Project Information", font=("Segoe UI", 14, "bold"), foreground="#89b4fa").pack(anchor=tk.W, pady=5)
        
        self.project_type = "Unknown"
        pkg_path = os.path.join(self.project_dir.get(), "package.json")
        req_path = os.path.join(self.project_dir.get(), "requirements.txt")
        doc_path = os.path.join(self.project_dir.get(), "Dockerfile")
        
        desc_text = "No recognized project file found (package.json, requirements.txt, Dockerfile)."
        total_deps = 0
        name = "Unknown Project"
        version = "0.0.0"

        if os.path.exists(pkg_path):
            self.project_type = "Node.js"
            try:
                with open(pkg_path, "r", encoding="utf-8") as f:
                    pkg = json.load(f)
                name = pkg.get("name", "Unnamed Node App")
                version = pkg.get("version", "0.0.0")
                desc_text = pkg.get("description", "Node.js Frontend/Backend Project")
                deps = pkg.get("dependencies", {})
                dev_deps = pkg.get("devDependencies", {})
                total_deps = len(deps) + len(dev_deps)
            except Exception as e:
                desc_text = f"Error reading package.json: {e}"
        elif os.path.exists(req_path):
            self.project_type = "Python"
            name = "Python Application"
            desc_text = "Python Backend Project"
            try:
                with open(req_path, "r", encoding="utf-8") as f:
                    total_deps = len([line for line in f if line.strip() and not line.startswith("#")])
            except:
                pass
        elif os.path.exists(doc_path):
            self.project_type = "Docker"
            name = "Dockerized Application"
            desc_text = "Containerized Project"

        info_frame = ttk.Frame(self.action_content)
        info_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(info_frame, text=f"📦 Name: {name} (v{version})", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text=f"⚙️ Type: {self.project_type}", foreground="#a6e3a1", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text=f"📝 Desc: {desc_text}", foreground="#bac2de").pack(anchor=tk.W, pady=2)
        if self.project_type in ["Node.js", "Python"]:
            ttk.Label(info_frame, text=f"🧩 Dependencies: {total_deps} packages found", foreground="#a6adc8").pack(anchor=tk.W, pady=2)

        # Readme Preview
        md_files = [f for f in os.listdir(self.project_dir.get()) if f.lower().endswith(".md")]
        
        def show_readme():
            if not md_files: return
            md_path = os.path.join(self.project_dir.get(), md_files[0])
            try:
                with open(md_path, 'r', encoding="utf-8") as f:
                    content = f.read()
                    
                # Convert Markdown to HTML
                html_content = markdown2.markdown(content, extras=["fenced-code-blocks", "tables", "header-ids"])
                
                # Inject Dark Mode CSS ensuring high contrast
                dark_css = """
                <style>
                    body {
                        background-color: #11111b;
                        color: #cdd6f4;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        font-size: 14px;
                        line-height: 1.6;
                        padding: 15px;
                    }
                    h1, h2, h3, h4 { color: #89b4fa; }
                    h2 { color: #f9e2af; border-bottom: 1px solid #313244; padding-bottom: 5px; }
                    a { color: #89dceb; text-decoration: none; }
                    code { background-color: #313244; color: #fab387; padding: 2px 4px; border-radius: 3px; font-family: 'Consolas', monospace; }
                    pre { background-color: #181825; padding: 10px; border-radius: 5px; overflow-x: auto; }
                    pre code { background-color: transparent; color: #a6e3a1; }
                    blockquote { border-left: 4px solid #89b4fa; padding-left: 10px; color: #a6adc8; font-style: italic; }
                    ul, ol { padding-left: 20px; }
                    table { border-collapse: collapse; width: 100%; margin-bottom: 15px; }
                    th, td { border: 1px solid #313244; padding: 8px; text-align: left; }
                    th { background-color: #181825; }
                </style>
                """
                full_html = f"<html><head>{dark_css}</head><body>{html_content}</body></html>"

                top = tk.Toplevel(self)
                top.title(f"Viewing: {md_files[0]}")
                top.geometry("850x650")
                top.configure(bg="#1e1e2e")
                
                html_view = HTMLScrolledText(top, html=full_html, background="#11111b")
                html_view.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to parse markdown file: {e}")

        btn_frame = ttk.Frame(self.action_content)
        btn_frame.pack(fill=tk.X, pady=15)
        
        if md_files:
            btn_readme = ttk.Button(btn_frame, text=f"📄 View {md_files[0]}", command=show_readme)
            btn_readme.pack(side=tk.LEFT, padx=(0, 10))

        btn = ttk.Button(btn_frame, text="Proceed to System Check ➜", style="Action.TButton", command=lambda: self.run_step(2))
        btn.pack(side=tk.LEFT)
        self.log(f"Project '{name}' selected. {total_deps} packages found.")

    def step_system_check(self):
        ttk.Label(self.action_content, text="Checking system requirements...", font=("Segoe UI", 12)).pack(anchor=tk.W, pady=5)
        self.log(f"Validating system requirements for {self.project_type}...", color="#89b4fa")
        
        status_frame = ttk.Frame(self.action_content)
        status_frame.pack(fill=tk.X, pady=10)
        
        passed = False
        missing_tool = ""
        dl_link = ""
        
        if self.project_type == "Node.js":
            if shutil.which("node") and shutil.which("npm"): passed = True
            else: missing_tool, dl_link = "Node.js / NPM", "https://nodejs.org/"
        elif self.project_type == "Python":
            if shutil.which("python") or shutil.which("python3"): passed = True
            else: missing_tool, dl_link = "Python", "https://python.org/"
        elif self.project_type == "Docker":
            if shutil.which("docker"): passed = True
            else: missing_tool, dl_link = "Docker", "https://docker.com/"
        else:
            ttk.Label(status_frame, text="⚠️ Unknown project type. Cannot verify requirements.", foreground="#f9e2af", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
            btn = ttk.Button(self.action_content, text="Force Continue", style="Action.TButton", command=lambda: self.run_step(3))
            btn.pack(anchor=tk.W, pady=10)
            return
            
        if passed:
            ttk.Label(status_frame, text=f"✅ System check passed for {self.project_type}.", foreground="#a6e3a1", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
            btn = ttk.Button(self.action_content, text="Continue to Dependencies", style="Action.TButton", command=lambda: self.run_step(3))
            btn.pack(anchor=tk.W, pady=10)
            self.log("System check passed.")
        else:
            ttk.Label(status_frame, text=f"❌ {missing_tool} is missing.", foreground="#f38ba8", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
            ttk.Label(self.action_content, text=f"This tool requires {missing_tool} to run. Please install it.").pack(anchor=tk.W)
            
            btn_install = ttk.Button(self.action_content, text=f"Download {missing_tool}", style="Action.TButton", command=lambda: webbrowser.open(dl_link))
            btn_install.pack(side=tk.LEFT, pady=15, padx=(0, 10))
            
            btn_refresh = ttk.Button(self.action_content, text="Re-check System", command=lambda: self.run_step(2))
            btn_refresh.pack(side=tk.LEFT, pady=15)
            self.log(f"System check failed: {missing_tool} missing.")

    def step_dependencies(self):
        ttk.Label(self.action_content, text="Checking Project Dependencies...", font=("Segoe UI", 12)).pack(anchor=tk.W, pady=5)
        
        has_deps = False
        if self.project_type == "Node.js":
            has_deps = os.path.exists(os.path.join(self.project_dir.get(), "node_modules"))
        elif self.project_type == "Python":
            # For simplicity, we'll force install/update Python deps in a venv or global
            has_deps = False # Always prompt for Python to ensure env is ready
        elif self.project_type == "Docker":
            has_deps = True # Docker handles its own dependencies
            
        status_frame = ttk.Frame(self.action_content)
        status_frame.pack(fill=tk.X, pady=10)
        
        if has_deps or self.project_type == "Docker":
            ttk.Label(status_frame, text=f"✅ Dependencies ready for {self.project_type}.", foreground="#a6e3a1", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
            btn_cont = ttk.Button(self.action_content, text="Continue to Build", style="Action.TButton", command=lambda: self.run_step(4))
            btn_cont.pack(side=tk.LEFT, pady=10, padx=(0, 10))
            if self.project_type != "Docker":
                btn_reinstall = ttk.Button(self.action_content, text="Force Re-install", command=self.do_install_deps)
                btn_reinstall.pack(side=tk.LEFT, pady=10)
            self.log("Dependencies check passed.")
        else:
            ttk.Label(status_frame, text="⚠️ Dependencies require installation.", foreground="#f9e2af", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
            btn_install = ttk.Button(self.action_content, text="Install Dependencies", style="Action.TButton", command=self.do_install_deps)
            btn_install.pack(side=tk.LEFT, pady=10)
            self.log("Dependencies missing. Awaiting user action.")

    def do_install_deps(self):
        self.clear_action_frame()
        self.start_loading()
        ttk.Label(self.action_content, text=f"⏳ Installing dependencies for {self.project_type}... Please wait.", foreground="#89b4fa", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=10)
        
        def task():
            try:
                cmd = []
                if self.project_type == "Node.js":
                    self.log("Running nested package installation (npm install)...")
                    cmd = [self.npm_cmd, "install"]
                elif self.project_type == "Python":
                    python_cmd = shutil.which("python3") or shutil.which("python")
                    self.log("Running pip install -r requirements.txt...")
                    cmd = [python_cmd, "-m", "pip", "install", "-r", "requirements.txt"]
                
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=self.project_dir.get())
                for line in iter(proc.stdout.readline, ''):
                    if line.strip():
                        self.term.insert(tk.END, "> "+ line)
                        self.term.see(tk.END)
                proc.wait()
                if proc.returncode == 0:
                    self.log("Dependencies installed successfully.")
                else:
                    self.log("Warning: Installation reported issues, but we can try to proceed.")
            except Exception as e:
                self.log(f"Error during dependency installation: {str(e)}")
            self.after(0, self.stop_loading)
            self.after(0, lambda: self.run_step(4))
            
        threading.Thread(target=task, daemon=True).start()

    def step_build(self):
        ttk.Label(self.action_content, text="Checking Application Build...", font=("Segoe UI", 12)).pack(anchor=tk.W, pady=5)
        
        has_dist = False
        needs_build = False
        
        if self.project_type == "Node.js":
            has_dist = any(os.path.exists(os.path.join(self.project_dir.get(), d)) for d in ["dist", ".next", "build"])
            needs_build = True
        elif self.project_type == "Python":
            has_dist = True # Usually scripts don't compile
            needs_build = False
        elif self.project_type == "Docker":
            # Assuming docker needs build every time for simplicity, or we can force it
            needs_build = True
            has_dist = False 
        
        status_frame = ttk.Frame(self.action_content)
        status_frame.pack(fill=tk.X, pady=10)
        
        if has_dist or not needs_build:
            ttk.Label(status_frame, text=f"✅ Build ready or not required for {self.project_type}.", foreground="#a6e3a1", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
            btn_cont = ttk.Button(self.action_content, text="Continue to Local Server", style="Action.TButton", command=lambda: self.run_step(5))
            btn_cont.pack(side=tk.LEFT, pady=10, padx=(0, 10))
            if needs_build:
                btn_rebuild = ttk.Button(self.action_content, text="Force Re-build", command=self.do_build_app)
                btn_rebuild.pack(side=tk.LEFT, pady=10)
            self.log("Build checks passed. Ready to serve.")
        else:
            ttk.Label(status_frame, text="⚠️ Application build required.", foreground="#f9e2af", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
            btn_build = ttk.Button(self.action_content, text="Build Application", style="Action.TButton", command=self.do_build_app)
            btn_build.pack(side=tk.LEFT, pady=10)
            self.log("Build required. Awaiting user action.")

    def do_build_app(self):
        self.clear_action_frame()
        self.start_loading()
        ttk.Label(self.action_content, text=f"⏳ Building {self.project_type} application...", foreground="#89b4fa", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=10)
        
        def task():
            try:
                cmd = []
                if self.project_type == "Node.js":
                    self.log("Running application build (npm run build)...")
                    cmd = [self.npm_cmd, "run", "build"]
                elif self.project_type == "Docker":
                    self.log("Running Docker build (docker build -t app_image .)...")
                    cmd = [shutil.which("docker"), "build", "-t", "app_image", "."]
                    
                if cmd:
                    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=self.project_dir.get())
                    for line in iter(proc.stdout.readline, ''):
                        if line.strip():
                            self.term.insert(tk.END, "> "+ line)
                            self.term.see(tk.END)
                    proc.wait()
                    if proc.returncode == 0:
                        self.log("Application built successfully.")
                        self.after(0, lambda: self.run_step(5))
                    else:
                        self.log("Application build failed! Please check logs.")
                        self.after(0, lambda: self.run_step(4))
                else:
                    self.log("No build command required for this project.")
                    self.after(0, lambda: self.run_step(5))
            except Exception as e:
                self.log(f"Error during build: {str(e)}")
                self.after(0, lambda: self.run_step(4))
            finally:
                self.after(0, self.stop_loading)
            
        threading.Thread(target=task, daemon=True).start()

    def step_local_server(self):
        ttk.Label(self.action_content, text="Local Development Server", font=("Helvetica", 12)).pack(anchor=tk.W, pady=5)
        
        if self.local_proc is None:
            ttk.Label(self.action_content, text="Server is currently offline.").pack(anchor=tk.W, pady=5)
            
            btn_frame = ttk.Frame(self.action_content)
            btn_frame.pack(fill=tk.X, pady=10)
            
            btn_start = ttk.Button(btn_frame, text="▶ Start Local Server", style="Action.TButton", command=self.do_start_local)
            btn_start.pack(side=tk.LEFT, padx=(0, 10))
            
            btn_skip = ttk.Button(btn_frame, text="Skip to Global Tunnel", command=lambda: self.run_step(6))
            btn_skip.pack(side=tk.LEFT)
        else:
            ttk.Label(self.action_content, text=f"🚀 Local server is RUNNING (Port {self.active_port})", foreground="#a6e3a1", font=("Helvetica", 11, "bold")).pack(anchor=tk.W, pady=5)
            
            btn_frame = ttk.Frame(self.action_content)
            btn_frame.pack(fill=tk.X, pady=10)
            
            btn_open = ttk.Button(btn_frame, text="🌐 Open Browser", style="Action.TButton", command=lambda: webbrowser.open(f"http://localhost:{self.active_port}"))
            btn_open.pack(side=tk.LEFT, padx=(0, 10))
            
            btn_stop = ttk.Button(btn_frame, text="⏹ Terminate Local", command=self.do_stop_local)
            btn_stop.pack(side=tk.LEFT, padx=(0, 10))
            
            btn_next = ttk.Button(btn_frame, text="Continue to Global Tunnel ➜", command=lambda: self.run_step(6))
            btn_next.pack(side=tk.LEFT)

    def get_free_port(self):
        s = socket.socket()
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
        s.close()
        return port

    def spawn_system_terminal(self):
        # Spawns a separate window exclusively for stdout/stderr logs
        if not hasattr(self, 'live_term_window') or not self.live_term_window.winfo_exists():
            self.live_term_window = tk.Toplevel(self)
            self.live_term_window.title("Live Application Terminal")
            self.live_term_window.geometry("800x500")
            self.live_term_window.configure(bg="#11111b")
            
            lbl = ttk.Label(self.live_term_window, text="Live Server Logs", font=("Helvetica", 12, "bold"), background="#11111b", foreground="#a6e3a1")
            lbl.pack(pady=10)
            
            self.live_term = tk.Text(self.live_term_window, bg="#1e1e2e", fg="#cdd6f4", font=("Courier", 11), borderwidth=0, wrap=tk.WORD)
            scrollbar = ttk.Scrollbar(self.live_term_window, orient=tk.VERTICAL, command=self.live_term.yview)
            self.live_term.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.live_term.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.live_term_window.lift()

    def do_start_local(self):
        self.clear_action_frame()
        self.start_loading()
        ttk.Label(self.action_content, text="⏳ Starting local server...", foreground="#89b4fa").pack(anchor=tk.W, pady=10)
        
        btn_terminal = ttk.Button(self.action_content, text="🖥️ Open Separate Terminal", command=self.spawn_system_terminal)
        btn_terminal.pack(anchor=tk.W, pady=5)
        
        def task():
            self.log(f"Analyzing {self.project_type} project to determine start command...")
            env = os.environ.copy()
            
            try:
                self.active_port = self.get_free_port()
            except Exception:
                self.active_port = 5555
                
            cmd = []
            if self.project_type == "Node.js":
                pkg_path = os.path.join(self.project_dir.get(), "package.json")
                cmd = [self.npm_cmd, "run", "dev"]
                if os.path.exists(pkg_path):
                    try:
                        with open(pkg_path, "r", encoding="utf-8") as f:
                            pkg = json.load(f)
                        dev_script = pkg.get("scripts", {}).get("dev", "")
                        start_script = pkg.get("scripts", {}).get("start", "")
                        
                        if not dev_script and start_script:
                            cmd = [self.npm_cmd, "run", "start"]
                            script_to_check = start_script
                        else:
                            script_to_check = dev_script
                            
                        if "vite" in script_to_check: cmd.extend(["--", "--port", str(self.active_port)])
                        elif "next" in script_to_check: cmd.extend(["--", "-p", str(self.active_port)])
                        elif "nuxt" in script_to_check: cmd.extend(["--", "--port", str(self.active_port)])
                        else: env["PORT"] = str(self.active_port)
                    except Exception as e:
                        self.log(f"Warning: Could not parse package.json. {e}")
            elif self.project_type == "Python":
                python_cmd = shutil.which("python3") or shutil.which("python")
                if os.path.exists(os.path.join(self.project_dir.get(), "app.py")):
                    cmd = [python_cmd, "app.py"]
                elif os.path.exists(os.path.join(self.project_dir.get(), "main.py")):
                    cmd = [python_cmd, "main.py"]
                elif os.path.exists(os.path.join(self.project_dir.get(), "manage.py")):
                    cmd = [python_cmd, "manage.py", "runserver", str(self.active_port)]
                else:
                    self.log("Could not find app.py, main.py or manage.py. Failing.")
                    self.after(0, self.stop_loading)
                    return
                env["PORT"] = str(self.active_port)
            elif self.project_type == "Docker":
                cmd = [shutil.which("docker"), "run", "-p", f"{self.active_port}:80", "app_image"]
                self.log(f"Mapping docker port 80 to localhost:{self.active_port}")

            self.log(f"Executing: {' '.join(cmd)}")
            self.after(0, self.spawn_system_terminal)
            
            try:
                self.local_proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=self.project_dir.get())
                self.after(0, self.stop_loading)
                self.after(0, lambda: self.run_step(5)) # Refresh UI
                for line in iter(self.local_proc.stdout.readline, ''):
                    if line.strip():
                        # Simple uncolored log
                        self.term.insert(tk.END, "[SERVER] " + line)
                        self.term.see(tk.END)
                        if hasattr(self, 'live_term') and self.live_term.winfo_exists():
                            self.live_term.insert(tk.END, line)
                            self.live_term.see(tk.END)
                self.local_proc.wait()
                self.log("Local server process terminated.")
            except Exception as e:
                self.after(0, self.stop_loading)
                self.log(f"Failed to start server: {e}")
            finally:
                self.local_proc = None
                if self.current_step == 5:
                    self.after(0, lambda: self.run_step(5))
                
        threading.Thread(target=task, daemon=True).start()

    def do_stop_local(self):
        if self.local_proc:
            self.local_proc.terminate()
            self.local_proc = None
            self.log("Server stopped directly by user.")
            self.run_step(5)

    def step_global_tunnel(self):
        ttk.Label(self.action_content, text="Global SSH Tunnel Access", font=("Helvetica", 12)).pack(anchor=tk.W, pady=5)
        
        if self.tunnel_proc is None:
            ttk.Label(self.action_content, text="Make your local server accessible from anywhere.", foreground="#bac2de").pack(anchor=tk.W, pady=5)
            
            btn_start = ttk.Button(self.action_content, text="🌐 Start Public Tunnel", style="Action.TButton", command=self.do_start_tunnel)
            btn_start.pack(anchor=tk.W, pady=10)
        else:
            ttk.Label(self.action_content, text="🌍 Global Tunnel is RUNNING", foreground="#a6e3a1", font=("Helvetica", 11, "bold")).pack(anchor=tk.W, pady=5)
            if self.tunnel_url:
                url_frame = ttk.Frame(self.action_content)
                url_frame.pack(fill=tk.X, pady=5)
                ttk.Label(url_frame, text="Public URL: ", foreground="#cdd6f4", font=("Helvetica", 10)).pack(side=tk.LEFT)
                
                url_entry = tk.Entry(url_frame, bg="#313244", fg="#a6e3a1", font=("Helvetica", 10, "bold"), width=35, borderwidth=0)
                url_entry.insert(0, self.tunnel_url)
                url_entry.configure(state='readonly')
                url_entry.pack(side=tk.LEFT, padx=5)
                
            btn_frame = ttk.Frame(self.action_content)
            btn_frame.pack(fill=tk.X, pady=10)
            
            if self.tunnel_url:
                btn_copy = ttk.Button(btn_frame, text="📋 Copy App Link", style="Action.TButton", command=self.copy_tunnel_url)
                btn_copy.pack(side=tk.LEFT, padx=(0, 10))
            
            btn_stop = ttk.Button(btn_frame, text="⏹ Terminate Tunnel", command=self.do_stop_tunnel)
            btn_stop.pack(side=tk.LEFT)

    def do_start_tunnel(self):
        self.clear_action_frame()
        self.start_loading()
        ttk.Label(self.action_content, text="⏳ Establishing tunnel connection via localhost.run...", foreground="#89b4fa").pack(anchor=tk.W, pady=10)
        
        def task():
            self.log("Starting SSH tunnel via localhost.run (no installation required)...")
            try:
                ssh_dir = os.path.expanduser("~/.ssh")
                key_path = os.path.join(ssh_dir, "universal_deployer_key")
                if not os.path.exists(key_path):
                    self.log("Generating dedicated SSH key for secure tunnel connection...")
                    os.makedirs(ssh_dir, exist_ok=True)
                    subprocess.run(["ssh-keygen", "-t", "ed25519", "-N", "", "-f", key_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                tunnel_cmd = ["ssh", "-i", key_path, "-R", f"80:127.0.0.1:{self.active_port}", "-o", "StrictHostKeyChecking=no", "ssh.localhost.run", "-T"]
                
                if not shutil.which("ssh"):
                    raise Exception("SSH command not found on this system. Please install OpenSSH.")
                    
                self.tunnel_proc = subprocess.Popen(tunnel_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=self.project_dir.get())
                self.after(0, self.stop_loading)
                self.after(0, lambda: self.run_step(6))
                for line in iter(self.tunnel_proc.stdout.readline, ''):
                    if line.strip():
                        self.term.insert(tk.END, "[TUNNEL] " + line)
                        self.term.see(tk.END)
                        
                        # Parse localhost.run output
                        if "tunneled with tls termination," in line.lower():
                            parts = line.split("https://")
                            if len(parts) > 1:
                                self.tunnel_url = "https://" + parts[1].strip().split()[0]
                                self.log(f"TUNNEL SUCCESS! URL: {self.tunnel_url}")
                                self.after(0, lambda: self.run_step(6))
                self.tunnel_proc.wait()
                self.log("Tunnel process disconnected.")
            except Exception as e:
                self.after(0, self.stop_loading)
                self.log(f"Failed to start tunnel: {e}")
            finally:
                self.tunnel_proc = None
                self.tunnel_url = ""
                if self.current_step == 6:
                    self.after(0, lambda: self.run_step(6))
                    
        threading.Thread(target=task, daemon=True).start()

    def do_stop_tunnel(self):
        if self.tunnel_proc:
            self.tunnel_proc.terminate()
            self.tunnel_proc = None
            self.tunnel_url = ""
            self.log("Tunnel stopped by user.")
            self.run_step(6)

    def copy_tunnel_url(self):
        if self.tunnel_url:
            self.clipboard_clear()
            self.clipboard_append(self.tunnel_url)
            messagebox.showinfo("Copied", f"Link copied to clipboard!\n\n{self.tunnel_url}")

if __name__ == "__main__":
    try:
        app = UniversalAppDeployer()
        app.mainloop()
    except Exception as e:
        import traceback
        desktop = os.path.expanduser("~/Desktop")
        with open(os.path.join(desktop, "universal_deployer_crash.txt"), "w") as f:
            f.write(f"Version: {__version__}\n")
            f.write(f"Platform: {platform.platform()}\n")
            f.write(str(e))
            f.write("\n\n" + traceback.format_exc())
        
        # Also try to show a message box if possible
        try:
            import tkinter.messagebox as mb
            root = tk.Tk()
            root.withdraw()
            mb.showerror("Startup Error", f"The application failed to start.\n\nA crash log has been created on your Desktop.\n\nError: {e}")
        except:
            pass
