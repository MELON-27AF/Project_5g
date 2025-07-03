#!/usr/bin/env python3
"""
5G Network Emulator GUI
Aplikasi untuk membuat dan mengkonfigurasi topologi jaringan 5G secara visual
dengan drag and drop interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import math
import subprocess
import threading
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import os

@dataclass
class Component:
    """Data class untuk komponen jaringan 5G"""
    id: str
    type: str
    name: str
    x: float
    y: float
    config: Dict
    connections: List[str]

class ComponentLibrary:
    """Library komponen 5G yang tersedia"""
    
    COMPONENTS = {
        # Core Network Components
        'AMF': {
            'name': 'Access and Mobility Management Function',
            'color': '#FF6B6B',
            'icon': '🏢',
            'default_config': {
                'plmn_id': {'mcc': '999', 'mnc': '70'},
                'port': 7777,
                'tai': {'tac': 1}
            }
        },
        'SMF': {
            'name': 'Session Management Function', 
            'color': '#4ECDC4',
            'icon': '⚙️',
            'default_config': {
                'port': 7777,
                'pfcp_port': 8805
            }
        },
        'UPF': {
            'name': 'User Plane Function',
            'color': '#45B7D1',
            'icon': '📡',
            'default_config': {
                'pfcp_port': 8805,
                'gtpu_port': 2152
            }
        },
        'NRF': {
            'name': 'Network Repository Function',
            'color': '#96CEB4',
            'icon': '📋',
            'default_config': {
                'port': 7777
            }
        },
        'UDM': {
            'name': 'Unified Data Management',
            'color': '#FFEAA7',
            'icon': '💾',
            'default_config': {
                'port': 7777
            }
        },
        'UDR': {
            'name': 'Unified Data Repository',
            'color': '#DDA0DD',
            'icon': '🗄️',
            'default_config': {
                'port': 7777
            }
        },
        'PCF': {
            'name': 'Policy Control Function',
            'color': '#FFB347',
            'icon': '📏',
            'default_config': {
                'port': 7777
            }
        },
        'AUSF': {
            'name': 'Authentication Server Function',
            'color': '#F0A0A0',
            'icon': '🔐',
            'default_config': {
                'port': 7777
            }
        },
        # RAN Components
        'gNB': {
            'name': '5G NodeB (Base Station)',
            'color': '#8E44AD',
            'icon': '📶',
            'default_config': {
                'mcc': '999',
                'mnc': '70',
                'nci': 1,
                'tac': 1
            }
        },
        'UE': {
            'name': 'User Equipment',
            'color': '#E74C3C',
            'icon': '📱',
            'default_config': {
                'imsi': '999700000000001',
                'key': '465B5CE8B199B49FAA5F0A2EE238A6BC'
            }
        },
        # Network Components
        'Switch': {
            'name': 'Network Switch',
            'color': '#34495E',
            'icon': '🔀',
            'default_config': {
                'dpid': 1
            }
        },
        'Router': {
            'name': 'Network Router',
            'color': '#2C3E50',
            'icon': '🌐',
            'default_config': {
                'ip': '192.168.1.1'
            }
        }
    }

class DragDropCanvas:
    """Canvas untuk drag and drop komponen"""
    
    def __init__(self, parent):
        self.parent = parent
        self.canvas = tk.Canvas(parent, bg='white', width=1200, height=800)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Data structures
        self.components: Dict[str, Component] = {}
        self.component_objects: Dict[str, int] = {}  # component_id -> canvas_object_id
        self.connections: List[Tuple[str, str]] = []
        self.connection_objects: List[int] = []
        
        # Interaction state
        self.selected_component = None
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.connection_mode = False
        self.connection_start = None
        
        # Bind events
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        
    def add_component(self, component_type: str, x: float, y: float) -> str:
        """Menambahkan komponen baru ke canvas"""
        component_id = f"{component_type}_{len([c for c in self.components.values() if c.type == component_type]) + 1}"
        
        component = Component(
            id=component_id,
            type=component_type,
            name=component_id,
            x=x,
            y=y,
            config=ComponentLibrary.COMPONENTS[component_type]['default_config'].copy(),
            connections=[]
        )
        
        self.components[component_id] = component
        self._draw_component(component)
        return component_id
    
    def _draw_component(self, component: Component):
        """Menggambar komponen di canvas"""
        comp_info = ComponentLibrary.COMPONENTS[component.type]
        
        # Draw component box
        x, y = component.x, component.y
        box_id = self.canvas.create_rectangle(
            x - 40, y - 30, x + 40, y + 30,
            fill=comp_info['color'],
            outline='black',
            width=2,
            tags=('component', component.id)
        )
        
        # Draw icon and label
        icon_id = self.canvas.create_text(
            x, y - 10,
            text=comp_info['icon'],
            font=('Arial', 16),
            tags=('component', component.id)
        )
        
        text_id = self.canvas.create_text(
            x, y + 10,
            text=component.name,
            font=('Arial', 8),
            tags=('component', component.id)
        )
        
        self.component_objects[component.id] = box_id
        
    def on_click(self, event):
        """Handle klik mouse"""
        clicked_items = self.canvas.find_overlapping(event.x-1, event.y-1, event.x+1, event.y+1)
        
        if self.connection_mode:
            self._handle_connection_click(event, clicked_items)
        else:
            self._handle_normal_click(event, clicked_items)
    
    def _handle_connection_click(self, event, clicked_items):
        """Handle klik dalam mode koneksi"""
        component_clicked = None
        for item in clicked_items:
            tags = self.canvas.gettags(item)
            if 'component' in tags:
                component_clicked = tags[1]  # component_id
                break
        
        if component_clicked:
            if self.connection_start is None:
                self.connection_start = component_clicked
                messagebox.showinfo("Info", f"Pilih komponen tujuan untuk menghubungkan dengan {component_clicked}")
            else:
                if component_clicked != self.connection_start:
                    self.create_connection(self.connection_start, component_clicked)
                    self.connection_start = None
                    self.toggle_connection_mode()
                else:
                    messagebox.showwarning("Warning", "Tidak bisa menghubungkan komponen dengan dirinya sendiri")
    
    def _handle_normal_click(self, event, clicked_items):
        """Handle klik normal"""
        component_clicked = None
        for item in clicked_items:
            tags = self.canvas.gettags(item)
            if 'component' in tags:
                component_clicked = tags[1]  # component_id
                break
        
        if component_clicked:
            self.selected_component = component_clicked
            self.dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            # Highlight selected component
            self.canvas.itemconfig(self.component_objects[component_clicked], outline='red', width=3)
        else:
            self.deselect_all()
    
    def on_drag(self, event):
        """Handle drag mouse"""
        if self.dragging and self.selected_component:
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            
            # Move component
            items = self.canvas.find_withtag(self.selected_component)
            for item in items:
                self.canvas.move(item, dx, dy)
            
            # Update component position
            self.components[self.selected_component].x += dx
            self.components[self.selected_component].y += dy
            
            # Update connections
            self._update_connections()
            
            self.drag_start_x = event.x
            self.drag_start_y = event.y
    
    def on_release(self, event):
        """Handle release mouse"""
        self.dragging = False
    
    def on_right_click(self, event):
        """Handle klik kanan - show context menu"""
        clicked_items = self.canvas.find_overlapping(event.x-1, event.y-1, event.x+1, event.y+1)
        
        component_clicked = None
        for item in clicked_items:
            tags = self.canvas.gettags(item)
            if 'component' in tags:
                component_clicked = tags[1]
                break
        
        if component_clicked:
            self._show_context_menu(event, component_clicked)
    
    def on_double_click(self, event):
        """Handle double click - edit component"""
        clicked_items = self.canvas.find_overlapping(event.x-1, event.y-1, event.x+1, event.y+1)
        
        component_clicked = None
        for item in clicked_items:
            tags = self.canvas.gettags(item)
            if 'component' in tags:
                component_clicked = tags[1]
                break
        
        if component_clicked:
            self.edit_component(component_clicked)
    
    def _show_context_menu(self, event, component_id):
        """Menampilkan context menu"""
        context_menu = tk.Menu(self.parent, tearoff=0)
        context_menu.add_command(label="Edit", command=lambda: self.edit_component(component_id))
        context_menu.add_command(label="Delete", command=lambda: self.delete_component(component_id))
        context_menu.add_separator()
        context_menu.add_command(label="Connect", command=lambda: self.start_connection(component_id))
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def deselect_all(self):
        """Deselect semua komponen"""
        if self.selected_component:
            self.canvas.itemconfig(self.component_objects[self.selected_component], outline='black', width=2)
        self.selected_component = None
    
    def toggle_connection_mode(self):
        """Toggle mode koneksi"""
        self.connection_mode = not self.connection_mode
        if not self.connection_mode:
            self.connection_start = None
    
    def start_connection(self, component_id):
        """Mulai mode koneksi dari komponen tertentu"""
        self.connection_mode = True
        self.connection_start = component_id
        messagebox.showinfo("Info", f"Mode koneksi aktif. Pilih komponen tujuan untuk menghubungkan dengan {component_id}")
    
    def create_connection(self, source_id: str, target_id: str):
        """Membuat koneksi antara dua komponen"""
        if (source_id, target_id) not in self.connections and (target_id, source_id) not in self.connections:
            self.connections.append((source_id, target_id))
            self.components[source_id].connections.append(target_id)
            self.components[target_id].connections.append(source_id)
            self._draw_connection(source_id, target_id)
            messagebox.showinfo("Success", f"Koneksi berhasil dibuat antara {source_id} dan {target_id}")
    
    def _draw_connection(self, source_id: str, target_id: str):
        """Menggambar koneksi antara dua komponen"""
        source = self.components[source_id]
        target = self.components[target_id]
        
        line_id = self.canvas.create_line(
            source.x, source.y, target.x, target.y,
            fill='blue', width=2,
            tags=('connection', f"{source_id}-{target_id}")
        )
        
        self.connection_objects.append(line_id)
    
    def _update_connections(self):
        """Update posisi semua koneksi"""
        # Remove old connection lines
        for line_id in self.connection_objects:
            self.canvas.delete(line_id)
        self.connection_objects.clear()
        
        # Redraw all connections
        for source_id, target_id in self.connections:
            self._draw_connection(source_id, target_id)
    
    def delete_component(self, component_id: str):
        """Menghapus komponen"""
        if messagebox.askyesno("Confirm", f"Hapus komponen {component_id}?"):
            # Remove connections
            connections_to_remove = []
            for conn in self.connections:
                if component_id in conn:
                    connections_to_remove.append(conn)
            
            for conn in connections_to_remove:
                self.connections.remove(conn)
            
            # Remove from other components' connection lists
            for comp in self.components.values():
                if component_id in comp.connections:
                    comp.connections.remove(component_id)
            
            # Remove from canvas
            items = self.canvas.find_withtag(component_id)
            for item in items:
                self.canvas.delete(item)
            
            # Remove from data structures
            del self.components[component_id]
            del self.component_objects[component_id]
            
            self._update_connections()
    
    def edit_component(self, component_id: str):
        """Edit konfigurasi komponen"""
        component = self.components[component_id]
        ConfigEditor(self.parent, component, self._on_component_updated)
    
    def _on_component_updated(self, component: Component):
        """Callback ketika komponen diupdate"""
        self.components[component.id] = component
        # Redraw component with new name
        items = self.canvas.find_withtag(component.id)
        for item in items:
            self.canvas.delete(item)
        self._draw_component(component)
    
    def clear_canvas(self):
        """Membersihkan canvas"""
        self.canvas.delete("all")
        self.components.clear()
        self.component_objects.clear()
        self.connections.clear()
        self.connection_objects.clear()
        self.selected_component = None
    
    def get_topology_config(self) -> Dict:
        """Mendapatkan konfigurasi topologi"""
        return {
            'components': {cid: asdict(comp) for cid, comp in self.components.items()},
            'connections': self.connections
        }

class ConfigEditor:
    """Editor untuk konfigurasi komponen"""
    
    def __init__(self, parent, component: Component, callback):
        self.component = component
        self.callback = callback
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"Edit {component.name}")
        self.window.geometry("400x500")
        self.window.resizable(True, True)
        
        self.create_widgets()
    
    def create_widgets(self):
        """Membuat widget untuk editor"""
        # Main frame
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Component info
        info_frame = ttk.LabelFrame(main_frame, text="Component Information")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(info_frame, text=self.component.id).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(info_frame, text="Type:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(info_frame, text=self.component.type).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(info_frame, text="Name:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.name_var = tk.StringVar(value=self.component.name)
        name_entry = ttk.Entry(info_frame, textvariable=self.name_var)
        name_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)
        
        info_frame.columnconfigure(1, weight=1)
        
        # Configuration
        config_frame = ttk.LabelFrame(main_frame, text="Configuration")
        config_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Scrollable text widget for JSON config
        config_text_frame = ttk.Frame(config_frame)
        config_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.config_text = tk.Text(config_text_frame, height=15, width=50)
        scrollbar = ttk.Scrollbar(config_text_frame, orient=tk.VERTICAL, command=self.config_text.yview)
        self.config_text.configure(yscrollcommand=scrollbar.set)
        
        self.config_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load current config
        config_json = json.dumps(self.component.config, indent=2)
        self.config_text.insert(tk.END, config_json)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Save", command=self.save_config).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Reset", command=self.reset_config).pack(side=tk.LEFT)
    
    def save_config(self):
        """Menyimpan konfigurasi"""
        try:
            # Update name
            self.component.name = self.name_var.get()
            
            # Update config
            config_text = self.config_text.get(1.0, tk.END).strip()
            if config_text:
                self.component.config = json.loads(config_text)
            
            # Callback to update component
            self.callback(self.component)
            
            messagebox.showinfo("Success", "Configuration saved successfully!")
            self.window.destroy()
            
        except json.JSONDecodeError as e:
            messagebox.showerror("Error", f"Invalid JSON configuration:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving configuration:\n{str(e)}")
    
    def reset_config(self):
        """Reset konfigurasi ke default"""
        default_config = ComponentLibrary.COMPONENTS[self.component.type]['default_config']
        config_json = json.dumps(default_config, indent=2)
        
        self.config_text.delete(1.0, tk.END)
        self.config_text.insert(tk.END, config_json)

class TopologyGenerator:
    """Generator untuk membuat file konfigurasi topologi"""
    
    def __init__(self, topology_config: Dict):
        self.config = topology_config
    
    def generate_mininet_script(self) -> str:
        """Generate Mininet script"""
        script = """#!/usr/bin/env python3

