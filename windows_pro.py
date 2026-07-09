#!/usr/bin/env python3
"""
Ultimate Windows Tools Manager Pro - Enhanced Edition
Auto-detect and launch all Wine Windows applications
For Kali Linux
"""

import os
import sys
import subprocess
import platform
import threading
import json
import time
import shutil
import hashlib
import re
import socket
import queue
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog
import tempfile
import stat

try:
    import psutil
except ImportError:
    print("Installing psutil...")
    subprocess.run(['pip3', 'install', 'psutil'], check=True)
    import psutil

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("PIL not installed. Icon support limited.")

class UltimateWindowsManager:
    """Enhanced Windows Tools Manager with auto-app detection"""
    
    def __init__(self):
        self.wine_prefixes = []
        self.installed_apps = []
        self.all_wine_apps = []
        self.current_prefix = None
        self.operations_log = []
        self.settings = self.load_settings()
        self.progress_queue = queue.Queue()
        self.is_scanning = False
        self.app_icons = {}
        self.wine_drive_c = None
        
    def load_settings(self):
        """Load settings from config"""
        config_file = os.path.expanduser("~/.windows_manager_config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'wine_prefix': os.path.expanduser("~/.wine"),
            'default_arch': 'win64',
            'wine_version': 'system',
            'playonlinux_prefix': os.path.expanduser("~/.PlayOnLinux"),
            'auto_scan_apps': True,
            'scan_interval': 60,
            'theme': 'dark',
            'max_log_size': 1000,
            'icon_cache_dir': os.path.expanduser("~/.wine_icons"),
            'scan_locations': [
                os.path.expanduser("~/.wine/drive_c/Program Files"),
                os.path.expanduser("~/.wine/drive_c/Program Files (x86)"),
                os.path.expanduser("~/.wine/drive_c/"),
                os.path.expanduser("~/.PlayOnLinux/*/drive_c/Program Files"),
                os.path.expanduser("~/.PlayOnLinux/*/drive_c/Program Files (x86)"),
            ]
        }
    
    def save_settings(self):
        """Save settings"""
        config_file = os.path.expanduser("~/.windows_manager_config.json")
        try:
            with open(config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except:
            pass
    
    # === WINE MANAGEMENT ===
    
    def check_wine_installed(self):
        """Check Wine installation"""
        try:
            result = subprocess.run(['wine', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def get_wine_version(self):
        """Get Wine version"""
        try:
            result = subprocess.run(['wine', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.stdout.strip() if result.returncode == 0 else "Not installed"
        except:
            return "Not installed"
    
    def get_wine_prefixes(self):
        """Get all Wine prefixes"""
        prefixes = []
        home = os.path.expanduser("~")
        
        # Default Wine prefix
        default_prefix = os.path.join(home, ".wine")
        if os.path.exists(default_prefix):
            prefixes.append({
                'name': 'default',
                'path': default_prefix,
                'arch': self._get_prefix_arch(default_prefix),
                'wine': self.get_wine_version(),
                'apps': []
            })
        
        # Custom Wine prefixes
        custom_dir = os.path.join(home, ".wine_prefixes")
        if os.path.exists(custom_dir):
            for prefix in os.listdir(custom_dir):
                prefix_path = os.path.join(custom_dir, prefix)
                if os.path.isdir(prefix_path):
                    prefixes.append({
                        'name': prefix,
                        'path': prefix_path,
                        'arch': self._get_prefix_arch(prefix_path),
                        'wine': self._get_prefix_wine_version(prefix_path),
                        'apps': []
                    })
        
        # PlayOnLinux prefixes
        pol_prefixes = os.path.join(home, ".PlayOnLinux", "wineprefix")
        if os.path.exists(pol_prefixes):
            for prefix in os.listdir(pol_prefixes):
                prefix_path = os.path.join(pol_prefixes, prefix)
                if os.path.isdir(prefix_path):
                    prefixes.append({
                        'name': f"POL-{prefix}",
                        'path': prefix_path,
                        'arch': self._get_prefix_arch(prefix_path),
                        'wine': self._get_prefix_wine_version(prefix_path),
                        'apps': []
                    })
        
        self.wine_prefixes = prefixes
        return prefixes
    
    def _get_prefix_arch(self, prefix_path):
        """Get prefix architecture"""
        try:
            system_reg = os.path.join(prefix_path, "system.reg")
            if os.path.exists(system_reg):
                with open(system_reg, 'r') as f:
                    if '[Software\\Wow6432Node]' in f.read():
                        return 'win32'
            return 'win64'
        except:
            return 'unknown'
    
    def _get_prefix_wine_version(self, prefix_path):
        """Get Wine version for prefix"""
        try:
            version_file = os.path.join(prefix_path, ".wine-version")
            if os.path.exists(version_file):
                with open(version_file, 'r') as f:
                    return f.read().strip()
        except:
            pass
        return self.get_wine_version()
    
    # === ENHANCED APP SCANNING ===
    
    def scan_all_apps(self, callback=None):
        """Scan ALL Windows applications in ALL Wine prefixes"""
        self.is_scanning = True
        all_apps = []
        
        # Get all prefixes
        prefixes = self.get_wine_prefixes()
        total_prefixes = len(prefixes)
        
        for i, prefix in enumerate(prefixes):
            if callback:
                progress = int((i / max(total_prefixes, 1)) * 100)
                callback(progress, f"Scanning {prefix['name']}...")
            
            # Scan this prefix
            apps = self.scan_prefix_apps(prefix['path'])
            prefix['apps'] = apps
            all_apps.extend(apps)
        
        # Also scan common locations even without prefixes
        extra_apps = self.scan_common_locations()
        all_apps.extend(extra_apps)
        
        self.installed_apps = all_apps
        self.all_wine_apps = all_apps
        self.is_scanning = False
        
        if callback:
            callback(100, f"Found {len(all_apps)} applications")
        
        self.log_operation(f"Found {len(all_apps)} Windows applications")
        return all_apps
    
    def scan_prefix_apps(self, prefix_path):
        """Scan a single Wine prefix for applications"""
        apps = []
        drive_c = os.path.join(prefix_path, "drive_c")
        
        if not os.path.exists(drive_c):
            return apps
        
        # Scan common program locations
        scan_locations = [
            os.path.join(drive_c, "Program Files"),
            os.path.join(drive_c, "Program Files (x86)"),
            drive_c,  # Root of C: drive
        ]
        
        # Check for common app folders
        common_apps = [
            "TFT MTK V7",
            "TFT Tools Manager",
            "MetaTrader 5",
            "MetaTrader 4",
            "MT5",
            "MT4",
            "TFT_UNLOCKER",
            "TFT",
        ]
        
        for location in scan_locations:
            if not os.path.exists(location):
                continue
            
            # Walk through directories
            for root, dirs, files in os.walk(location, topdown=True, followlinks=False):
                # Limit depth to avoid scanning too much
                depth = root.replace(location, '').count(os.sep)
                if depth > 3:
                    continue
                
                # Look for exe files
                for file in files:
                    if file.lower().endswith('.exe'):
                        exe_path = os.path.join(root, file)
                        app_name = os.path.basename(root)
                        
                        # Try to get a better app name
                        if file.lower() in ['tftmtk.exe', 'tft_mtk.exe', 'tft.exe']:
                            app_name = "TFT MTK Tool"
                        elif 'metatrader' in file.lower() or 'terminal' in file.lower():
                            app_name = "MetaTrader"
                        elif 'mt5' in file.lower():
                            app_name = "MT5"
                        elif 'mt4' in file.lower():
                            app_name = "MT4"
                        elif 'unlocker' in file.lower() or 'unlock' in file.lower():
                            app_name = "Unlocker Tool"
                        
                        # Extract icon
                        icon_path = self._extract_icon(exe_path)
                        
                        # Get file size
                        try:
                            size = os.path.getsize(exe_path)
                        except:
                            size = 0
                        
                        apps.append({
                            'name': app_name,
                            'exe_path': exe_path,
                            'exe_file': file,
                            'path': root,
                            'prefix': os.path.basename(prefix_path),
                            'prefix_path': prefix_path,
                            'icon': icon_path,
                            'size': size,
                            'size_formatted': self._format_size(size)
                        })
        
        # Also check for specific named apps at root
        for app_name in common_apps:
            for location in [drive_c, os.path.join(drive_c, "Program Files"), os.path.join(drive_c, "Program Files (x86)")]:
                app_dir = os.path.join(location, app_name)
                if os.path.exists(app_dir) and os.path.isdir(app_dir):
                    # Find exe in this dir
                    for root, dirs, files in os.walk(app_dir, topdown=True, followlinks=False):
                        for file in files:
                            if file.lower().endswith('.exe'):
                                exe_path = os.path.join(root, file)
                                icon_path = self._extract_icon(exe_path)
                                
                                # Check if already added
                                already_added = False
                                for app in apps:
                                    if app['exe_path'] == exe_path:
                                        already_added = True
                                        break
                                
                                if not already_added:
                                    apps.append({
                                        'name': app_name,
                                        'exe_path': exe_path,
                                        'exe_file': file,
                                        'path': root,
                                        'prefix': os.path.basename(prefix_path),
                                        'prefix_path': prefix_path,
                                        'icon': icon_path,
                                        'size': os.path.getsize(exe_path) if os.path.exists(exe_path) else 0,
                                        'size_formatted': self._format_size(os.path.getsize(exe_path)) if os.path.exists(exe_path) else '0 B'
                                    })
        
        return apps
    
    def scan_common_locations(self):
        """Scan common locations for apps even without explicit prefixes"""
        apps = []
        
        # Check Desktop for exe files
        desktop = os.path.expanduser("~/Desktop")
        if os.path.exists(desktop):
            for file in os.listdir(desktop):
                if file.lower().endswith('.exe'):
                    exe_path = os.path.join(desktop, file)
                    apps.append({
                        'name': file.replace('.exe', ''),
                        'exe_path': exe_path,
                        'exe_file': file,
                        'path': desktop,
                        'prefix': 'Desktop',
                        'prefix_path': '',
                        'icon': None,
                        'size': os.path.getsize(exe_path),
                        'size_formatted': self._format_size(os.path.getsize(exe_path))
                    })
        
        # Check heavy_software folder
        heavy = os.path.expanduser("~/Desktop/heavy_software")
        if os.path.exists(heavy):
            for file in os.listdir(heavy):
                if file.lower().endswith('.exe'):
                    exe_path = os.path.join(heavy, file)
                    apps.append({
                        'name': file.replace('.exe', ''),
                        'exe_path': exe_path,
                        'exe_file': file,
                        'path': heavy,
                        'prefix': 'Desktop/heavy_software',
                        'prefix_path': '',
                        'icon': None,
                        'size': os.path.getsize(exe_path),
                        'size_formatted': self._format_size(os.path.getsize(exe_path))
                    })
        
        return apps
    
    def _extract_icon(self, exe_path):
        """Extract icon from executable"""
        try:
            icon_cache = self.settings['icon_cache_dir']
            os.makedirs(icon_cache, exist_ok=True)
            
            # Generate hash for cache
            hash_obj = hashlib.md5(exe_path.encode())
            icon_file = os.path.join(icon_cache, f"{hash_obj.hexdigest()}.png")
            
            if os.path.exists(icon_file):
                return icon_file
            
            # Try to extract icon using wrestool
            if shutil.which('wrestool'):
                temp_ico = os.path.join(icon_cache, f"{hash_obj.hexdigest()}.ico")
                try:
                    subprocess.run(['wrestool', '-x', '-t', '14', exe_path, '-o', temp_ico],
                                 capture_output=True, timeout=5)
                    
                    if os.path.exists(temp_ico) and HAS_PIL:
                        img = Image.open(temp_ico)
                        img.save(icon_file, 'PNG')
                        os.remove(temp_ico)
                        return icon_file
                except:
                    pass
            
            return None
        except:
            return None
    
    def _format_size(self, bytes):
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} PB"
    
    # === RUN APPLICATIONS ===
    
    def run_application(self, exe_path, prefix_path=None):
        """Run a Windows application"""
        try:
            env = os.environ.copy()
            if prefix_path and os.path.exists(prefix_path):
                env['WINEPREFIX'] = prefix_path
            
            # Show progress
            self.progress_queue.put(10)
            time.sleep(0.3)
            self.progress_queue.put(50)
            
            # Launch application
            process = subprocess.Popen(['wine', exe_path], env=env)
            self.progress_queue.put(100)
            
            self.log_operation(f"Started: {os.path.basename(exe_path)}")
            return {'success': True, 'message': f'Application started: {os.path.basename(exe_path)}', 'process': process}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def run_application_with_prefix(self, app_name):
        """Run application by name"""
        for app in self.all_wine_apps:
            if app['name'] == app_name or app_name in app['name']:
                return self.run_application(app['exe_path'], app.get('prefix_path'))
        return {'success': False, 'message': f'Application "{app_name}" not found'}
    
    # === WINE TOOLS ===
    
    def configure_wine(self, prefix_path=None):
        """Open Wine configuration"""
        try:
            env = os.environ.copy()
            if prefix_path:
                env['WINEPREFIX'] = prefix_path
            subprocess.Popen(['winecfg'], env=env)
            self.log_operation("Launched Wine configuration")
            return {'success': True, 'message': 'Wine configuration launched'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def run_regedit(self, prefix_path=None):
        """Open Registry Editor"""
        try:
            env = os.environ.copy()
            if prefix_path:
                env['WINEPREFIX'] = prefix_path
            subprocess.Popen(['wine', 'regedit'], env=env)
            self.log_operation("Launched Registry Editor")
            return {'success': True, 'message': 'Registry Editor launched'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def run_explorer(self, prefix_path=None):
        """Open Wine Explorer"""
        try:
            env = os.environ.copy()
            if prefix_path:
                env['WINEPREFIX'] = prefix_path
            subprocess.Popen(['wine', 'explorer'], env=env)
            self.log_operation("Launched Wine Explorer")
            return {'success': True, 'message': 'Wine Explorer launched'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def run_winetricks(self, prefix_path=None):
        """Open Winetricks"""
        try:
            env = os.environ.copy()
            if prefix_path:
                env['WINEPREFIX'] = prefix_path
            subprocess.Popen(['winetricks'], env=env)
            self.log_operation("Launched Winetricks")
            return {'success': True, 'message': 'Winetricks launched'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def get_system_info(self):
        """Get system information"""
        info = {
            'os': platform.system(),
            'os_version': platform.release(),
            'architecture': platform.machine(),
            'python_version': platform.python_version(),
            'wine_version': self.get_wine_version(),
            'prefixes_count': len(self.wine_prefixes),
            'apps_count': len(self.all_wine_apps),
            'wine_installed': self.check_wine_installed()
        }
        return info
    
    def log_operation(self, operation):
        """Log operations"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.operations_log.append(f"[{timestamp}] {operation}")
        if len(self.operations_log) > 1000:
            self.operations_log = self.operations_log[-1000:]


class WindowsToolsGUI:
    """Main GUI for Windows Tools Manager"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Windows Tools Manager Pro - All Wine Apps")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e1e2e')
        
        self.manager = UltimateWindowsManager()
        self.current_progress = 0
        self.progress_window = None
        self.progress_bar = None
        self.progress_label = None
        self.filtered_apps = []
        
        self.setup_ui()
        self.refresh_data()
        
        # Auto-scan after startup
        self.root.after(1000, self.scan_apps_async)
    
    def setup_ui(self):
        main = tk.Frame(self.root, bg='#1e1e2e')
        main.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Header
        header = tk.Frame(main, bg='#1e1e2e')
        header.pack(fill='x', pady=(0, 10))
        
        title = tk.Label(header, text="🍷 Windows Tools Manager Pro", 
                        font=('Helvetica', 24, 'bold'), 
                        fg='#89b4fa', bg='#1e1e2e')
        title.pack(side='left')
        
        # Status
        self.status_indicator = tk.Label(header, text="●", 
                                        font=('Helvetica', 16),
                                        fg='#a6e3a1', bg='#1e1e2e')
        self.status_indicator.pack(side='right', padx=5)
        
        self.status_text = tk.Label(header, text="Ready", 
                                   font=('Helvetica', 11),
                                   fg='#cdd6f4', bg='#1e1e2e')
        self.status_text.pack(side='right')
        
        # Stats
        self.stats_label = tk.Label(header, text="", 
                                   font=('Helvetica', 11),
                                   fg='#f9e2af', bg='#1e1e2e')
        self.stats_label.pack(side='right', padx=20)
        
        # Main content
        content = tk.Frame(main, bg='#1e1e2e')
        content.pack(fill='both', expand=True)
        
        # Left panel: App list
        left_panel = tk.Frame(content, bg='#313244', relief='flat', bd=1)
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Search bar
        search_frame = tk.Frame(left_panel, bg='#313244')
        search_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(search_frame, text="🔍 Search:", 
                fg='#cdd6f4', bg='#313244',
                font=('Helvetica', 11)).pack(side='left', padx=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_apps())
        
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                               bg='#1e1e2e', fg='#cdd6f4',
                               font=('Helvetica', 11), width=25)
        search_entry.pack(side='left', fill='x', expand=True)
        
        # Refresh button
        tk.Button(search_frame, text="🔄 Refresh", command=self.scan_apps_async,
                 bg='#89b4fa', fg='white',
                 font=('Helvetica', 10, 'bold'),
                 padx=10, pady=5, relief='flat').pack(side='right', padx=(10, 0))
        
        # App list with scrollbar
        list_frame = tk.Frame(left_panel, bg='#313244')
        list_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Treeview with columns
        columns = ('Icon', 'Application', 'Prefix', 'Location', 'Size')
        self.apps_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=25)
        
        self.apps_tree.heading('Icon', text='')
        self.apps_tree.heading('Application', text='Application')
        self.apps_tree.heading('Prefix', text='Prefix')
        self.apps_tree.heading('Location', text='Location')
        self.apps_tree.heading('Size', text='Size')
        
        self.apps_tree.column('Icon', width=40, anchor='center')
        self.apps_tree.column('Application', width=250)
        self.apps_tree.column('Prefix', width=120)
        self.apps_tree.column('Location', width=350)
        self.apps_tree.column('Size', width=80)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', 
                                 command=self.apps_tree.yview)
        self.apps_tree.configure(yscrollcommand=scrollbar.set)
        
        self.apps_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Double-click to run
        self.apps_tree.bind('<Double-Button-1>', self.on_app_double_click)
        self.apps_tree.bind('<Return>', self.on_app_double_click)
        
        # Right-click menu
        self.apps_menu = tk.Menu(self.root, tearoff=0, bg='#313244', fg='#cdd6f4')
        self.apps_menu.add_command(label="▶️ Run Application", command=self.run_selected_app)
        self.apps_menu.add_command(label="📂 Open Folder", command=self.open_app_folder)
        self.apps_menu.add_command(label="🔍 Show Details", command=self.show_app_details)
        self.apps_menu.add_separator()
        self.apps_menu.add_command(label="🔄 Refresh List", command=self.scan_apps_async)
        
        self.apps_tree.bind('<Button-3>', self.show_apps_menu)
        
        # Right panel: Tools and controls
        right_panel = tk.Frame(content, bg='#1e1e2e', width=300)
        right_panel.pack(side='right', fill='both')
        
        # Quick actions
        quick_frame = tk.LabelFrame(right_panel, text="⚡ Quick Actions", 
                                   bg='#1e1e2e', fg='#cdd6f4')
        quick_frame.pack(fill='x', pady=(0, 10))
        
        actions = [
            ("▶️ Run Selected", self.run_selected_app, '#a6e3a1'),
            ("📂 Open Folder", self.open_app_folder, '#89b4fa'),
            ("🔧 Wine Config", self.open_winecfg, '#89b4fa'),
            ("📦 Winetricks", self.open_winetricks, '#89b4fa'),
            ("📝 Registry", self.open_regedit, '#89b4fa'),
            ("📁 Explorer", self.open_explorer, '#89b4fa'),
            ("🔄 Scan Apps", self.scan_apps_async, '#89b4fa'),
            ("📊 System Info", self.show_system_info, '#f9e2af'),
        ]
        
        for i, (text, command, color) in enumerate(actions):
            btn = tk.Button(quick_frame, text=text, command=command,
                           bg=color, fg='#1e1e2e',
                           font=('Helvetica', 10, 'bold'),
                           padx=10, pady=8, relief='flat')
            btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky='ew')
        
        quick_frame.grid_columnconfigure(0, weight=1)
        quick_frame.grid_columnconfigure(1, weight=1)
        
        # App info panel
        info_frame = tk.LabelFrame(right_panel, text="📋 Application Info", 
                                   bg='#1e1e2e', fg='#cdd6f4')
        info_frame.pack(fill='both', expand=True)
        
        self.app_info_text = scrolledtext.ScrolledText(info_frame,
                                                       bg='#1e1e2e', fg='#cdd6f4',
                                                       font=('Monospace', 10),
                                                       height=10)
        self.app_info_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.app_info_text.insert('1.0', "Select an application to see details...")
        
        # Status bar
        status_frame = tk.Frame(main, bg='#313244')
        status_frame.pack(side='bottom', fill='x', pady=(10, 0))
        
        self.status_bar = tk.Label(status_frame, text="Ready", 
                                   bg='#313244', fg='#cdd6f4',
                                   anchor='w', padx=15,
                                   font=('Helvetica', 10))
        self.status_bar.pack(side='left', fill='x', expand=True)
        
        self.status_progress = ttk.Progressbar(status_frame, mode='determinate',
                                              length=150, value=0)
        self.status_progress.pack(side='right', padx=10)
    
    # === PROGRESS FUNCTIONS ===
    
    def show_progress(self, title="Processing"):
        """Show progress window"""
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title(title)
        self.progress_window.geometry("400x150")
        self.progress_window.configure(bg='#1e1e2e')
        self.progress_window.transient(self.root)
        self.progress_window.grab_set()
        
        self.progress_window.update_idletasks()
        width = self.progress_window.winfo_width()
        height = self.progress_window.winfo_height()
        x = (self.progress_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.progress_window.winfo_screenheight() // 2) - (height // 2)
        self.progress_window.geometry(f'{width}x{height}+{x}+{y}')
        
        label = tk.Label(self.progress_window, text="Processing...", 
                        font=('Helvetica', 14),
                        fg='#cdd6f4', bg='#1e1e2e')
        label.pack(pady=(20, 10))
        
        self.progress_label = tk.Label(self.progress_window, text="0%", 
                                      font=('Helvetica', 12),
                                      fg='#89b4fa', bg='#1e1e2e')
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(self.progress_window, 
                                           mode='determinate',
                                           length=300)
        self.progress_bar.pack(pady=10)
        
        self.update_progress()
    
    def update_progress(self):
        """Update progress bar"""
        try:
            while not self.manager.progress_queue.empty():
                progress = self.manager.progress_queue.get_nowait()
                self.current_progress = progress
                if self.progress_bar:
                    self.progress_bar['value'] = progress
                if self.progress_label:
                    self.progress_label.config(text=f"{progress}%")
                if self.status_progress:
                    self.status_progress['value'] = progress
                self.root.update_idletasks()
            
            if self.current_progress < 100:
                self.root.after(100, self.update_progress)
            else:
                self.root.after(500, self.close_progress)
        except:
            pass
    
    def close_progress(self):
        """Close progress window"""
        if self.progress_window:
            self.progress_window.destroy()
            self.progress_window = None
            self.progress_bar = None
            self.progress_label = None
            self.current_progress = 0
            if self.status_progress:
                self.status_progress['value'] = 0
    
    # === DATA REFRESH ===
    
    def refresh_data(self):
        """Refresh all data"""
        self.refresh_wine_status()
        self.update_stats()
    
    def refresh_wine_status(self):
        """Refresh Wine status"""
        if self.manager.check_wine_installed():
            version = self.manager.get_wine_version()
            self.status_indicator.config(fg='#a6e3a1')
            self.status_text.config(text=f"Wine {version}")
        else:
            self.status_indicator.config(fg='#f38ba8')
            self.status_text.config(text="Wine not installed")
    
    def update_stats(self):
        """Update stats"""
        info = self.manager.get_system_info()
        self.stats_label.config(text=f"Apps: {info.get('apps_count', 0)} | Prefixes: {info.get('prefixes_count', 0)}")
    
    # === APP SCANNING ===
    
    def scan_apps_async(self):
        """Scan for applications with progress"""
        if self.manager.is_scanning:
            return
        
        self.show_progress("Scanning for Windows Applications...")
        self.status_bar.config(text="Scanning for Windows applications...")
        
        thread = threading.Thread(target=self._scan_apps_thread)
        thread.daemon = True
        thread.start()
    
    def _scan_apps_thread(self):
        """Scan apps in background"""
        def update_progress(progress, message):
            self.manager.progress_queue.put(progress)
            if message:
                self.root.after(0, lambda: self.status_bar.config(text=message))
        
        self.manager.scan_all_apps(callback=update_progress)
        self.root.after(0, self._scan_complete)
    
    def _scan_complete(self):
        """Called when scan is complete"""
        self.manager.progress_queue.put(100)
        self.populate_apps()
        self.update_stats()
        self.status_bar.config(text=f"Found {len(self.manager.all_wine_apps)} applications")
        self.close_progress()
    
    # === APP DISPLAY ===
    
    def populate_apps(self, filter_text=None):
        """Populate the apps tree"""
        for item in self.apps_tree.get_children():
            self.apps_tree.delete(item)
        
        apps = self.manager.all_wine_apps
        
        # Filter if search text
        if filter_text:
            filter_text = filter_text.lower()
            apps = [app for app in apps if filter_text in app['name'].lower() or filter_text in app['exe_file'].lower()]
        
        for app in apps:
            # Determine icon
            if 'tft' in app['name'].lower():
                icon = "🔧"
            elif 'metatrader' in app['name'].lower() or 'mt5' in app['name'].lower() or 'mt4' in app['name'].lower():
                icon = "📈"
            elif 'unlocker' in app['name'].lower() or 'unlock' in app['name'].lower():
                icon = "🔓"
            else:
                icon = "📦"
            
            # Truncate long paths
            location = app.get('path', '')
            if len(location) > 50:
                location = "..." + location[-47:]
            
            self.apps_tree.insert('', 'end', values=(
                icon,
                app['name'],
                app.get('prefix', 'default'),
                location,
                app.get('size_formatted', '0 B')
            ), tags=(app['exe_path'], app.get('prefix_path', '')))
    
    def filter_apps(self):
        """Filter apps based on search text"""
        search_text = self.search_var.get()
        self.populate_apps(search_text)
    
    # === APP OPERATIONS ===
    
    def get_selected_app(self):
        """Get the selected application from tree"""
        selection = self.apps_tree.selection()
        if not selection:
            return None
        
        values = self.apps_tree.item(selection[0])['values']
        tags = self.apps_tree.item(selection[0])['tags']
        
        # Find the app in the list
        app_name = values[1]
        for app in self.manager.all_wine_apps:
            if app['name'] == app_name:
                return app
        
        return None
    
    def on_app_double_click(self, event):
        """Handle double-click on app"""
        self.run_selected_app()
    
    def run_selected_app(self):
        """Run selected application"""
        app = self.get_selected_app()
        if not app:
            messagebox.showwarning("No Selection", "Please select an application first")
            return
        
        self.show_progress(f"Running {app['name']}")
        result = self.manager.run_application(app['exe_path'], app.get('prefix_path'))
        self.root.after(0, lambda: self.show_result(result))
        self.close_progress()
    
    def open_app_folder(self):
        """Open the folder containing the application"""
        app = self.get_selected_app()
        if not app:
            messagebox.showwarning("No Selection", "Please select an application first")
            return
        
        folder = os.path.dirname(app['exe_path'])
        if os.path.exists(folder):
            subprocess.run(['xdg-open', folder], capture_output=True)
            self.status_bar.config(text=f"Opened: {folder}")
        else:
            messagebox.showerror("Error", f"Folder not found: {folder}")
    
    def show_app_details(self):
        """Show application details"""
        app = self.get_selected_app()
        if not app:
            messagebox.showwarning("No Selection", "Please select an application first")
            return
        
        details = f"""📋 Application Details
{'='*50}

Name: {app['name']}
Executable: {app['exe_file']}
Full Path: {app['exe_path']}
Folder: {app['path']}
Prefix: {app.get('prefix', 'default')}
Size: {app.get('size_formatted', 'Unknown')}

📌 Quick Run Command:
wine "{app['exe_path']}"
"""
        
        messagebox.showinfo("Application Details", details)
        
        # Update info panel
        self.app_info_text.delete('1.0', tk.END)
        self.app_info_text.insert('1.0', details)
    
    def show_apps_menu(self, event):
        """Show context menu for apps"""
        try:
            self.apps_tree.selection_set(self.apps_tree.identify_row(event.y))
            self.apps_menu.post(event.x_root, event.y_root)
        except:
            pass
    
    # === WINE TOOLS ===
    
    def open_winecfg(self):
        """Open Wine configuration"""
        result = self.manager.configure_wine()
        self.show_result(result)
    
    def open_regedit(self):
        """Open Registry Editor"""
        result = self.manager.run_regedit()
        self.show_result(result)
    
    def open_explorer(self):
        """Open Wine Explorer"""
        result = self.manager.run_explorer()
        self.show_result(result)
    
    def open_winetricks(self):
        """Open Winetricks"""
        result = self.manager.run_winetricks()
        self.show_result(result)
    
    def show_system_info(self):
        """Show system information"""
        info = self.manager.get_system_info()
        info_text = f"""📊 System Information
{'='*50}

OS: {info.get('os', 'Unknown')} {info.get('os_version', '')}
Architecture: {info.get('architecture', 'Unknown')}
Python: {info.get('python_version', 'Unknown')}

Wine: {info.get('wine_version', 'Not installed')}
Prefixes: {info.get('prefixes_count', 0)}
Installed Apps: {info.get('apps_count', 0)}
"""
        messagebox.showinfo("System Info", info_text)
    
    # === UTILITY ===
    
    def show_result(self, result):
        """Show operation result"""
        if result['success']:
            messagebox.showinfo("✅ Success", result['message'])
            self.status_bar.config(text=result['message'])
        else:
            messagebox.showerror("❌ Error", result['message'])
            self.status_bar.config(text=f"Error: {result['message']}")


def main():
    # Check for required packages
    try:
        import psutil
    except ImportError:
        print("📦 Installing psutil...")
        subprocess.run(['pip3', 'install', 'psutil'], check=True)
        import psutil
    
    root = tk.Tk()
    app = WindowsToolsGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
