from os import environ
import json

import psycopg
from psycopg.types import TypeInfo
from psycopg.types.shapely import register_shapely

# coordinates to ID
vertices: dict[tuple[float, float], int] = {}
# ordered ID tuples (from, to)
edges = set()
# mapping between osm_id and edges for troubleshooting
vertex_mapping: dict[int, set[int]] = {}

with psycopg.connect(environ["POSTGIS_CONNSTR"]) as conn:
    info = TypeInfo.fetch(conn, "geometry")
    assert info is not None, "no geometry type found, is PostGIS installed?"
    register_shapely(info, conn)

    with conn.cursor(binary=True) as cur:
        cur.execute(
            """
        select
            ro.osm_id    as original_osm_id,
            ro.geom      as original_geom,
            ri.osm_id    as intersecting_osm_id,
            ri.geom      as intersecting_geom,
            ro.oneway    as original_oneway,
            ri.oneway    as intersecting_oneway

        from osm_data.osm.road_line ro
                join osm_data.osm.road_line ri ON st_intersects(ro.geom, ri.geom)
        -- ignore intersection with itself AND consider each pair only once
        AND ro.osm_id > ri.osm_id
        -- ignore bridges, not real intersections
        and not (GREATEST(ro.layer, ri.layer) > 0 and LEAST(ro.layer, ri.layer) < 0)
        and ro.route_cycle = TRUE
        and ri.route_cycle = TRUE
        """
        )

        they_intersect = 0
        they_dont_intersect = 0

        # I use the names "original" and "intersecting" for each row for clarity
        # but they are on the same level
        for record in cur:
            original_point_ids = []
            xs, ys = record[1].geoms[0].coords.xy
            for coord in zip(xs, ys):
                if coord not in vertices:
                    vertices[coord] = len(vertices) + 1
                if record[0] not in vertex_mapping:
                    vertex_mapping[record[0]] = set()
                vertex_mapping[record[0]].add(vertices[coord])
                original_point_ids.append(vertices[coord])

            intersecting_point_ids = []
            xs, ys = record[3].geoms[0].coords.xy
            for coord in zip(xs, ys):
                if coord not in vertices:
                    vertices[coord] = len(vertices) + 1
                if record[2] not in vertex_mapping:
                    vertex_mapping[record[2]] = set()
                vertex_mapping[record[2]].add(vertices[coord])
                intersecting_point_ids.append(vertices[coord])
            if set(original_point_ids).isdisjoint(set(intersecting_point_ids)):
                they_dont_intersect += 1
                # this could be an error, but taking some samples and checking in the map they do
                # not intersect (e.g. bridges, tunnels) so I just ignore these cases
            else:
                they_intersect += 1
                for from_p, to_p in zip(original_point_ids, original_point_ids[1:]):
                    edges.add((from_p, to_p))
                    if record[4]:
                        edges.add((to_p, from_p))
                for from_p, to_p in zip(
                    intersecting_point_ids, intersecting_point_ids[1:]
                ):
                    edges.add((from_p, to_p))
                    if record[5]:
                        edges.add((to_p, from_p))

        print(f"distinct points for navigation: {len(vertices)}")
        print(f"distinct edges for navigation: {len(edges)}")

        print(f"ways with a point in common (intersecting): {they_intersect}")
        print(
            f"ways without a point in common (not intersecting): {they_dont_intersect}"
        )

with open("osm_id_to_vertex_id.json", "w") as fw:
    json.dump({k: list(v) for k, v in vertex_mapping.items()}, fw, indent=2)

with open("edges.json", "w") as fw:
    json.dump(list(edges), fw, indent=2)

with open("vertices.json", "w") as fw:
    json.dump({v: k for k, v in vertices.items()}, fw, indent=2)