from mininet.node import OVSKernelSwitch, Host
from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi

def topology():
    \"\"\"Create 5G network topology\"\"\"
    net = Mininet_wifi()
    
    info("*** Creating nodes\\n")
    
    # Components
"""
        
        # Add components
        for comp_id, comp_data in self.config['components'].items():
            comp_type = comp_data['type']
            x, y = comp_data['x'], comp_data['y']
            
            if comp_type == 'UE':
                script += f"    {comp_id.lower()} = net.addStation('{comp_id.lower()}', position='{x},{y},0')\n"
            elif comp_type == 'gNB':
                script += f"    {comp_id.lower()} = net.addAccessPoint('{comp_id.lower()}', ssid='{comp_id}-ssid', mode='g', channel='1', position='{x},{y},0')\n"
            elif comp_type in ['Switch', 'Router']:
                script += f"    {comp_id.lower()} = net.addSwitch('{comp_id.lower()}', cls=OVSKernelSwitch, position='{x},{y},0')\n"
            else:
                script += f"    {comp_id.lower()} = net.addHost('{comp_id.lower()}', position='{x},{y},0')\n"
        
        script += """
    info("*** Adding controller\\n")
    c1 = net.addController('c1')
    
    info("*** Configuring wifi nodes\\n")
    net.configureWifiNodes()
    
    info("*** Creating links\\n")
