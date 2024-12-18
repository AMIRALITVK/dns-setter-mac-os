import tkinter as tk
from tkinter import messagebox
import subprocess
import os

DNS_FILE = "dns_list.txt"

# Function to get the active network interface
def get_active_interface():
    try:
        result = subprocess.run(
            ["networksetup", "-listallhardwareports"],
            capture_output=True, text=True, check=True
        )
        lines = result.stdout.splitlines()
        interface_map = {}

        current_port = None
        for line in lines:
            if "Hardware Port" in line:
                current_port = line.split(": ")[1].strip()
            elif "Device" in line and current_port:
                device = line.split(": ")[1].strip()
                interface_map[current_port] = device

        for port, device in interface_map.items():
            status = subprocess.run(
                ["ifconfig", device],
                capture_output=True, text=True
            )
            if "status: active" in status.stdout:
                return port
        return None
    except subprocess.CalledProcessError:
        return None

# Function to check current DNS
def get_current_dns(interface):
    try:
        result = subprocess.run(
            ["networksetup", "-getdnsservers", interface],
            capture_output=True, text=True, check=True
        )
        dns_servers = result.stdout.strip().splitlines()

        if "There aren't any DNS Servers set" in dns_servers:
            return None
        return ", ".join(dns_servers)
    except subprocess.CalledProcessError:
        return None

# Function to update checkbox color
def update_checkbox_color():
    if dns_toggle_var.get() == 1:
        toggle_btn.config(selectcolor="green")
    else:
        toggle_btn.config(selectcolor="white")

# Function to toggle DNS
def toggle_dns():
    interface = get_active_interface()
    selected_dns = dns_listbox.get(tk.ACTIVE).split(' - ')[0]  # Get DNS IP only
    is_on = dns_toggle_var.get()

    if not interface:
        messagebox.showerror("Error", "No active network interface found.")
        dns_toggle_var.set(0)
        update_checkbox_color()
        return

    try:
        if is_on:
            if not selected_dns:
                messagebox.showerror("Error", "Select a DNS server from the list.")
                dns_toggle_var.set(0)
                update_checkbox_color()
                return

            subprocess.run(
                ["networksetup", "-setdnsservers", interface, selected_dns], check=True
            )
            dns_label.config(text=selected_dns)
            messagebox.showinfo("Success", f"DNS set to {selected_dns} on {interface}")
        else:
            subprocess.run(
                ["networksetup", "-setdnsservers", interface, "Empty"], check=True
            )
            dns_label.config(text="")
            messagebox.showinfo("Success", f"DNS removed from {interface}")

        update_checkbox_color()

    except subprocess.CalledProcessError:
        messagebox.showerror("Error", "Failed to apply DNS settings.")
        dns_toggle_var.set(int(not is_on))
        update_checkbox_color()

# Function to add a new DNS with name
def add_dns():
    new_dns_ip = dns_ip_var.get().strip()
    new_dns_name = dns_name_var.get().strip()

    if new_dns_ip and new_dns_name and new_dns_ip not in dns_listbox.get(0, tk.END):
        dns_listbox.insert(tk.END, f"{new_dns_ip} - {new_dns_name}")
        save_dns_list()
        dns_ip_var.set("")
        dns_name_var.set("")
    else:
        messagebox.showwarning("Warning", "DNS IP or Name is empty, or DNS already exists.")

# Function to delete selected DNS
def delete_dns():
    selected_index = dns_listbox.curselection()
    if selected_index:
        dns_listbox.delete(selected_index)
        save_dns_list()
    else:
        messagebox.showwarning("Warning", "Select a DNS server to delete.")

# Save DNS list to file
def save_dns_list():
    with open(DNS_FILE, "w") as f:
        for dns in dns_listbox.get(0, tk.END):
            f.write(dns + "\n")

# Load DNS list from file
def load_dns_list():
    if os.path.exists(DNS_FILE):
        with open(DNS_FILE, "r") as f:
            for line in f:
                dns = line.strip()
                if dns and dns not in dns_listbox.get(0, tk.END):
                    dns_listbox.insert(tk.END, dns)

# GUI Setup
root = tk.Tk()
root.title("macOS DNS Setter")

# DNS IP Entry
tk.Label(root, text="DNS IP:").grid(row=0, column=0, padx=3, pady=5)
dns_ip_var = tk.StringVar()
dns_ip_entry = tk.Entry(root, textvariable=dns_ip_var, width=20)
dns_ip_entry.grid(row=0, column=1, padx=5, pady=5)

# DNS Name Entry
tk.Label(root, text="DNS Name:").grid(row=0, column=2, padx=3, pady=5)
dns_name_var = tk.StringVar()
dns_name_entry = tk.Entry(root, textvariable=dns_name_var, width=20)
dns_name_entry.grid(row=0, column=3, padx=5, pady=5)

# Add Button
tk.Button(root, text="Add", command=add_dns).grid(row=0, column=4, padx=2)

# DNS Server List
tk.Label(root, text="DNS Servers:").grid(row=1, column=0, padx=5, pady=5)
dns_listbox = tk.Listbox(root, height=5, width=50)
dns_listbox.grid(row=1, column=1, columnspan=3, padx=2, pady=5)

# Delete Button
tk.Button(root, text="Delete", command=delete_dns).grid(row=0, column=5, padx=3)

# Toggle Button
dns_toggle_var = tk.IntVar()

# Pre-check and display current DNS
active_interface = get_active_interface()
current_dns = get_current_dns(active_interface)

dns_label = tk.Label(root, text=current_dns if current_dns else "")
dns_label.grid(row=3, columnspan=3, pady=5)

# Load saved DNS records
load_dns_list()

# Select current DNS in the list if available
if current_dns:
    dns_toggle_var.set(1)
    dns_items = dns_listbox.get(0, tk.END)
    
    # Insert current DNS if not already in the list
    if current_dns not in dns_items:
        dns_listbox.insert(tk.END, current_dns)

    # Select and activate the current DNS in the list
    if current_dns in dns_items:
        index = dns_items.index(current_dns)
        dns_listbox.selection_set(index)
        dns_listbox.activate(index)
else:
    dns_toggle_var.set(0)

# Create Toggle Checkbutton
toggle_btn = tk.Checkbutton(
    root, text="Enable DNS", variable=dns_toggle_var, command=lambda: (toggle_dns(), update_checkbox_color())
)
toggle_btn.grid(row=2, column=0, columnspan=2, pady=10)
update_checkbox_color()

root.mainloop()