import * as THREE from 'three';
import QuickHull from 'quickhull3d';

export interface ConvexHullResult {
  center: THREE.Vector3;
  largestFaceNormal: THREE.Vector3;
  volume: number;
  faces: Array<{
    normal: THREE.Vector3;
    vertices: THREE.Vector3[];
    isLargest: boolean;
  }>;
}

/**
 * Compute convex hull of 3D points and find the largest face
 */
export function computeConvexHull(points: THREE.Vector3[]): ConvexHullResult | null {
  if (points.length < 4) {
    return null;
  }


  try {
    // Convert THREE.Vector3 points to QuickHull format (Float32Array for each point)
    const hullPoints = points.map(p => new Float32Array([p.x, p.y, p.z]));
    
    // Compute convex hull using QuickHull library
    const hull = QuickHull(hullPoints);
    
    // Convert QuickHull result to our face format
    const faces = convertQuickHullToFaces(hull, points);
    
      
    // Calculate bounding box and center
    const box = new THREE.Box3().setFromPoints(points);
    const center = new THREE.Vector3();
    box.getCenter(center);
    
    // Find largest face by area
    let maxArea = 0;
    let largestFaceNormal = new THREE.Vector3(0, 1, 0);
    
    faces.forEach((face: { normal: THREE.Vector3; vertices: THREE.Vector3[]; isLargest: boolean }) => {
      const area = calculateFaceArea(face.vertices);
      if (area > maxArea) {
        maxArea = area;
        largestFaceNormal = face.normal.clone();
      }
    });
    
    // Mark largest face
    faces.forEach((face: { normal: THREE.Vector3; vertices: THREE.Vector3[]; isLargest: boolean }) => {
      face.isLargest = face.normal.distanceTo(largestFaceNormal) < 0.001;
    });

    console.log('5. Largest face - Normal:', `(${largestFaceNormal.x.toFixed(2)}, ${largestFaceNormal.y.toFixed(2)}, ${largestFaceNormal.z.toFixed(2)})`, 'Area:', maxArea.toFixed(3));

    return {
      center,
      largestFaceNormal,
      volume: 0, // TODO: Calculate actual volume
      faces
    };
    
  } catch (error) {
    console.error('QuickHull failed, falling back to simplified algorithm:', error);
    return computeConvexHullFromSolution(points);
  }
}

/**
 * Compute convex hull from solution points using projection-based face detection
 */