"""
        
        # Add connections
        for source_id, target_id in self.config['connections']:
            script += f"    net.addLink({source_id.lower()}, {target_id.lower()})\n"
        
        script += """
    info("*** Starting network\\n")
    net.build()
    c1.start()
    
    info("*** Running CLI\\n")
    CLI(net)
    
    info("*** Stopping network\\n")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()
"""
        
        return script
    
    def generate_docker_compose(self) -> str:
        """Generate Docker Compose file untuk 5G core"""
        compose = {
            'version': '3.8',
            'services': {}
        }
        
        # Add core network components
        for comp_id, comp_data in self.config['components'].items():
            comp_type = comp_data['type']
            
            if comp_type in ['AMF', 'SMF', 'UPF', 'NRF', 'UDM', 'UDR', 'PCF', 'AUSF']:
                service_name = comp_id.lower()
                compose['services'][service_name] = {
                    'image': f'open5gs/{comp_type.lower()}:latest',
                    'container_name': service_name,
                    'environment': comp_data['config'],
                    'networks': ['5g-network']
                }
        
        compose['networks'] = {
            '5g-network': {
                'driver': 'bridge'
            }
        }
        
        return json.dumps(compose, indent=2)

class FiveGEmulatorGUI:
    """Main application class"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("5G Network Emulator")
        self.root.geometry("1400x900")
        self.root.state('zoomed')  # Maximize window on Windows
        
        self.current_file = None
        self.create_widgets()
        self.create_menu()
        
    def create_menu(self):
        """Membuat menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_topology, accelerator="Ctrl+N")
        file_menu.add_command(label="Open", command=self.open_topology, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_topology, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As", command=self.save_topology_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Export Mininet Script", command=self.export_mininet)
        file_menu.add_command(label="Export Docker Compose", command=self.export_docker_compose)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Clear All", command=self.clear_topology)
        edit_menu.add_command(label="Connection Mode", command=self.toggle_connection_mode)
        
        # Run menu
        run_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Run", menu=run_menu)
        run_menu.add_command(label="Start Emulation", command=self.start_emulation)
        run_menu.add_command(label="Stop Emulation", command=self.stop_emulation)
        run_menu.add_command(label="Deploy to Docker", command=self.deploy_docker)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
        # Keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self.new_topology())
        self.root.bind('<Control-o>', lambda e: self.open_topology())
        self.root.bind('<Control-s>', lambda e: self.save_topology())
        self.root.bind('<Control-Shift-S>', lambda e: self.save_topology_as())
    
    def create_widgets(self):
        """Membuat widget utama"""
        # Main paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Component library
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # Component library
        ttk.Label(left_frame, text="Component Library", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Create component buttons
        components_frame = ttk.Frame(left_frame)
        components_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Core Network Components
        core_frame = ttk.LabelFrame(components_frame, text="Core Network")
        core_frame.pack(fill=tk.X, pady=(0, 5))
        
        core_components = ['AMF', 'SMF', 'UPF', 'NRF', 'UDM', 'UDR', 'PCF', 'AUSF']
        for i, comp_type in enumerate(core_components):
            comp_info = ComponentLibrary.COMPONENTS[comp_type]
            btn = tk.Button(
                core_frame, 
                text=f"{comp_info['icon']} {comp_type}",
                bg=comp_info['color'],
                command=lambda ct=comp_type: self.add_component_to_canvas(ct),
                width=12,
                font=('Arial', 8)
            )
            btn.grid(row=i//2, column=i%2, padx=2, pady=2, sticky=tk.EW)
        
        core_frame.columnconfigure(0, weight=1)
        core_frame.columnconfigure(1, weight=1)
        
        # RAN Components
        ran_frame = ttk.LabelFrame(components_frame, text="RAN")
        ran_frame.pack(fill=tk.X, pady=5)
        
        ran_components = ['gNB', 'UE']
        for i, comp_type in enumerate(ran_components):
            comp_info = ComponentLibrary.COMPONENTS[comp_type]
            btn = tk.Button(
                ran_frame,
                text=f"{comp_info['icon']} {comp_type}",
                bg=comp_info['color'],
                command=lambda ct=comp_type: self.add_component_to_canvas(ct),
                width=12,
                font=('Arial', 8)
            )
            btn.grid(row=i//2, column=i%2, padx=2, pady=2, sticky=tk.EW)
        
        ran_frame.columnconfigure(0, weight=1)
        ran_frame.columnconfigure(1, weight=1)
        
        # Network Components
        net_frame = ttk.LabelFrame(components_frame, text="Network")
        net_frame.pack(fill=tk.X, pady=5)
        
        net_components = ['Switch', 'Router']
        for i, comp_type in enumerate(net_components):
            comp_info = ComponentLibrary.COMPONENTS[comp_type]
            btn = tk.Button(
                net_frame,
                text=f"{comp_info['icon']} {comp_type}",
                bg=comp_info['color'],
                command=lambda ct=comp_type: self.add_component_to_canvas(ct),
                width=12,
                font=('Arial', 8)
            )
            btn.grid(row=i//2, column=i%2, padx=2, pady=2, sticky=tk.EW)
        
        net_frame.columnconfigure(0, weight=1)
        net_frame.columnconfigure(1, weight=1)
        
        # Control buttons
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="🔗 Connection Mode", 
                  command=self.toggle_connection_mode).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="🗑️ Clear All", 
                  command=self.clear_topology).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="▶️ Start Emulation", 
                  command=self.start_emulation).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="⏹️ Stop Emulation", 
                  command=self.stop_emulation).pack(fill=tk.X, pady=2)
        
        # Right panel - Canvas
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=4)
        
        # Canvas frame with title
        canvas_title_frame = ttk.Frame(right_frame)
        canvas_title_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(canvas_title_frame, text="Network Topology Designer", 
                 font=('Arial', 14, 'bold')).pack()
        
        # Instructions
        instructions = ttk.Label(canvas_title_frame, 
                               text="Drag components from the library • Double-click to edit • Right-click for menu",
                               font=('Arial', 9))
        instructions.pack()
        
        # Canvas
        canvas_frame = ttk.Frame(right_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.canvas_widget = DragDropCanvas(canvas_frame)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Set paned window weights
        main_paned.configure(sashrelief=tk.RAISED)
    
    def add_component_to_canvas(self, component_type: str):
        """Menambahkan komponen ke canvas di posisi tengah"""
        # Add component at center of visible canvas
        canvas_width = self.canvas_widget.canvas.winfo_width()
        canvas_height = self.canvas_widget.canvas.winfo_height()
        
        if canvas_width <= 1:  # Canvas not initialized yet
            canvas_width, canvas_height = 600, 400
        
        x = canvas_width // 2 + (len(self.canvas_widget.components) % 5) * 100 - 200
        y = canvas_height // 2 + (len(self.canvas_widget.components) // 5) * 80 - 200
        
        component_id = self.canvas_widget.add_component(component_type, x, y)
        self.status_var.set(f"Added {component_type} component: {component_id}")
    
    def toggle_connection_mode(self):
        """Toggle mode koneksi"""
        self.canvas_widget.toggle_connection_mode()
        if self.canvas_widget.connection_mode:
            self.status_var.set("Connection mode ON - Click two components to connect them")
        else:
            self.status_var.set("Connection mode OFF")
    
    def new_topology(self):
        """Membuat topologi baru"""
        if messagebox.askyesno("New Topology", "Create new topology? Current work will be lost."):
            self.canvas_widget.clear_canvas()
            self.current_file = None
            self.status_var.set("New topology created")
    
    def open_topology(self):
        """Membuka file topologi"""
        file_path = filedialog.askopenfilename(
            title="Open Topology",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                self.canvas_widget.clear_canvas()
                
                # Load components
                for comp_id, comp_data in data.get('components', {}).items():
                    component = Component(**comp_data)
                    self.canvas_widget.components[comp_id] = component
                    self.canvas_widget._draw_component(component)
                
                # Load connections
                self.canvas_widget.connections = data.get('connections', [])
                self.canvas_widget._update_connections()
                
                self.current_file = file_path
                self.status_var.set(f"Opened: {os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file:\n{str(e)}")
    
    def save_topology(self):
        """Menyimpan topologi"""
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self.save_topology_as()
    
    def save_topology_as(self):
        """Menyimpan topologi sebagai file baru"""
        file_path = filedialog.asksaveasfilename(
            title="Save Topology As",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            self._save_to_file(file_path)
            self.current_file = file_path
    
    def _save_to_file(self, file_path: str):
        """Menyimpan data ke file"""
        try:
            data = self.canvas_widget.get_topology_config()
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.status_var.set(f"Saved: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")
    
    def clear_topology(self):
        """Membersihkan topologi"""
        if messagebox.askyesno("Clear Topology", "Clear all components?"):
            self.canvas_widget.clear_canvas()
            self.status_var.set("Topology cleared")
    
    def export_mininet(self):
        """Export ke Mininet script"""
        file_path = filedialog.asksaveasfilename(
            title="Export Mininet Script",
            defaultextension=".py",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                config = self.canvas_widget.get_topology_config()
                generator = TopologyGenerator(config)
                script = generator.generate_mininet_script()
                
                with open(file_path, 'w') as f:
                    f.write(script)
                
                self.status_var.set(f"Mininet script exported: {os.path.basename(file_path)}")
                messagebox.showinfo("Success", f"Mininet script exported successfully!\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export script:\n{str(e)}")
    
    def export_docker_compose(self):
        """Export ke Docker Compose"""
        file_path = filedialog.asksaveasfilename(
            title="Export Docker Compose",
            defaultextension=".yml",
            filetypes=[("YAML files", "*.yml"), ("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                config = self.canvas_widget.get_topology_config()
                generator = TopologyGenerator(config)
                compose = generator.generate_docker_compose()
                
                with open(file_path, 'w') as f:
                    f.write(compose)
                
                self.status_var.set(f"Docker Compose exported: {os.path.basename(file_path)}")
                messagebox.showinfo("Success", f"Docker Compose file exported successfully!\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export Docker Compose:\n{str(e)}")
    
    def start_emulation(self):
        """Memulai emulasi"""
        if not self.canvas_widget.components:
            messagebox.showwarning("Warning", "No components to emulate!")
            return
        
        # Check if required components exist
        has_core = any(comp.type in ['AMF', 'SMF', 'UPF'] for comp in self.canvas_widget.components.values())
        has_ran = any(comp.type in ['gNB', 'UE'] for comp in self.canvas_widget.components.values())
        
        if not has_core:
            messagebox.showwarning("Warning", "No core network components found!")
            return
        
        if not has_ran:
            messagebox.showwarning("Warning", "No RAN components found!")
            return
        
        # Start emulation in separate thread
        self.status_var.set("Starting emulation...")
        
        def run_emulation():
            try:
                # Generate temporary script
                config = self.canvas_widget.get_topology_config()
                generator = TopologyGenerator(config)
                script = generator.generate_mininet_script()
                
                temp_file = "temp_topology.py"
                with open(temp_file, 'w') as f:
                    f.write(script)
                
                # Run script
                subprocess.run(['python', temp_file], check=True)
                
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Emulation failed:\n{str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"Error starting emulation:\n{str(e)}")
            finally:
                self.status_var.set("Emulation stopped")
        
        emulation_thread = threading.Thread(target=run_emulation, daemon=True)
        emulation_thread.start()
    
    def stop_emulation(self):
        """Menghentikan emulasi"""
        try:
            # Kill mininet processes
            subprocess.run(['sudo', 'mn', '-c'], check=False)
            self.status_var.set("Emulation stopped")
            messagebox.showinfo("Info", "Emulation stopped and cleaned up")
        except Exception as e:
            messagebox.showerror("Error", f"Error stopping emulation:\n{str(e)}")
    
    def deploy_docker(self):
        """Deploy ke Docker"""
        if not self.canvas_widget.components:
            messagebox.showwarning("Warning", "No components to deploy!")
            return
        
        try:
            config = self.canvas_widget.get_topology_config()
            generator = TopologyGenerator(config)
            compose = generator.generate_docker_compose()
            
            # Save docker-compose.yml
            with open('docker-compose-5g.yml', 'w') as f:
                f.write(compose)
            
            # Run docker-compose
            result = messagebox.askyesno("Deploy", 
                                       "Docker Compose file created. Deploy now?")
            
            if result:
                subprocess.run(['docker-compose', '-f', 'docker-compose-5g.yml', 'up', '-d'], 
                             check=True)
                self.status_var.set("Deployed to Docker")
                messagebox.showinfo("Success", "5G network deployed to Docker!")
            
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Docker deployment failed:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error deploying to Docker:\n{str(e)}")
    
    def show_about(self):
        """Menampilkan dialog about"""
        about_text = """
5G Network Emulator GUI v1.0

A visual tool for designing and deploying 5G network topologies.

Features:
• Drag and drop interface
• Visual topology design
• Component configuration
• Mininet script generation
• Docker deployment
• Real-time emulation

Developed for 5G network research and education.
        """
        messagebox.showinfo("About", about_text)
    
    def run(self):
        """Menjalankan aplikasi"""
        self.root.mainloop()

if __name__ == "__main__":
    app = FiveGEmulatorGUI()
    app.run()
