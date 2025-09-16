import React, { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { useAppStore } from "../store";
import { fccToWorld } from "../lib/fcc";

// Compute center using correct FCC conversion
function computeCenter(cells: [number,number,number][], scale = 0.5) {
  if (!cells.length) return { x: 0, y: 0, z: 0 };
  let sx = 0, sy = 0, sz = 0;
  for (const [x,y,z] of cells) {
    const w = fccToWorld(x, y, z, scale);
    sx += w.x; sy += w.y; sz += w.z;
  }
  const n = cells.length;
  return { x: sx / n, y: sy / n, z: sz / n };
}

type Placement = { piece: string; ori: number; t: [number,number,number] };

const COLORS = [
  "#4e79a7","#f28e2b","#e15759","#76b7b2","#59a14f",
  "#edc949","#af7aa1","#ff9da7","#9c755f","#bab0ab"
];

function pieceColor(id: string) {
  const idx = (id.charCodeAt(0) - 65) % COLORS.length; // 'A'.. maps
  return new THREE.Color(COLORS[(idx+COLORS.length)%COLORS.length]);
}

export const Viewer3D: React.FC = () => {
  const containerObj = useAppStore(s => s.containerObj);
  const solutionObj  = useAppStore(s => s.solutionObj);
  const selectedIdx  = useAppStore(s => s.selectedPlacementIdx);
  const setSelected  = useAppStore(s => s.setSelectedPlacementIdx);

  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene>();
  const cameraRef = useRef<THREE.PerspectiveCamera>();
  const rendererRef = useRef<THREE.WebGLRenderer>();
  const controlsRef = useRef<OrbitControls>();

  // Derived data
  const containerCells: [number,number,number][] = useMemo(() => {
    if (!containerObj?.coordinates) return [];
    return containerObj.coordinates as [number,number,number][];
  }, [containerObj]);

  const placements: Placement[] = useMemo(() => {
    if (!solutionObj?.placements) return [];
    return solutionObj.placements as Placement[];
  }, [solutionObj]);

  // Build a flat list of all covered cells from placements (approx: display anchors only in M2)
  // For MVP we'll render container cells + anchors of placements (the 't' positions).
  const placementAnchors: { pos: [number,number,number], color: THREE.Color }[] = useMemo(() => {
    return placements.map(p => ({ pos: p.t, color: pieceColor(p.piece) }));
  }, [placements]);

  useEffect(() => {
    const mount = mountRef.current!;
    const width = mount.clientWidth || mount.parentElement?.clientWidth || 800;
    const height = mount.clientHeight || 600;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#ffffff");
    const camera = new THREE.PerspectiveCamera(45, width/height, 0.1, 2000);
    camera.position.set(8, 10, 16);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    mount.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;

    // Lights
    const amb = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(amb);
    const dir = new THREE.DirectionalLight(0xffffff, 0.6);
    dir.position.set(5,10,7);
    scene.add(dir);

    // Grid (optional visual aid)
    const grid = new THREE.GridHelper(40, 40, 0xcccccc, 0xeeeeee);
    grid.rotation.x = Math.PI/2; // align with xy plane visually
    scene.add(grid);

    // Save refs
    sceneRef.current = scene;
    cameraRef.current = camera;
    rendererRef.current = renderer;
    controlsRef.current = controls;

    const onResize = () => {
      const w = mount.clientWidth || 800;
      const h = mount.clientHeight || 600;
      renderer.setSize(w,h);
      camera.aspect = w/h;
      camera.updateProjectionMatrix();
    };
    window.addEventListener("resize", onResize);

    let raf = 0;
    const animate = () => {
      raf = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", onResize);
      controls.dispose();
      renderer.dispose();
      mount.removeChild(renderer.domElement);
    };
  }, []);

  // (Re)build content when data changes
  useEffect(() => {
    const scene = sceneRef.current;
    if (!scene) return;

    // Clear previous content except lights/grid
    for (let i = scene.children.length - 1; i >= 0; i--) {
      const obj = scene.children[i];
      if ((obj as any).isLight || obj.type === "GridHelper") continue;
      scene.remove(obj);
    }

    const SCALE = 0.5;

    // Compute center of container to frame the scene
    const center = computeCenter(containerCells, SCALE);

    // Draw container cells as small gray spheres
    const cellGeom = new THREE.SphereGeometry(0.14, 16, 16);
    const cellMat = new THREE.MeshStandardMaterial({ color: 0x999999, metalness: 0.0, roughness: 0.8 });
    const contInst = new THREE.InstancedMesh(cellGeom, cellMat, containerCells.length);
    let i = 0;
    const m = new THREE.Matrix4();
    for (const [x,y,z] of containerCells) {
      const w = fccToWorld(x, y, z, SCALE);
      m.setPosition(w.x - center.x, w.y - center.y, w.z - center.z);
      contInst.setMatrixAt(i++, m);
    }
    contInst.instanceMatrix.needsUpdate = true;
    scene.add(contInst);

    // Draw placement anchors as colored spheres (MVP)
    const ancGeom = new THREE.SphereGeometry(0.18, 16, 16);
    const ancInst = new THREE.InstancedMesh(ancGeom, new THREE.MeshStandardMaterial({ color: 0xffffff }), placementAnchors.length);
    i = 0;
    for (const a of placementAnchors) {
      const w = fccToWorld(a.pos[0], a.pos[1], a.pos[2], SCALE);
      m.setPosition(w.x - center.x, w.y - center.y, w.z - center.z);
      ancInst.setMatrixAt(i, m);
      ancInst.setColorAt(i, a.color);
      i++;
    }
    ancInst.instanceColor!.needsUpdate = true;
    ancInst.instanceMatrix.needsUpdate = true;
    scene.add(ancInst);

  }, [containerCells, placementAnchors]);

  return <div ref={mountRef} style={{ width:"100%", height:"calc(100vh - 140px)" }} />;
};
