"""Browser relationship viewer and static SVG graph writer."""

from __future__ import annotations

import math
from html import escape
from pathlib import Path
from typing import Any


def relationship_viewer_html() -> str:
    """Return a dependency-free interactive graph viewer page."""
    return r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Document Relationship Viewer</title>
  <style>
    :root { --bg:#f4f7fb; --panel:#ffffff; --text:#172033; --muted:#64748b; --line:#94a3b8; --accent:#2563eb; }
    * { box-sizing:border-box; }
    body { margin:0; font-family:Arial,Helvetica,sans-serif; background:var(--bg); color:var(--text); }
    header { display:flex; justify-content:space-between; align-items:center; padding:18px 24px; background:#0f172a; color:white; }
    header h1 { margin:0; font-size:21px; }
    header a { color:#bfdbfe; text-decoration:none; margin-left:16px; }
    .layout { display:grid; grid-template-columns:minmax(0,1fr) 330px; gap:16px; padding:16px; height:calc(100vh - 65px); }
    .graph-card,.panel { background:var(--panel); border-radius:12px; box-shadow:0 2px 10px rgba(15,23,42,.08); overflow:hidden; }
    .toolbar { display:flex; gap:10px; align-items:center; padding:12px 16px; border-bottom:1px solid #e2e8f0; }
    .toolbar input { width:280px; padding:9px 11px; border:1px solid #cbd5e1; border-radius:8px; }
    .toolbar button { border:0; background:var(--accent); color:white; padding:9px 13px; border-radius:8px; cursor:pointer; }
    #graph { width:100%; height:calc(100% - 57px); min-height:520px; }
    .panel { padding:18px; overflow:auto; }
    .panel h2 { font-size:17px; margin:0 0 12px; }
    .metric { display:grid; grid-template-columns:1fr auto; gap:8px; padding:8px 0; border-bottom:1px solid #eef2f7; }
    .muted { color:var(--muted); font-size:13px; }
    .legend { margin-top:18px; }
    .legend div { margin:8px 0; font-size:13px; }
    .dot { display:inline-block; width:11px; height:11px; border-radius:50%; margin-right:7px; }
    .details { margin-top:20px; padding:12px; background:#f8fafc; border-radius:8px; font-size:13px; white-space:pre-wrap; }
    .edge { stroke:var(--line); stroke-width:1.5; marker-end:url(#arrow); opacity:.75; }
    .edge-label { font-size:10px; fill:#475569; pointer-events:none; }
    .node circle,.node rect { stroke:white; stroke-width:2; filter:drop-shadow(0 1px 2px rgba(0,0,0,.2)); cursor:pointer; }
    .node text { font-size:11px; fill:#0f172a; pointer-events:none; text-anchor:middle; }
    @media(max-width:900px){ .layout{grid-template-columns:1fr;height:auto}.graph-card{height:650px}.panel{min-height:280px} }
  </style>
</head>
<body>
<header>
  <h1>AI Document Relationship Viewer</h1>
  <nav><a href="/dashboard">Dashboard</a><a href="/docs">API Docs</a></nav>
</header>
<div class="layout">
  <div class="graph-card">
    <div class="toolbar">
      <input id="search" placeholder="Filter by title, type, or filename">
      <button id="reload">Reload Graph</button>
      <span id="status" class="muted"></span>
    </div>
    <svg id="graph" role="img" aria-label="Document relationship graph"></svg>
  </div>
  <aside class="panel">
    <h2>Graph Summary</h2>
    <div id="summary"></div>
    <div class="legend">
      <h2>Legend</h2>
      <div><span class="dot" style="background:#2563eb"></span>Drawing / Shop Drawing</div>
      <div><span class="dot" style="background:#7c3aed"></span>Specification</div>
      <div><span class="dot" style="background:#dc2626"></span>RFI</div>
      <div><span class="dot" style="background:#059669"></span>Meeting Minutes</div>
      <div><span class="dot" style="background:#f59e0b"></span>Action Item</div>
      <div><span class="dot" style="background:#64748b"></span>Other Document</div>
    </div>
    <h2 style="margin-top:22px">Selected Item</h2>
    <div id="details" class="details">Click a node to view details.</div>
  </aside>
</div>
<script>
const svg = document.getElementById('graph');
const statusEl = document.getElementById('status');
const summaryEl = document.getElementById('summary');
const detailsEl = document.getElementById('details');
let graphData = {nodes:[],edges:[]};

function color(group){
  const g=(group||'').toLowerCase();
  if(g.includes('drawing')) return '#2563eb';
  if(g.includes('specification')) return '#7c3aed';
  if(g==='rfi') return '#dc2626';
  if(g.includes('meeting')) return '#059669';
  if(g.includes('action')) return '#f59e0b';
  return '#64748b';
}
function shortLabel(text,max=24){ text=String(text||''); return text.length>max?text.slice(0,max-1)+'…':text; }
function element(name,attrs={}){ const el=document.createElementNS('http://www.w3.org/2000/svg',name); Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,v)); return el; }
function render(filter=''){
  svg.innerHTML='';
  const width=svg.clientWidth||900, height=svg.clientHeight||600;
  svg.setAttribute('viewBox',`0 0 ${width} ${height}`);
  const defs=element('defs');
  const marker=element('marker',{id:'arrow',viewBox:'0 0 10 10',refX:'9',refY:'5',markerWidth:'6',markerHeight:'6',orient:'auto-start-reverse'});
  marker.appendChild(element('path',{d:'M 0 0 L 10 5 L 0 10 z',fill:'#94a3b8'})); defs.appendChild(marker); svg.appendChild(defs);

  const q=filter.trim().toLowerCase();
  const matched=new Set(graphData.nodes.filter(n=>!q||JSON.stringify(n).toLowerCase().includes(q)).map(n=>n.id));
  const edges=graphData.edges.filter(e=>matched.has(e.source)&&matched.has(e.target));
  const used=new Set(edges.flatMap(e=>[e.source,e.target]));
  const nodes=graphData.nodes.filter(n=>matched.has(n.id)&&(!q||used.has(n.id)||graphData.nodes.length===1));
  const cx=width/2, cy=height/2, radius=Math.max(150,Math.min(width,height)*.36);
  const pos={};
  nodes.forEach((n,i)=>{ const angle=(Math.PI*2*i/Math.max(1,nodes.length))-Math.PI/2; pos[n.id]={x:cx+radius*Math.cos(angle),y:cy+radius*Math.sin(angle)}; });

  edges.forEach(e=>{
    if(!pos[e.source]||!pos[e.target]) return;
    const p1=pos[e.source],p2=pos[e.target];
    svg.appendChild(element('line',{x1:p1.x,y1:p1.y,x2:p2.x,y2:p2.y,class:'edge'}));
    const t=element('text',{x:(p1.x+p2.x)/2,y:(p1.y+p2.y)/2-4,class:'edge-label'}); t.textContent=shortLabel(e.label.replaceAll('_',' '),25); svg.appendChild(t);
  });

  nodes.forEach(n=>{
    const p=pos[n.id],g=element('g',{class:'node',tabindex:'0'});
    if(n.entity_type==='action_item') g.appendChild(element('rect',{x:p.x-36,y:p.y-18,width:72,height:36,rx:7,fill:color(n.group)}));
    else g.appendChild(element('circle',{cx:p.x,cy:p.y,r:27,fill:color(n.group)}));
    const label=element('text',{x:p.x,y:p.y+45}); label.textContent=shortLabel(n.label,28); g.appendChild(label);
    const show=()=>{detailsEl.textContent=JSON.stringify(n,null,2)}; g.addEventListener('click',show); g.addEventListener('keypress',show); svg.appendChild(g);
  });
  statusEl.textContent=`${nodes.length} nodes · ${edges.length} edges`;
}
async function load(){
  statusEl.textContent='Loading…';
  const response=await fetch('/relationships/graph-data?limit=300&include_action_items=true');
  graphData=await response.json();
  const s=graphData.summary||{};
  summaryEl.innerHTML=`<div class="metric"><span>Nodes</span><b>${s.nodes||0}</b></div><div class="metric"><span>Edges</span><b>${s.edges||0}</b></div><div class="metric"><span>Documents</span><b>${s.document_nodes||0}</b></div><div class="metric"><span>Action Items</span><b>${s.action_item_nodes||0}</b></div>`;
  render(document.getElementById('search').value);
}
document.getElementById('search').addEventListener('input',e=>render(e.target.value));
document.getElementById('reload').addEventListener('click',load);
window.addEventListener('resize',()=>render(document.getElementById('search').value));
load().catch(error=>{statusEl.textContent='Could not load graph';detailsEl.textContent=String(error)});
</script>
</body>
</html>
"""


def write_graph_svg(graph_data: dict[str, Any], output_path: str | Path) -> Path:
    """Write a simple standalone SVG relationship graph for demonstrations."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    width, height = 1200, 800
    cx, cy = width / 2, height / 2
    radius = min(width, height) * 0.36
    positions: dict[str, tuple[float, float]] = {}
    for index, node in enumerate(nodes):
        angle = (2 * math.pi * index / max(1, len(nodes))) - math.pi / 2
        positions[node["id"]] = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))

    color_map = {
        "Drawing": "#2563eb",
        "Shop Drawing": "#2563eb",
        "Specification": "#7c3aed",
        "RFI": "#dc2626",
        "Meeting Minutes": "#059669",
        "Action Item": "#f59e0b",
    }
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8"/></marker></defs>',
        '<text x="35" y="45" font-family="Arial" font-size="26" font-weight="bold" fill="#0f172a">Week 20 Document Relationship Graph</text>',
    ]
    for edge in edges:
        if edge["source"] not in positions or edge["target"] not in positions:
            continue
        x1, y1 = positions[edge["source"]]
        x2, y2 = positions[edge["target"]]
        lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#94a3b8" stroke-width="2" marker-end="url(#arrow)"/>')
        label = escape(str(edge.get("label", "")).replace("_", " "))
        lines.append(f'<text x="{(x1+x2)/2:.1f}" y="{(y1+y2)/2-5:.1f}" font-family="Arial" font-size="11" fill="#475569" text-anchor="middle">{label}</text>')
    for node in nodes:
        x, y = positions[node["id"]]
        fill = color_map.get(str(node.get("group")), "#64748b")
        label = escape(str(node.get("label", "")))
        if len(label) > 34:
            label = label[:33] + "…"
        if node.get("entity_type") == "action_item":
            lines.append(f'<rect x="{x-42:.1f}" y="{y-21:.1f}" width="84" height="42" rx="8" fill="{fill}" stroke="#fff" stroke-width="2"/>')
        else:
            lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="31" fill="{fill}" stroke="#fff" stroke-width="3"/>')
        lines.append(f'<text x="{x:.1f}" y="{y+50:.1f}" font-family="Arial" font-size="12" fill="#0f172a" text-anchor="middle">{label}</text>')
    lines.append('</svg>')
    output.write_text("\n".join(lines), encoding="utf-8")
    return output
