import json

import pyproj
import networkx as nx


proj = pyproj.Transformer.from_crs(3857, 4326, always_xy=True)

with open("osm_id_to_vertex_id.json") as fr:
    vertex_mapping = {int(osm_id): idx for osm_id, idx in json.load(fr).items()}


with open("edges.json") as fr:
    edges = [(from_id, to_id) for [from_id, to_id] in json.load(fr)]

with open("vertices.json") as fr:
    vertices = {int(k): v for k, v in json.load(fr).items()}

# Hochstraße, Berlin
FROM_ID = 42690514
# Ehrenbergstraße, Berlin
TO_ID = 4685797


def shortest_path(from_osm_id, to_osm_id):
    G = nx.Graph()
    G.add_edges_from(edges)
    return nx.shortest_path(
        G, source=vertex_mapping[from_osm_id][0], target=vertex_mapping[to_osm_id][0]
    )


if __name__ == "__main__":
    path = shortest_path(FROM_ID, TO_ID)
    print(path)
    with open("shortest_path.json", "w") as fw:
        fw.write(
            """
        {
            "type": "FeatureCollection",
            "features": [
                {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
        """
        )
        coord_strings = []
        for point_id in path:
            lat, lon = vertices[point_id]
            lat, lon = proj.transform(lat, lon)
            coord_strings.append(f"[{lat}, {lon}]")
        fw.write(",\n".join(coord_strings))
        fw.write(
            """
                    ]
                }
                }
            ]
        }
        """
        )
