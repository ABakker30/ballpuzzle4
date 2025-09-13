/**
 * Container loader for v1.0 standard with validation and CID verification
 * Only supports v1.0 containers - legacy formats are deprecated
 */

import { ContainerV1 } from '../types/shape';

// Container v1.0 schema for validation
const CONTAINER_V1_SCHEMA = {
  type: 'object',
  required: ['version', 'lattice', 'cells', 'cid', 'designer'],
  additionalProperties: false,
  properties: {
    version: { type: 'string', enum: ['1.0'] },
    lattice: { type: 'string', enum: ['fcc'] },
    cells: {
      type: 'array',
      minItems: 1,
      items: {
        type: 'array',
        minItems: 3,
        maxItems: 3,
        items: { type: 'integer' }
      }
    },
    cid: {
      type: 'string',
      pattern: '^sha256:[a-f0-9]{64}$'
    },
    designer: {
      type: 'object',
      required: ['name', 'date'],
      properties: {
        name: { type: 'string' },
        date: { type: 'string' },
        email: { type: 'string' }
      },
      additionalProperties: false
    }
  }
};

export interface ContainerLoadSuccess {
  success: true;
  container: ContainerV1;
  cidMismatch?: boolean;
  computedCid?: string;
}

export interface ContainerLoadError {
  success: false;
  error: string;
  details?: string[];
}

export type ContainerLoadResponse = ContainerLoadSuccess | ContainerLoadError;

/**
 * Simple schema validator (basic implementation)
 */
function validateSchema(data: any): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  // Check required fields
  const required = ['version', 'lattice', 'cells', 'cid', 'designer'];
  for (const field of required) {
    if (!(field in data)) {
      errors.push(`Missing required field: ${field}`);
    }
  }

  // Check version
  if (data.version !== '1.0') {
    errors.push(`Invalid version: expected "1.0", got "${data.version}"`);
  }

  // Check lattice
  if (data.lattice !== 'fcc') {
    errors.push(`Invalid lattice: expected "fcc", got "${data.lattice}"`);
  }

  // Check cells format
  if (!Array.isArray(data.cells)) {
    errors.push('cells must be an array');
  } else if (data.cells.length === 0) {
    errors.push('cells array cannot be empty');
  } else {
    data.cells.forEach((cell: any, index: number) => {
      if (!Array.isArray(cell) || cell.length !== 3) {
        errors.push(`cells[${index}] must be [x,y,z] array`);
      } else if (!cell.every((coord: any) => Number.isInteger(coord))) {
        errors.push(`cells[${index}] must contain integers only`);
      }
    });
  }

  // Check CID format
  if (typeof data.cid !== 'string' || !data.cid.startsWith('sha256:') || data.cid.length !== 71) {
    errors.push('cid must be "sha256:" followed by 64 hex characters');
  } else {
    // Validate hex characters
    const hexPart = data.cid.slice(7);
    if (!/^[0-9a-f]{64}$/i.test(hexPart)) {
      errors.push('cid must be "sha256:" followed by 64 hex characters');
    }
  }

  // Check designer
  if (typeof data.designer !== 'object' || !data.designer) {
    errors.push('designer must be an object');
  } else {
    if (!data.designer.name) {
      errors.push('designer.name is required');
    }
    if (!data.designer.date) {
      errors.push('designer.date is required');
    }
  }

  // Check for unexpected fields
  const allowedFields = ['version', 'lattice', 'cells', 'cid', 'designer'];
  const extraFields = Object.keys(data).filter(key => !allowedFields.includes(key));
  if (extraFields.length > 0) {
    errors.push(`Unexpected fields: ${extraFields.join(', ')}`);
  }

  return { valid: errors.length === 0, errors };
}

/**
 * Normalize cells to origin (for CID computation)
 */
function normalizeTranslation(cells: number[][]): number[][] {
  if (cells.length === 0) return cells;
  
  const xs = cells.map(c => c[0]);
  const ys = cells.map(c => c[1]);
  const zs = cells.map(c => c[2]);
  
  const minX = Math.min(...xs);
  const minY = Math.min(...ys);
  const minZ = Math.min(...zs);
  
  return cells.map(([x, y, z]) => [x - minX, y - minY, z - minZ]);
}

/**
 * Apply rotation matrix to cells
 */
function applyRotation(cells: number[][], rotation: number[][]): number[][] {
  return cells.map(([x, y, z]) => [
    rotation[0][0] * x + rotation[0][1] * y + rotation[0][2] * z,
    rotation[1][0] * x + rotation[1][1] * y + rotation[1][2] * z,
    rotation[2][0] * x + rotation[2][1] * y + rotation[2][2] * z
  ]);
}

/**
 * FCC rotation matrices (24 proper rotations)
 */
