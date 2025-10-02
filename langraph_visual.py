from graphviz import Digraph
from langgraph.graph import StateGraph

# ---- Setup LangGraph ----
graph = StateGraph()

graph.add_node("Intro")
graph.add_node("Ask Question")
graph.add_node("Evaluate Answer")
graph.add_node("Follow-up Decision")
graph.add_node("End")

graph.add_edge("Intro", "Ask Question")
graph.add_edge("Ask Question", "Evaluate Answer")
graph.add_edge("Evaluate Answer", "Follow-up Decision")
graph.add_edge("Follow-up Decision", "Ask Question")  # loop
graph.add_edge("Follow-up Decision", "End")

# ---- Simple Visualizer ----
def render_graph(active_node=None):
    dot = Digraph(comment="Interview Flow", format="png")
    nodes = ["Intro", "Ask Question", "Evaluate Answer", "Follow-up Decision", "End"]

    for n in nodes:
        if n == active_node:
            dot.node(n, n, style="filled", fillcolor="lightgreen", shape="box")
        else:
            dot.node(n, n, shape="box")

    dot.edge("Intro", "Ask Question")
    dot.edge("Ask Question", "Evaluate Answer")
    dot.edge("Evaluate Answer", "Follow-up Decision")
    dot.edge("Follow-up Decision", "Ask Question", label="follow-up")
    dot.edge("Follow-up Decision", "End", label="end")

    file_path = dot.render("interview_flow")
    print(f"Graph rendered at {file_path}")

# ---- Simulate running interview ----
for node in ["Intro", "Ask Question", "Evaluate Answer", "Follow-up Decision", "End"]:
    print(f"\n▶️ Running node: {node}")
    render_graph(active_node=node)
