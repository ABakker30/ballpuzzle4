#!/usr/bin/env python3
"""
Comprehensive tests for v1.0 container validation and handling.
"""

import pytest
import json
import tempfile
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.io.container import load_container


class TestContainerV1Validation:
    """Test v1.0 container validation and loading."""
    
    def test_valid_v1_container(self):
        """Test loading a valid v1.0 container."""
        valid_container = {
            "version": "1.0",
            "lattice": "fcc",
            "cells": [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
            "cid": "sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "designer": {
                "name": "Test Designer",
                "date": "2025-09-12"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fcc.json', delete=False) as f:
            json.dump(valid_container, f)
            temp_path = f.name
        
        try:
            container = load_container(temp_path)
            assert container["version"] == "1.0"
            assert container["lattice"] == "fcc"
            assert len(container["cells"]) == 3
            assert "coordinates" in container  # Backward compatibility mapping
            assert container["coordinates"] == container["cells"]
        finally:
            Path(temp_path).unlink()
    
    def test_reject_legacy_container(self):
        """Test that legacy containers are rejected."""
        legacy_container = {
            "name": "Legacy Container",
            "lattice_type": "fcc",
            "coordinates": [[0, 0, 0], [1, 0, 0]]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(legacy_container, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported container version"):
                load_container(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_reject_wrong_version(self):
        """Test rejection of containers with wrong version."""
        wrong_version = {
            "version": "2.0",
            "lattice": "fcc",
            "cells": [[0, 0, 0]],
            "cid": "sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "designer": {"name": "Test", "date": "2025-09-12"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(wrong_version, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported container version: 2.0"):
                load_container(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_missing_required_fields(self):
        """Test rejection when required fields are missing."""
        # Missing designer
        incomplete_container = {
            "version": "1.0",
            "lattice": "fcc",
            "cells": [[0, 0, 0]],
            "cid": "sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(incomplete_container, f)
            temp_path = f.name
        
        try:
            with pytest.raises(Exception):  # Schema validation error
                load_container(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_invalid_cid_format(self):
        """Test rejection of invalid CID format."""
        invalid_cid = {
            "version": "1.0",
            "lattice": "fcc", 
            "cells": [[0, 0, 0]],
            "cid": "invalid-cid-format",
            "designer": {"name": "Test", "date": "2025-09-12"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_cid, f)
            temp_path = f.name
        
        try:
            with pytest.raises(Exception):  # Schema validation error
                load_container(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_missing_cells_field(self):
        """Test rejection when cells field is missing."""
        no_cells = {
            "version": "1.0",
            "lattice": "fcc",
            "coordinates": [[0, 0, 0]],  # Legacy field name
            "cid": "sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "designer": {"name": "Test", "date": "2025-09-12"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(no_cells, f)
            temp_path = f.name
        
        try:
            with pytest.raises(Exception):  # Schema validation will fail first
                load_container(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_cid_computation_and_mapping(self):
        """Test that CID is computed and coordinates mapping works."""
        container = {
            "version": "1.0",
            "lattice": "fcc",
            "cells": [[0, 0, 0], [1, 1, 1], [2, 2, 2]],
            "cid": "sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "designer": {"name": "Test", "date": "2025-09-12"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(container, f)
            temp_path = f.name
        
        try:
            loaded = load_container(temp_path)
            
            # Check CID computation
            assert "cid_sha256" in loaded
            assert loaded["cid_sha256"].startswith("sha256:") or len(loaded["cid_sha256"]) == 64
            
            # Check backward compatibility mapping
            assert "coordinates" in loaded
            assert loaded["coordinates"] == loaded["cells"]
            assert len(loaded["coordinates"]) == 3
            
        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
