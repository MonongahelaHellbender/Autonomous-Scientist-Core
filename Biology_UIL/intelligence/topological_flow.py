import pandas as pd
import numpy as np
import networkx as nx
from sklearn.datasets import load_breast_cancer
from sklearn.preprocessing import StandardScaler

def map_topological_flow():
    print("--- UIL Biological Intelligence: Mapping Topological Information Flow ---")
    
    # 1. Load Data
    raw_data = load_breast_cancer()
    df = pd.DataFrame(raw_data.data, columns=raw_data.feature_names)
    
    # 2. Filter for 'Spine' Hubs (High Mutual Information)
    # We create a graph where edges represent high correlation (>0.85)
    corr = df.corr().abs()
    G = nx.Graph()
    
    for i in range(len(corr.columns)):
        for j in range(i):
            if corr.iloc[i, j] > 0.85:
                G.add_edge(corr.columns[i], corr.columns[j], weight=corr.iloc[i, j])
    
    # 3. Analyze Flow (Centrality)
    # This identifies which variables are the 'gatekeepers' of the ~2.8 ID
    centrality = nx.degree_centrality(G)
    hubs = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
    
    # 4. Partition the Graph (Modularity)
    communities = list(nx.community.greedy_modularity_communities(G))
    
    print(f"\n=== TOPOLOGICAL FLOW REPORT ===")
    print(f"Primary Information Hub: {hubs[0][0]}")
    print(f"Information Gatekeeper:  {hubs[1][0]}")
    print(f"Number of Stable Communities: {len(communities)}")
    
    # 5. UIL Verdict: Structural Integrity of the ID
    # If the system has exactly 3-6 communities, it matches our ID verification.
    if 3 <= len(communities) <= 6:
        print(f"\n[VERDICT] FLOW MATCHES DIMENSION.")
        print(f"Logic: The ~{len(communities)} communities form the {len(communities)}-dimensional manifold found in Pass 3.")
    else:
        print("\n[VERDICT] FLOW MISMATCH.")
        print(f"Logic: Found {len(communities)} clusters, but expected ~3.")

if __name__ == "__main__":
    map_topological_flow()
