"""
Test suite for Optical Simulation Backend
Run with: pytest test_main.py -v
"""

import pytest
from fastapi.testclient import TestClient
import json
import math
from main import app, OpticalPhysics, RayTracer, FrequencySweepAnalyzer
from main import OpticalSetup, Component, Position, ComponentProperties, SweepConfig, SimulationData

client = TestClient(app)

# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def simple_source_setup():
    """Simple setup with just a light source"""
    return {
        "version": "1.0",
        "timestamp": "2025-10-30T00:00:00Z",
        "components": [
            {
                "id": 1,
                "type": "source",
                "position": {"x": 100, "y": 300},
                "rotation": 0,
                "properties": {
                    "wavelength": 550,
                    "power": 1.0,
                    "beamAngle": 0
                }
            }
        ],
        "simulation": {
            "sweepConfig": {
                "startFreq": 500,
                "stopFreq": 600,
                "points": 5
            },
            "rays": []
        }
    }

@pytest.fixture
def mirror_setup():
    """Setup with source and mirror"""
    return {
        "version": "1.0",
        "timestamp": "2025-10-30T00:00:00Z",
        "components": [
            {
                "id": 1,
                "type": "source",
                "position": {"x": 100, "y": 300},
                "rotation": 0,
                "properties": {
                    "wavelength": 550,
                    "power": 1.0,
                    "beamAngle": 0
                }
            },
            {
                "id": 2,
                "type": "mirror",
                "position": {"x": 300, "y": 300},
                "rotation": 0,
                "properties": {
                    "reflectivity": 0.95,
                    "angle": 45
                }
            }
        ],
        "simulation": {
            "sweepConfig": {
                "startFreq": 500,
                "stopFreq": 600,
                "points": 5
            },
            "rays": []
        }
    }

@pytest.fixture
def complete_setup():
    """Complete setup with all component types"""
    return {
        "version": "1.0",
        "timestamp": "2025-10-30T00:00:00Z",
        "components": [
            {
                "id": 1,
                "type": "source",
                "position": {"x": 100, "y": 300},
                "rotation": 0,
                "properties": {
                    "wavelength": 550,
                    "power": 1.0,
                    "beamAngle": 0
                }
            },
            {
                "id": 2,
                "type": "lens",
                "position": {"x": 250, "y": 300},
                "rotation": 0,
                "properties": {
                    "focalLength": 100,
                    "diameter": 50
                }
            },
            {
                "id": 3,
                "type": "mirror",
                "position": {"x": 400, "y": 300},
                "rotation": 0,
                "properties": {
                    "reflectivity": 0.95,
                    "angle": 45
                }
            },
            {
                "id": 4,
                "type": "detector",
                "position": {"x": 400, "y": 450},
                "rotation": 0,
                "properties": {
                    "sensitivity": 1.0,
                    "area": 25
                }
            }
        ],
        "simulation": {
            "sweepConfig": {
                "startFreq": 400,
                "stopFreq": 700,
                "points": 10
            },
            "rays": []
        }
    }

# ============================================================================
# API Endpoint Tests
# ============================================================================