export function computeConvexHullFromSolution(points: THREE.Vector3[]): ConvexHullResult {
  console.log(' 3. COMPUTING ACTUAL CONVEX HULL:');
  console.log('   Input points:', points.length);
  console.log('   All points:', points.map(p => `(${p.x.toFixed(1)}, ${p.y.toFixed(1)}, ${p.z.toFixed(1)})`));

  // Calculate bounding box and center
  const box = new THREE.Box3().setFromPoints(points);
  const center = new THREE.Vector3();
  box.getCenter(center);
  
  // For now, use simplified approach: test 6 primary directions to find largest projected face
  // TODO: Replace with proper 3D convex hull algorithm (QuickHull, etc.)
  const directions = [
    new THREE.Vector3(1, 0, 0),   // +X
    new THREE.Vector3(-1, 0, 0),  // -X
    new THREE.Vector3(0, 1, 0),   // +Y
    new THREE.Vector3(0, -1, 0),  // -Y
    new THREE.Vector3(0, 0, 1),   // +Z
    new THREE.Vector3(0, 0, -1),  // -Z
  ];
  
  let maxProjectedArea = 0;
  let largestFaceNormal = new THREE.Vector3(0, 1, 0);
  const faces: Array<{ normal: THREE.Vector3; vertices: THREE.Vector3[]; isLargest: boolean }> = [];
  
  console.log('   Testing', directions.length, 'orthogonal directions for largest face...');
  
  directions.forEach(direction => {
    const projectedPoints: { x: number; y: number }[] = [];
    
    // Create orthogonal basis for projection plane
    const up = Math.abs(direction.y) < 0.9 ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(1, 0, 0);
    const right = new THREE.Vector3().crossVectors(direction, up).normalize();
    const forward = new THREE.Vector3().crossVectors(right, direction).normalize();
    
    points.forEach(point => {
      const relative = point.clone().sub(center);
      projectedPoints.push({
        x: relative.dot(right),
        y: relative.dot(forward)
      });
    });
    
    // Calculate area of projected convex hull (simplified as bounding box area)
    let minX = Infinity, maxX = -Infinity;
    let minY = Infinity, maxY = -Infinity;
    
    projectedPoints.forEach(p => {
      minX = Math.min(minX, p.x);
      maxX = Math.max(maxX, p.x);
      minY = Math.min(minY, p.y);
      maxY = Math.max(maxY, p.y);
    });
    
    const projectedArea = (maxX - minX) * (maxY - minY);
    
    // Find vertices on this face (simplified - use bounding box corners)
    const faceVertices: THREE.Vector3[] = [];
    const corners = [
      new THREE.Vector3().addVectors(center, right.clone().multiplyScalar(minX)).add(forward.clone().multiplyScalar(minY)),
      new THREE.Vector3().addVectors(center, right.clone().multiplyScalar(maxX)).add(forward.clone().multiplyScalar(minY)),
      new THREE.Vector3().addVectors(center, right.clone().multiplyScalar(maxX)).add(forward.clone().multiplyScalar(maxY)),
      new THREE.Vector3().addVectors(center, right.clone().multiplyScalar(minX)).add(forward.clone().multiplyScalar(maxY))
    ];
    faceVertices.push(...corners);
    
    faces.push({
      normal: direction.clone(),
      vertices: faceVertices,
      isLargest: false
    });
    
    if (projectedArea > maxProjectedArea) {
      maxProjectedArea = projectedArea;
      largestFaceNormal = direction.clone();
    }
  });
  
  // Mark the largest face
  faces.forEach(face => {
    face.isLargest = face.normal.distanceTo(largestFaceNormal) < 0.001;
  });
  
  console.log('🔍 3. HULL FACES BY SURFACE AREA:');
  faces.forEach((face, i) => {
    const area = face.normal.equals(largestFaceNormal) ? maxProjectedArea : 'N/A';
    console.log(`   Face ${i}: Normal(${face.normal.x.toFixed(1)}, ${face.normal.y.toFixed(1)}, ${face.normal.z.toFixed(1)}) Area=${area} ${face.isLargest ? '← LARGEST' : ''}`);
  });
  
  console.log('🎯 4. SELECTED LARGEST FACE:', {
    normal: `(${largestFaceNormal.x.toFixed(2)}, ${largestFaceNormal.y.toFixed(2)}, ${largestFaceNormal.z.toFixed(2)})`,
    projectedArea: maxProjectedArea.toFixed(3),
    center: `(${center.x.toFixed(2)}, ${center.y.toFixed(2)}, ${center.z.toFixed(2)})`
  });
  
  // Debug: Test if face normal is actually different from Y-axis
  const yAxis = new THREE.Vector3(0, 1, 0);
  const dotProduct = largestFaceNormal.dot(yAxis);
  console.log('ConvexHull: Face normal dot Y-axis:', dotProduct.toFixed(3), '(1.0 = already aligned)');
  
  // If already aligned to Y, no rotation needed - this might be the issue!
  if (Math.abs(dotProduct) > 0.999) {
    console.log('ConvexHull: WARNING - Face normal already aligned to Y-axis, rotation will be minimal!');
  }
  
  return {
    center,
    largestFaceNormal,
    volume: box.getSize(new THREE.Vector3()).x * box.getSize(new THREE.Vector3()).y * box.getSize(new THREE.Vector3()).z,
    faces
  };
}

/**
 * Fallback convex hull computation using actual point analysis
 */
function computeConvexHullFallback(points: THREE.Vector3[]): ConvexHullResult {
  // Calculate bounding box
  const box = new THREE.Box3();
  points.forEach(point => box.expandByPoint(point));
  
  const center = new THREE.Vector3();
  box.getCenter(center);
  
  const size = new THREE.Vector3();
  box.getSize(size);
  
  // Analyze actual point distribution to find the most stable face
  // Count points near each face of the bounding box
  const tolerance = Math.min(size.x, size.y, size.z) * 0.1; // 10% tolerance
  
  const faceCounts = {
    minX: 0, maxX: 0,
    minY: 0, maxY: 0, 
    minZ: 0, maxZ: 0
  };
  
  points.forEach(point => {
    if (Math.abs(point.x - box.min.x) < tolerance) faceCounts.minX++;
    if (Math.abs(point.x - box.max.x) < tolerance) faceCounts.maxX++;
    if (Math.abs(point.y - box.min.y) < tolerance) faceCounts.minY++;
    if (Math.abs(point.y - box.max.y) < tolerance) faceCounts.maxY++;
    if (Math.abs(point.z - box.min.z) < tolerance) faceCounts.minZ++;
    if (Math.abs(point.z - box.max.z) < tolerance) faceCounts.maxZ++;
  });
  
  // Find face with most points (most stable for sitting)
  const faces = [
    { normal: new THREE.Vector3(-1, 0, 0), count: faceCounts.minX, area: size.y * size.z }, // -X face (points at min X)
    { normal: new THREE.Vector3(1, 0, 0), count: faceCounts.maxX, area: size.y * size.z },  // +X face (points at max X)
    { normal: new THREE.Vector3(0, -1, 0), count: faceCounts.minY, area: size.x * size.z }, // -Y face (points at min Y)
    { normal: new THREE.Vector3(0, 1, 0), count: faceCounts.maxY, area: size.x * size.z },  // +Y face (points at max Y)
    { normal: new THREE.Vector3(0, 0, -1), count: faceCounts.minZ, area: size.x * size.y }, // -Z face (points at min Z)
    { normal: new THREE.Vector3(0, 0, 1), count: faceCounts.maxZ, area: size.x * size.y },  // +Z face (points at max Z)
  ];
  
  // Sort by point count first (stability), then by area (size)
  faces.sort((a, b) => {
    if (b.count !== a.count) return b.count - a.count; // More points = more stable
    return b.area - a.area; // Larger area = better base
  });
  
  const largestFaceNormal = faces[0].normal.clone();
  
  console.log('ConvexHull: Face analysis:', faceCounts);
  console.log('ConvexHull: Selected face normal:', largestFaceNormal, 'with', faces[0].count, 'points');
  
  return {
    center,
    largestFaceNormal,
    volume: size.x * size.y * size.z,
    faces: faces.map(f => ({
      normal: f.normal,
      vertices: [], // Simplified for fallback
      isLargest: f.normal.distanceTo(largestFaceNormal) < 0.001
    }))
  };
}

