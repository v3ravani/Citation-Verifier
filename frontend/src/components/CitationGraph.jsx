import React, { useState } from "react";
import { Share2 } from "lucide-react";

export default function CitationGraph({ graph, onSelectReference }) {
  const [hoveredNode, setHoveredNode] = useState(null);

  if (!graph || !graph.nodes || graph.nodes.length <= 1) {
    return (
      <div className="academic-card" style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>
        <Share2 size={24} style={{ margin: "0 auto 0.5rem", display: "block" }} />
        <p style={{ fontSize: "0.875rem" }}>Insufficient reference data available to generate a citation relationship graph.</p>
      </div>
    );
  }

  const paperNode = graph.nodes.find((n) => n.type === "paper") || graph.nodes[0];
  const refNodes = graph.nodes.filter((n) => n.type !== "paper");

  const width = 800;
  const height = 450;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) * 0.38;

  // Calculate radial positions for reference nodes
  const totalRefs = refNodes.length;
  const positionedRefs = refNodes.map((node, i) => {
    const angle = (2 * Math.PI * i) / totalRefs - Math.PI / 2;
    return {
      ...node,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
  });

  const getStatusColor = (status) => {
    switch (status) {
      case "verified_exact":
      case "user_verified":
        return "#10B981"; // Emerald
      case "verified_probable":
        return "#3B82F6"; // Blue
      case "metadata_mismatch":
        return "#F59E0B"; // Amber
      case "unverified":
        return "#EF4444"; // Red
      default:
        return "#94A3B8"; // Slate
    }
  };

  return (
    <div className="academic-card" style={{ padding: "1.25rem", position: "relative" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.75rem" }}>
        <h3 style={{ fontSize: "0.9375rem", fontWeight: 600, color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "0.375rem" }}>
          <Share2 size={16} style={{ color: "var(--accent-primary)" }} />
          <span>Citation Relationship Network</span>
        </h3>
        {/* Legend */}
        <div style={{ display: "flex", gap: "1rem", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
          <span style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
            <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#10B981" }} />
            Verified Exact
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
            <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#3B82F6" }} />
            Probable
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
            <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#F59E0B" }} />
            Mismatch
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
            <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#EF4444" }} />
            Unverified
          </span>
        </div>
      </div>

      <div style={{ width: "100%", overflowX: "auto", border: "1px solid var(--border-subtle)", borderRadius: "6px", backgroundColor: "var(--bg-secondary)" }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: "auto", display: "block", minHeight: "340px" }}>
          {/* Edges from center paper to references */}
          {positionedRefs.map((node) => (
            <line
              key={`edge-${node.id}`}
              x1={centerX}
              y1={centerY}
              x2={node.x}
              y2={node.y}
              stroke="var(--border-subtle)"
              strokeWidth={hoveredNode && hoveredNode.id === node.id ? 2 : 1}
              strokeDasharray={node.status === "unverified" ? "4,4" : "none"}
            />
          ))}

          {/* Center Paper Node */}
          <g>
            <circle
              cx={centerX}
              cy={centerY}
              r={24}
              fill="var(--accent-primary)"
              stroke="#FFFFFF"
              strokeWidth={2}
            />
            <text
              x={centerX}
              y={centerY + 4}
              textAnchor="middle"
              fill="#FFFFFF"
              fontSize="10"
              fontWeight="600"
              pointerEvents="none"
            >
              Paper
            </text>
          </g>

          {/* Reference Nodes */}
          {positionedRefs.map((node) => {
            const color = getStatusColor(node.status);
            const isHovered = hoveredNode && hoveredNode.id === node.id;
            return (
              <g
                key={node.id}
                onClick={() => {
                  const refId = parseInt(node.id.replace("ref_", ""), 10);
                  if (onSelectReference && !isNaN(refId)) {
                    onSelectReference({ reference_id: refId });
                  }
                }}
                onMouseEnter={() => setHoveredNode(node)}
                onMouseLeave={() => setHoveredNode(null)}
                style={{ cursor: "pointer" }}
              >
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={isHovered ? 16 : 13}
                  fill={color}
                  stroke="#FFFFFF"
                  strokeWidth={2}
                  style={{ transition: "all 0.15s ease" }}
                />
                <text
                  x={node.x}
                  y={node.y + 3.5}
                  textAnchor="middle"
                  fill="#FFFFFF"
                  fontSize="8"
                  fontWeight="600"
                  pointerEvents="none"
                >
                  {node.label.replace("[", "").replace("]", "")}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Hover Info Tooltip */}
      {hoveredNode && (
        <div style={{ marginTop: "0.5rem", padding: "0.5rem 0.75rem", backgroundColor: "var(--bg-primary)", border: "1px solid var(--border-subtle)", borderRadius: "4px", fontSize: "0.75rem", display: "flex", justifyContent: "space-between" }}>
          <div>
            <strong>{hoveredNode.label}:</strong> {hoveredNode.title || "Scholarly reference"}
          </div>
          <div style={{ textTransform: "capitalize", color: getStatusColor(hoveredNode.status), fontWeight: 600 }}>
            {hoveredNode.status.replace("_", " ")}
          </div>
        </div>
      )}
    </div>
  );
}
