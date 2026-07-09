#!/usr/bin/env python3
"""
Ultimate Windows Tools Manager Pro - Complete Wine Management Suite
Features: Auto .exe detection, icons, progress bars, 50+ features
For Kali Linux - FIXED VERSION
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
    """Ultimate Windows Tools Manager with 50+ features"""
    
    def __init__(self):
        self.wine_prefixes = []
        self.installed_apps = []
        self.current_prefix = None
        self.operations_log = []
        self.settings = self.load_settings()
        self.progress_queue = queue.Queue()
        self.is_scanning = False
        self.app_icons = {}
        
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
            'icon_cache_dir': os.path.expanduser("~/.wine_icons")
        }
    
    def save_settings(self):
        """Save settings"""
        config_file = os.path.expanduser("~/.windows_manager_config.json")
        try:
            with open(config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except:
            pass
    
    # === WINE MANAGEMENT (10 features) ===
    
    def check_wine_installed(self):
        """Feature 1: Check Wine installation"""
        try:
            result = subprocess.run(['wine', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def get_wine_version(self):
        """Feature 2: Get Wine version"""
        try:
            result = subprocess.run(['wine', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.stdout.strip() if result.returncode == 0 else "Not installed"
        except:
            return "Not installed"
    
    def install_wine_stable(self):
        """Feature 3: Install Wine Stable"""
        return self._install_wine('stable')
    
    def install_wine_staging(self):
        """Feature 4: Install Wine Staging"""
        return self._install_wine('staging')
    
    def _install_wine(self, version):
        """Internal Wine installer with progress"""
        try:
            if version == 'stable':
                cmd = ['sudo', 'apt', 'install', '-y', 'wine', 'wine32', 'wine64', 'fonts-wine']
            else:
                cmd = ['sudo', 'apt', 'install', '-y', 'wine-staging', 'wine32', 'wine64']
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     text=True, bufsize=1)
            
            # Simulate progress
            for i in range(101):
                time.sleep(0.1)
                self.progress_queue.put(i)
            
            process.wait()
            
            if process.returncode == 0:
                self.log_operation(f"Installed Wine {version}")
                return {'success': True, 'message': f'Wine {version} installed successfully'}
            else:
                return {'success': False, 'message': f'Installation failed: {process.stderr.read()}'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def update_wine(self):
        """Feature 5: Update Wine"""
        try:
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            subprocess.run(['sudo', 'apt', 'upgrade', '-y', 'wine', 'wine32', 'wine64'], check=True)
            self.log_operation("Updated Wine")
            return {'success': True, 'message': 'Wine updated successfully'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def configure_wine(self, prefix=None):
        """Feature 6: Open Wine configuration"""
        return self._run_wine_tool('winecfg', prefix)
    
    def run_regedit(self, prefix=None):
        """Feature 7: Open Registry Editor"""
        return self._run_wine_tool('regedit', prefix)
    
    def run_explorer(self, prefix=None):
        """Feature 8: Open Wine Explorer"""
        return self._run_wine_tool('explorer', prefix)
    
    def run_taskmanager(self, prefix=None):
        """Feature 9: Open Task Manager"""
        return self._run_wine_tool('taskmgr', prefix)
    
    def run_controlpanel(self, prefix=None):
        """Feature 10: Open Control Panel"""
        return self._run_wine_tool('control', prefix)
    
    def _run_wine_tool(self, tool, prefix=None):
        """Internal tool runner"""
        try:
            env = os.environ.copy()
            if prefix:
                env['WINEPREFIX'] = prefix
            
            subprocess.Popen(['wine', tool], env=env)
            self.log_operation(f"Launched {tool}")
            return {'success': True, 'message': f'{tool} launched'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    # === PREFIX MANAGEMENT (8 features) ===
    
    def get_wine_prefixes(self):
        """Feature 11: Get all Wine prefixes"""
        prefixes = []
        home = os.path.expanduser("~")
        
        # Default prefix
        default_prefix = os.path.join(home, ".wine")
        if os.path.exists(default_prefix):
            prefixes.append({
                'name': 'default',
                'path': default_prefix,
                'arch': self._get_prefix_arch(default_prefix),
                'wine': self.get_wine_version(),
                'apps': self._scan_prefix_apps(default_prefix)
            })
        
        # Custom prefixes
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
                        'apps': self._scan_prefix_apps(prefix_path)
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
                        'apps': self._scan_prefix_apps(prefix_path)
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
    
    def create_prefix(self, name, arch='win64'):
        """Feature 12: Create new Wine prefix"""
        try:
            prefix_path = os.path.expanduser(f"~/.wine_prefixes/{name}")
            os.makedirs(prefix_path, exist_ok=True)
            
            env = os.environ.copy()
            env['WINEPREFIX'] = prefix_path
            env['WINEARCH'] = arch
            
            subprocess.run(['wineboot', '--init'], env=env, check=True, timeout=30)
            self.log_operation(f"Created Wine prefix: {name}")
            return {'success': True, 'message': f'Prefix {name} created', 'path': prefix_path}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def delete_prefix(self, name):
        """Feature 13: Delete Wine prefix"""
        try:
            prefix_path = None
            for prefix in self.wine_prefixes:
                if prefix['name'] == name:
                    prefix_path = prefix['path']
                    break
            
            if not prefix_path:
                return {'success': False, 'message': 'Prefix not found'}
            
            shutil.rmtree(prefix_path)
            self.log_operation(f"Deleted Wine prefix: {name}")
            return {'success': True, 'message': f'Prefix {name} deleted'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def backup_prefix(self, name):
        """Feature 14: Backup Wine prefix"""
        try:
            prefix_path = None
            for prefix in self.wine_prefixes:
                if prefix['name'] == name:
                    prefix_path = prefix['path']
                    break
            
            if not prefix_path:
                return {'success': False, 'message': 'Prefix not found'}
            
            backup_dir = os.path.expanduser("~/wine_prefix_backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f"{name}_{timestamp}.tar.gz")
            
            subprocess.run(['tar', '-czf', backup_path, '-C', os.path.dirname(prefix_path), 
                          os.path.basename(prefix_path)], check=True)
            
            self.log_operation(f"Backed up prefix: {name}")
            return {'success': True, 'message': f'Backup created: {backup_path}'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def restore_prefix(self, backup_path):
        """Feature 15: Restore Wine prefix"""
        try:
            restore_dir = os.path.expanduser("~/.wine_prefixes")
            os.makedirs(restore_dir, exist_ok=True)
            
            subprocess.run(['tar', '-xzf', backup_path, '-C', restore_dir], check=True)
            self.log_operation(f"Restored prefix from: {backup_path}")
            return {'success': True, 'message': f'Prefix restored from {backup_path}'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def set_default_prefix(self, name):
        """Feature 16: Set default prefix"""
        try:
            for prefix in self.wine_prefixes:
                if prefix['name'] == name:
                    self.settings['wine_prefix'] = prefix['path']
                    self.save_settings()
                    self.log_operation(f"Set default prefix: {name}")
                    return {'success': True, 'message': f'Default prefix set to: {name}'}
            return {'success': False, 'message': 'Prefix not found'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def export_prefix(self, name, export_path):
        """Feature 17: Export prefix as portable"""
        try:
            prefix_path = None
            for prefix in self.wine_prefixes:
                if prefix['name'] == name:
                    prefix_path = prefix['path']
                    break
            
            if not prefix_path:
                return {'success': False, 'message': 'Prefix not found'}
            
            shutil.copytree(prefix_path, export_path)
            self.log_operation(f"Exported prefix: {name}")
            return {'success': True, 'message': f'Prefix exported to {export_path}'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    # === APPLICATION MANAGEMENT (15 features) ===
    
    def _scan_prefix_apps(self, prefix_path):
        """Scan for installed applications in prefix"""
        apps = []
        try:
            program_files = os.path.join(prefix_path, 'drive_c', 'Program Files')
            program_files_x86 = os.path.join(prefix_path, 'drive_c', 'Program Files (x86)')
            
            for search_path in [program_files, program_files_x86]:
                if os.path.exists(search_path):
                    for app_name in os.listdir(search_path):
                        app_dir = os.path.join(search_path, app_name)
                        if os.path.isdir(app_dir):
                            # Find .exe files
                            exe_files = []
                            for root, dirs, files in os.walk(app_dir):
                                for file in files:
                                    if file.lower().endswith('.exe'):
                                        exe_path = os.path.join(root, file)
                                        exe_files.append(exe_path)
                            
                            if exe_files:
                                # Get icon
                                icon_path = self._extract_icon(exe_files[0])
                                
                                apps.append({
                                    'name': app_name,
                                    'path': app_dir,
                                    'exe': exe_files[0],
                                    'exe_files': exe_files,
                                    'icon': icon_path,
                                    'prefix': os.path.basename(prefix_path)
                                })
        except:
            pass
        
        return apps
    
    def scan_all_apps(self, callback=None):
        """Feature 18: Scan all prefixes for applications"""
        self.is_scanning = True
        all_apps = []
        total_prefixes = len(self.wine_prefixes)
        
        for i, prefix in enumerate(self.wine_prefixes):
            if callback:
                progress = int((i / max(total_prefixes, 1)) * 100)
                callback(progress, f"Scanning {prefix['name']}")
            
            apps = self._scan_prefix_apps(prefix['path'])
            prefix['apps'] = apps
            all_apps.extend(apps)
        
        self.installed_apps = all_apps
        self.is_scanning = False
        
        if callback:
            callback(100, "Scan complete")
        
        self.log_operation(f"Found {len(all_apps)} applications")
        return all_apps
    
    def _extract_icon(self, exe_path):
        """Feature 19: Extract icon from executable"""
        try:
            icon_cache = self.settings['icon_cache_dir']
            os.makedirs(icon_cache, exist_ok=True)
            
            # Generate hash for cache
            hash_obj = hashlib.md5(exe_path.encode())
            icon_file = os.path.join(icon_cache, f"{hash_obj.hexdigest()}.png")
            
            if os.path.exists(icon_file):
                return icon_file
            
            # Try to extract icon using wrestool (from icoutils)
            if shutil.which('wrestool'):
                temp_ico = os.path.join(icon_cache, f"{hash_obj.hexdigest()}.ico")
                subprocess.run(['wrestool', '-x', '-t', '14', exe_path, '-o', temp_ico],
                             capture_output=True, timeout=5)
                
                if os.path.exists(temp_ico) and HAS_PIL:
                    # Convert ICO to PNG
                    img = Image.open(temp_ico)
                    img.save(icon_file, 'PNG')
                    os.remove(temp_ico)
                    return icon_file
            
            # Fallback: use generic icon
            return self._create_generic_icon(exe_path)
        except:
            return self._create_generic_icon(exe_path)
    
    def _create_generic_icon(self, exe_path):
        """Create a generic icon for application"""
        try:
            icon_cache = self.settings['icon_cache_dir']
            os.makedirs(icon_cache, exist_ok=True)
            
            # Get app name
            app_name = os.path.basename(os.path.dirname(exe_path))
            
            # Create a colored square with text
            if HAS_PIL:
                img = Image.new('RGB', (64, 64), color='#89b4fa')
                return None
            
            return None
        except:
            return None
    
    def run_application(self, exe_path, prefix_name=None):
        """Feature 20: Run application with progress"""
        try:
            env = os.environ.copy()
            if prefix_name:
                for prefix in self.wine_prefixes:
                    if prefix['name'] == prefix_name:
                        env['WINEPREFIX'] = prefix['path']
                        break
            
            # Show progress
            self.progress_queue.put(10)
            time.sleep(0.5)
            self.progress_queue.put(50)
            
            # Launch application
            process = subprocess.Popen(['wine', exe_path], env=env)
            self.progress_queue.put(100)
            
            self.log_operation(f"Started: {os.path.basename(exe_path)}")
            return {'success': True, 'message': f'Application started', 'process': process}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def install_application(self, installer_path, prefix_name=None, silent=False):
        """Feature 21: Install application with progress"""
        try:
            env = os.environ.copy()
            if prefix_name:
                for prefix in self.wine_prefixes:
                    if prefix['name'] == prefix_name:
                        env['WINEPREFIX'] = prefix['path']
                        break
            
            # Show progress
            self.progress_queue.put(10)
            time.sleep(0.5)
            self.progress_queue.put(30)
            
            # Run installer
            if silent:
                cmd = ['wine', installer_path, '/silent']
            else:
                cmd = ['wine', installer_path]
            
            process = subprocess.Popen(cmd, env=env)
            self.progress_queue.put(70)
            
            # Wait for completion
            process.wait()
            self.progress_queue.put(100)
            
            # Rescan apps
            self.scan_all_apps()
            
            self.log_operation(f"Installed: {os.path.basename(installer_path)}")
            return {'success': True, 'message': f'Installation completed'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def uninstall_application(self, app_name, prefix_name=None):
        """Feature 22: Uninstall application"""
        try:
            # Find application
            app_to_remove = None
            for app in self.installed_apps:
                if app['name'] == app_name:
                    app_to_remove = app
                    break
            
            if not app_to_remove:
                return {'success': False, 'message': 'Application not found'}
            
            # Remove directory
            shutil.rmtree(app_to_remove['path'])
            self.installed_apps.remove(app_to_remove)
            
            self.log_operation(f"Uninstalled: {app_name}")
            return {'success': True, 'message': f'Uninstalled: {app_name}'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def get_app_details(self, app_name):
        """Feature 23: Get application details"""
        for app in self.installed_apps:
            if app['name'] == app_name:
                details = {
                    'name': app['name'],
                    'path': app['path'],
                    'exe': app['exe'],
                    'exe_files': app.get('exe_files', []),
                    'prefix': app.get('prefix', 'default'),
                    'size': self._get_folder_size(app['path']),
                    'created': datetime.fromtimestamp(os.path.getctime(app['path'])).strftime('%Y-%m-%d %H:%M:%S'),
                    'modified': datetime.fromtimestamp(os.path.getmtime(app['path'])).strftime('%Y-%m-%d %H:%M:%S')
                }
                return {'success': True, 'details': details}
        return {'success': False, 'message': 'Application not found'}
    
    def _get_folder_size(self, folder_path):
        """Calculate folder size"""
        total_size = 0
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except:
                        pass
        except:
            pass
        return self._format_size(total_size)
    
    def _format_size(self, bytes):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} PB"
    
    def create_shortcut(self, app_name, desktop=True):
        """Feature 24: Create desktop shortcut"""
        try:
            for app in self.installed_apps:
                if app['name'] == app_name:
                    if desktop:
                        shortcut_dir = os.path.expanduser("~/Desktop")
                    else:
                        shortcut_dir = os.path.expanduser("~/.local/share/applications")
                    
                    os.makedirs(shortcut_dir, exist_ok=True)
                    
                    shortcut_path = os.path.join(shortcut_dir, f"{app_name}.desktop")
                    content = f"""[Desktop Entry]