const FCC_ROTATIONS = [
  // Identity
  [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
  
  // Face rotations around X-axis
  [[1, 0, 0], [0, 0, -1], [0, 1, 0]],   // 90°
  [[1, 0, 0], [0, -1, 0], [0, 0, -1]],  // 180°
  [[1, 0, 0], [0, 0, 1], [0, -1, 0]],   // 270°
  
  // Face rotations around Y-axis
  [[0, 0, 1], [0, 1, 0], [-1, 0, 0]],   // 90°
  [[-1, 0, 0], [0, 1, 0], [0, 0, -1]],  // 180°
  [[0, 0, -1], [0, 1, 0], [1, 0, 0]],   // 270°
  
  // Face rotations around Z-axis
  [[0, -1, 0], [1, 0, 0], [0, 0, 1]],   // 90°
  [[-1, 0, 0], [0, -1, 0], [0, 0, 1]],  // 180°
  [[0, 1, 0], [-1, 0, 0], [0, 0, 1]],   // 270°
  
  // Edge rotations (180° around edges)
  [[0, 1, 0], [1, 0, 0], [0, 0, -1]],   // [1,1,0]
  [[0, -1, 0], [-1, 0, 0], [0, 0, -1]], // [1,-1,0]
  [[0, 0, 1], [0, -1, 0], [1, 0, 0]],   // [1,0,1]
  [[0, 0, -1], [0, -1, 0], [-1, 0, 0]], // [1,0,-1]
  [[-1, 0, 0], [0, 0, 1], [0, 1, 0]],   // [0,1,1]
  [[-1, 0, 0], [0, 0, -1], [0, -1, 0]], // [0,1,-1]
  
  // Vertex rotations (120° and 240° around body diagonals)
  [[0, 0, 1], [1, 0, 0], [0, 1, 0]],    // 120° [1,1,1]
  [[0, 1, 0], [0, 0, 1], [1, 0, 0]],    // 240° [1,1,1]
  [[0, 0, -1], [1, 0, 0], [0, -1, 0]],  // 120° [1,1,-1]
  [[0, -1, 0], [0, 0, -1], [1, 0, 0]],  // 240° [1,1,-1]
  [[0, 0, 1], [-1, 0, 0], [0, -1, 0]],  // 120° [1,-1,1]
  [[0, -1, 0], [0, 0, 1], [-1, 0, 0]],  // 240° [1,-1,1]
  [[0, 0, -1], [-1, 0, 0], [0, 1, 0]],  // 120° [-1,1,1]
  [[0, 1, 0], [0, 0, -1], [-1, 0, 0]],  // 240° [-1,1,1]
];

/**
 * Compute canonical form using FCC rotations
 */
function canonicalizeCells(cells: number[][]): number[][] {
  if (cells.length === 0) return cells;
  
  const normalized = normalizeTranslation(cells);
  const candidates: number[][][] = [];
  
  // Apply all 24 FCC rotations
  for (const rotation of FCC_ROTATIONS) {
    const rotated = applyRotation(normalized, rotation);
    const renormalized = normalizeTranslation(rotated);
    const sorted = [...renormalized].sort((a, b) => {
      for (let i = 0; i < 3; i++) {
        if (a[i] !== b[i]) return a[i] - b[i];
      }
      return 0;
    });
    candidates.push(sorted);
  }
  
  // Return lexicographically smallest candidate
  return candidates.reduce((min, candidate) => {
    const compareArrays = (a: number[][], b: number[][]) => {
      for (let i = 0; i < Math.min(a.length, b.length); i++) {
        for (let j = 0; j < 3; j++) {
          if (a[i][j] !== b[i][j]) return a[i][j] - b[i][j];
        }
      }
      return a.length - b.length;
    };
    
    return compareArrays(candidate, min) < 0 ? candidate : min;
  });
}

/**
 * Compute CID from container data
 */
async function computeCid(container: { version: string; lattice: string; cells: number[][] }): Promise<string> {
  const canonicalCells = canonicalizeCells(container.cells);
  const payload = {
    version: container.version,
    lattice: container.lattice,
    cells: canonicalCells
  };
  
  const serialized = JSON.stringify(payload, null, 0);
  const encoder = new TextEncoder();
  const data = encoder.encode(serialized);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  
  return `sha256:${hashHex}`;
}

/**
 * Load and validate a container file according to v1.0 standard
 * Only accepts v1.0 format containers
 */
export async function loadContainerV1(file: File): Promise<ContainerLoadResponse> {
  try {
    // Read file content
    const content = await file.text();
    // Parse JSON
    let containerData: ContainerV1;
    try {
      containerData = JSON.parse(content) as ContainerV1;
    } catch (parseError) {
      return {
        success: false,
        error: 'Invalid JSON format',
        details: [parseError instanceof Error ? parseError.message : 'Unknown parse error']
      };
    }

    // Quick format check before schema validation
    if (containerData.version !== '1.0') {
      return {
        success: false,
        error: 'Unsupported container version',
        details: [
          `Expected version "1.0", got "${containerData.version || 'undefined'}"`,
          'Only v1.0 containers are supported. Legacy formats are deprecated.'
        ]
      };
    }

    // Schema validation
    const schemaResult = validateSchema(containerData);
    if (!schemaResult.valid) {
      return {
        success: false,
        error: 'Container does not conform to v1.0 schema',
        details: schemaResult.errors
      };
    }

    // CID validation
    const computedCid = await computeCid({
      version: containerData.version,
      lattice: containerData.lattice,
      cells: containerData.cells
    });

    const cidMismatch = computedCid !== containerData.cid;

    // Convert to internal format with UI compatibility
    const container: ContainerV1 = {
      version: containerData.version,
      lattice: containerData.lattice,
      cells: containerData.cells,
      cid: containerData.cid,
      designer: containerData.designer,
      coordinates: containerData.cells // Map cells to coordinates for UI compatibility
    };

    return {
      success: true,
      container,
      cidMismatch,
      computedCid: cidMismatch ? computedCid : undefined
    };

  } catch (error) {
    return {
      success: false,
      error: 'Failed to load container',
      details: [error instanceof Error ? error.message : 'Unknown error']
    };
  }
}
