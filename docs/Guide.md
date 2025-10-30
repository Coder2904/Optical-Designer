# 🔬 Optical Setup Designer

A powerful web application for designing and simulating optical setups with real-time ray tracing and frequency sweep analysis.

## ✨ Features

### 🎨 Visual Design Interface
- **Drag & Drop**: Intuitive component placement on grid-based canvas
- **Real-time Editing**: Adjust component properties instantly
- **Component Library**: Light sources, mirrors, lenses, and detectors
- **Rotation & Positioning**: Precise control over component orientation

### 🌈 Physics-Based Ray Tracing
- **Snell's Law**: Accurate refraction calculations
- **Fresnel Equations**: Realistic reflection coefficients
- **Thin Lens Approximation**: Proper ray bending through lenses
- **Multiple Rays**: Traces main beam + cone rays for realistic simulation
- **Intensity Tracking**: Accounts for transmission/reflection losses

### 📊 Frequency Sweep Analysis
- **Wavelength Range**: Configurable start/stop wavelengths (nm)
- **Spectral Analysis**: Multi-point frequency sweep (400-700nm default)
- **Detector Readings**: Per-detector intensity measurements
- **Path Length Analysis**: Optical path calculations
- **Frequency Conversion**: Wavelength ↔ Frequency (THz)

### 💾 Data Management
- **JSON Export**: Save complete setups with simulation results
- **JSON Import**: Load previously designed setups
- **Structured Format**: Easy integration with other tools
- **Timestamp Tracking**: Version control for your designs

## 🚀 Quick Start

### Prerequisites
```bash
# Node.js 18+
node --version

# Python 3.9+
python --version
```

### Installation

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 🎯 Usage Guide

### 1. Design Your Setup
1. Click component buttons (Light Source, Mirror, Lens, Detector)
2. Drag components onto canvas
3. Select and configure properties in right panel

### 2. Configure Simulation
- Set wavelength range (400-700nm)
- Choose number of sweep points
- Adjust component properties (reflectivity, focal length, etc.)

### 3. Run Simulation
- Click "Run Simulation" to trace rays through your setup
- View colored rays representing light paths
- Check results panel for statistics

### 4. Export Results
- Click "Export JSON" to save your design
- Includes component positions, properties, and simulation results
- Import later to continue work

## 🏗️ Architecture

### Frontend (React + Vite)
- **UI Framework**: React 18 with Hooks
- **Styling**: Tailwind CSS
- **Canvas Rendering**: HTML5 Canvas API
- **State Management**: React useState/useEffect
- **Icons**: Lucide React

### Backend (FastAPI + Python)
- **Web Framework**: FastAPI
- **Physics Engine**: NumPy + Custom algorithms
- **Data Validation**: Pydantic models
- **API Documentation**: Auto-generated Swagger UI

### Communication
- RESTful API
- JSON data exchange
- CORS-enabled for cross-origin requests

## 📡 API Documentation

### `POST /api/simulate`
Run optical simulation

**Request Body:**
```json
{
  "version": "1.0",
  "timestamp": "2025-10-30T12:00:00Z",
  "components": [
    {
      "id": 1,
      "type": "source",
      "position": {"x": 100, "y": 300},
      "rotation": 0,
      "properties": {
        "wavelength": 550,
        "power": 1,
        "beamAngle": 0
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
```

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-10-30T12:00:01Z",
  "rays": [...],
  "frequencySweep": [...],
  "statistics": {
    "totalRays": 3,
    "totalPathLength": 1250.5,
    "averageIntensity": 0.82,
    "totalInteractions": 5
  },
  "warnings": []
}
```

### `POST /api/validate`
Validate setup without simulation

### `GET /health`
Check service health status

Full API documentation available at: `http://localhost:8000/docs`

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
pytest tests/
```

### Test API Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Test simulation
curl -X POST http://localhost:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d @sample_setup.json
```

## 🌐 Deployment

### Deploy Backend (Render)
1. Push to GitHub
2. Connect repository to Render
3. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Deploy

### Deploy Frontend (Vercel)
1. Update API_URL in code
2. Connect repository to Vercel
3. Set build command: `npm run build`
4. Deploy

**Live Demo**: [Coming Soon]

## 🔬 Physics Implementation

### Ray Tracing Algorithm
```python
# Snell's Law (Refraction)
sin(θ₂) = (n₁/n₂) × sin(θ₁)

# Reflection
r⃗ = d⃗ - 2(d⃗·n⃗)n⃗

# Thin Lens
deflection ≈ -distance_from_axis / focal_length

# Fresnel Reflection
R = 0.5 × (rs² + rp²)
```

### Optical Components

| Component | Parameters | Physics Model |
|-----------|-----------|---------------|
| Light Source | Wavelength, Power, Beam Angle | Point source with cone emission |
| Mirror | Reflectivity, Angle | Specular reflection + Fresnel losses |
| Lens | Focal Length, Diameter | Thin lens approximation |
| Detector | Sensitivity, Area | Absorption with quantum efficiency |

## 📊 Example Use Cases

### 1. Michelson Interferometer
- Two mirrors at 90° angles
- Beam splitter (partial mirror)
- Single detector
- Wavelength sweep to observe interference

### 2. Lens Focusing System
- Light source at focal point
- Collimating lens
- Focusing lens
- Detector at focus

### 3. Multi-bounce Mirror System
- Single source
- Multiple mirrors in series
- Path length measurement
- Intensity loss analysis

## 🛠️ Development

### Project Structure
```
optical-designer/
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── index.jsx        # Entry point
│   │   └── index.css        # Styles
│   ├── public/
│   └── package.json
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── tests/
├── docs/
│   └── DEPLOYMENT.md
└── README.md
```

### Adding New Components

**Frontend (App.jsx):**
```javascript
const COMPONENT_TYPES = {
  your_component: { 
    name: 'Your Component', 
    color: '#hexcolor', 
    icon: '◆' 
  }
};
```

**Backend (main.py):**
```python
def _interact_with_your_component(self, ray: dict, component: Component):
    # Your physics implementation
    pass
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### Code Style
- **Frontend**: ESLint + Prettier
- **Backend**: Black + isort
- **Commits**: Conventional Commits format

## 📋 Roadmap

- [x] Basic ray tracing
- [x] Frequency sweep analysis
- [x] JSON import/export
- [ ] Beam splitters & polarizers
- [ ] 3D visualization
- [ ] Database integration
- [ ] User authentication
- [ ] Collaborative editing
- [ ] Advanced optics (diffraction, interference)
- [ ] Result visualization charts
- [ ] Batch simulations

## 🐛 Known Issues

- Ray tracing may show artifacts at component boundaries
- Large number of components (>50) may impact performance
- Free tier hosting may have cold start delays

See [Issues](https://github.com/Coder0429/optical-designer/issues) for full list.

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Physics algorithms based on fundamental optics principles
- UI inspired by modern design tools
- Built with love for the optics community

## 📧 Contact

**Project Maintainer**: Your Name
- GitHub: [@Coder0429](https://github.com/Coder0429)
- Email: optical-designer@gmail.com

**Project Link**: [https://github.com/Coder0429/optical-designer](https://github.com/yourusername/optical-designer)

---

⭐ Star this repo if you find it helpful!

💡 Have ideas? Open an issue or PR!

🚀 Happy Designing!