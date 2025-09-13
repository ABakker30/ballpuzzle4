# Canonicalization Algorithm (CID)

The CID is a stable, deterministic fingerprint of a container's geometry.

---

## Algorithm (v1.0)

**Input**: `{version, lattice, cells}`  
**Output**: `cid` string

1. **Normalize translation**  
   - Subtract min(x), min(y), min(z) from all cells → bbox min at `[0,0,0]`.

2. **Generate candidates**  
   - Apply all 24 proper FCC rotation matrices (see below).
   - For each result: normalize again, sort triplets lex order.

3. **Pick canonical**  
   - Compare all candidates lex order.
   - Choose the smallest array.

4. **Serialize**  
   ```python
   json.dumps(
     {"version": version, "lattice": lattice, "cells": canonical},
     separators=(",", ":"),
     ensure_ascii=False
   )
   ```

5. **Hash**  
   - Compute SHA-256 hex of the serialized string.
   - `cid = "sha256:" + hexdigest`

---

## FCC Rotations (24)

The FCC lattice shares cubic symmetry with the cube.  
The 24 matrices are the proper rotations of the cube (det=+1).

### Identity (I):
```
[1, 0, 0]
[0, 1, 0]
[0, 0, 1]
```

### Face rotations (6):
```
# +X face 90°, 180°, 270°
[1, 0, 0]    [1, 0, 0]    [1, 0, 0]
[0, 0,-1]    [0,-1, 0]    [0, 0, 1]
[0, 1, 0]    [0, 0,-1]    [0,-1, 0]

# +Y face 90°, 180°, 270°
[0, 0, 1]    [-1, 0, 0]    [0, 0,-1]
[0, 1, 0]    [0, 1, 0]     [0, 1, 0]
[-1, 0, 0]   [0, 0,-1]     [1, 0, 0]

# +Z face 90°, 180°, 270°
[0,-1, 0]    [-1, 0, 0]    [0, 1, 0]
[1, 0, 0]    [0,-1, 0]     [-1, 0, 0]
[0, 0, 1]    [0, 0, 1]     [0, 0, 1]
```

### Edge rotations (12):
```
# 180° around edge [1,1,0]
[0, 1, 0]
[1, 0, 0]
[0, 0,-1]

# 180° around edge [1,-1,0]
[0,-1, 0]
[-1, 0, 0]
[0, 0,-1]

# 180° around edge [1,0,1]
[0, 0, 1]
[0,-1, 0]
[1, 0, 0]

# 180° around edge [1,0,-1]
[0, 0,-1]
[0,-1, 0]
[-1, 0, 0]

# 180° around edge [0,1,1]
[-1, 0, 0]
[0, 0, 1]
[0, 1, 0]

# 180° around edge [0,1,-1]
[-1, 0, 0]
[0, 0,-1]
[0,-1, 0]
```

### Vertex rotations (8):
```
# 120° around vertex [1,1,1]
[0, 0, 1]
[1, 0, 0]
[0, 1, 0]

# 240° around vertex [1,1,1]
[0, 1, 0]
[0, 0, 1]
[1, 0, 0]

# 120° around vertex [1,1,-1]
[0, 0,-1]
[1, 0, 0]
[0,-1, 0]

# 240° around vertex [1,1,-1]
[0,-1, 0]
[0, 0,-1]
[1, 0, 0]

# 120° around vertex [1,-1,1]
[0, 0, 1]
[-1, 0, 0]
[0,-1, 0]

# 240° around vertex [1,-1,1]
[0,-1, 0]
[0, 0, 1]
[-1, 0, 0]

# 120° around vertex [-1,1,1]
[0, 0, 1]
[1, 0, 0]
[0,-1, 0]

# 240° around vertex [-1,1,1]
[0,-1, 0]
[0, 0, 1]
[1, 0, 0]
```

---

## Test Vectors

### Input
```json
{
  "version":"1.0",
  "lattice":"fcc",
  "cells":[[1,1,0],[0,1,0],[1,0,0],[0,0,0]]
}
```

### Canonical cells
```json
[[0,0,0],[0,1,0],[1,0,0],[1,1,0]]
```

### CID
```
sha256:7a91e53f33d3f1e6b07d... (truncated)
```
