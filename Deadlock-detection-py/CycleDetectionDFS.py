import networkx as nx
import matplotlib.pyplot as plt
class CycleDetectionDFS:
    def __init__(self):
        self.nodes=self.getNumberNodes()
        self.adjList=self.getAdjList()
        self.visited=[False]*self.nodes
        self.recTrack=[False]*self.nodes
        self.cyclePath=[]
        self.parent={}
        
    def getNumberNodes(self):
        self.nodes=int(input("Enter the number of nodes:"))
        return self.nodes
    def getAdjList(self):
        self.adjList=[]
        for i in range(self.nodes):
            print(f"Enter the nodes on which process P{i} waits for:",end="\n")
            temp=[]
            while True:
                node=int(input())
                if node==-1:
                    break
                temp.append(node)
            
            self.adjList.append(temp)
        return self.adjList
    
        
    def findCycle(self):
        for i in range(self.nodes):
            if not self.visited[i]:
                if self.dfs(i):
                    print("Cycle has been found and deadlock is detected!!")
                    
                    self.cyclePath.reverse()
                    return self.cyclePath
        print("No cycle has been found and deadlock is not detected!!")
        return None
    
    def dfs(self,node):
        self.visited[node]=True
        self.recTrack[node]=True
        
        for i in self.adjList[node]:
            if not self.visited[i]:
                self.parent[i]=node
                if self.dfs(i):
                    return True
            elif self.recTrack[i]:
                curr=node
                self.cyclePath.append(i)
                self.cyclePath.append(curr)
                while(curr!=i):
                    curr=self.parent[curr]
                    self.cyclePath.append(curr)
                
                
                return True
        self.recTrack[node]=False
        return False
    def runAlgo(self):
        self.cyclePath=self.findCycle()
        print(self.cyclePath)
        if self.cyclePath:
            self.displayCyclePath()

    def displayCyclePath(self):
        print("Cycle Path is:")
        for i in range(len(self.cyclePath)):
            if i==len(self.cyclePath)-1:
                print(self.cyclePath[i])
            else:
                print(self.cyclePath[i],end="->")
        print()
    

class VisualizeGraph:
    def __init__(self,cyclePath):
        self.cyclePath=cyclePath
        self.graph=nx.DiGraph()
        self.nodes=len(cyclePath)
        self.addEdges()
        self.drawGraph()
    def addEdges(self):
        for i in range(self.nodes-1):
            self.graph.add_edge(self.cyclePath[i],self.cyclePath[(i+1)%self.nodes])
    
    def drawGraph(self):
        pos=nx.spring_layout(self.graph)
        nx.draw(self.graph,pos,with_labels=True,arrows=True)
        plt.show()

if __name__=="__main__":
    cycleDetection=CycleDetectionDFS()
    cycleDetection.runAlgo()
    if cycleDetection.cyclePath:
        visualizeGraph=VisualizeGraph(cycleDetection.cyclePath)
        visualizeGraph.drawGraph()
    else:
        print("No cycle to visualize.")
                
