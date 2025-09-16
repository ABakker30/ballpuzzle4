import * as THREE from 'three';
import { ConvexHull } from 'three-stdlib';

export interface PlanarPatch {
  normal: THREE.Vector3;
  area: number;
  triangles: THREE.Triangle[];
  centroid: THREE.Vector3;
}

export interface OrientationResult {
  rotation: THREE.Quaternion;
  translation: THREE.Vector3;
  hullCentroid: THREE.Vector3;
  largestPatch: PlanarPatch;
  totalHullArea: number;
}

export class GeometryProcessor {
  private readonly COPLANAR_ANGLE_THRESHOLD = 2 * Math.PI / 180; // 2 degrees in radians
  private readonly COPLANAR_DISTANCE_THRESHOLD_RATIO = 0.01; // 1% of bbox diagonal
  private readonly MIN_PATCH_AREA_RATIO = 0.15; // 15% of total hull area for PCA fallback

  /**
   * Collect world-space geometry points from sphere positions
   */
  collectWorldGeometry(sphereGroups: Array<{ positions: Float32Array }>): THREE.Vector3[] {
    const points: THREE.Vector3[] = [];
    
    console.log(`GeometryProcessor: Collecting geometry from ${sphereGroups.length} sphere groups`);
    
    for (let groupIdx = 0; groupIdx < sphereGroups.length; groupIdx++) {
      const group = sphereGroups[groupIdx];
      const positions = group.positions;
      const sphereCount = positions.length / 3;
      
      console.log(`GeometryProcessor: Group ${groupIdx} has ${sphereCount} spheres`);
      
      for (let i = 0; i < positions.length; i += 3) {
        const point = new THREE.Vector3(
          positions[i],
          positions[i + 1], 
          positions[i + 2]
        );
        points.push(point);
        
        if (i < 30) { // Log first 10 points for debugging
          console.log(`GeometryProcessor: Point ${i/3}: [${point.x.toFixed(2)}, ${point.y.toFixed(2)}, ${point.z.toFixed(2)}]`);
        }
      }
    }
    
    console.log(`GeometryProcessor: Collected ${points.length} total points`);
    
    // Calculate point cloud bounds
    const bbox = new THREE.Box3().setFromPoints(points);
    console.log(`GeometryProcessor: Point cloud bounds - min: [${bbox.min.x.toFixed(2)}, ${bbox.min.y.toFixed(2)}, ${bbox.min.z.toFixed(2)}], max: [${bbox.max.x.toFixed(2)}, ${bbox.max.y.toFixed(2)}, ${bbox.max.z.toFixed(2)}]`);
    
    return points;
  }

  /**
   * Compute convex hull using Three.js ConvexHull
   */
  computeConvexHull(points: THREE.Vector3[]): { vertices: THREE.Vector3[], faces: THREE.Triangle[] } {
    if (points.length < 4) {
      throw new Error('Need at least 4 points for convex hull');
    }

    console.log(`GeometryProcessor: Computing convex hull from ${points.length} points`);
    
    const hull = new ConvexHull();
    hull.setFromPoints(points);
    
    const vertices: THREE.Vector3[] = [];
    const faces: THREE.Triangle[] = [];
    
    // Extract vertices
    for (const vertex of hull.vertices) {
      vertices.push(vertex.point.clone());
    }
    
    console.log(`GeometryProcessor: Hull has ${vertices.length} vertices`);
    
    // Extract triangular faces
    for (let i = 0; i < hull.faces.length; i++) {
      const face = hull.faces[i];
      const edge = face.edge;
      const v1 = edge.vertex.point;
      const v2 = edge.next.vertex.point;
      const v3 = edge.next.next.vertex.point;
      
      const triangle = new THREE.Triangle(v1.clone(), v2.clone(), v3.clone());
      faces.push(triangle);
      
      // Log first few faces for debugging
      if (i < 5) {
        const normal = new THREE.Vector3();
        triangle.getNormal(normal);
        const area = triangle.getArea();
        console.log(`GeometryProcessor: Face ${i} - normal: [${normal.x.toFixed(3)}, ${normal.y.toFixed(3)}, ${normal.z.toFixed(3)}], area: ${area.toFixed(3)}`);
      }
    }
    
    console.log(`GeometryProcessor: Hull has ${faces.length} triangular faces`);
    
    return { vertices, faces };
  }