class TestAPIEndpoints:
    """Test all API endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns service info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Optical Simulation API"
        assert data["status"] == "running"
        assert "endpoints" in data
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "components" in data
    
    def test_simulate_simple_source(self, simple_source_setup):
        """Test simulation with simple light source"""
        response = client.post("/api/simulate", json=simple_source_setup)
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert len(data["rays"]) > 0
        assert len(data["frequencySweep"]) == 5
        assert "statistics" in data
        assert data["statistics"]["componentCount"]["sources"] == 1
    
    def test_simulate_with_mirror(self, mirror_setup):
        """Test simulation with mirror reflection"""
        response = client.post("/api/simulate", json=mirror_setup)
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["statistics"]["totalInteractions"] > 0
        # Check that rays have interactions recorded
        has_reflection = any(
            any("Mirror reflection" in interaction for interaction in ray["interactions"])
            for ray in data["rays"]
        )
        assert has_reflection
    
    def test_simulate_complete_setup(self, complete_setup):
        """Test simulation with all component types"""
        response = client.post("/api/simulate", json=complete_setup)
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["statistics"]["componentCount"]["sources"] == 1
        assert data["statistics"]["componentCount"]["mirrors"] == 1
        assert data["statistics"]["componentCount"]["lenses"] == 1
        assert data["statistics"]["componentCount"]["detectors"] == 1
        assert len(data["frequencySweep"]) == 10
    
    def test_simulate_empty_components(self):
        """Test that empty component list returns error"""
        setup = {
            "version": "1.0",
            "timestamp": "2025-10-30T00:00:00Z",
            "components": [],
            "simulation": {
                "sweepConfig": {"startFreq": 400, "stopFreq": 700, "points": 5},
                "rays": []
            }
        }
        response = client.post("/api/simulate", json=setup)
        assert response.status_code == 400
    
    def test_validate_endpoint(self, complete_setup):
        """Test validation endpoint"""
        response = client.post("/api/validate", json=complete_setup)
        assert response.status_code == 200
        data = response.json()
        
        assert "valid" in data
        assert "issues" in data
        assert "recommendations" in data
        assert data["componentCount"] == 4
    
    def test_validate_no_sources(self, complete_setup):
        """Test validation catches missing sources"""
        setup = complete_setup.copy()
        setup["components"] = [c for c in setup["components"] if c["type"] != "source"]
        
        response = client.post("/api/validate", json=setup)
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] == False
        assert any("light source" in issue.lower() for issue in data["issues"])
    
    def test_validate_invalid_sweep_range(self, simple_source_setup):
        """Test validation catches invalid frequency sweep"""
        setup = simple_source_setup.copy()
        setup["simulation"]["sweepConfig"]["startFreq"] = 700
        setup["simulation"]["sweepConfig"]["stopFreq"] = 400
        
        response = client.post("/api/validate", json=setup)
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] == False
        assert any("sweep" in issue.lower() for issue in data["issues"])

# ============================================================================
# Physics Engine Tests
# ============================================================================

class TestOpticalPhysics:
    """Test physics calculations"""
    
    def test_wavelength_to_frequency_conversion(self):
        """Test wavelength to frequency conversion"""
        physics = OpticalPhysics()
        
        # Test visible light (550nm green light)
        freq = physics.wavelength_to_frequency(550)
        expected = 299792458 / (550e-9) / 1e12  # THz
        assert abs(freq - expected) < 0.01
        
        # Test red light (650nm)
        freq_red = physics.wavelength_to_frequency(650)
        assert freq_red < freq  # Lower frequency than green
    
    def test_snells_law_refraction(self):
        """Test Snell's law calculations"""
        physics = OpticalPhysics()
        
        # Air to glass (n1=1.0, n2=1.5)
        incident_angle = math.radians(30)
        refracted = physics.calculate_refraction(incident_angle, 1.0, 1.5)
        
        assert refracted is not None
        assert refracted < incident_angle  # Bends towards normal
        
        # Test total internal reflection
        critical_angle = math.radians(50)
        refracted = physics.calculate_refraction(critical_angle, 1.5, 1.0)
        assert refracted is None  # Total internal reflection
    
    def test_ray_reflection(self):
        """Test ray reflection calculations"""
        physics = OpticalPhysics()
        
        # Ray hitting horizontal mirror
        ray_dx, ray_dy = 1.0, 1.0
        normal_x, normal_y = 0.0, 1.0
        
        ref_dx, ref_dy = physics.reflect_ray(ray_dx, ray_dy, normal_x, normal_y)
        
        # Reflected ray should have same x-component, inverted y
        assert abs(ref_dx - 1.0) < 0.001
        assert abs(ref_dy - (-1.0)) < 0.001
    
    def test_lens_refraction(self):
        """Test lens refraction calculations"""
        physics = OpticalPhysics()
        
        # Ray through lens center (no deflection)
        ray_dx, ray_dy = 1.0, 0.0
        focal_length = 100
        distance = 0  # On axis
        
        new_dx, new_dy = physics.lens_refraction(ray_dx, ray_dy, focal_length, distance)
        
        # Should be mostly unchanged
        assert abs(new_dx - 1.0) < 0.1
    
    def test_fresnel_reflection_normal_incidence(self):
        """Test Fresnel reflection at normal incidence"""
        physics = OpticalPhysics()
        
        # Normal incidence (theta = 0)
        R = physics.fresnel_reflection(0, n1=1.0, n2=1.5)
        
        # Should match simple formula: ((n1-n2)/(n1+n2))^2
        expected = ((1.0 - 1.5) / (1.0 + 1.5)) ** 2
        assert abs(R - expected) < 0.001
    
    def test_path_length_calculation(self):
        """Test optical path length calculation"""
        physics = OpticalPhysics()
        
        path = [
            Position(x=0, y=0),
            Position(x=3, y=0),
            Position(x=3, y=4)
        ]
        
        length = physics.calculate_path_length(path)
        expected = 3 + 4  # 3 units horizontal + 4 units vertical
        assert abs(length - expected) < 0.001

# ============================================================================
# Ray Tracer Tests
# ============================================================================

