import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Global variables
process_list = []
ProbeQueue = []
running = True
log_text = None
canvas = None

class Probe:
    def __init__(self, origin, sender, receiver):
        self.origin = origin
        self.sender = sender
        self.receiver = receiver
    
    def __repr__(self):
        return f"Probe(origin={self.origin.pid}, sender={self.sender.pid}, receiver={self.receiver.pid})"

class Process:
    def __init__(self, pid, sid, process_count, isBlocked=False, isWaitingOn=None):
        self.pid = pid
        self.sid = sid
        self.process_count = process_count
        # Initially the dependency is set to false for all processes
        # dependent[j] is true if j depends on i
        self.dependent = [False] * self.process_count
        self.isBlocked = isBlocked
        self.deadlockDetected = False
        # List of process on which the current process is waiting on
        self.isWaitingOn = isWaitingOn if isWaitingOn is not None else []
        # Each process maintains its own list of probes sent, received and their counts
        self.probeReceveQueue = []
        self.probeSendQueue = []
        self.probeReceiveCount = 0
        self.probeSentCount = 0
        # This is the list of event listeners and when a probe is received the event is added to the event_listener
        self.listeners = {}

    def add_event_listener(self, event_name, handler):
        self.listeners[event_name] = handler
    
    def remove_event_listener(self, event_name):
        if event_name in self.listeners:
            del self.listeners[event_name]
    
    def trigger_event(self, event_name, *args, **kwargs):
        if event_name in self.listeners:
            handler = self.listeners[event_name]
            log_message(f"Arguments: {args}")
            handler(*args, **kwargs)

    # Case where the process is blocked on itself
    def makeProcessBlocked(self):
        self.isBlocked = True
        if self.pid not in self.isWaitingOn:
            self.isWaitingOn.append(self.pid)
        self.dependent[self.pid] = True

    def declareDeadlock(self):
        log_message(f"DEADLOCK DETECTED: Process {self.pid} is in a deadlock state")
        # The process is blocked on itself and hence it is in a deadlock state
        self.deadlockDetected = True
        self.isBlocked = True
        self.makeProcessBlocked()
        
    def isLocallyDependentOn(self, process):
        if self.pid == process.pid:
            return True
        if process.dependent[self.pid] and process.sid == self.sid:
            return True
        return False

    def checkWaitingOn(self, process):
        if process.pid in self.isWaitingOn:
            return True
        return False
        
    def checkDifferentSites(self, process):
        return self.sid != process.sid

    def sendProbe(self, initiator, sender, receiver):
        print(sender.checkWaitingOn(receiver), initiator.isLocallyDependentOn(sender))
        if sender.checkWaitingOn(receiver) and initiator.isLocallyDependentOn(sender) :          ##and sender.checkDifferentSites(receiver) and initiator.isLocallyDependentOn(sender):
            probe = Probe(initiator, sender, receiver)
            log_message(f"Sent probe: {probe}")
            sender.probeSendQueue.append(probe)
            sender.probeSentCount += 1
            receiver.add_event_listener('receiveProbe', receiver.receiveProbe)
            ProbeQueue.append(probe)

    def checkIfNotReplied(self, process):
        for probe in self.probeReceveQueue:
            if probe.sender == process:
                return True
        return False

    def receiveProbe(self, probe):
        log_message(f"Received probe: {probe}")
        self.probeReceveQueue.append(probe)
        self.probeReceiveCount += 1
        initiator = probe.origin
        sender = probe.sender
        receiver = probe.receiver
       
        if receiver.isBlocked and (not receiver.dependent[initiator.pid]) and receiver.checkIfNotReplied(sender):
            receiver.dependent[initiator.pid] = True
            
            if receiver.pid == initiator.pid:
                receiver.declareDeadlock()
            else:
                for m_pid in range(receiver.process_count):
                    if m_pid < len(process_list):  # Ensure valid index
                        Pm = process_list[m_pid]
                        for n_pid in Pm.isWaitingOn:
                            if n_pid < len(process_list):  # Make sure the n_pid is valid
                                Pn = process_list[n_pid]
                                
                                if receiver.isLocallyDependentOn(Pm) and \
                                Pm.checkWaitingOn(Pn) :                        ##and \
                                                                                ##Pm.checkDifferentSites(Pn)
                                    new_probe = Probe(initiator, Pm, Pn)
                                    receiver.probeSendQueue.append(new_probe)
                                    receiver.probeSentCount += 1
                                    Pn.add_event_listener('receiveProbe', Pn.receiveProbe)
                                    ProbeQueue.append(new_probe)