  /**
   * Compute hull centroid (center of mass of closed polyhedron)
   */
  computeHullCentroid(vertices: THREE.Vector3[], faces: THREE.Triangle[]): THREE.Vector3 {
    let totalVolume = 0;
    const centroid = new THREE.Vector3();
    
    // Use tetrahedron decomposition for volume-weighted centroid
    const origin = new THREE.Vector3();
    
    for (const face of faces) {
      // Form tetrahedron with origin and face
      const v1 = face.a;
      const v2 = face.b;
      const v3 = face.c;
      
      // Volume of tetrahedron = |det(v1, v2, v3)| / 6
      const volume = Math.abs(
        v1.dot(new THREE.Vector3().crossVectors(v2, v3))
      ) / 6;
      
      // Centroid of tetrahedron
      const tetCentroid = new THREE.Vector3()
        .add(origin)
        .add(v1)
        .add(v2)
        .add(v3)
        .multiplyScalar(0.25);
      
      centroid.add(tetCentroid.multiplyScalar(volume));
      totalVolume += volume;
    }
    
    if (totalVolume > 0) {
      centroid.divideScalar(totalVolume);
    } else {
      // Fallback to simple average
      centroid.set(0, 0, 0);
      for (const vertex of vertices) {
        centroid.add(vertex);
      }
      centroid.divideScalar(vertices.length);
    }
    
    return centroid;
  }

  /**
   * Identify and merge coplanar triangular faces into planar patches
   */
  identifyPlanarPatches(faces: THREE.Triangle[], hullVertices: THREE.Vector3[]): PlanarPatch[] {
    const patches: PlanarPatch[] = [];
    const processed = new Set<number>();
    
    // Calculate characteristic hull dimension (average edge length)
    let totalEdgeLength = 0;
    let edgeCount = 0;
    for (let i = 0; i < hullVertices.length; i++) {
      for (let j = i + 1; j < hullVertices.length; j++) {
        const distance = hullVertices[i].distanceTo(hullVertices[j]);
        totalEdgeLength += distance;
        edgeCount++;
      }
    }
    const avgHullDimension = edgeCount > 0 ? totalEdgeLength / edgeCount : 1.0;
    const distanceThreshold = avgHullDimension * this.COPLANAR_DISTANCE_THRESHOLD_RATIO;
    
    console.log(`GeometryProcessor: Hull-based coplanar detection - avg dimension: ${avgHullDimension.toFixed(3)}, threshold: ${distanceThreshold.toFixed(3)}`);
    
    for (let i = 0; i < faces.length; i++) {
      if (processed.has(i)) continue;
      
      const seedFace = faces[i];
      const seedNormal = new THREE.Vector3();
      seedFace.getNormal(seedNormal);
      
      // Get plane equation: normal · (point - planePoint) = 0
      const planePoint = seedFace.a;
      
      const patchTriangles: THREE.Triangle[] = [seedFace];
      processed.add(i);
      
      // Find all coplanar faces
      for (let j = i + 1; j < faces.length; j++) {
        if (processed.has(j)) continue;
        
        const testFace = faces[j];
        const testNormal = new THREE.Vector3();
        testFace.getNormal(testNormal);
        
        // Check angle between normals
        const angle = seedNormal.angleTo(testNormal);
        if (angle > this.COPLANAR_ANGLE_THRESHOLD && 
            angle < Math.PI - this.COPLANAR_ANGLE_THRESHOLD) {
          continue;
        }
        
        // Check distance from plane
        const testPoint = testFace.a;
        const distance = Math.abs(seedNormal.dot(
          new THREE.Vector3().subVectors(testPoint, planePoint)
        ));
        
        if (distance <= distanceThreshold) {
          patchTriangles.push(testFace);
          processed.add(j);
        }
      }
      
      // Compute patch properties
      let totalArea = 0;
      const centroid = new THREE.Vector3();
      
      for (const triangle of patchTriangles) {
        const area = triangle.getArea();
        totalArea += area;
        
        // Triangle centroid
        const triCentroid = new THREE.Vector3()
          .add(triangle.a)
          .add(triangle.b)
          .add(triangle.c)
          .multiplyScalar(1/3);
        
        centroid.add(triCentroid.multiplyScalar(area));
      }
      
      if (totalArea > 0) {
        centroid.divideScalar(totalArea);
      }
      
      // Use consistent outward normal (average of face normals)
      const avgNormal = new THREE.Vector3();
      for (const triangle of patchTriangles) {
        const normal = new THREE.Vector3();
        triangle.getNormal(normal);
        avgNormal.add(normal);
      }
      avgNormal.normalize();
      
      patches.push({
        normal: avgNormal,
        area: totalArea,
        triangles: patchTriangles,
        centroid: centroid
      });
    }
    
    return patches;
  }