Name={app_name}
Comment=Windows Application
Exec=wine "{app['exe']}"
Icon=wine
Terminal=false
Type=Application
Categories=Utility;
"""
                    with open(shortcut_path, 'w') as f:
                        f.write(content)
                    
                    os.chmod(shortcut_path, 0o755)
                    
                    self.log_operation(f"Created shortcut for: {app_name}")
                    return {'success': True, 'message': f'Shortcut created: {shortcut_path}'}
            
            return {'success': False, 'message': 'Application not found'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def export_app_list(self, output_file):
        """Feature 25: Export application list"""
        try:
            app_data = []
            for app in self.installed_apps:
                app_data.append({
                    'name': app['name'],
                    'path': app['path'],
                    'exe': app['exe'],
                    'prefix': app.get('prefix', 'default')
                })
            
            with open(output_file, 'w') as f:
                json.dump(app_data, f, indent=2)
            
            return {'success': True, 'message': f'Exported to {output_file}'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def import_app_list(self, input_file):
        """Feature 26: Import application list"""
        try:
            with open(input_file, 'r') as f:
                app_data = json.load(f)
            
            # Scan for these apps
            for app_info in app_data:
                if os.path.exists(app_info['path']):
                    self.installed_apps.append(app_info)
            
            self.log_operation(f"Imported {len(app_data)} applications")
            return {'success': True, 'message': f'Imported {len(app_data)} applications'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def batch_run_apps(self, app_list):
        """Feature 27: Run multiple applications"""
        results = []
        for app_name in app_list:
            for app in self.installed_apps:
                if app['name'] == app_name:
                    result = self.run_application(app['exe'], app.get('prefix'))
                    results.append(result)
                    break
        return results
    
    # === WINETRICKS (10 features) ===
    
    def install_winetricks(self):
        """Feature 28: Install Winetricks"""
        try:
            self.progress_queue.put(10)
            subprocess.run(['sudo', 'wget', '-O', '/usr/local/bin/winetricks',
                          'https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks'], 
                         check=True)
            self.progress_queue.put(50)
            subprocess.run(['sudo', 'chmod', '+x', '/usr/local/bin/winetricks'], check=True)
            self.progress_queue.put(100)
            
            self.log_operation("Installed Winetricks")
            return {'success': True, 'message': 'Winetricks installed successfully'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def run_winetricks_gui(self, prefix_name=None):
        """Feature 29: Open Winetricks GUI"""
        try:
            env = os.environ.copy()
            if prefix_name:
                for prefix in self.wine_prefixes:
                    if prefix['name'] == prefix_name:
                        env['WINEPREFIX'] = prefix['path']
                        break
            
            subprocess.Popen(['winetricks'], env=env)
            self.log_operation("Launched Winetricks GUI")
            return {'success': True, 'message': 'Winetricks GUI launched'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def install_component_via_winetricks(self, component, prefix_name=None):
        """Feature 30: Install component via Winetricks"""
        try:
            env = os.environ.copy()
            if prefix_name:
                for prefix in self.wine_prefixes:
                    if prefix['name'] == prefix_name:
                        env['WINEPREFIX'] = prefix['path']
                        break
            
            # Show progress
            self.progress_queue.put(20)
            
            cmd = ['winetricks', component]
            process = subprocess.Popen(cmd, env=env)
            
            # Wait for completion
            process.wait()
            self.progress_queue.put(100)
            
            self.log_operation(f"Installed {component} via Winetricks")
            return {'success': True, 'message': f'{component} installed successfully'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def install_dotnet48(self, prefix_name=None):
        """Feature 31: Install .NET 4.8"""
        return self.install_component_via_winetricks('dotnet48', prefix_name)
    
    def install_vcrun2019(self, prefix_name=None):
        """Feature 32: Install Visual C++ 2019"""
        return self.install_component_via_winetricks('vcrun2019', prefix_name)
    
    def install_directx(self, prefix_name=None):
        """Feature 33: Install DirectX"""
        return self.install_component_via_winetricks('directx9', prefix_name)
    
    def install_corefonts(self, prefix_name=None):
        """Feature 34: Install core fonts"""
        return self.install_component_via_winetricks('corefonts', prefix_name)
    
    def install_all(self, prefix_name=None):
        """Feature 35: Install all common components"""
        components = ['dotnet48', 'vcrun2019', 'vcrun2017', 'vcrun2015', 
                     'corefonts', 'directx9']
        
        results = []
        for component in components:
            result = self.install_component_via_winetricks(component, prefix_name)
            results.append(result)
        
        return {'success': True, 'message': f'Installed {len(components)} components'}
    
    def list_winetricks_components(self):
        """Feature 36: List available components"""
        try:
            result = subprocess.run(['winetricks', 'list'], capture_output=True, text=True)
            return {'success': True, 'message': result.stdout}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    # === PLAYONLINUX (5 features) ===
    
    def install_playonlinux(self):
        """Feature 37: Install PlayOnLinux"""
        try:
            self.progress_queue.put(10)
            subprocess.run(['sudo', 'apt', 'install', '-y', 'playonlinux'], check=True)
            self.progress_queue.put(100)
            
            self.log_operation("Installed PlayOnLinux")
            return {'success': True, 'message': 'PlayOnLinux installed successfully'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def run_playonlinux(self):
        """Feature 38: Launch PlayOnLinux"""
        try:
            subprocess.Popen(['playonlinux'])
            self.log_operation("Launched PlayOnLinux")
            return {'success': True, 'message': 'PlayOnLinux launched'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def install_app_playonlinux(self, app_name):
        """Feature 39: Install app via PlayOnLinux"""
        try:
            cmd = ['playonlinux', '--install', app_name]
            process = subprocess.Popen(cmd)
            process.wait()
            
            self.log_operation(f"Installed {app_name} via PlayOnLinux")
            return {'success': True, 'message': f'Installed {app_name}'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def list_playonlinux_apps(self):
        """Feature 40: List available PlayOnLinux apps"""
        try:
            result = subprocess.run(['playonlinux', '--list'], capture_output=True, text=True)
            return {'success': True, 'message': result.stdout}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def update_playonlinux(self):
        """Feature 41: Update PlayOnLinux"""
        try:
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            subprocess.run(['sudo', 'apt', 'upgrade', '-y', 'playonlinux'], check=True)
            self.log_operation("Updated PlayOnLinux")
            return {'success': True, 'message': 'PlayOnLinux updated'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    # === SYSTEM & UTILITY (9 features) ===
    
    def get_system_info(self):
        """Feature 42: Get system information"""
        info = {
            'os': platform.system(),
            'os_version': platform.release(),
            'architecture': platform.machine(),
            'python_version': platform.python_version(),
            'wine_version': self.get_wine_version(),
            'prefixes_count': len(self.wine_prefixes),
            'apps_count': len(self.installed_apps),
            'wine_installed': self.check_wine_installed()
        }
        return info
    
    def cleanup_prefix(self, prefix_name=None):
        """Feature 43: Cleanup Wine prefix"""
        try:
            env = os.environ.copy()
            if prefix_name:
                for prefix in self.wine_prefixes:
                    if prefix['name'] == prefix_name:
                        env['WINEPREFIX'] = prefix['path']
                        break
            
            # Clean temp files
            temp_dir = os.path.join(env.get('WINEPREFIX', '~/.wine'), 'drive_c', 'windows', 'temp')
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                os.makedirs(temp_dir)
            
            self.log_operation("Cleaned prefix")
            return {'success': True, 'message': 'Prefix cleaned'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def reset_prefix(self, prefix_name=None):
        """Feature 44: Reset Wine prefix"""
        try:
            prefix_path = None
            if prefix_name:
                for prefix in self.wine_prefixes:
                    if prefix['name'] == prefix_name:
                        prefix_path = prefix['path']
                        break
            else:
                prefix_path = self.settings['wine_prefix']
            
            if not prefix_path or not os.path.exists(prefix_path):
                return {'success': False, 'message': 'Prefix not found'}
            
            # Backup first
            backup_path = f"{prefix_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copytree(prefix_path, backup_path)
            
            # Reset
            shutil.rmtree(prefix_path)
            os.makedirs(prefix_path)
            
            env = os.environ.copy()
            env['WINEPREFIX'] = prefix_path
            subprocess.run(['wineboot', '--init'], env=env, check=True)
            
            self.log_operation(f"Reset prefix: {prefix_name or 'default'}")
            return {'success': True, 'message': 'Prefix reset successfully'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def debug_prefix(self, prefix_name=None):
        """Feature 45: Debug Wine prefix"""
        try:
            env = os.environ.copy()
            if prefix_name:
                for prefix in self.wine_prefixes:
                    if prefix['name'] == prefix_name:
                        env['WINEPREFIX'] = prefix['path']
                        break
            
            # Collect debug info
            debug_info = {
                'prefix': prefix_name or 'default',
                'wine_version': self.get_wine_version(),
                'env': dict(env),
                'prefix_path': env.get('WINEPREFIX', '~/.wine')
            }
            
            # Check registry
            system_reg = os.path.join(env.get('WINEPREFIX', '~/.wine'), 'system.reg')
            if os.path.exists(system_reg):
                with open(system_reg, 'r') as f:
                    debug_info['registry_size'] = os.path.getsize(system_reg)
            
            self.log_operation(f"Debugged prefix: {prefix_name or 'default'}")
            return {'success': True, 'debug_info': debug_info}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def monitor_processes(self):
        """Feature 46: Monitor Wine processes"""
        try:
            wine_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'wine' in proc.info['name'].lower():
                        wine_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        })
                except:
                    pass
            return {'success': True, 'processes': wine_processes}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def kill_wine_processes(self):
        """Feature 47: Kill all Wine processes"""
        try:
            killed = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'wine' in proc.info['name'].lower():
                        proc.kill()
                        killed.append(proc.info['pid'])
                except:
                    pass
            
            self.log_operation(f"Killed {len(killed)} Wine processes")
            return {'success': True, 'message': f'Killed {len(killed)} processes'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def log_operation(self, operation):
        """Feature 48: Log operations"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.operations_log.append(f"[{timestamp}] {operation}")
        if len(self.operations_log) > self.settings.get('max_log_size', 1000):
            self.operations_log = self.operations_log[-self.settings['max_log_size']:]
    
    def export_logs(self, output_file):
        """Feature 49: Export logs"""
        try:
            with open(output_file, 'w') as f:
                for entry in self.operations_log:
                    f.write(entry + '\n')
            return {'success': True, 'message': f'Logs exported to {output_file}'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def clear_logs(self):
        """Feature 50: Clear logs"""
        self.operations_log = []
        return {'success': True, 'message': 'Logs cleared'}


class UltimateWindowsGUI:
    """Ultimate GUI for Windows Tools Manager"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Ultimate Windows Tools Manager Pro - 50+ Features")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e1e2e')
        
        self.manager = UltimateWindowsManager()
        self.current_progress = 0
        self.progress_window = None
        self.progress_bar = None
        self.progress_label = None
        
        # Initialize status_bar first
        self.status_bar = None
        self.status_text = None
        self.status_indicator = None
        self.stats_label = None
        self.dashboard_labels = {}
        
        self.setup_ui()
        self.refresh_data()
        
        # Start auto-scan
        if self.manager.settings.get('auto_scan_apps', True):
            self.root.after(5000, self.scan_apps_async)
    
    def setup_ui(self):
        # Main container
        main = tk.Frame(self.root, bg='#1e1e2e')
        main.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Header
        header = tk.Frame(main, bg='#1e1e2e')
        header.pack(fill='x', pady=(0, 10))
        
        title = tk.Label(header, text="🍷 Ultimate Windows Tools Manager-created by Allin Isla MInde", 
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
        
        # Notebook for tabs
        notebook = ttk.Notebook(main)
        notebook.pack(fill='both', expand=True)
        
        # Tab 1: Dashboard
        dashboard_tab = tk.Frame(notebook, bg='#1e1e2e')
        notebook.add(dashboard_tab, text='📊 Dashboard')
        self.create_dashboard_tab(dashboard_tab)
        
        # Tab 2: Wine Applications
        apps_tab = tk.Frame(notebook, bg='#1e1e2e')
        notebook.add(apps_tab, text='📦 Wine Apps')
        self.create_apps_tab(apps_tab)
        
        # Tab 3: Prefixes
        prefix_tab = tk.Frame(notebook, bg='#1e1e2e')
        notebook.add(prefix_tab, text='📁 Prefixes')
        self.create_prefix_tab(prefix_tab)
        
        # Tab 4: Wine Management
        wine_tab = tk.Frame(notebook, bg='#1e1e2e')
        notebook.add(wine_tab, text='🍷 Wine')
        self.create_wine_tab(wine_tab)
        
        # Tab 5: Winetricks
        winetricks_tab = tk.Frame(notebook, bg='#1e1e2e')
        notebook.add(winetricks_tab, text='📦 Winetricks')
        self.create_winetricks_tab(winetricks_tab)
        
        # Tab 6: PlayOnLinux
        pol_tab = tk.Frame(notebook, bg='#1e1e2e')
        notebook.add(pol_tab, text='🎮 PlayOnLinux')
        self.create_playonlinux_tab(pol_tab)
        
        # Tab 7: System
        system_tab = tk.Frame(notebook, bg='#1e1e2e')
        notebook.add(system_tab, text='⚙️ System')
        self.create_system_tab(system_tab)
        
        # Tab 8: Log
        log_tab = tk.Frame(notebook, bg='#1e1e2e')
        notebook.add(log_tab, text='📜 Log')
        self.create_log_tab(log_tab)
        
        # Status bar - create after tabs
        status_frame = tk.Frame(main, bg='#313244')
        status_frame.pack(side='bottom', fill='x', pady=(10, 0))
        
        self.status_bar = tk.Label(status_frame, text="Ready", 
                                   bg='#313244', fg='#cdd6f4',
                                   anchor='w', padx=15,
                                   font=('Helvetica', 10))
        self.status_bar.pack(side='left', fill='x', expand=True)
        
        # Progress bar in status
        self.status_progress = ttk.Progressbar(status_frame, mode='determinate',
                                              length=150, value=0)
        self.status_progress.pack(side='right', padx=10)
    
    def create_dashboard_tab(self, parent):
        """Dashboard tab"""
        frame = tk.Frame(parent, bg='#1e1e2e')
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Stats cards
        cards_frame = tk.Frame(frame, bg='#1e1e2e')
        cards_frame.pack(fill='x', pady=(0, 20))
        
        stats = [
            ("🍷 Wine", self.manager.get_wine_version() or "Not installed"),
            ("📦 Apps", "0"),
            ("📁 Prefixes", "0"),
            ("🔧 Features", "50+")
        ]
        
        for i, (label, value) in enumerate(stats):
            card = tk.Frame(cards_frame, bg='#313244', relief='flat', bd=1)
            card.grid(row=0, column=i, padx=10, sticky='ew')
            
            tk.Label(card, text=label, font=('Helvetica', 14),
                    fg='#cdd6f4', bg='#313244').pack(pady=(10, 0))
            
            label_widget = tk.Label(card, text=value, 
                                   font=('Helvetica', 24, 'bold'),
                                   fg='#89b4fa', bg='#313244')
            label_widget.pack(pady=(5, 10))
            self.dashboard_labels[label] = label_widget
        
        cards_frame.grid_columnconfigure(0, weight=1)
        cards_frame.grid_columnconfigure(1, weight=1)
        cards_frame.grid_columnconfigure(2, weight=1)
        cards_frame.grid_columnconfigure(3, weight=1)
        
        # Quick actions
        quick_frame = tk.LabelFrame(frame, text="⚡ Quick Actions", 
                                   bg='#1e1e2e', fg='#cdd6f4')
        quick_frame.pack(fill='x', pady=10)
        
        actions = [
            ("▶️ Run App", self.run_application_dialog),
            ("📦 Install App", self.install_app_dialog),
            ("🔧 Wine Config", self.open_winecfg),
            ("📦 Winetricks", self.open_winetricks),
            ("🎮 PlayOnLinux", self.open_playonlinux),
            ("🔄 Scan Apps", self.scan_apps_async),
        ]
        
        for i, (text, command) in enumerate(actions):
            btn = tk.Button(quick_frame, text=text, command=command,
                           bg='#89b4fa', fg='white',
                           font=('Helvetica', 11),
                           padx=20, pady=10, relief='flat')
            btn.grid(row=i//3, column=i%3, padx=5, pady=5, sticky='ew')
        
        quick_frame.grid_columnconfigure(0, weight=1)
        quick_frame.grid_columnconfigure(1, weight=1)
        quick_frame.grid_columnconfigure(2, weight=1)
        
        # System info
        sys_frame = tk.LabelFrame(frame, text="System Information", 
                                 bg='#1e1e2e', fg='#cdd6f4')
        sys_frame.pack(fill='both', expand=True)
        
        self.sys_info = scrolledtext.ScrolledText(sys_frame, height=6,
                                                  bg='#1e1e2e', fg='#cdd6f4',
                                                  font=('Monospace', 10))
        self.sys_info.pack(fill='both', expand=True, padx=5, pady=5)
    
    def create_apps_tab(self, parent):
        """Applications tab with icons and progress"""
        frame = tk.Frame(parent, bg='#1e1e2e')
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Toolbar
        toolbar = tk.Frame(frame, bg='#1e1e2e')
        toolbar.pack(fill='x', pady=(0, 10))
        
        tk.Button(toolbar, text="🔄 Scan Apps", command=self.scan_apps_async,
                 bg='#89b4fa', fg='white',
                 font=('Helvetica', 11, 'bold'),
                 padx=15, pady=8, relief='flat').pack(side='left', padx=2)
        
        tk.Button(toolbar, text="▶️ Run", command=self.run_application_dialog,
                 bg='#a6e3a1', fg='#1e1e2e',
                 font=('Helvetica', 11, 'bold'),
                 padx=15, pady=8, relief='flat').pack(side='left', padx=2)
        
        tk.Button(toolbar, text="📦 Install", command=self.install_app_dialog,
                 bg='#89b4fa', fg='white',
                 font=('Helvetica', 11, 'bold'),
                 padx=15, pady=8, relief='flat').pack(side='left', padx=2)
        
        tk.Button(toolbar, text="🗑️ Uninstall", command=self.uninstall_app,
                 bg='#f38ba8', fg='white',
                 font=('Helvetica', 11, 'bold'),
                 padx=15, pady=8, relief='flat').pack(side='left', padx=2)
        
        tk.Button(toolbar, text="🔍 Details", command=self.show_app_details,
                 bg='#f9e2af', fg='#1e1e2e',
                 font=('Helvetica', 11, 'bold'),
                 padx=15, pady=8, relief='flat').pack(side='left', padx=2)
        
        tk.Button(toolbar, text="📊 Export", command=self.export_apps,
                 bg='#f9e2af', fg='#1e1e2e',
                 font=('Helvetica', 11, 'bold'),
                 padx=15, pady=8, relief='flat').pack(side='left', padx=2)
        
        # Apps list with icons
        list_frame = tk.Frame(frame, bg='#313244')
        list_frame.pack(fill='both', expand=True)
        
        # Treeview with columns
        columns = ('Icon', 'Application', 'Prefix', 'Path', 'Size')
        self.apps_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=20)
        
        self.apps_tree.heading('Icon', text='')
        self.apps_tree.heading('Application', text='Application')
        self.apps_tree.heading('Prefix', text='Prefix')
        self.apps_tree.heading('Path', text='Path')
        self.apps_tree.heading('Size', text='Size')
        
        self.apps_tree.column('Icon', width=40, anchor='center')
        self.apps_tree.column('Application', width=200)
        self.apps_tree.column('Prefix', width=100)
        self.apps_tree.column('Path', width=300)
        self.apps_tree.column('Size', width=80)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', 
                                 command=self.apps_tree.yview)
        self.apps_tree.configure(yscrollcommand=scrollbar.set)
        
        self.apps_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Double-click to run
        self.apps_tree.bind('<Double-Button-1>', self.on_app_double_click)
        
        # Right-click menu
        self.apps_menu = tk.Menu(self.root, tearoff=0, bg='#313244', fg='#cdd6f4')
        self.apps_menu.add_command(label="▶️ Run", command=self.run_selected_app)
        self.apps_menu.add_command(label="🔍 Details", command=self.show_app_details)
        self.apps_menu.add_command(label="📌 Create Shortcut", command=self.create_shortcut)
        self.apps_menu.add_separator()
        self.apps_menu.add_command(label="🗑️ Uninstall", command=self.uninstall_app)
        
        self.apps_tree.bind('<Button-3>', self.show_apps_menu)
        
        # Don't scan here - will be called after setup
    
    def create_prefix_tab(self, parent):
        """Prefixes management tab"""
        frame = tk.Frame(parent, bg='#1e1e2e')
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Toolbar
        toolbar = tk.Frame(frame, bg='#1e1e2e')
        toolbar.pack(fill='x', pady=(0, 10))
        
        tk.Button(toolbar, text="➕ Create", command=self.create_prefix,
                 bg='#a6e3a1', fg='#1e1e2e',
                 font=('Helvetica', 11, 'bold'),
                 padx=15, pady=8, relief='flat').pack(side='left', padx=2)
        
        tk.Button(toolbar, text="🗑️ Delete", command=self.delete_prefix,
                 bg='#f38ba8', fg='white',
                 font=('Helvetica', 11, 'bold'),
                 padx=15, pady=8, relief='flat').pack(side='left', padx=2)
        
        tk.Button(toolbar, text="💾 Backup", command=self.backup_prefix,
                 bg='#89b4fa', fg='white',
                 font=('Helvetica', 11, 'bold'),
                 padx=15, pady=8, relief='flat').pack(side='left', padx=2)
        
        tk.Button(toolbar, text="🔄 Refresh", command=self.refresh_prefixes,
                 bg='#89b4fa', fg='white',
                 font=('Helvetica', 11, 'bold'),
                 padx=15, pady=8, relief='flat').pack(side='left', padx=2)
        
        # Prefix list
        list_frame = tk.Frame(frame, bg='#313244')
        list_frame.pack(fill='both', expand=True)
        
        columns = ('Name', 'Path', 'Architecture', 'Wine Version', 'Apps')
        self.prefix_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        for col in columns:
            self.prefix_tree.heading(col, text=col)
            self.prefix_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', 
                                 command=self.prefix_tree.yview)
        self.prefix_tree.configure(yscrollcommand=scrollbar.set)
        
        self.prefix_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.prefix_tree.bind('<Double-Button-1>', self.on_prefix_double_click)
        
        self.refresh_prefixes()
    
    def create_wine_tab(self, parent):
        """Wine management tab"""
        frame = tk.Frame(parent, bg='#1e1e2e')
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Status
        status_frame = tk.LabelFrame(frame, text="Wine Status", 
                                    bg='#1e1e2e', fg='#cdd6f4')
        status_frame.pack(fill='x', pady=(0, 10))
        
        self.wine_status_label = tk.Label(status_frame, 
                                          text="Checking Wine...",
                                          font=('Helvetica', 12),
                                          fg='#cdd6f4', bg='#1e1e2e')
        self.wine_status_label.pack(pady=10)
        
        # Actions
        actions_frame = tk.LabelFrame(frame, text="Actions", 
                                     bg='#1e1e2e', fg='#cdd6f4')
        actions_frame.pack(fill='x', pady=10)
        
        actions = [
            ("🍷 Install Stable", self.install_wine_stable),
            ("🍷 Install Staging", self.install_wine_staging),
            ("🔄 Update Wine", self.update_wine),
            ("🔧 Configure", self.open_winecfg),
            ("📝 Registry", self.open_regedit),
            ("📁 Explorer", self.open_explorer),
            ("📊 Task Manager", self.open_taskmanager),
            ("🔄 Control Panel", self.open_controlpanel),
        ]
        
        for i, (text, command) in enumerate(actions):
            btn = tk.Button(actions_frame, text=text, command=command,
                           bg='#89b4fa', fg='white',
                           font=('Helvetica', 11),
                           padx=15, pady=8, relief='flat')
            btn.grid(row=i//3, column=i%3, padx=5, pady=5, sticky='ew')
        
        actions_frame.grid_columnconfigure(0, weight=1)
        actions_frame.grid_columnconfigure(1, weight=1)
        actions_frame.grid_columnconfigure(2, weight=1)
    
    def create_winetricks_tab(self, parent):
        """Winetricks management tab"""
        frame = tk.Frame(parent, bg='#1e1e2e')
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Toolbar
        toolbar = tk.Frame(frame, bg='#1e1e2e')
        toolbar.pack(fill='x', pady=(0, 10))
        
        tk.Button(toolbar, text="📦 Install Winetricks", command=self.install_winetricks,
                 bg='#89b4fa', fg='white',
                 font=('Helvetica', 11, 'bold'),
                 padx=15, pady=8, relief='flat').pack(side='left', padx=2)
        
        tk.Button(toolbar, text="🔄 Open GUI", command=self.open_winetricks,
                 bg='#89b4fa', fg='white',
                 font=('Helvetica', 11, 'bold'),
                 padx=15, pady=8, relief='flat').pack(side='left', padx=2)
        
        # Components
        components_frame = tk.LabelFrame(frame, text="Common Components", 
                                       bg='#1e1e2e', fg='#cdd6f4')
        components_frame.pack(fill='both', expand=True, pady=10)
        
        components = [
            (".NET Framework 4.8", self.install_dotnet48),
            ("Visual C++ 2019", self.install_vcrun2019),
            ("DirectX 9", self.install_directx),
            ("Core Fonts", self.install_corefonts),
            ("Install All", self.install_all_components),
        ]
        
        for i, (text, command) in enumerate(components):
            btn = tk.Button(components_frame, text=text, command=command,
                           bg='#89b4fa', fg='white',
                           font=('Helvetica', 11),
                           padx=15, pady=10, relief='flat')
            btn.grid(row=i//2, column=i%2, padx=10, pady=10, sticky='ew')
        
        components_frame.grid_columnconfigure(0, weight=1)
        components_frame.grid_columnconfigure(1, weight=1)
    
    def create_playonlinux_tab(self, parent):
        """PlayOnLinux tab"""
        frame = tk.Frame(parent, bg='#1e1e2e')
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Actions
        actions_frame = tk.LabelFrame(frame, text="PlayOnLinux", 
                                    bg='#1e1e2e', fg='#cdd6f4')
        actions_frame.pack(fill='both', expand=True, pady=10)
        
        actions = [
            ("🎮 Install PlayOnLinux", self.install_playonlinux),
            ("🎮 Launch PlayOnLinux", self.open_playonlinux),
            ("🔄 Update PlayOnLinux", self.update_playonlinux),
            ("📋 List Apps", self.list_playonlinux_apps),
        ]
        
        for i, (text, command) in enumerate(actions):
            btn = tk.Button(actions_frame, text=text, command=command,
                           bg='#89b4fa', fg='white',
                           font=('Helvetica', 11),
                           padx=15, pady=15, relief='flat')
            btn.grid(row=i//2, column=i%2, padx=10, pady=10, sticky='ew')
        
        actions_frame.grid_columnconfigure(0, weight=1)
        actions_frame.grid_columnconfigure(1, weight=1)
    
    def create_system_tab(self, parent):
        """System management tab"""
        frame = tk.Frame(parent, bg='#1e1e2e')
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # System tools
        tools_frame = tk.LabelFrame(frame, text="System Tools", 
                                  bg='#1e1e2e', fg='#cdd6f4')
        tools_frame.pack(fill='both', expand=True, pady=10)
        
        tools = [
            ("🔧 Cleanup Prefix", self.cleanup_prefix),
            ("🔄 Reset Prefix", self.reset_prefix),
            ("🐛 Debug Prefix", self.debug_prefix),
            ("📊 Monitor Processes", self.monitor_processes),
            ("💀 Kill Wine Processes", self.kill_wine_processes),
            ("📋 System Info", self.show_system_info),
            ("🗑️ Clear Logs", self.clear_logs),
            ("📥 Export Logs", self.export_logs),
        ]
        
        for i, (text, command) in enumerate(tools):
            btn = tk.Button(tools_frame, text=text, command=command,
                           bg='#585b70', fg='#cdd6f4',
                           font=('Helvetica', 11),
                           padx=15, pady=12, relief='flat')
            btn.grid(row=i//2, column=i%2, padx=10, pady=10, sticky='ew')
        
        tools_frame.grid_columnconfigure(0, weight=1)
        tools_frame.grid_columnconfigure(1, weight=1)
    
    def create_log_tab(self, parent):
        """Log tab"""
        frame = tk.Frame(parent, bg='#1e1e2e')
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Toolbar
        toolbar = tk.Frame(frame, bg='#1e1e2e')
        toolbar.pack(fill='x', pady=(0, 10))
        
        tk.Button(toolbar, text="🔄 Refresh", command=self.refresh_log,
                 bg='#89b4fa', fg='white',
                 font=('Helvetica', 11, 'bold'),
                 padx=15, pady=8, relief='flat').pack(side='left', padx=2)
        
        tk.Button(toolbar, text="🗑️ Clear", command=self.clear_logs,
                 bg='#f38ba8', fg='white',
                 font=('Helvetica', 11, 'bold'),
                 padx=15, pady=8, relief='flat').pack(side='left', padx=2)
        
        tk.Button(toolbar, text="📥 Export", command=self.export_logs,
                 bg='#f9e2af', fg='#1e1e2e',
                 font=('Helvetica', 11, 'bold'),
                 padx=15, pady=8, relief='flat').pack(side='left', padx=2)
        
        # Log display
        self.log_text = scrolledtext.ScrolledText(frame,
                                                  bg='#1e1e2e', fg='#cdd6f4',
                                                  font=('Monospace', 10))
        self.log_text.pack(fill='both', expand=True)
        
        self.refresh_log()
    
    # === PROGRESS BAR FUNCTIONS ===
    
    def show_progress(self, title="Processing"):
        """Show progress window"""
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title(title)
        self.progress_window.geometry("400x150")
        self.progress_window.configure(bg='#1e1e2e')
        self.progress_window.transient(self.root)
        self.progress_window.grab_set()
        
        # Center window
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
        
        # Update progress
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
                # Close progress window after a delay
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
        self.refresh_prefixes()
        self.update_dashboard()
        self.update_system_info()
    
    def refresh_wine_status(self):
        """Refresh Wine status"""
        if self.manager.check_wine_installed():
            version = self.manager.get_wine_version()
            self.wine_status_label.config(text=f"✅ Wine is installed: {version}", fg='#a6e3a1')
            self.status_indicator.config(fg='#a6e3a1')
            self.status_text.config(text=f"Wine {version}")
        else:
            self.wine_status_label.config(text="❌ Wine is not installed", fg='#f38ba8')
            self.status_indicator.config(fg='#f38ba8')
            self.status_text.config(text="Wine not installed")
    
    def refresh_prefixes(self):
        """Refresh prefixes"""
        for item in self.prefix_tree.get_children():
            self.prefix_tree.delete(item)
        
        prefixes = self.manager.get_wine_prefixes()
        for prefix in prefixes:
            apps_count = len(prefix.get('apps', []))
            self.prefix_tree.insert('', 'end', values=(
                prefix['name'],
                prefix['path'],
                prefix['arch'],
                prefix['wine'],
                str(apps_count)
            ))
    
    def refresh_apps(self):
        """Refresh applications list"""
        for item in self.apps_tree.get_children():
            self.apps_tree.delete(item)
        
        apps = self.manager.installed_apps
        for app in apps:
            # Use generic icon
            icon_text = "📦"
            self.apps_tree.insert('', 'end', values=(
                icon_text,
                app['name'],
                app.get('prefix', 'default'),
                app['path'],
                self.manager._get_folder_size(app['path'])
            ))
    
    def refresh_log(self):
        """Refresh log"""
        self.log_text.delete('1.0', tk.END)
        for entry in self.manager.operations_log[-100:]:
            self.log_text.insert(tk.END, entry + '\n')
        self.log_text.see(tk.END)
    
    def update_dashboard(self):
        """Update dashboard"""
        info = self.manager.get_system_info()
        stats = {
            "🍷 Wine": info.get('wine_version', 'Not installed'),
            "📦 Apps": str(info.get('apps_count', 0)),
            "📁 Prefixes": str(info.get('prefixes_count', 0)),
            "🔧 Features": "50+"
        }
        
        for key, value in stats.items():
            if key in self.dashboard_labels:
                self.dashboard_labels[key].config(text=value)
        
        self.stats_label.config(text=f"Apps: {info.get('apps_count', 0)} | Prefixes: {info.get('prefixes_count', 0)}")
    
    def update_system_info(self):
        """Update system info"""
        info = self.manager.get_system_info()
        sys_text = f"""
OS: {info.get('os', 'Unknown')} {info.get('os_version', '')}
Architecture: {info.get('architecture', 'Unknown')}
Python: {info.get('python_version', 'Unknown')}
Wine: {info.get('wine_version', 'Not installed')}
Prefixes: {info.get('prefixes_count', 0)}
Installed Apps: {info.get('apps_count', 0)}
Wine Installed: {info.get('wine_installed', False)}
"""
        if hasattr(self, 'sys_info'):
            self.sys_info.delete('1.0', tk.END)
            self.sys_info.insert('1.0', sys_text)
    
    # === SCAN APPS (with progress) ===
    
    def scan_apps_async(self):
        """Scan for applications with progress"""
        if self.manager.is_scanning:
            return
        
        self.show_progress("Scanning for Windows Applications")
        if self.status_bar:
            self.status_bar.config(text="Scanning for Windows applications...")
        
        thread = threading.Thread(target=self._scan_apps_thread)
        thread.daemon = True
        thread.start()
    
    def _scan_apps_thread(self):
        """Scan apps in background"""
        def update_progress(progress, message):
            self.manager.progress_queue.put(progress)
            if message and self.status_bar:
                self.status_bar.config(text=message)
        
        self.manager.scan_all_apps(callback=update_progress)
        
        self.root.after(0, self._scan_complete)
    
    def _scan_complete(self):
        """Called when scan is complete"""
        self.manager.progress_queue.put(100)
        self.refresh_apps()
        self.refresh_prefixes()
        self.update_dashboard()
        if self.status_bar:
            self.status_bar.config(text=f"Found {len(self.manager.installed_apps)} applications")
        self.close_progress()
    
    # === APP OPERATIONS ===
    
    def on_app_double_click(self, event):
        """Handle double-click on app"""
        self.run_selected_app()
    
    def run_selected_app(self):
        """Run selected application"""
        selection = self.apps_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Select an application first")
            return
        
        values = self.apps_tree.item(selection[0])['values']
        if len(values) < 4:
            return
        
        app_name = values[1]
        prefix = values[2]
        
        for app in self.manager.installed_apps:
            if app['name'] == app_name:
                self.show_progress(f"Running {app_name}")
                result = self.manager.run_application(app['exe'], prefix)
                self.root.after(0, lambda: self.show_result(result))
                self.close_progress()
                break
    
    def run_application_dialog(self):
        """Run application via dialog"""
        # Let user select EXE
        exe_path = filedialog.askopenfilename(
            title="Select Windows executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if not exe_path:
            return
        
        # Select prefix
        prefix_name = None
        if self.prefix_tree.selection():
            values = self.prefix_tree.item(self.prefix_tree.selection()[0])['values']
            if values:
                prefix_name = values[0]
        
        self.show_progress(f"Running {os.path.basename(exe_path)}")
        result = self.manager.run_application(exe_path, prefix_name)
        self.root.after(0, lambda: self.show_result(result))
        self.close_progress()
    
    def install_app_dialog(self):
        """Install application via dialog"""
        installer = filedialog.askopenfilename(
            title="Select Windows installer",
            filetypes=[("Installer files", "*.exe *.msi"), ("All files", "*.*")]
        )
        if not installer:
            return
        
        # Select prefix
        prefix_name = None
        if self.prefix_tree.selection():
            values = self.prefix_tree.item(self.prefix_tree.selection()[0])['values']
            if values:
                prefix_name = values[0]
        
        self.show_progress(f"Installing {os.path.basename(installer)}")
        
        thread = threading.Thread(target=self._install_app_thread, 
                                  args=(installer, prefix_name))
        thread.daemon = True
        thread.start()
    
    def _install_app_thread(self, installer, prefix_name):
        """Install app in background"""
        result = self.manager.install_application(installer, prefix_name)
        self.root.after(0, lambda: self.show_result(result))
        self.root.after(0, self.scan_apps_async)
    
    def uninstall_app(self):
        """Uninstall application"""
        selection = self.apps_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Select an application first")
            return
        
        values = self.apps_tree.item(selection[0])['values']
        if len(values) < 2:
            return
        
        app_name = values[1]
        
        if messagebox.askyesno("Confirm Uninstall", 
                              f"Uninstall {app_name}?\nThis will remove the application folder."):
            result = self.manager.uninstall_application(app_name)
            self.show_result(result)
            self.refresh_apps()
            self.update_dashboard()
    
    def show_app_details(self):
        """Show application details"""
        selection = self.apps_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Select an application first")
            return
        
        values = self.apps_tree.item(selection[0])['values']
        if len(values) < 2:
            return
        
        app_name = values[1]
        result = self.manager.get_app_details(app_name)
        
        if result['success']:
            details = result['details']
            info = f"📋 Application Details\n{'='*40}\n\n"
            info += f"Name: {details['name']}\n"
            info += f"Path: {details['path']}\n"
            info += f"Executable: {details['exe']}\n"
            info += f"Prefix: {details['prefix']}\n"
            info += f"Size: {details['size']}\n"
            info += f"Created: {details['created']}\n"
            info += f"Modified: {details['modified']}\n"
            
            if details.get('exe_files'):
                info += f"\nExecutables found:\n"
                for exe in details['exe_files'][:5]:
                    info += f"  - {os.path.basename(exe)}\n"
                if len(details['exe_files']) > 5:
                    info += f"  ... and {len(details['exe_files']) - 5} more\n"
            
            messagebox.showinfo("Application Details", info)
        else:
            messagebox.showerror("Error", result['message'])
    
    def create_shortcut(self):
        """Create desktop shortcut"""
        selection = self.apps_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Select an application first")
            return
        
        values = self.apps_tree.item(selection[0])['values']
        if len(values) < 2:
            return
        
        app_name = values[1]
        result = self.manager.create_shortcut(app_name)
        self.show_result(result)
    
    def export_apps(self):
        """Export application list"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            result = self.manager.export_app_list(file_path)
            self.show_result(result)
    
    def show_apps_menu(self, event):
        """Show context menu for apps"""
        try:
            self.apps_tree.selection_set(self.apps_tree.identify_row(event.y))
            self.apps_menu.post(event.x_root, event.y_root)
        except:
            pass
    
    # === PREFIX OPERATIONS ===
    
    def create_prefix(self):
        """Create new prefix"""
        name = simpledialog.askstring("Prefix Name", "Enter prefix name:")
        if not name:
            return
        
        arch = simpledialog.askstring("Architecture", "Architecture (win32/win64):", 
                                     initialvalue="win64")
        if arch not in ['win32', 'win64']:
            messagebox.showerror("Error", "Invalid architecture")
            return
        
        self.show_progress(f"Creating prefix {name}")
        result = self.manager.create_prefix(name, arch)
        self.root.after(0, lambda: self.show_result(result))
        self.root.after(0, self.refresh_prefixes)
        self.close_progress()
    
    def delete_prefix(self):
        """Delete prefix"""
        selection = self.prefix_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Select a prefix first")
            return
        
        values = self.prefix_tree.item(selection[0])['values']
        if not values:
            return
        
        name = values[0]
        if messagebox.askyesno("Confirm Delete", f"Delete prefix '{name}'?"):
            self.show_progress(f"Deleting prefix {name}")
            result = self.manager.delete_prefix(name)
            self.root.after(0, lambda: self.show_result(result))
            self.root.after(0, self.refresh_prefixes)
            self.root.after(0, self.update_dashboard)
            self.close_progress()
    
    def backup_prefix(self):
        """Backup prefix"""
        selection = self.prefix_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Select a prefix first")
            return
        
        values = self.prefix_tree.item(selection[0])['values']
        if not values:
            return
        
        name = values[0]
        self.show_progress(f"Backing up prefix {name}")
        result = self.manager.backup_prefix(name)
        self.root.after(0, lambda: self.show_result(result))
        self.close_progress()
    
    def on_prefix_double_click(self, event):
        """Handle double-click on prefix"""
        selection = self.prefix_tree.selection()
        if selection:
            values = self.prefix_tree.item(selection[0])['values']
            if values:
                self.manager.current_prefix = values[0]
                self.open_winecfg()
    
    # === WINE OPERATIONS ===
    
    def install_wine_stable(self):
        """Install Wine Stable with progress"""
        self.show_progress("Installing Wine Stable")
        thread = threading.Thread(target=self._install_wine_thread, args=('stable',))
        thread.daemon = True
        thread.start()
    
    def install_wine_staging(self):
        """Install Wine Staging with progress"""
        self.show_progress("Installing Wine Staging")
        thread = threading.Thread(target=self._install_wine_thread, args=('staging',))
        thread.daemon = True
        thread.start()
    
    def _install_wine_thread(self, version):
        """Install Wine in background"""
        if version == 'stable':
            result = self.manager.install_wine_stable()
        else:
            result = self.manager.install_wine_staging()
        
        self.root.after(0, lambda: self.show_result(result))
        self.root.after(0, self.refresh_wine_status)
        self.root.after(0, self.update_dashboard)
        self.close_progress()
    
    def update_wine(self):
        """Update Wine"""
        self.show_progress("Updating Wine")
        result = self.manager.update_wine()
        self.root.after(0, lambda: self.show_result(result))
        self.root.after(0, self.refresh_wine_status)
        self.close_progress()
    
    def open_winecfg(self):
        """Open Wine configuration"""
        prefix = None
        if self.prefix_tree.selection():
            values = self.prefix_tree.item(self.prefix_tree.selection()[0])['values']
            if values:
                prefix = values[0]
        
        result = self.manager.configure_wine(prefix)
        self.show_result(result)
    
    def open_regedit(self):
        """Open Registry Editor"""
        prefix = None
        if self.prefix_tree.selection():
            values = self.prefix_tree.item(self.prefix_tree.selection()[0])['values']
            if values:
                prefix = values[0]
        
        result = self.manager.run_regedit(prefix)
        self.show_result(result)
    
    def open_explorer(self):
        """Open Wine Explorer"""
        prefix = None
        if self.prefix_tree.selection():
            values = self.prefix_tree.item(self.prefix_tree.selection()[0])['values']
            if values:
                prefix = values[0]
        
        result = self.manager.run_explorer(prefix)
        self.show_result(result)
    
    def open_taskmanager(self):
        """Open Task Manager"""
        prefix = None
        if self.prefix_tree.selection():
            values = self.prefix_tree.item(self.prefix_tree.selection()[0])['values']
            if values:
                prefix = values[0]
        
        result = self.manager.run_taskmanager(prefix)
        self.show_result(result)
    
    def open_controlpanel(self):
        """Open Control Panel"""
        prefix = None
        if self.prefix_tree.selection():
            values = self.prefix_tree.item(self.prefix_tree.selection()[0])['values']
            if values:
                prefix = values[0]
        
        result = self.manager.run_controlpanel(prefix)
        self.show_result(result)
    
    # === WINETRICKS OPERATIONS ===
    
    def install_winetricks(self):
        """Install Winetricks"""
        self.show_progress("Installing Winetricks")
        result = self.manager.install_winetricks()
        self.root.after(0, lambda: self.show_result(result))
        self.close_progress()
    
    def open_winetricks(self):
        """Open Winetricks GUI"""
        prefix = None
        if self.prefix_tree.selection():
            values = self.prefix_tree.item(self.prefix_tree.selection()[0])['values']
            if values:
                prefix = values[0]
        
        result = self.manager.run_winetricks_gui(prefix)
        self.show_result(result)
    
    def install_dotnet48(self):
        """Install .NET 4.8"""
        self._install_component('dotnet48')
    
    def install_vcrun2019(self):
        """Install Visual C++ 2019"""
        self._install_component('vcrun2019')
    
    def install_directx(self):
        """Install DirectX"""
        self._install_component('directx9')
    
    def install_corefonts(self):
        """Install Core Fonts"""
        self._install_component('corefonts')
    
    def install_all_components(self):
        """Install all components"""
        self.show_progress("Installing all components")
        thread = threading.Thread(target=self._install_all_thread)
        thread.daemon = True
        thread.start()
    
    def _install_component(self, component):
        """Install component via Winetricks"""
        prefix = None
        if self.prefix_tree.selection():
            values = self.prefix_tree.item(self.prefix_tree.selection()[0])['values']
            if values:
                prefix = values[0]
        
        self.show_progress(f"Installing {component}")
        thread = threading.Thread(target=self._install_component_thread, 
                                 args=(component, prefix))
        thread.daemon = True
        thread.start()
    
    def _install_component_thread(self, component, prefix):
        """Install component in background"""
        result = self.manager.install_component_via_winetricks(component, prefix)
        self.root.after(0, lambda: self.show_result(result))
        self.close_progress()
    
    def _install_all_thread(self):
        """Install all components in background"""
        result = self.manager.install_all()
        self.root.after(0, lambda: self.show_result(result))
        self.close_progress()
    
    # === PLAYONLINUX OPERATIONS ===
    
    def install_playonlinux(self):
        """Install PlayOnLinux"""
        self.show_progress("Installing PlayOnLinux")
        result = self.manager.install_playonlinux()
        self.root.after(0, lambda: self.show_result(result))
        self.close_progress()
    
    def open_playonlinux(self):
        """Launch PlayOnLinux"""
        result = self.manager.run_playonlinux()
        self.show_result(result)
    
    def update_playonlinux(self):
        """Update PlayOnLinux"""
        self.show_progress("Updating PlayOnLinux")
        result = self.manager.update_playonlinux()
        self.root.after(0, lambda: self.show_result(result))
        self.close_progress()
    
    def list_playonlinux_apps(self):
        """List PlayOnLinux applications"""
        result = self.manager.list_playonlinux_apps()
        if result['success']:
            messagebox.showinfo("PlayOnLinux Apps", result['message'][:5000])
        else:
            messagebox.showerror("Error", result['message'])
    
    # === SYSTEM OPERATIONS ===
    
    def cleanup_prefix(self):
        """Cleanup prefix"""
        prefix = None
        if self.prefix_tree.selection():
            values = self.prefix_tree.item(self.prefix_tree.selection()[0])['values']
            if values:
                prefix = values[0]
        
        self.show_progress("Cleaning prefix")
        result = self.manager.cleanup_prefix(prefix)
        self.root.after(0, lambda: self.show_result(result))
        self.close_progress()
    
    def reset_prefix(self):
        """Reset prefix"""
        prefix = None
        if self.prefix_tree.selection():
            values = self.prefix_tree.item(self.prefix_tree.selection()[0])['values']
            if values:
                prefix = values[0]
        
        if messagebox.askyesno("Confirm Reset", "This will reset the prefix. Continue?"):
            self.show_progress("Resetting prefix")
            result = self.manager.reset_prefix(prefix)
            self.root.after(0, lambda: self.show_result(result))
            self.root.after(0, self.refresh_prefixes)
            self.close_progress()
    
    def debug_prefix(self):
        """Debug prefix"""
        prefix = None
        if self.prefix_tree.selection():
            values = self.prefix_tree.item(self.prefix_tree.selection()[0])['values']
            if values:
                prefix = values[0]
        
        result = self.manager.debug_prefix(prefix)
        if result['success']:
            debug_info = result['debug_info']
            info = f"🐛 Debug Information\n{'='*40}\n\n"
            for key, value in debug_info.items():
                info += f"{key}: {value}\n"
            messagebox.showinfo("Debug Info", info)
        else:
            messagebox.showerror("Error", result['message'])
    
    def monitor_processes(self):
        """Monitor Wine processes"""
        result = self.manager.monitor_processes()
        if result['success']:
            processes = result['processes']
            if processes:
                info = f"📊 Wine Processes ({len(processes)})\n{'='*40}\n\n"
                for proc in processes:
                    info += f"PID: {proc['pid']}\n"
                    info += f"Name: {proc['name']}\n"
                    info += f"Command: {proc['cmdline'][:100]}\n\n"
                messagebox.showinfo("Processes", info)
            else:
                messagebox.showinfo("Processes", "No Wine processes found")
        else:
            messagebox.showerror("Error", result['message'])
    
    def kill_wine_processes(self):
        """Kill all Wine processes"""
        if messagebox.askyesno("Confirm Kill", "Kill all Wine processes?"):
            result = self.manager.kill_wine_processes()
            self.show_result(result)
    
    def show_system_info(self):
        """Show system information"""
        info = self.manager.get_system_info()
        info_text = f"📊 System Information\n{'='*40}\n\n"
        for key, value in info.items():
            info_text += f"{key}: {value}\n"
        messagebox.showinfo("System Info", info_text)
    
    def clear_logs(self):
        """Clear logs"""
        if messagebox.askyesno("Confirm Clear", "Clear all logs?"):
            result = self.manager.clear_logs()
            self.show_result(result)
            self.refresh_log()
    
    def export_logs(self):
        """Export logs"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            result = self.manager.export_logs(file_path)
            self.show_result(result)
    
    # === UTILITY ===
    
    def show_result(self, result):
        """Show operation result"""
        if result['success']:
            messagebox.showinfo("✅ Success", result['message'])
            if self.status_bar:
                self.status_bar.config(text=result['message'])
        else:
            messagebox.showerror("❌ Error", result['message'])
            if self.status_bar:
                self.status_bar.config(text=f"Error: {result['message']}")
        
        self.refresh_log()
        self.update_dashboard()


def main():
    # Check for required packages
    required_packages = ['psutil']
    for pkg in required_packages:
        try:
            __import__(pkg)
        except ImportError:
            print(f"📦 Installing {pkg}...")
            subprocess.run(['pip3', 'install', pkg], check=True)
    
    root = tk.Tk()
    app = UltimateWindowsGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
