import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { Share2, RotateCcw, Play, Pause, Maximize2, Layers } from "lucide-react";

export default function CitationGraph3D({ graph, onSelectReference }) {
  const mountRef = useRef(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const [autoRotate, setAutoRotate] = useState(true);
  const [viewMode, setViewMode] = useState("3d"); // "3d" or "2d"

  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const rendererRef = useRef(null);
  const animFrameIdRef = useRef(null);
  const nodeMeshesRef = useRef([]);
  const isDraggingRef = useRef(false);
  const previousMousePositionRef = useRef({ x: 0, y: 0 });
  const rotationRef = useRef({ x: 0.3, y: 0.6 });
  const autoRotateRef = useRef(true);

  autoRotateRef.current = autoRotate;

  const getStatusColorHex = (status) => {
    switch (status) {
      case "verified_exact":
      case "user_verified":
        return 0x16a34a; // Green
      case "verified_probable":
        return 0x2563eb; // Royal Blue
      case "metadata_mismatch":
        return 0xd97706; // Amber
      case "unverified":
        return 0xdc2626; // Crimson
      default:
        return 0x64748b; // Slate
    }
  };

  const getStatusColorCss = (status) => {
    switch (status) {
      case "verified_exact":
      case "user_verified":
        return "#16a34a";
      case "verified_probable":
        return "#2563eb";
      case "metadata_mismatch":
        return "#d97706";
      case "unverified":
        return "#dc2626";
      default:
        return "#64748b";
    }
  };

  useEffect(() => {
    if (viewMode !== "3d" || !mountRef.current || !graph || !graph.nodes || graph.nodes.length <= 1) {
      return;
    }

    const container = mountRef.current;
    const width = container.clientWidth || 800;
    const height = 480;

    // 1. Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xfcfcfc);
    sceneRef.current = scene;

    // 2. Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 40, 220);
    camera.lookAt(0, 0, 0);
    cameraRef.current = camera;

    // 3. Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    container.innerHTML = "";
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // 4. Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.7);
    dirLight1.position.set(60, 100, 80);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0xe2e8f0, 0.4);
    dirLight2.position.set(-60, -40, -80);
    scene.add(dirLight2);

    // Subtle 3D Grid helper at base
    const grid = new THREE.GridHelper(260, 26, 0xe2e8f0, 0xf1f5f9);
    grid.position.y = -60;
    scene.add(grid);

    // 5. Build Graph Nodes
    const rootGroup = new THREE.Group();
    scene.add(rootGroup);

    const paperNode = graph.nodes.find((n) => n.type === "paper") || graph.nodes[0];
    const refNodes = graph.nodes.filter((n) => n.type !== "paper");
    const meshes = [];

    // Central Paper Node
    const centerGeo = new THREE.SphereGeometry(14, 32, 32);
    const centerMat = new THREE.MeshStandardMaterial({
      color: 0x0f172a,
      roughness: 0.3,
      metalness: 0.2,
      emissive: 0x1e293b,
      emissiveIntensity: 0.3,
    });
    const centerMesh = new THREE.Mesh(centerGeo, centerMat);
    centerMesh.position.set(0, 0, 0);
    centerMesh.userData = { nodeData: paperNode, isRoot: true };
    rootGroup.add(centerMesh);
    meshes.push(centerMesh);

    // Central paper orbital ring
    const ringGeo = new THREE.RingGeometry(18, 19, 64);
    const ringMat = new THREE.MeshBasicMaterial({ color: 0xcbd5e1, side: THREE.DoubleSide, transparent: true, opacity: 0.6 });
    const ringMesh = new THREE.Mesh(ringGeo, ringMat);
    ringMesh.rotation.x = Math.PI / 2;
    rootGroup.add(ringMesh);

    // Reference Nodes distributed in 3D Fibonacci sphere
    const totalRefs = refNodes.length;
    const radius = Math.min(85 + totalRefs * 2.5, 115);
    const goldenRatio = (1 + Math.sqrt(5)) / 2;

    refNodes.forEach((node, i) => {
      // Fibonacci sphere coordinates
      const theta = 2 * Math.PI * i / goldenRatio;
      const phi = Math.acos(1 - (2 * (i + 0.5)) / totalRefs);

      const x = radius * Math.sin(phi) * Math.cos(theta);
      const y = radius * Math.cos(phi) * 0.75; // flatten slightly vertically
      const z = radius * Math.sin(phi) * Math.sin(theta);

      const colorHex = getStatusColorHex(node.status);
      const nodeGeo = new THREE.SphereGeometry(6, 24, 24);
      const nodeMat = new THREE.MeshStandardMaterial({
        color: colorHex,
        roughness: 0.35,
        metalness: 0.15,
      });

      const nodeMesh = new THREE.Mesh(nodeGeo, nodeMat);
      nodeMesh.position.set(x, y, z);
      nodeMesh.userData = { nodeData: node, isRoot: false, baseColor: colorHex };
      rootGroup.add(nodeMesh);
      meshes.push(nodeMesh);

      // Line connecting center to reference
      const lineMat = new THREE.LineBasicMaterial({
        color: colorHex,
        transparent: true,
        opacity: node.status === "unverified" ? 0.3 : 0.55,
        linewidth: 1,
      });
      const points = [new THREE.Vector3(0, 0, 0), new THREE.Vector3(x, y, z)];
      const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
      const line = new THREE.Line(lineGeo, lineMat);
      rootGroup.add(line);
    });

    nodeMeshesRef.current = meshes;

    // 6. Interaction: Raycasting on Mouse Move & Click
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const handlePointerMove = (e) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      // Rotate group on drag
      if (isDraggingRef.current) {
        const deltaX = e.clientX - previousMousePositionRef.current.x;
        const deltaY = e.clientY - previousMousePositionRef.current.y;
        rotationRef.current.y += deltaX * 0.008;
        rotationRef.current.x += deltaY * 0.008;
        previousMousePositionRef.current = { x: e.clientX, y: e.clientY };
      }

      // Check intersections
      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(meshes, false);

      if (intersects.length > 0) {
        const hit = intersects[0].object;
        setHoveredNode(hit.userData.nodeData);
        setTooltipPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
        container.style.cursor = "pointer";

        // Highlight hit mesh
        meshes.forEach((m) => {
          if (m === hit) {
            m.scale.set(1.4, 1.4, 1.4);
          } else {
            m.scale.set(1, 1, 1);
          }
        });
      } else {
        setHoveredNode(null);
        container.style.cursor = isDraggingRef.current ? "grabbing" : "grab";
        meshes.forEach((m) => m.scale.set(1, 1, 1));
      }
    };

    const handleMouseDown = (e) => {
      if (e.button === 0) {
        isDraggingRef.current = true;
        previousMousePositionRef.current = { x: e.clientX, y: e.clientY };
      }
    };

    const handleMouseUp = (e) => {
      isDraggingRef.current = false;
    };

    const handleClick = (e) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(meshes, false);

      if (intersects.length > 0) {
        const hit = intersects[0].object;
        const nData = hit.userData.nodeData;
        if (!hit.userData.isRoot && nData) {
          const refId = parseInt(nData.id.replace("ref_", ""), 10);
          if (onSelectReference && !isNaN(refId)) {
            onSelectReference({ reference_id: refId });
          }
        }
      }
    };

    const handleWheel = (e) => {
      e.preventDefault();
      camera.position.z += e.deltaY * 0.15;
      camera.position.z = Math.max(90, Math.min(360, camera.position.z));
    };

    const dom = renderer.domElement;
    dom.addEventListener("mousemove", handlePointerMove);
    dom.addEventListener("mousedown", handleMouseDown);
    window.addEventListener("mouseup", handleMouseUp);
    dom.addEventListener("click", handleClick);
    dom.addEventListener("wheel", handleWheel, { passive: false });

    // 7. Animation Loop
    const animate = () => {
      animFrameIdRef.current = requestAnimationFrame(animate);

      if (autoRotateRef.current && !isDraggingRef.current) {
        rotationRef.current.y += 0.003;
      }

      rootGroup.rotation.y = rotationRef.current.y;
      rootGroup.rotation.x = rotationRef.current.x;

      renderer.render(scene, camera);
    };

    animate();

    // 8. Resize Listener
    const handleResize = () => {
      if (!container || !renderer || !camera) return;
      const newW = container.clientWidth;
      camera.aspect = newW / height;
      camera.updateProjectionMatrix();
      renderer.setSize(newW, height);
    };

    window.addEventListener("resize", handleResize);

    // Cleanup
    return () => {
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("mouseup", handleMouseUp);
      dom.removeEventListener("mousemove", handlePointerMove);
      dom.removeEventListener("mousedown", handleMouseDown);
      dom.removeEventListener("click", handleClick);
      dom.removeEventListener("wheel", handleWheel);

      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
      }
      if (renderer) {
        renderer.dispose();
      }
    };
  }, [graph, viewMode, onSelectReference]);

  if (!graph || !graph.nodes || graph.nodes.length <= 1) {
    return (
      <div className="academic-card" style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>
        <Share2 size={24} style={{ margin: "0 auto 0.5rem", display: "block" }} />
        <p style={{ fontSize: "0.875rem" }}>Insufficient reference data available to generate a 3D citation graph.</p>
      </div>
    );
  }

  const paperNode = graph.nodes.find((n) => n.type === "paper") || graph.nodes[0];
  const refNodes = graph.nodes.filter((n) => n.type !== "paper");

  const resetCamera = () => {
    rotationRef.current = { x: 0.3, y: 0.6 };
    if (cameraRef.current) {
      cameraRef.current.position.set(0, 40, 220);
      cameraRef.current.lookAt(0, 0, 0);
    }
  };

  return (
    <div className="academic-card" style={{ padding: "1.25rem", position: "relative" }}>
      {/* Header & Controls Bar */}
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: "0.75rem", marginBottom: "0.75rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <h3 style={{ fontSize: "0.9375rem", fontWeight: 600, color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "0.375rem", margin: 0 }}>
            <Share2 size={16} style={{ color: "var(--accent-primary)" }} />
            <span>Interactive 3D Citation Graph ({refNodes.length} nodes)</span>
          </h3>
        </div>

        {/* View Mode & Orbit Controls */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <button
            type="button"
            className="btn-secondary btn-sm"
            onClick={() => setViewMode(viewMode === "3d" ? "2d" : "3d")}
            title="Toggle between 3D WebGL and 2D Planar view"
          >
            <Layers size={13} />
            <span>{viewMode === "3d" ? "Switch to 2D" : "Switch to 3D"}</span>
          </button>

          {viewMode === "3d" && (
            <>
              <button
                type="button"
                className="btn-secondary btn-sm"
                onClick={() => setAutoRotate(!autoRotate)}
                title={autoRotate ? "Pause rotation" : "Auto rotate"}
              >
                {autoRotate ? <Pause size={13} /> : <Play size={13} />}
                <span>{autoRotate ? "Pause" : "Rotate"}</span>
              </button>

              <button
                type="button"
                className="btn-secondary btn-sm"
                onClick={resetCamera}
                title="Reset view angle"
              >
                <RotateCcw size={13} />
                <span>Reset</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Main 3D Canvas / 2D SVG View */}
      {viewMode === "3d" ? (
        <div
          ref={mountRef}
          style={{
            width: "100%",
            height: "480px",
            position: "relative",
            backgroundColor: "#fcfcfc",
            border: "1px solid var(--border-subtle)",
            borderRadius: "6px",
            overflow: "hidden",
            cursor: "grab",
          }}
        />
      ) : (
        /* 2D Planar View fallback */
        <div style={{ width: "100%", overflowX: "auto", border: "1px solid var(--border-subtle)", borderRadius: "6px", backgroundColor: "#FFFFFF", padding: "1rem" }}>
          <svg viewBox="0 0 800 450" style={{ width: "100%", height: "auto", display: "block" }}>
            {refNodes.map((node, i) => {
              const angle = (2 * Math.PI * i) / refNodes.length - Math.PI / 2;
              const x = 400 + 150 * Math.cos(angle);
              const y = 225 + 150 * Math.sin(angle);
              const color = getStatusColorCss(node.status);
              return (
                <g key={node.id}>
                  <line x1={400} y1={225} x2={x} y2={y} stroke="var(--border-subtle)" strokeWidth={1} strokeDasharray={node.status === "unverified" ? "4,4" : "none"} />
                  <circle
                    cx={x}
                    cy={y}
                    r={12}
                    fill={color}
                    stroke="#FFFFFF"
                    strokeWidth={2}
                    style={{ cursor: "pointer" }}
                    onClick={() => {
                      const refId = parseInt(node.id.replace("ref_", ""), 10);
                      if (onSelectReference && !isNaN(refId)) onSelectReference({ reference_id: refId });
                    }}
                  />
                  <text x={x} y={y + 3.5} textAnchor="middle" fill="#FFFFFF" fontSize="8" fontWeight="600" pointerEvents="none">
                    {node.label.replace("[", "").replace("]", "")}
                  </text>
                </g>
              );
            })}
            <circle cx={400} cy={225} r={22} fill="var(--accent-primary)" stroke="#FFFFFF" strokeWidth={2} />
            <text x={400} y={229} textAnchor="middle" fill="#FFFFFF" fontSize="10" fontWeight="600" pointerEvents="none">Paper</text>
          </svg>
        </div>
      )}

      {/* Floating 3D Tooltip */}
      {hoveredNode && viewMode === "3d" && (
        <div
          style={{
            position: "absolute",
            left: `${Math.min(tooltipPos.x + 12, (mountRef.current?.clientWidth || 800) - 260)}px`,
            top: `${Math.max(10, tooltipPos.y - 45)}px`,
            backgroundColor: "#FFFFFF",
            border: "1px solid var(--border-subtle)",
            boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
            borderRadius: "6px",
            padding: "0.5rem 0.75rem",
            fontSize: "0.75rem",
            pointerEvents: "none",
            zIndex: 10,
            maxWidth: "280px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.5rem", marginBottom: "0.25rem" }}>
            <span style={{ fontWeight: 700, color: "var(--text-primary)" }}>{hoveredNode.label}</span>
            <span style={{ color: getStatusColorCss(hoveredNode.status), fontWeight: 600, textTransform: "capitalize", fontSize: "0.7rem" }}>
              {hoveredNode.status.replace("_", " ")}
            </span>
          </div>
          <div style={{ color: "var(--text-secondary)", marginBottom: "0.25rem", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {hoveredNode.title || (hoveredNode.type === "paper" ? "Current Analyzed Paper" : "Scholarly reference")}
          </div>
          {hoveredNode.score !== undefined && hoveredNode.score !== null && (
            <div style={{ color: "var(--text-muted)", fontSize: "0.7rem" }}>
              Score: <strong>{hoveredNode.score}/100</strong> • Click node to inspect details
            </div>
          )}
        </div>
      )}

      {/* Academic Status Legend */}
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: "0.75rem", marginTop: "0.75rem", paddingTop: "0.5rem", borderTop: "1px solid var(--border-subtle)", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem" }}>
          <span style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
            <span style={{ width: "9px", height: "9px", borderRadius: "50%", backgroundColor: "#16a34a" }} />
            Verified Exact
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
            <span style={{ width: "9px", height: "9px", borderRadius: "50%", backgroundColor: "#2563eb" }} />
            Probable Match
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
            <span style={{ width: "9px", height: "9px", borderRadius: "50%", backgroundColor: "#d97706" }} />
            Metadata Warning
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
            <span style={{ width: "9px", height: "9px", borderRadius: "50%", backgroundColor: "#dc2626" }} />
            Unverified / Hallucination
          </span>
        </div>
        <div style={{ color: "var(--text-muted)", fontSize: "0.7rem" }}>
          💡 Drag to rotate in 3D • Scroll wheel to zoom • Click any sphere to view citation audit
        </div>
      </div>
    </div>
  );
}
