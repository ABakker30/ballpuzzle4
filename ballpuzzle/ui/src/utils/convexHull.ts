import * as THREE from 'three';

export interface ConvexHullResult {
  center: THREE.Vector3;
  largestFaceNormal: THREE.Vector3;
  volume: number;
}

/**
 * Compute convex hull of 3D points and find the largest face
 */
export function computeConvexHull(points: THREE.Vector3[]): ConvexHullResult | null {
  if (points.length < 4) {
    return null;
  }

  // Use simplified convex hull based on actual solution geometry
  return computeConvexHullFromSolution(points);
}

/**
 * Compute convex hull from solution points using projection-based face detection
 */
function computeConvexHullFromSolution(points: THREE.Vector3[]): ConvexHullResult {
  // Calculate bounding box and center
  const box = new THREE.Box3();
  points.forEach(point => box.expandByPoint(point));
  
  const center = new THREE.Vector3();
  box.getCenter(center);
  
  // Test 6 primary directions to find largest projected face
  const directions = [
    new THREE.Vector3(1, 0, 0),   // +X
    new THREE.Vector3(-1, 0, 0),  // -X
    new THREE.Vector3(0, 1, 0),   // +Y
    new THREE.Vector3(0, -1, 0),  // -Y
    new THREE.Vector3(0, 0, 1),   // +Z
    new THREE.Vector3(0, 0, -1),  // -Z
  ];
  
  let largestFaceNormal = new THREE.Vector3(0, 0, -1);
  let maxProjectedArea = 0;
  
  directions.forEach(direction => {
    // Project all points onto plane perpendicular to direction
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
    
    if (projectedArea > maxProjectedArea) {
      maxProjectedArea = projectedArea;
      largestFaceNormal = direction.clone();
    }
  });
  
  console.log('ConvexHull: Largest face normal:', largestFaceNormal, 'with projected area:', maxProjectedArea);
  
  return {
    center,
    largestFaceNormal,
    volume: box.getSize(new THREE.Vector3()).x * box.getSize(new THREE.Vector3()).y * box.getSize(new THREE.Vector3()).z
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
    volume: size.x * size.y * size.z
  };
}

/**
 * Calculate rotation matrix to orient largest face to lie flat on XY plane
 */
export function calculateOrientationMatrix(hullResult: ConvexHullResult): THREE.Matrix4 {
  const { largestFaceNormal } = hullResult;
  
  // The face normal should point downward (negative Z) so the face sits on XY plane
  // If the normal is pointing upward, we need to flip it
  let faceNormal = largestFaceNormal.clone().normalize();
  
  // Target normal is negative Z (pointing down) so the face sits on XY plane
  const targetNormal = new THREE.Vector3(0, 0, -1);
  
  // If the face normal is pointing upward (positive Z component), flip it
  // This ensures we orient the face to sit down, not float up
  if (faceNormal.z > 0) {
    faceNormal.negate();
  }
  
  console.log('OrientationMatrix: Original face normal:', largestFaceNormal);
  console.log('OrientationMatrix: Adjusted face normal:', faceNormal);
  console.log('OrientationMatrix: Target normal:', targetNormal);
  
  // Calculate rotation quaternion to align face normal with -Z axis
  const quaternion = new THREE.Quaternion();
  quaternion.setFromUnitVectors(faceNormal, targetNormal);
  
  // Create rotation matrix
  const rotationMatrix = new THREE.Matrix4();
  rotationMatrix.makeRotationFromQuaternion(quaternion);
  
  return rotationMatrix;
}

/**
 * Apply orientation transformation to a set of points and position on XY plane
 */
export function orientPoints(
  points: THREE.Vector3[],
  rotationMatrix: THREE.Matrix4,
  centerOffset?: THREE.Vector3
): THREE.Vector3[] {
  const transformedPoints = points.map(point => {
    const transformedPoint = point.clone();
    
    // Apply center offset if provided (to rotate around hull center)
    if (centerOffset) {
      transformedPoint.sub(centerOffset);
    }
    
    // Apply rotation
    transformedPoint.applyMatrix4(rotationMatrix);
    
    // Restore center offset
    if (centerOffset) {
      transformedPoint.add(centerOffset);
    }
    
    return transformedPoint;
  });
  
  // Find the minimum Z value to place the solution on the XY plane
  let minZ = Infinity;
  transformedPoints.forEach(point => {
    if (point.z < minZ) {
      minZ = point.z;
    }
  });
  
  // Translate all points so the bottom face sits at Z=0
  if (minZ !== Infinity) {
    transformedPoints.forEach(point => {
      point.z -= minZ;
    });
  }
  
  return transformedPoints;
}
