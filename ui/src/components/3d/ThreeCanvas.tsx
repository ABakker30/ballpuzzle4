import React, { useRef, useEffect, forwardRef, useImperativeHandle } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

export interface ThreeCanvasRef {
  fit: (bounds: THREE.Box3) => void;
  setTarget: (center: THREE.Vector3) => void;
}

export interface ThreeCanvasProps {
  children?: React.ReactNode;
  onReady?: (context: {
    scene: THREE.Scene;
    camera: THREE.PerspectiveCamera;
    controls: OrbitControls;
    renderer: THREE.WebGLRenderer;
  }) => void;
  onFrame?: (deltaTime: number) => void;
}

export const ThreeCanvas = forwardRef<ThreeCanvasRef, ThreeCanvasProps>(
  ({ children, onReady, onFrame }, ref) => {
    const mountRef = useRef<HTMLDivElement>(null);
    const sceneRef = useRef<THREE.Scene>();
    const cameraRef = useRef<THREE.PerspectiveCamera>();
    const rendererRef = useRef<THREE.WebGLRenderer>();
    const controlsRef = useRef<OrbitControls>();
    const frameIdRef = useRef<number>();
    const clockRef = useRef<THREE.Clock>();

    useImperativeHandle(ref, () => ({
      fit: (bounds: THREE.Box3) => {
        if (!cameraRef.current || !controlsRef.current) return;
        
        const center = bounds.getCenter(new THREE.Vector3());
        const size = bounds.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        
        // Position camera to fit the bounds
        const distance = maxDim * 2;
        cameraRef.current.position.copy(center);
        cameraRef.current.position.add(new THREE.Vector3(distance, distance, distance));
        cameraRef.current.lookAt(center);
        
        controlsRef.current.target.copy(center);
        controlsRef.current.update();
      },
      setTarget: (center: THREE.Vector3) => {
        if (!controlsRef.current) return;
        
        controlsRef.current.target.copy(center);
        controlsRef.current.update();
      }
    }));

    useEffect(() => {
      if (!mountRef.current) return;

      const mount = mountRef.current;
      
      // Scene setup
      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0xffffff); // Pure white background
      sceneRef.current = scene;

      // Camera setup
      const camera = new THREE.PerspectiveCamera(
        45,
        mount.clientWidth / mount.clientHeight,
        0.1,
        1000
      );
      camera.position.set(10, 10, 10);
      cameraRef.current = camera;

      // Renderer setup
      const renderer = new THREE.WebGLRenderer({ 
        antialias: true,
        alpha: true,
        powerPreference: "high-performance"
      });
      renderer.setSize(mount.clientWidth, mount.clientHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      rendererRef.current = renderer;

      // Controls setup
      const controls = new OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.05;
      controls.enableZoom = true;
      controls.enablePan = true;
      controlsRef.current = controls;

      // Lighting setup - comprehensive multi-directional lighting
      const ambientLight = new THREE.AmbientLight(0x404040, 1.2);
      scene.add(ambientLight);

      // Main directional light (key light)
      const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
      directionalLight.position.set(10, 10, 5);
      directionalLight.castShadow = true;
      directionalLight.shadow.mapSize.width = 2048;
      directionalLight.shadow.mapSize.height = 2048;
      scene.add(directionalLight);

      // Fill lights from multiple directions for even illumination
      const fillLight1 = new THREE.DirectionalLight(0xffffff, 0.4);
      fillLight1.position.set(-10, 5, -5);
      scene.add(fillLight1);

      const fillLight2 = new THREE.DirectionalLight(0xffffff, 0.3);
      fillLight2.position.set(5, -10, 10);
      scene.add(fillLight2);

      const fillLight3 = new THREE.DirectionalLight(0xffffff, 0.3);
      fillLight3.position.set(-5, 10, -10);
      scene.add(fillLight3);

      // Back light to illuminate rear surfaces
      const backLight = new THREE.DirectionalLight(0xffffff, 0.5);
      backLight.position.set(-10, -10, -10);
      scene.add(backLight);

      // Clock for animation
      const clock = new THREE.Clock();
      clockRef.current = clock;

      // Animation loop
      const animate = () => {
        frameIdRef.current = requestAnimationFrame(animate);
        
        const deltaTime = clock.getDelta();
        
        controls.update();
        
        if (onFrame) {
          onFrame(deltaTime);
        }
        
        renderer.render(scene, camera);
      };

      // Handle resize
      const handleResize = () => {
        if (!mount) return;
        
        camera.aspect = mount.clientWidth / mount.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(mount.clientWidth, mount.clientHeight);
      };

      window.addEventListener('resize', handleResize);
      mount.appendChild(renderer.domElement);

      // Notify parent component
      onReady?.({ scene, camera, controls, renderer });

      animate();

      // Cleanup
      return () => {
        if (frameIdRef.current) {
          cancelAnimationFrame(frameIdRef.current);
        }
        window.removeEventListener('resize', handleResize);
        if (mount && renderer.domElement) {
          mount.removeChild(renderer.domElement);
        }
        renderer.dispose();
      };
    }, []);

    return (
      <div 
        ref={mountRef} 
        style={{ 
          width: '100%', 
          height: '100%',
          position: 'relative'
        }}
      >
        {children}
      </div>
    );
  }
);

ThreeCanvas.displayName = 'ThreeCanvas';