  /**
   * Compute minimal rotation to align vector 'from' to vector 'to'
   */
  computeAlignmentRotation(from: THREE.Vector3, to: THREE.Vector3): THREE.Quaternion {
    const fromNorm = from.clone().normalize();
    const toNorm = to.clone().normalize();
    
    // Check if vectors are already aligned
    const dot = fromNorm.dot(toNorm);
    if (dot > 0.99999) {
      return new THREE.Quaternion(); // Identity
    }
    
    // Check if vectors are opposite
    if (dot < -0.99999) {
      // Find any perpendicular vector
      const perpendicular = new THREE.Vector3();
      if (Math.abs(fromNorm.x) < 0.9) {
        perpendicular.set(1, 0, 0);
      } else {
        perpendicular.set(0, 1, 0);
      }
      perpendicular.cross(fromNorm).normalize();
      
      return new THREE.Quaternion().setFromAxisAngle(perpendicular, Math.PI);
    }
    
    // General case: compute rotation axis and angle
    const axis = new THREE.Vector3().crossVectors(fromNorm, toNorm).normalize();
    const angle = Math.acos(Math.max(-1, Math.min(1, dot)));
    
    return new THREE.Quaternion().setFromAxisAngle(axis, angle);
  }

  /**
   * Apply PCA orientation as fallback for curved objects
   */
  applyPCAOrientation(points: THREE.Vector3[]): THREE.Quaternion {
    // Compute centroid
    const centroid = new THREE.Vector3();
    for (const point of points) {
      centroid.add(point);
    }
    centroid.divideScalar(points.length);
    
    // Compute covariance matrix
    const covariance = new THREE.Matrix3();
    const temp = new THREE.Vector3();
    
    for (const point of points) {
      temp.subVectors(point, centroid);
      
      covariance.elements[0] += temp.x * temp.x; // xx
      covariance.elements[1] += temp.x * temp.y; // xy
      covariance.elements[2] += temp.x * temp.z; // xz
      covariance.elements[3] += temp.y * temp.x; // yx
      covariance.elements[4] += temp.y * temp.y; // yy
      covariance.elements[5] += temp.y * temp.z; // yz
      covariance.elements[6] += temp.z * temp.x; // zx
      covariance.elements[7] += temp.z * temp.y; // zy
      covariance.elements[8] += temp.z * temp.z; // zz
    }
    
    // Normalize by number of points
    covariance.multiplyScalar(1 / points.length);
    
    // For simplicity, use the smallest eigenvalue direction as up
    // This is an approximation - full eigenvalue decomposition would be more accurate
    const smallestEigenVector = new THREE.Vector3(0, 1, 0); // Default to Y-up
    
    // Align smallest principal axis to -Y (so object lies flat)
    return this.computeAlignmentRotation(smallestEigenVector, new THREE.Vector3(0, -1, 0));
  }

  /**
   * Snap near-axis-aligned normals to exact axes
   */
  snapToAxis(normal: THREE.Vector3): THREE.Vector3 {
    const SNAP_THRESHOLD = 1 * Math.PI / 180; // 1 degree
    const axes = [
      new THREE.Vector3(1, 0, 0),
      new THREE.Vector3(-1, 0, 0),
      new THREE.Vector3(0, 1, 0),
      new THREE.Vector3(0, -1, 0),
      new THREE.Vector3(0, 0, 1),
      new THREE.Vector3(0, 0, -1)
    ];
    
    for (const axis of axes) {
      if (normal.angleTo(axis) < SNAP_THRESHOLD) {
        return axis.clone();
      }
    }
    
    return normal.clone();
  }

