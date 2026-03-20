const graphNodes = new vis.DataSet();
const graphEdges = new vis.DataSet();

new vis.Network(document.getElementById('graph-container'), {
  nodes: graphNodes, edges: graphEdges
}, {
  layout: {
    hierarchical: {
      enabled: true, direction: 'UD', sortMethod: 'directed',
      levelSeparation: 140, nodeSpacing: 180
    }
  },
  physics: {
    hierarchicalRepulsion: { springLength: 180, nodeDistance: 220 },
    stabilization: { iterations: 150 }
  },
  nodes: {
    font: { size: 13, color: '#2c2c2c', face: 'sans-serif' },
    borderWidth: 2, shape: 'dot'
  },
  edges: {
    smooth: { type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.4 },
    width: 1.5
  },
  interaction: { hover: true, zoomView: true, dragView: true, dragNodes: true }
});

window.updateGraph = function (data) {
  const existingNodeIds = new Set(graphNodes.getIds());
  const existingEdgeIds = new Set(graphEdges.getIds());

  const newNodes = data.nodes.filter(n => !existingNodeIds.has(n.id));
  const newEdges = data.edges.filter(e => {
    const eid = e.from + '→' + e.to;
    return !existingEdgeIds.has(eid);
  });

  newEdges.forEach(e => { e.id = e.from + '→' + e.to; });

  if (newNodes.length) graphNodes.add(newNodes);
  if (newEdges.length) graphEdges.add(newEdges);

  const empty = document.querySelector('.graph-empty');
  if (empty && graphNodes.length) empty.style.display = 'none';
};
