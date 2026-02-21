"""Tests for Elisa Kotiakku manifest."""
import json
import os

def test_manifest_structure():
    """Verify that the manifest.json is valid and contains required keys."""
    manifest_path = "custom_components/elisa_kotiakku/manifest.json"
    
    assert os.path.exists(manifest_path)
    
    with open(manifest_path) as f:
        manifest = json.load(f)
        
    assert manifest["domain"] == "elisa_kotiakku"
    assert manifest["name"] == "Elisa Kotiakku"
    assert "version" in manifest
    assert "codeowners" in manifest
    assert manifest["iot_class"] == "cloud_polling"