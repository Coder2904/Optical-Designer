"""
Optical Setup Simulation Backend
FastAPI-based service for optical ray tracing and frequency sweep analysis
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import numpy as np
import math
from datetime import datetime

app = FastAPI(
    title="Optical Simulation API",
    description="Backend service for optical setup design and simulation",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Data Models
# ============================================================================

class Position(BaseModel):
    x: float
    y: float

class ComponentProperties(BaseModel):
    """Dynamic properties for different component types"""
    wavelength: Optional[float] = None
    power: Optional[float] = None
    beamAngle: Optional[float] = None
    reflectivity: Optional[float] = None
    roc: Optional[float] = None  # Radius of curvature
    angle: Optional[float] = None
    transmissivity: Optional[float] = None
    focalLength: Optional[float] = None
    diameter: Optional[float] = None
    sensitivity: Optional[float] = None
    area: Optional[float] = None

class Component(BaseModel):
    id: int
    type: str  # laser, mirror, lens, photodetector, beamsplitter
    position: Position
    rotation: float
    properties: ComponentProperties

class Connection(BaseModel):
    id: int
    from_: Dict[str, Any] = Field(..., alias="from")
    to: Dict[str, Any]
    
    class Config:
        populate_by_name = True

class SweepConfig(BaseModel):
    startFreq: float = Field(..., description="Start wavelength in nm")
    stopFreq: float = Field(..., description="Stop wavelength in nm")
    points: int = Field(..., description="Number of sweep points")

class SimulationData(BaseModel):
    sweepConfig: SweepConfig
    rays: Optional[List[Dict]] = []

class OpticalSetup(BaseModel):
    version: str
    timestamp: str
    components: List[Component]
    connections: Optional[List[Connection]] = []
    simulation: SimulationData

class RayPath(BaseModel):
    path: List[Position]
    wavelength: float
    intensity: float
    pathLength: float
    interactions: List[str]

class DetectorReading(BaseModel):
    detectorId: int
    intensity: float
    wavelength: float
    incidentAngle: float

class FrequencySweepResult(BaseModel):
    wavelength: float
    frequency: float  # THz
    totalIntensity: float
    detectorReadings: List[DetectorReading]
    pathLengths: Dict[str, float]

class SimulationResult(BaseModel):
    success: bool
    timestamp: str
    rays: List[RayPath]
    frequencySweep: List[FrequencySweepResult]
    statistics: Dict[str, Any]
    warnings: List[str]

# ============================================================================
# Physics Engine
# ============================================================================

class OpticalPhysics:
    """Core physics calculations for optical simulation"""
    
    SPEED_OF_LIGHT = 299792458  # m/s
    
    @staticmethod
    def wavelength_to_frequency(wavelength_nm: float) -> float:
        """Convert wavelength (nm) to frequency (THz)"""
        wavelength_m = wavelength_nm * 1e-9
        frequency_hz = OpticalPhysics.SPEED_OF_LIGHT / wavelength_m
        return frequency_hz / 1e12  # Convert to THz
    
    @staticmethod
    def calculate_refraction(incident_angle: float, n1: float, n2: float) -> Optional[float]:
        """
        Snell's Law: Calculate refraction angle
        Returns None if total internal reflection occurs
        """
        sin_theta2 = (n1 / n2) * math.sin(incident_angle)
        if abs(sin_theta2) > 1:
            return None  # Total internal reflection
        return math.asin(sin_theta2)
    
    @staticmethod
    def reflect_ray(ray_dx: float, ray_dy: float, normal_x: float, normal_y: float) -> tuple:
        """Calculate reflected ray direction using vector reflection"""
        # Normalize normal vector
        norm = math.sqrt(normal_x**2 + normal_y**2)
        normal_x /= norm
        normal_y /= norm
        
        # Reflection formula: r = d - 2(d·n)n
        dot = ray_dx * normal_x + ray_dy * normal_y
        ref_dx = ray_dx - 2 * dot * normal_x
        ref_dy = ray_dy - 2 * dot * normal_y
        
        return ref_dx, ref_dy
    
    @staticmethod
    def lens_refraction(ray_dx: float, ray_dy: float, focal_length: float, 
                       distance_from_axis: float) -> tuple:
        """
        Thin lens approximation for ray refraction
        Uses paraxial approximation for simplicity
        """
        if focal_length == 0:
            return ray_dx, ray_dy
        
        # Thin lens equation: deflection angle ≈ -distance/f
        deflection = -distance_from_axis / focal_length
        
        # Apply small angle approximation
        new_dy = ray_dy + deflection * abs(ray_dx)
        
        # Normalize
        magnitude = math.sqrt(ray_dx**2 + new_dy**2)
        return ray_dx / magnitude, new_dy / magnitude
    
    @staticmethod
    def calculate_path_length(path: List[Position]) -> float:
        """Calculate total optical path length"""
        length = 0.0
        for i in range(len(path) - 1):
            dx = path[i+1].x - path[i].x
            dy = path[i+1].y - path[i].y
            length += math.sqrt(dx**2 + dy**2)
        return length
    
    @staticmethod
    def fresnel_reflection(theta_i: float, n1: float = 1.0, n2: float = 1.5) -> float:
        """
        Calculate Fresnel reflection coefficient (simplified)
        Assumes unpolarized light
        """
        if theta_i == 0:
            r = ((n1 - n2) / (n1 + n2)) ** 2
            return r
        
        theta_t = OpticalPhysics.calculate_refraction(theta_i, n1, n2)
        if theta_t is None:
            return 1.0  # Total internal reflection
        
        # Fresnel equations for s and p polarization
        rs = math.sin(theta_i - theta_t) / math.sin(theta_i + theta_t)
        rp = math.tan(theta_i - theta_t) / math.tan(theta_i + theta_t)
        
        # Average for unpolarized light
        R = 0.5 * (rs**2 + rp**2)
        return R

# ============================================================================
# Ray Tracing Engine
# ============================================================================

class RayTracer:
    """Advanced ray tracing engine with physics-based interactions"""
    
    def __init__(self, setup: OpticalSetup, canvas_width: int = 800, 
                 canvas_height: int = 600):
        self.setup = setup
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.physics = OpticalPhysics()
        
    def trace_all_rays(self, wavelength: float = None) -> List[RayPath]:
        """Trace rays from all light sources following connections"""
        lasers = [c for c in self.setup.components if c.type == "laser"]
        all_rays = []
        
        for laser in lasers:
            # Use laser wavelength if not specified
            wl = wavelength or laser.properties.wavelength or 550
            
            # Find connections from this laser
            laser_connections = [
                conn for conn in self.setup.connections 
                if conn.from_['componentId'] == laser.id
            ]
            
            if not laser_connections:
                # No connections, trace in default direction
                angle = math.radians(laser.rotation)
                ray = {
                    'x': laser.position.x,
                    'y': laser.position.y,
                    'dx': math.cos(angle),
                    'dy': math.sin(angle),
                    'wavelength': wl,
                    'intensity': laser.properties.power or 1.0,
                    'path': [Position(x=laser.position.x, y=laser.position.y)],
                    'interactions': []
                }
                traced_ray = self._trace_single_ray(ray)
                all_rays.append(traced_ray)
            else:
                # Trace along connections
                for conn in laser_connections:
                    target_comp = next(
                        (c for c in self.setup.components if c.id == conn.to['componentId']), 
                        None
                    )
                    if target_comp:
                        # Calculate direction to target
                        dx = target_comp.position.x - laser.position.x
                        dy = target_comp.position.y - laser.position.y
                        dist = math.sqrt(dx**2 + dy**2)
                        
                        ray = {
                            'x': laser.position.x,
                            'y': laser.position.y,
                            'dx': dx / dist if dist > 0 else 1,
                            'dy': dy / dist if dist > 0 else 0,
                            'wavelength': wl,
                            'intensity': laser.properties.power or 1.0,
                            'path': [Position(x=laser.position.x, y=laser.position.y)],
                            'interactions': []
                        }
                        traced_ray = self._trace_single_ray(ray)
                        all_rays.append(traced_ray)
        
        return all_rays
    
    def _trace_single_ray(self, ray: dict, max_bounces: int = 50) -> RayPath:
        """Trace a single ray through the optical system"""
        step_size = 10  # pixels per step
        
        for bounce in range(max_bounces):
            # Propagate ray
            ray['x'] += ray['dx'] * step_size
            ray['y'] += ray['dy'] * step_size
            
            # Check boundaries
            if (ray['x'] < 0 or ray['x'] > self.canvas_width or 
                ray['y'] < 0 or ray['y'] > self.canvas_height):
                break
            
            ray['path'].append(Position(x=ray['x'], y=ray['y']))
            
            # Check interactions with components
            interacted = False
            
            # Check beam splitters first
            for beamsplitter in [c for c in self.setup.components if c.type == "beamsplitter"]:
                if self._check_intersection(ray, beamsplitter, threshold=30):
                    ray = self._interact_with_beamsplitter(ray, beamsplitter)
                    interacted = True
                    break
            
            if interacted:
                continue
            
            # Check mirrors
            for mirror in [c for c in self.setup.components if c.type == "mirror"]:
                if self._check_intersection(ray, mirror, threshold=25):
                    ray = self._interact_with_mirror(ray, mirror)
                    interacted = True
                    break
            
            if interacted:
                continue
            
            # Check lenses
            for lens in [c for c in self.setup.components if c.type == "lens"]:
                if self._check_intersection(ray, lens, threshold=30):
                    ray = self._interact_with_lens(ray, lens)
                    interacted = True
                    break
            
            if interacted:
                continue
            
            # Check photodetectors (absorption)
            for detector in [c for c in self.setup.components if c.type == "photodetector"]:
                if self._check_intersection(ray, detector, threshold=25):
                    ray['interactions'].append(f"Detected at ({detector.position.x:.0f}, {detector.position.y:.0f})")
                    ray['intensity'] = 0  # Absorbed
                    break
            
            # Stop if intensity too low
            if ray['intensity'] < 0.01:
                break
        
        path_length = self.physics.calculate_path_length(ray['path'])
        
        return RayPath(
            path=ray['path'],
            wavelength=ray['wavelength'],
            intensity=ray['intensity'],
            pathLength=path_length,
            interactions=ray['interactions']
        )
    
    def _check_intersection(self, ray: dict, component: Component, 
                           threshold: float) -> bool:
        """Check if ray intersects with component"""
        dx = ray['x'] - component.position.x
        dy = ray['y'] - component.position.y
        distance = math.sqrt(dx**2 + dy**2)
        return distance < threshold
    
    def _interact_with_mirror(self, ray: dict, mirror: Component) -> dict:
        """Handle ray-mirror interaction"""
        # Calculate mirror normal
        mirror_angle = math.radians(mirror.properties.angle or 45)
        normal_x = math.sin(mirror_angle)
        normal_y = -math.cos(mirror_angle)
        
        # Calculate incident angle
        incident_angle = math.acos(
            abs(ray['dx'] * normal_x + ray['dy'] * normal_y)
        )
        
        # Reflect ray
        ray['dx'], ray['dy'] = self.physics.reflect_ray(
            ray['dx'], ray['dy'], normal_x, normal_y
        )
        
        # Apply reflectivity and Fresnel losses
        reflectivity = mirror.properties.reflectivity or 0.95
        fresnel = self.physics.fresnel_reflection(incident_angle)
        ray['intensity'] *= reflectivity * (1 - 0.1 * (1 - fresnel))
        
        ray['interactions'].append(
            f"Mirror reflection at ({mirror.position.x:.0f}, {mirror.position.y:.0f}), "
            f"angle={math.degrees(incident_angle):.1f}°"
        )
        
        return ray
    
    def _interact_with_beamsplitter(self, ray: dict, beamsplitter: Component) -> dict:
        """Handle ray-beamsplitter interaction"""
        # Calculate beamsplitter normal (45 degrees to surface)
        bs_angle = math.radians(beamsplitter.rotation + 45)
        normal_x = math.sin(bs_angle)
        normal_y = -math.cos(bs_angle)
        
        # Calculate incident angle
        incident_angle = math.acos(
            abs(ray['dx'] * normal_x + ray['dy'] * normal_y)
        )
        
        # Split beam: reflect and transmit
        reflectivity = beamsplitter.properties.reflectivity or 0.5
        transmissivity = beamsplitter.properties.transmissivity or 0.5
        
        # For simplicity, we'll modify the main ray (reflected component)
        # In a full implementation, we'd spawn a second ray for transmission
        ray['dx'], ray['dy'] = self.physics.reflect_ray(
            ray['dx'], ray['dy'], normal_x, normal_y
        )
        
        # Apply beam splitting losses
        ray['intensity'] *= reflectivity * 0.98  # 2% loss
        
        ray['interactions'].append(
            f"Beam splitter at ({beamsplitter.position.x:.0f}, {beamsplitter.position.y:.0f}), "
            f"R={reflectivity:.2f}, T={transmissivity:.2f}"
        )
        
        return ray
    
    def _interact_with_lens(self, ray: dict, lens: Component) -> dict:
        """Handle ray-lens interaction"""
        # Distance from optical axis (center of lens)
        distance_from_axis = abs(ray['y'] - lens.position.y)
        
        focal_length = lens.properties.focalLength or 100
        
        # Apply thin lens refraction
        ray['dx'], ray['dy'] = self.physics.lens_refraction(
            ray['dx'], ray['dy'], focal_length, distance_from_axis
        )
        
        # Transmission loss (simplified)
        ray['intensity'] *= 0.96  # 4% loss typical for coated optics
        
        ray['interactions'].append(
            f"Lens refraction at ({lens.position.x:.0f}, {lens.position.y:.0f}), "
            f"f={focal_length:.0f}mm"
        )
        
        return ray

# ============================================================================
# Frequency Sweep Analyzer
# ============================================================================

class FrequencySweepAnalyzer:
    """Perform frequency sweep analysis across wavelength range"""
    
    def __init__(self, setup: OpticalSetup, ray_tracer: RayTracer):
        self.setup = setup
        self.ray_tracer = ray_tracer
        self.physics = OpticalPhysics()
    
    def perform_sweep(self) -> List[FrequencySweepResult]:
        """Execute frequency sweep simulation"""
        config = self.setup.simulation.sweepConfig
        
        # Generate wavelength points
        wavelengths = np.linspace(
            config.startFreq, 
            config.stopFreq, 
            config.points
        )
        
        results = []
        detectors = [c for c in self.setup.components if c.type == "photodetector"]
        
        for wl in wavelengths:
            # Trace rays at this wavelength
            rays = self.ray_tracer.trace_all_rays(wavelength=float(wl))
            
            # Calculate detector readings
            detector_readings = []
            total_intensity = 0.0
            
            for detector in detectors:
                intensity = 0.0
                incident_angles = []
                
                for ray in rays:
                    # Check if ray hits detector
                    for i, point in enumerate(ray.path):
                        dx = point.x - detector.position.x
                        dy = point.y - detector.position.y
                        dist = math.sqrt(dx**2 + dy**2)
                        
                        if dist < 25:  # Detector radius
                            # Calculate incident angle
                            if i > 0:
                                prev_point = ray.path[i-1]
                                ray_dx = point.x - prev_point.x
                                ray_dy = point.y - prev_point.y
                                angle = math.atan2(ray_dy, ray_dx)
                                incident_angles.append(angle)
                            
                            # Add intensity
                            sensitivity = detector.properties.sensitivity or 1.0
                            intensity += ray.intensity * sensitivity
                            break
                
                avg_angle = np.mean(incident_angles) if incident_angles else 0.0
                
                detector_readings.append(DetectorReading(
                    detectorId=detector.id,
                    intensity=intensity,
                    wavelength=wl,
                    incidentAngle=float(math.degrees(avg_angle))
                ))
                
                total_intensity += intensity
            
            # Calculate path lengths
            path_lengths = {
                f"ray_{i}": ray.pathLength 
                for i, ray in enumerate(rays)
            }
            
            results.append(FrequencySweepResult(
                wavelength=float(wl),
                frequency=self.physics.wavelength_to_frequency(float(wl)),
                totalIntensity=total_intensity,
                detectorReadings=detector_readings,
                pathLengths=path_lengths
            ))
        
        return results

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Optical Simulation API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "simulate": "/api/simulate",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "ray_tracer": "operational",
            "frequency_sweep": "operational",
            "physics_engine": "operational"
        }
    }

@app.post("/api/simulate", response_model=SimulationResult)
async def simulate_optical_setup(setup: OpticalSetup):
    """
    Main simulation endpoint
    
    Accepts optical setup JSON and returns:
    - Ray tracing results with path data
    - Frequency sweep analysis
    - Statistical analysis
    - Warnings and recommendations
    """
    try:
        warnings = []
        
        # Validate setup
        if not setup.components:
            raise HTTPException(status_code=400, detail="No components in setup")
        
        lasers = [c for c in setup.components if c.type == "laser"]
        if not lasers:
            warnings.append("No laser sources found in setup")
        
        detectors = [c for c in setup.components if c.type == "photodetector"]
        if not detectors:
            warnings.append("No detectors found - results will not be measured")
        
        # Validate connections
        if setup.connections:
            for conn in setup.connections:
                from_comp = next((c for c in setup.components if c.id == conn.from_['componentId']), None)
                to_comp = next((c for c in setup.components if c.id == conn.to['componentId']), None)
                if not from_comp or not to_comp:
                    warnings.append(f"Invalid connection: component not found")
        
        # Initialize ray tracer
        ray_tracer = RayTracer(setup)
        
        # Trace rays at default wavelength
        rays = ray_tracer.trace_all_rays()
        
        # Perform frequency sweep
        sweep_analyzer = FrequencySweepAnalyzer(setup, ray_tracer)
        frequency_sweep = sweep_analyzer.perform_sweep()
        
        # Calculate statistics
        total_path_length = sum(ray.pathLength for ray in rays)
        avg_intensity = np.mean([ray.intensity for ray in rays])
        total_interactions = sum(len(ray.interactions) for ray in rays)
        
        statistics = {
            "totalRays": len(rays),
            "totalPathLength": float(total_path_length),
            "averageIntensity": float(avg_intensity),
            "totalInteractions": total_interactions,
            "componentCount": {
                "lasers": len(lasers),
                "mirrors": len([c for c in setup.components if c.type == "mirror"]),
                "beamsplitters": len([c for c in setup.components if c.type == "beamsplitter"]),
                "lenses": len([c for c in setup.components if c.type == "lens"]),
                "photodetectors": len(detectors)
            },
            "connectionCount": len(setup.connections) if setup.connections else 0,
            "frequencySweepPoints": len(frequency_sweep),
            "wavelengthRange": {
                "min": setup.simulation.sweepConfig.startFreq,
                "max": setup.simulation.sweepConfig.stopFreq,
                "unit": "nm"
            }
        }
        
        # Performance warnings
        if len(rays) > 100:
            warnings.append("Large number of rays may impact performance")
        
        if total_interactions < 2 and len(setup.components) > 3:
            warnings.append("Few ray-component interactions detected - check alignment")
        
        return SimulationResult(
            success=True,
            timestamp=datetime.now().isoformat(),
            rays=rays,
            frequencySweep=frequency_sweep,
            statistics=statistics,
            warnings=warnings
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Simulation error: {str(e)}"
        )

@app.post("/api/validate")
async def validate_setup(setup: OpticalSetup):
    """Validate optical setup without running simulation"""
    issues = []
    recommendations = []
    
    # Check for lasers
    lasers = [c for c in setup.components if c.type == "laser"]
    if not lasers:
        issues.append("No laser sources found")
    
    # Check for detectors
    detectors = [c for c in setup.components if c.type == "photodetector"]
    if not detectors:
        recommendations.append("Add photodetectors to measure light intensity")
    
    # Check connections
    if not setup.connections or len(setup.connections) == 0:
        recommendations.append("Connect components using ports for better simulation accuracy")
    
    # Check component overlap
    for i, comp1 in enumerate(setup.components):
        for comp2 in setup.components[i+1:]:
            dx = comp1.position.x - comp2.position.x
            dy = comp1.position.y - comp2.position.y
            dist = math.sqrt(dx**2 + dy**2)
            if dist < 40:
                issues.append(
                    f"Components {comp1.id} and {comp2.id} may be overlapping"
                )
    
    # Check sweep configuration
    if setup.simulation.sweepConfig.startFreq >= setup.simulation.sweepConfig.stopFreq:
        issues.append("Invalid frequency sweep range")
    
    if setup.simulation.sweepConfig.points < 2:
        issues.append("Frequency sweep needs at least 2 points")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "recommendations": recommendations,
        "componentCount": len(setup.components)
    }

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)