/**
 * Calculate orientation matrix to align the largest face normal to a target axis
 * @param hullResult - Result from convex hull computation
 * @param target - Target axis ('Y' => align face normal to +Y (face lies on XZ, Y-up), 'Z' for Z-up)
 * @returns Rotation matrix
 */
export function calculateOrientationMatrix(
  hullResult: ConvexHullResult,
  target: 'Y' | 'Z' = 'Z'
): THREE.Matrix4 {
  const { largestFaceNormal } = hullResult;
  const faceNormal = largestFaceNormal.clone().normalize();
  
  // Target axis: +Y for Y-up (face normal points up), -Z for legacy
  const targetAxis =
    target === 'Y'
      ? new THREE.Vector3(0, -1, 0)  // Point down so largest face lies flat on XZ plane
      : new THREE.Vector3(0, 0, -1); // -Z for legacy viewer
  
  const q = new THREE.Quaternion().setFromUnitVectors(faceNormal, targetAxis);
  

  // Create rotation matrix
  const matrix = new THREE.Matrix4().makeRotationFromQuaternion(q);
  return matrix;
}

/**
 * Orient points using rotation matrix and optional center offset
 * @param points - Points to orient
 * @param rotationMatrix - Rotation matrix from calculateOrientationMatrix
 * @param centerOffset - Optional center to rotate around
 * @returns Oriented and grounded points with ground offset
 */
export function orientPoints(
  points: THREE.Vector3[],
  rotationMatrix: THREE.Matrix4,
  centerOffset?: THREE.Vector3
): { points: THREE.Vector3[]; groundOffsetY: number } {
  
  const oriented = points.map(point => {
    let p = point.clone();
    
    // Apply center offset if provided
    if (centerOffset) {
      p.sub(centerOffset);
    }
    
    // Apply rotation
    p.applyMatrix4(rotationMatrix);
    
    // Add center offset back if provided
    if (centerOffset) {
      p.add(centerOffset);
    }
    
    return p;
  });
  
  // Ground all points to Y=0 by finding the minimum Y and offsetting
  const minY = Math.min(...oriented.map(p => p.y));
  const groundOffsetY = -minY;
  
  oriented.forEach(p => {
    p.y += groundOffsetY;
  });
  
  console.log('   Reoriented points - Y range:', `[${Math.min(...oriented.map(p => p.y)).toFixed(3)}, ${Math.max(...oriented.map(p => p.y)).toFixed(3)}]`);
  
  return { points: oriented, groundOffsetY };
}

/**
 * Convert QuickHull triangular faces to grouped planar faces
 */
function convertQuickHullToFaces(
  hull: number[][],
  originalPoints: THREE.Vector3[]
): Array<{ normal: THREE.Vector3; vertices: THREE.Vector3[]; isLargest: boolean }> {
  const faces: Array<{ normal: THREE.Vector3; vertices: THREE.Vector3[]; isLargest: boolean }> = [];
  
  // QuickHull returns triangular faces as indices into the point array
  hull.forEach(triangle => {
    if (triangle.length >= 3) {
      const vertices = triangle.map(index => originalPoints[index]).filter(v => v);
      if (vertices.length >= 3) {
        // Calculate face normal from first 3 vertices
        const v1 = vertices[1].clone().sub(vertices[0]);
        const v2 = vertices[2].clone().sub(vertices[0]);
        const normal = new THREE.Vector3().crossVectors(v1, v2).normalize();
        
        faces.push({
          normal,
          vertices,
          isLargest: false
        });
      }
    }
  });
  
  return faces;
}

/**
 * Calculate area of a face from its vertices
 */
function calculateFaceArea(vertices: THREE.Vector3[]): number {
  if (vertices.length < 3) return 0;
  
  // Use triangulation for polygons with more than 3 vertices
  let totalArea = 0;
  const origin = vertices[0];
  
  for (let i = 1; i < vertices.length - 1; i++) {
    const v1 = vertices[i].clone().sub(origin);
    const v2 = vertices[i + 1].clone().sub(origin);
    const cross = new THREE.Vector3().crossVectors(v1, v2);
    totalArea += cross.length() * 0.5;
  }
  
  return totalArea;
}