# Global log function
def log_message(message):
    global log_text
    if log_text:
        log_text.insert(tk.END, message + "\n")
        log_text.see(tk.END)
    else:
        print(message)

def ProbeDispatcher():
    global running
    while running:
        if ProbeQueue:
            probe = ProbeQueue.pop(0)
            receiver = probe.receiver
            receiver.trigger_event('receiveProbe', probe)
        else:
            time.sleep(0.1)

def print_system_state():
    """Print the current state of all processes"""
    state_text = "\n=== SYSTEM STATE ===\n"
    for p in process_list:
        status = "BLOCKED" if p.isBlocked else "ACTIVE"
        deadlock = "DEADLOCKED" if p.deadlockDetected else ""
        state_text += f"Process {p.pid} (Site {p.sid}): {status} {deadlock}\n"
        state_text += f"  Waiting on: {p.isWaitingOn}\n"
        state_text += f"  Dependencies: {[i for i, dep in enumerate(p.dependent) if dep]}\n"
        state_text += f"  Probes sent: {p.probeSentCount}, received: {p.probeReceiveCount}\n"
    state_text += "===================\n"
    log_message(state_text)
    return state_text

class DeadlockDetectionApp:
    def __init__(self, root):
        global log_text, canvas
        
        self.root = root
        self.root.title("Chandy-Misra Deadlock Detection")
        self.root.geometry("1200x800")
        
        # Create main frames
        self.left_frame = ttk.Frame(root, padding=10)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.right_frame = ttk.Frame(root, padding=10)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Process configuration
        ttk.Label(self.left_frame, text="Process Configuration", font=("Arial", 12, "bold")).pack(pady=5)
        
        config_frame = ttk.Frame(self.left_frame)
        config_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(config_frame, text="Number of Processes:").grid(row=0, column=0, padx=5, pady=5)
        self.process_count_var = tk.IntVar(value=3)
        ttk.Spinbox(config_frame, from_=2, to=10, textvariable=self.process_count_var).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(config_frame, text="Create Processes", command=self.create_processes).grid(row=0, column=2, padx=5, pady=5)
        
        # Process dependency setup
        self.dependency_frame = ttk.LabelFrame(self.left_frame, text="Process Dependencies", padding=10)
        self.dependency_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create a frame for the log
        log_frame = ttk.LabelFrame(self.left_frame, text="Execution Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        log_text = scrolledtext.ScrolledText(log_frame, width=50, height=15)
        log_text.pack(fill=tk.BOTH, expand=True)
        
        # Control buttons
        control_frame = ttk.Frame(self.left_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(control_frame, text="Run Detection", command=self.run_detection).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Print State", command=print_system_state).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Update Graph", command=self.update_graph).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Clear", command=self.clear_all).pack(side=tk.LEFT, padx=5)
        
        # Graph display area
        graph_frame = ttk.LabelFrame(self.right_frame, text="Wait-For Graph Visualization", padding=10)
        graph_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create Figure and Canvas for matplotlib
        self.figure = Figure(figsize=(8, 6))
        self.canvas_widget = FigureCanvasTkAgg(self.figure, master=graph_frame)
        canvas = self.canvas_widget
        self.canvas_widget.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.ax = self.figure.add_subplot(111)
        
        # Initialize canvas drawing
        self.figure.tight_layout()
        self.canvas_widget.draw()
        
        self.dependency_widgets = []
        self.process_data = []
        
        # Start the dispatcher thread
        self.dispatcher_thread = None
        
        # Initial empty graph
        self.init_graph()
    
    def init_graph(self):
        """Initialize an empty graph"""
        self.ax.clear()
        self.ax.set_title("Wait-For Graph")
        self.ax.text(0.5, 0.5, "Create processes and run detection to see the graph",
                    horizontalalignment='center', verticalalignment='center',
                    transform=self.ax.transAxes, fontsize=12)
        self.ax.axis('off')
        self.canvas_widget.draw()
    
    def create_processes(self):
        global process_list, ProbeQueue
        process_list = []
        ProbeQueue = []
        
        # Clear the dependency frame
        for widget in self.dependency_widgets:
            widget.destroy()
        self.dependency_widgets = []
        
        process_count = self.process_count_var.get()
        
        # Create header row
        header_frame = ttk.Frame(self.dependency_frame)
        header_frame.pack(fill=tk.X)
        self.dependency_widgets.append(header_frame)
        
        ttk.Label(header_frame, text="Process", width=10).grid(row=0, column=0)
        ttk.Label(header_frame, text="Site ID", width=10).grid(row=0, column=1)
        ttk.Label(header_frame, text="Blocked", width=10).grid(row=0, column=2)
        ttk.Label(header_frame, text="Waiting On", width=20).grid(row=0, column=3)
        
        # Create rows for each process
        self.process_data = []
        for i in range(process_count):
            process_frame = ttk.Frame(self.dependency_frame)
            process_frame.pack(fill=tk.X, pady=2)
            self.dependency_widgets.append(process_frame)
            
            ttk.Label(process_frame, text=f"P{i}", width=10).grid(row=0, column=0)
            
            site_var = tk.IntVar(value=0)
            ttk.Spinbox(process_frame, from_=0, to=5, textvariable=site_var, width=7).grid(row=0, column=1)
            
            blocked_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(process_frame, variable=blocked_var).grid(row=0, column=2)
            
            waiting_var = tk.StringVar(value="")
            ttk.Entry(process_frame, textvariable=waiting_var, width=17).grid(row=0, column=3)
            
            self.process_data.append((site_var, blocked_var, waiting_var))
        
        log_message(f"Created configuration for {process_count} processes")
        self.init_graph()

    def parse_waiting_on(self, waiting_str):
        """Parse the waiting on string into a list of integers"""
        if not waiting_str.strip():
            return []
        
        try:
            # Split by commas or spaces, filter out empty strings, and convert to integers
            waiting_list = [int(pid.strip()) for pid in waiting_str.replace(',', ' ').split() if pid.strip()]
            return waiting_list
        except ValueError:
            messagebox.showerror("Invalid Input", "Waiting processes must be comma or space separated integers")
            return []
    
    def update_graph(self):
        """Update the graph visualization"""
        if not process_list:
            self.init_graph()
            return
        
        # Clear the current axis
        self.ax.clear()
        
        # Create directed graph
        G = nx.DiGraph()
        
        # Add all nodes first
        for p in process_list:
            node_label = f"P{p.pid}\nSite{p.sid}"
            G.add_node(node_label)
        
        # Add edges based on waiting relationships
        for p in process_list:
            for wait_pid in p.isWaitingOn:
                if wait_pid < len(process_list):  # Ensure valid index
                    G.add_edge(f"P{p.pid}\nSite{p.sid}", f"P{wait_pid}\nSite{process_list[wait_pid].sid}")
        
        # Set node colors based on process state
        node_colors = []
        for node in G.nodes():
            pid = int(node.split('\n')[0][1:])  # Extract pid from "P{pid}\nSite{sid}"
            if process_list[pid].deadlockDetected:
                node_colors.append('red')
            elif process_list[pid].isBlocked:
                node_colors.append('orange')
            else:
                node_colors.append('lightblue')
        
        # Create a spring layout
        pos = nx.spring_layout(G)
        
        # Draw the graph
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=1000, ax=self.ax)
        nx.draw_networkx_edges(G, pos, arrowsize=20, ax=self.ax)
        nx.draw_networkx_labels(G, pos, font_size=9, font_weight='bold', ax=self.ax)
        
        # Add edge labels showing probe info
        edge_labels = {}
        for p in process_list:
            for probe in p.probeSendQueue:
                sender = probe.sender.pid
                receiver = probe.receiver.pid
                origin = probe.origin.pid
                key = (f"P{sender}\nSite{probe.sender.sid}", f"P{receiver}\nSite{probe.receiver.sid}")
                if key in edge_labels:
                    edge_labels[key] += f",({origin},{sender},{receiver})"
                else:
                    edge_labels[key] = f"({origin},{sender},{receiver})"
        
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8, ax=self.ax)
        
        # Set title and disable axes
        self.ax.set_title("Wait-For Graph with Probe Information")
        self.ax.axis('off')
        
        # Update canvas
        self.figure.tight_layout()
        self.canvas_widget.draw()
        log_message("Graph visualization updated")
    
    def run_detection(self):
        global process_list, running, ProbeQueue
        
        if not self.process_data:
            messagebox.showinfo("Error", "Please create processes first")
            return
        
        # Initialize processes
        process_list = []
        ProbeQueue = []
        process_count = self.process_count_var.get()
        
        log_message("Creating processes...")
        
        for i, (site_var, blocked_var, waiting_var) in enumerate(self.process_data):
            site_id = site_var.get()
            is_blocked = blocked_var.get()
            waiting_on = self.parse_waiting_on(waiting_var.get())
            
            process = Process(
                pid=i,
                sid=site_id,
                process_count=process_count,
                isBlocked=is_blocked,
                isWaitingOn=waiting_on
            )
            process_list.append(process)
        
        log_message("All processes created")
        
        # Set up initial dependencies
        for p in process_list:
            for wait_pid in p.isWaitingOn:
                if wait_pid < len(process_list):
                    process_list[wait_pid].dependent[p.pid] = False
        
        # Start the dispatcher thread if not already running
        if not self.dispatcher_thread or not self.dispatcher_thread.is_alive():
            running = True
            self.dispatcher_thread = threading.Thread(target=ProbeDispatcher, daemon=True)
            self.dispatcher_thread.start()
            log_message("Dispatcher thread started")
        
        # Print initial state
        print_system_state()
        
        # Update the graph
        self.update_graph()
        
        # Start deadlock detection
        log_message("Starting deadlock detection...")
        for p in process_list:
            for other_p in process_list:
                p.sendProbe(initiator=p, sender=p, receiver=other_p)
        
        # Run detector for a short time
        self.root.after(2000, self.check_deadlock)
    
    def check_deadlock(self):
        deadlock_detected = False
        for p in process_list:
            if p.deadlockDetected:
                deadlock_detected = True
                break
        
        if deadlock_detected:
            log_message("DEADLOCK DETECTED in the system!")
            messagebox.showinfo("Detection Result", "Deadlock detected!")
        else:
            log_message("No deadlock detected yet, continuing...")
            self.root.after(2000, self.check_deadlock)
        
        # Update the graph and system state
        print_system_state()
        self.update_graph()
    
    def clear_all(self):
        global process_list, ProbeQueue, running
        process_list = []
        ProbeQueue = []
        
        # Stop the dispatcher thread
        running = False
        if self.dispatcher_thread and self.dispatcher_thread.is_alive():
            self.dispatcher_thread.join(timeout=1.0)
            log_message("Dispatcher thread stopped")
        
        # Clear log
        log_text.delete(1.0, tk.END)
        
        # Clear graph
        self.init_graph()
        
        # Remove process configuration
        for widget in self.dependency_widgets:
            widget.destroy()
        self.dependency_widgets = []
        self.process_data = []
        
        log_message("System cleared")

def main():
    root = tk.Tk()
    app = DeadlockDetectionApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (setattr(globals(), "running", False), root.destroy()))
    root.mainloop()

if __name__ == "__main__":
    main()