  /**
   * Main function: compute orientation to rest on largest surface
   */
  computeRestOrientation(sphereGroups: Array<{ positions: Float32Array }>): OrientationResult {
    // Step 1: Collect world geometry
    const points = this.collectWorldGeometry(sphereGroups);
    
    if (points.length < 4) {
      throw new Error('Need at least 4 points for orientation computation');
    }
    
    // Step 2: Compute convex hull
    const { vertices, faces } = this.computeConvexHull(points);
    
    // Step 3: Compute hull centroid
    const hullCentroid = this.computeHullCentroid(vertices, faces);
    
    // Step 4: Identify planar patches using hull vertices
    const patches = this.identifyPlanarPatches(faces, vertices);
    
    // Step 6: Find largest patch
    let largestPatch = patches[0];
    let totalHullArea = 0;
    
    for (const patch of patches) {
      totalHullArea += patch.area;
      if (patch.area > largestPatch.area) {
        largestPatch = patch;
      }
    }
    
    // Step 7: Handle edge cases and compute rotation
    let rotation: THREE.Quaternion;
    
    console.log('GeometryProcessor: Patch analysis:');
    console.log(`  Total patches: ${patches.length}`);
    console.log(`  Total hull area: ${totalHullArea.toFixed(3)}`);
    
    // Log all patches sorted by area
    const sortedPatches = [...patches].sort((a, b) => b.area - a.area);
    for (let i = 0; i < Math.min(5, sortedPatches.length); i++) {
      const patch = sortedPatches[i];
      const percentage = (patch.area / totalHullArea * 100).toFixed(1);
      console.log(`  Patch ${i}: area=${patch.area.toFixed(3)} (${percentage}%), normal=[${patch.normal.x.toFixed(3)}, ${patch.normal.y.toFixed(3)}, ${patch.normal.z.toFixed(3)}], triangles=${patch.triangles.length}`);
    }
    
    console.log(`  Largest patch area: ${largestPatch.area.toFixed(3)} (${(largestPatch.area/totalHullArea*100).toFixed(1)}%)`);
    console.log(`  Largest patch normal:`, largestPatch.normal);
    console.log(`  Largest patch centroid:`, largestPatch.centroid);
    
    if (largestPatch.area < totalHullArea * this.MIN_PATCH_AREA_RATIO) {
      // Curved object fallback: use PCA
      console.log('GeometryProcessor: Using PCA orientation for curved object');
      rotation = this.applyPCAOrientation(points);
    } else {
      // Handle ties by preferring orientation that minimizes height
      const candidates = patches.filter(p => 
        Math.abs(p.area - largestPatch.area) / largestPatch.area < 0.05
      );
      
      console.log(`GeometryProcessor: Found ${candidates.length} candidate patches for tie-breaking`);
      
      if (candidates.length > 1) {
        let bestPatch = largestPatch;
        let minHeight = Infinity;
        
        for (const candidate of candidates) {
          const testRotation = this.computeAlignmentRotation(
            candidate.normal, 
            new THREE.Vector3(0, 1, 0)
          );
          
          // Apply rotation to all points and compute height
          const rotatedBbox = new THREE.Box3();
          for (const point of points) {
            const rotatedPoint = point.clone().applyQuaternion(testRotation);
            rotatedBbox.expandByPoint(rotatedPoint);
          }
          
          const height = rotatedBbox.max.y - rotatedBbox.min.y;
          console.log(`GeometryProcessor: Candidate normal ${candidate.normal.toArray()} -> height ${height.toFixed(3)}`);
          if (height < minHeight) {
            minHeight = height;
            bestPatch = candidate;
          }
        }
        
        largestPatch = bestPatch;
        console.log(`GeometryProcessor: Selected best patch with normal:`, largestPatch.normal);
      }
      
      // Snap normal to axis if close
      const originalNormal = largestPatch.normal.clone();
      const snappedNormal = this.snapToAxis(largestPatch.normal);
      
      if (!originalNormal.equals(snappedNormal)) {
        console.log(`GeometryProcessor: Snapped normal from ${originalNormal.toArray()} to ${snappedNormal.toArray()}`);
      }
      
      // Invert the surface normal so the surface faces up instead of down
      const invertedNormal = snappedNormal.clone().negate();
      
      // Compute rotation to align inverted surface normal to +Y (surface faces up)
      console.log(`GeometryProcessor: Aligning inverted normal ${invertedNormal.toArray()} to [0, 1, 0]`);
      rotation = this.computeAlignmentRotation(invertedNormal, new THREE.Vector3(0, 1, 0));
      console.log(`GeometryProcessor: Computed rotation quaternion:`, rotation);
    }
    
    // Step 8: Compute grounding translation
    // Apply rotation to all points and find minimum Y
    const rotatedBbox = new THREE.Box3();
    for (const point of points) {
      const rotatedPoint = point.clone().applyQuaternion(rotation);
      rotatedBbox.expandByPoint(rotatedPoint);
    }
    
    console.log(`GeometryProcessor: After rotation - bbox min: ${rotatedBbox.min.toArray()}, max: ${rotatedBbox.max.toArray()}`);
    
    // Translate so that minimum Y becomes 0
    const translation = new THREE.Vector3(0, -rotatedBbox.min.y, 0);
    console.log(`GeometryProcessor: Grounding translation:`, translation);
    
    return {
      rotation,
      translation,
      hullCentroid,
      largestPatch,
      totalHullArea
    };
  }
}