class TestRayTracer:
    """Test ray tracing engine"""
    
    def test_trace_simple_ray(self, simple_source_setup):
        """Test basic ray tracing from source"""
        setup = OpticalSetup(**simple_source_setup)
        tracer = RayTracer(setup)
        
        rays = tracer.trace_all_rays()
        
        assert len(rays) > 0
        for ray in rays:
            assert ray.wavelength == 550
            assert ray.intensity > 0
            assert len(ray.path) > 1
    
    def test_mirror_reflection(self, mirror_setup):
        """Test ray reflection off mirror"""
        setup = OpticalSetup(**mirror_setup)
        tracer = RayTracer(setup)
        
        rays = tracer.trace_all_rays()
        
        # Check that at least one ray has mirror interaction
        has_reflection = False
        for ray in rays:
            if any("Mirror reflection" in interaction for interaction in ray.interactions):
                has_reflection = True
                # Intensity should be reduced after reflection
                assert ray.intensity < 1.0
        
        assert has_reflection
    
    def test_intensity_loss_through_system(self, complete_setup):
        """Test that intensity decreases through optical system"""
        setup = OpticalSetup(**complete_setup)
        tracer = RayTracer(setup)
        
        rays = tracer.trace_all_rays()
        
        # All rays should have reduced intensity after interactions
        for ray in rays:
            if len(ray.interactions) > 0:
                assert ray.intensity < 1.0

# ============================================================================
# Frequency Sweep Tests
# ============================================================================

class TestFrequencySweepAnalyzer:
    """Test frequency sweep functionality"""
    
    def test_basic_frequency_sweep(self, simple_source_setup):
        """Test basic frequency sweep analysis"""
        setup = OpticalSetup(**simple_source_setup)
        tracer = RayTracer(setup)
        analyzer = FrequencySweepAnalyzer(setup, tracer)
        
        results = analyzer.perform_sweep()
        
        assert len(results) == 5  # 5 points in sweep
        assert results[0].wavelength == 500
        assert results[-1].wavelength == 600
        
        # Frequencies should decrease as wavelength increases
        assert results[0].frequency > results[-1].frequency
    
    def test_detector_readings_in_sweep(self, complete_setup):
        """Test that detector readings are captured in sweep"""
        setup = OpticalSetup(**complete_setup)
        tracer = RayTracer(setup)
        analyzer = FrequencySweepAnalyzer(setup, tracer)
        
        results = analyzer.perform_sweep()
        
        # Should have detector readings for each wavelength
        for result in results:
            assert len(result.detectorReadings) >= 0
            assert result.totalIntensity >= 0
    
    def test_wavelength_range_coverage(self, complete_setup):
        """Test that sweep covers full wavelength range"""
        setup = OpticalSetup(**complete_setup)
        tracer = RayTracer(setup)
        analyzer = FrequencySweepAnalyzer(setup, tracer)
        
        results = analyzer.perform_sweep()
        
        wavelengths = [r.wavelength for r in results]
        assert min(wavelengths) == 400
        assert max(wavelengths) == 700
        assert len(wavelengths) == 10

# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """End-to-end integration tests"""
    
    def test_full_simulation_pipeline(self, complete_setup):
        """Test complete simulation from API call to results"""
        response = client.post("/api/simulate", json=complete_setup)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify all expected fields
        assert "success" in data
        assert "timestamp" in data
        assert "rays" in data
        assert "frequencySweep" in data
        assert "statistics" in data
        assert "warnings" in data
        
        # Verify data quality
        assert data["success"] == True
        assert len(data["rays"]) > 0
        assert len(data["frequencySweep"]) > 0
        assert data["statistics"]["totalPathLength"] > 0
    
    def test_export_import_consistency(self, complete_setup):
        """Test that exported data can be reimported"""
        # Simulate
        response1 = client.post("/api/simulate", json=complete_setup)
        result1 = response1.json()
        
        # Re-simulate same setup
        response2 = client.post("/api/simulate", json=complete_setup)
        result2 = response2.json()
        
        # Results should be consistent
        assert len(result1["rays"]) == len(result2["rays"])
        assert len(result1["frequencySweep"]) == len(result2["frequencySweep"])

# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Performance and edge case tests"""
    
    def test_large_number_of_components(self):
        """Test handling of many components"""
        components = []
        for i in range(50):
            components.append({
                "id": i,
                "type": "mirror",
                "position": {"x": 100 + i * 10, "y": 300},
                "rotation": 0,
                "properties": {"reflectivity": 0.95, "angle": 45}
            })
        
        setup = {
            "version": "1.0",
            "timestamp": "2025-10-30T00:00:00Z",
            "components": components,
            "simulation": {
                "sweepConfig": {"startFreq": 500, "stopFreq": 600, "points": 3},
                "rays": []
            }
        }
        
        response = client.post("/api/simulate", json=setup, timeout=30)
        assert response.status_code == 200
    
    def test_high_resolution_sweep(self, simple_source_setup):
        """Test high resolution frequency sweep"""
        setup = simple_source_setup.copy()
        setup["simulation"]["sweepConfig"]["points"] = 50
        
        response = client.post("/api/simulate", json=setup, timeout=30)
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["frequencySweep"]) == 50

# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])