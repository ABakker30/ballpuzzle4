// Simplified validation for MVP - will add full schema validation later
export function validateContainer(obj: any): void {
  if (!obj || typeof obj !== 'object') throw new Error("Invalid JSON object");
  if (!obj.name || typeof obj.name !== 'string') throw new Error("Missing required field: name");
  if (!obj.lattice_type || obj.lattice_type !== 'fcc') throw new Error("Invalid lattice_type, must be 'fcc'");
  if (!Array.isArray(obj.coordinates)) throw new Error("Missing required field: coordinates");
  if (obj.coordinates.length === 0) throw new Error("coordinates array cannot be empty");
}

export function validateSolution(obj: any): void {
  if (!obj || typeof obj !== 'object') throw new Error("Invalid JSON object");
  if (!obj.lattice || obj.lattice !== 'fcc') throw new Error("Invalid lattice, must be 'fcc'");
  if (!Array.isArray(obj.placements)) throw new Error("Missing required field: placements");
}

export function validateEventLine(obj: any): void {
  if (!obj || typeof obj !== 'object') throw new Error("Invalid JSON object");
  if (!obj.type || typeof obj.type !== 'string') throw new Error("Missing required field: type");
  if (!obj.t_ms || typeof obj.t_ms !== 'number') throw new Error("Missing required field: t_ms");
}
