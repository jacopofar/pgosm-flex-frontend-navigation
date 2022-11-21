import Graph from "graphology";
import { bidirectional } from "graphology-shortest-path";
import proj4 from "proj4";

const FROM_VERTEX_ID = 277088;
const TO_VERTEX_ID = 211586;

async function processGraph() {
  console.log("Fetching data files...");
  const verticesResponse = await fetch("vertices.json");
  const edgesResponse = await fetch("edges.json");
  console.log("fetch done, parsing them");
  const vertices = await verticesResponse.json();
  console.log("vertices loaded");
  const edges = await edgesResponse.json();
  console.log("edges loaded");
  const graph = new Graph();

  for (let [fromIdx, toIdx] of edges) {
    try {
      graph.addNode(fromIdx);
    } catch (e) {}
    try {
      graph.addNode(toIdx);
    } catch (e) {}
    graph.addEdge(fromIdx, toIdx);
  }
  console.log("graph object created");
  console.log("Number of nodes", graph.order);
  console.log("Number of edges", graph.size);
  const path = bidirectional(graph, FROM_VERTEX_ID, TO_VERTEX_ID);
  if (path === null) {
    console.log("no path found!");
    return;
  }
  console.log("path calculated, size", path.length);
  const coords3857 = path.map((e) => vertices[e]);
  console.log(coords3857);
  const coords4326 = coords3857.map((coord) =>
    proj4("EPSG:3857", "EPSG:4326", coord)
  );
  console.log(coords4326);
  const geoJSON = {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        properties: {},
        geometry: {
          type: "LineString",
          coordinates: coords4326,
        },
      },
    ],
  };
  console.log(geoJSON);
}

processGraph();
