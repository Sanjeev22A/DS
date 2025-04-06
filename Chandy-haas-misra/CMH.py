import threading
import time
process_list=[]
ProbeQueue=[]

class Probe:
    def __init__(self,origin,sender,receiver):
        self.origin = origin
        self.sender = sender
        self.receiver = receiver
    def __repr__(self):
        return f"Probe(origin={self.origin.pid}, sender={self.sender.pid}, receiver={self.receiver.pid})"
    
class Process:
    def __init__(self,pid,sid,process_count,isBlocked=False,isWaitingOn=None):
        self.pid=pid
        self.sid=sid
        self.process_count=process_count
        ##Initially the dependency is set to false for all processes
        ##depdendenti[j] is true if j depdends on i
        self.dependent=[False]*self.process_count
        self.isBlocked=isBlocked
        self.deadlockDetected=False
        ##List of process on which the current process is waiting on

        self.isWaitingOn=isWaitingOn if isWaitingOn is not None else []
        
        self.probeReceveQueue=[]
        self.probeSendQueue=[]
        self.probeReceiveCount=0
        self.probeSentCount=0
        self.listeners={}
    def add_event_listener(self,event_name,handler):
        self.listeners[event_name] = handler
    def remove_event_listener(self,event_name):
        if event_name in self.listeners:
            del self.listeners[event_name]
    
    def trigger_event(self,event_name,*args,**kwargs):
        if event_name in self.listeners:
            handler = self.listeners[event_name]
            handler(*args, **kwargs)
    

    

    ##Case where the process is blocked on itself
    def makeProcessBlocked(self):
        self.isBlocked=True
        self.isWaitingOn.append(self.pid)
        self.dependent[self.pid]=True

    def declareDeadlock(self):
        print(f"Process {self.pid} is in a deadlock state")
        ##The process is blocked on itself and hence it is in a deadlock state
        self.makeProcessBlocked()
        
    def isLocallyDependentOn(self,process):
        if self.pid==process.pid:
            return True
        if process.dependent[self.pid] and process.sid==self.sid:
            return True
        return False

    def checkWaitingOn(self,process):
        if process.pid in self.isWaitingOn:
            return True
        return False
    def checkDifferentSites(self,process):
        return self.sid!=process.sid
    

    def sendProbe(self,initiator,sender,receiver):
    
        if sender.checkWaitingOn(receiver):
            probe=Probe(initiator,sender,receiver)
            print("Sent probe : ",probe)
            sender.probeSendQueue.append(probe)
            sender.probeSentCount+=1
            receiver.add_event_listener('receiveProbe',receiver.receiveProbe)
            ProbeQueue.append(probe)

    def checkIfNotReplied(self,process):
        for probe in self.probeReceveQueue:
            if probe.sender==process:
                return True
        return False
    def declareDeadlock(self):
        print(f"DEADLOCK DETECTED: Process {self.pid} is in a deadlock state")
        self.deadlockDetected = True
        self.isBlocked = True
        
        self.makeProcessBlocked()
    


    def receiveProbe(self, probe):
        print("Received probe : ",probe)
        self.probeReceveQueue.append(probe)

        self.probeReceiveCount+=1
        initiator = probe.origin
        sender = probe.sender
        receiver = probe.receiver
       
        if receiver.isBlocked and (not receiver.dependent[initiator.pid]) and receiver.checkIfNotReplied(sender):
            receiver.dependent[initiator.pid] = True
            
            if receiver.pid == initiator.pid:
                receiver.declareDeadlock()
            else:
                for m_pid in range(receiver.process_count):
                    Pm = process_list[m_pid]
                    for n_pid in Pm.isWaitingOn:
                        Pn = process_list[n_pid]
                        
                        if receiver.isLocallyDependentOn(Pm) and \
                        Pm.checkWaitingOn(Pn) and \
                        Pm.checkDifferentSites(Pn):
                            new_probe = Probe(initiator, Pm, Pn)
                            receiver.probeSendQueue.append(new_probe)
                            receiver.probeSentCount += 1
                            Pn.add_event_listener('receiveProbe', Pn.receiveProbe)
                            ProbeQueue.append(new_probe)

                    


def ProbeDispatcher():
    while True:
        if ProbeQueue:
            probe=ProbeQueue.pop(0)
            receiver=probe.receiver
            receiver.trigger_event('receiveProbe', probe)
        else:
            time.sleep(0.1)

def print_system_state():
    """Print the current state of all processes"""
    print("\n=== SYSTEM STATE ===")
    for p in process_list:
        status = "BLOCKED" if p.isBlocked else "ACTIVE"
        deadlock = "DEADLOCKED" if p.deadlockDetected else ""
        print(f"Process {p.pid} (Site {p.sid}): {status} {deadlock}")
        print(f"  Waiting on: {p.isWaitingOn}")
        print(f"  Dependencies: {[i for i, dep in enumerate(p.dependent) if dep]}")
        print(f"  Probes sent: {p.probeSentCount}, received: {p.probeReceiveCount}")
    print("===================\n")

def main():
    global process_list, ProbeQueue, running
    
    # Start the dispatcher thread
    dispatcher_thread = threading.Thread(target=ProbeDispatcher, daemon=True)
    dispatcher_thread.start()
    print("Dispatcher thread started")
    
    try:
        # Setup processes
        process_count = 3
        print("Creating processes...")
        
        # Create processes with proper initialization of isWaitingOn
        P0 = Process(pid=0, sid=0, process_count=process_count, isBlocked=True, isWaitingOn=[1])
        P1 = Process(pid=1, sid=0, process_count=process_count, isBlocked=True, isWaitingOn=[2])
        P2 = Process(pid=2, sid=1, process_count=process_count, isBlocked=True,isWaitingOn=[1])
        
        # Add to global process list
        process_list.extend([P0, P1, P2])
        print("Processes created")
        
        # Set up dependencies
        print("Setting up dependencies...")
        P1.dependent[0] = False  # P0 depends on P1
        P2.dependent[1] = False  # P1 depends on P2
        P0.dependent[2] = False  # P2 depends on P0
        print("Dependencies set")
        
        # Print initial state
        print_system_state()
        
        # Start deadlock detection
        print("Starting deadlock detection from P0...")
        P0.sendProbe(initiator=P0, sender=P0, receiver=P1)
        P0.sendProbe(initiator=P0, sender=P0, receiver=P2)
        P1.sendProbe(initiator=P1, sender=P1, receiver=P0)
        P1.sendProbe(initiator=P1, sender=P1, receiver=P2)
        # Wait for probes to be processed
        print("Waiting for probe processing...")
        max_wait = 10  # Maximum seconds to wait
        start_time = time.time()
        
        deadlock_detected = False
        while time.time() - start_time < max_wait:
            # Check if any process detected a deadlock
            for p in process_list:
                if p.deadlockDetected:
                    deadlock_detected = True
                    break
            
            if deadlock_detected:
                print("Deadlock detected in the system!")
                break
                
            # Sleep briefly to avoid high CPU usage
            time.sleep(0.5)
        
        # Final system state
        print_system_state()
        
        if not deadlock_detected:
            print("No deadlock detected within the time limit.")
    
    finally:
        # Stop the dispatcher thread
        running = False
        dispatcher_thread.join(timeout=2.0)
        print("Dispatcher thread stopped")
if __name__ == "__main__":
    main()