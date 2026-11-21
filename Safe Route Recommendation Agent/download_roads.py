import osmnx as ox

# B.C. Road, Bantwal
CENTER = (12.88175, 75.02991)

# Download walking road network
ox.settings.use_cache = True

G = ox.graph_from_point(
    CENTER,
    dist=3000,
    network_type="walk",
    simplify=True
)

# Save road network
ox.save_graphml(
    G,
    filepath="bc_road_walk.graphml"
)

print("B.C. Road walking network downloaded!")
print("Nodes:", len(G.nodes))
print("Edges:", len(G.edges))