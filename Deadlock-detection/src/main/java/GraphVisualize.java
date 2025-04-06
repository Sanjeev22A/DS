import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.DirectedPseudograph;
import org.jgrapht.ext.JGraphXAdapter;
import com.mxgraph.layout.mxCircleLayout;
import com.mxgraph.swing.mxGraphComponent;
import javax.swing.*;
import java.util.ArrayList;
import java.util.List;

public class GraphVisualize {
    private DirectedPseudograph<Integer, DefaultEdge> graph;
    public GraphVisualize(List<List<Integer>> adjList){
        this.graph=new DirectedPseudograph<>(DefaultEdge.class);
        buildGraph(adjList);
    }
    private void buildGraph(List<List<Integer>> adj){

        int node=adj.size();
        //To add the vertex
        for(int i=0;i<node;i++){
            graph.addVertex(i);
        }
        //To add the edge
        for(int i=0;i<node;i++){
            for(int a:adj.get(i)){
                graph.addEdge(i,a);
            }
        }
    }

    public void visualize(){
        JGraphXAdapter<Integer,DefaultEdge> graphAdapter=new JGraphXAdapter<>(graph);
        //For the cirular layout
        new mxCircleLayout(graphAdapter).execute(graphAdapter.getDefaultParent());
        JFrame frame=new JFrame("Cycle visualization");
        frame.add(new mxGraphComponent(graphAdapter));
        frame.pack();
        frame.setVisible(true);
    }

    public static void main(String[] args) {
        // Example adjacency list
        int V = 5;
        List<List<Integer>> adj = new ArrayList<>();
        for (int i = 0; i < V; i++) adj.add(new ArrayList<>());

        // Add edges (Directed Graph)
        adj.get(0).add(1);
        adj.get(1).add(2);
        adj.get(2).add(3);
        adj.get(3).add(4);
        adj.get(4).add(1); // Cycle

        // Create GraphVisualizer instance
        GraphVisualize graphVisualizer = new GraphVisualize(adj);
        graphVisualizer.visualize();
    }
}

