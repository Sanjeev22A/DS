import java.util.*;

public class CycleDetectionDFS {
    int nodes;
    List<List<Integer>> adjList;
    boolean[] recTrack;
    boolean[] visited;
    Map<Integer,Integer> parent;
    List<Integer> cyclePath;
    Scanner sc;
    public CycleDetectionDFS(){
        sc=new Scanner(System.in);
        this.getNumberNodes();
        this.getAdjList();
        this.runAlgo();
    }
    private void getAdjList(){
        this.adjList=new ArrayList<>();
        for(int i=0;i<nodes;i++){
            System.out.printf("Enter the nodes on which process P%d waits for%n",i);
            List<Integer> temp=new ArrayList<>();
            for(int j=0;j<nodes;j++){
                if(i!=j){
                    System.out.printf("If P%d waits on P%d enter 1 else 0 : ",i,j);
                    int val=sc.nextInt();
                    if(val==1){
                        temp.add(j);
                    }
                }
            }
            this.adjList.add(temp);
        }
    }
    private void getNumberNodes(){
        System.out.print("Enter the number of process in the system : ");
        this.nodes=sc.nextInt();
        System.out.println();
    }
    private void initialize(){
        this.recTrack=new boolean[nodes];
        this.visited=new boolean[nodes];
        this.parent=new HashMap<>();
        this.cyclePath=new ArrayList<>();
    }
    public void runAlgo(){
        this.cyclePath=findCycle();
        if(cyclePath==null || cyclePath.isEmpty()){
            return;
        }
        else{
            this.displayCycle(this.cyclePath);
        }
    }
    void displayCycle(List<Integer> path){
        int i=0;
        for(int a:path){
            if(i==0){
                System.out.printf("%d",a);
            }
            else {
                System.out.printf("->%d", a);
            }
            i++;
        }
    }
    public List<Integer> findCycle(){
        this.initialize();
        for(int i=0;i<this.nodes;i++){
            if(!this.visited[i]){
                if(dfs(i)){
                    System.out.println("Cycle has been found and hence deadlock detected!!");
                    return this.cyclePath.reversed();
                }
            }
        }
        System.out.println("No cycle and hence no deadlock has been detected!!");
        return null;
    }

    private boolean dfs(int node){
        this.visited[node]=true;
        this.recTrack[node]=true;
        for(int a:this.adjList.get(node)){
            if(!visited[a]){
                this.parent.put(a,node);
                if(dfs(a)){
                    return true;
                }
            }
            else if(recTrack[a]){
                int curr=node;
                this.cyclePath.add(curr);
                while(curr!=a){
                    curr=this.parent.get(curr);
                    this.cyclePath.add(curr);
                }
                this.cyclePath.add(node);
                return true;
            }
        }
        recTrack[node]=false;
        return false;
    }
}
