import json
import random
import uuid

def generate_graph_json(num_nodes, output_filename="generated_graph.json"):
    """
    Generate a JSON file with specified number of nodes and random edges
    
    Args:
        num_nodes (int): Number of nodes to generate
        output_filename (str): Name of output JSON file
    """
    
    # Sample node types based on your document
    node_types = [
        "方剂", "药材", "药理", "疾病", "中医概念"
    ]
    
    # Sample relation types for edges
    relation_types = [
        "治法", "方剂组成包含", "对应", "包含", "等同于", 
        "中气为", "分布于", "主导", "承气为", "生", "成", "产生", "克"
    ]
    
    # Generate unique node names
    nodes = []
    node_names = set()
    
    for i in range(num_nodes):
        # Generate unique name
        while True:
            name = f"节点_{i+1}_{uuid.uuid4().hex[:6]}"
            if name not in node_names:
                node_names.add(name)
                break
        
        # Create node
        node = {
            "name": name,
            "type": random.choice(node_types),
            "attributes": random.choice([{}, random.randint(1, 1000)]),
            "resources": []
        }
        
        nodes.append(node)
    
    # Generate edges (relationships between nodes)
    edges = []
    node_names_list = list(node_names)
    
    # Generate random number of edges (roughly 0.5 to 2 times the number of nodes)
    num_edges = random.randint(num_nodes // 2, num_nodes * 2)
    
    for _ in range(num_edges):
        source = random.choice(node_names_list)
        target = random.choice(node_names_list)
        
        # Avoid self-loops
        if source != target:
            edge = {
                "source": source,
                "target": target,
                "relation_type": random.choice(relation_types),
                "resources": []
            }
            edges.append(edge)
    
    # Create final structure
    graph_data = {
        "nodes": nodes,
        "edges": edges
    }
    
    # Write to JSON file
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, ensure_ascii=False, indent=4)
    
    print(f"Generated graph with {len(nodes)} nodes and {len(edges)} edges")
    print(f"Saved to {output_filename}")
    
    return graph_data

# Example usage
if __name__ == "__main__":
    # Generate graph with specified number of nodes
    num_nodes = int(input("请输入要生成的节点数量: "))
    
    # Optional: specify output filename
    filename = input("请输入输出文件名 (回车使用默认名称): ").strip()
    if not filename:
        filename = "generated_graph.json"
    
    # Generate the graph
    generated_data = generate_graph_json(num_nodes, filename)
    
    # Print some statistics
    print(f"\n统计信息:")
    print(f"节点数量: {len(generated_data['nodes'])}")
    print(f"边数量: {len(generated_data['edges'])}")
    
    # Show first few nodes as example
    print(f"\n前3个节点示例:")
    for i, node in enumerate(generated_data['nodes'][:3]):
        print(f"{i+1}. {node['name']} ({node['type']})")