# Optical Setup Designer - Complete Deployment Guide

## 📁 Project Structure

```
optical-designer/
├── frontend/
│   ├── src/
│   │   ├── App.jsx (React component from artifact)
│   │   └── index.jsx
│   ├── public/
│   │   └── index.html
│   ├── package.json
│   └── vite.config.js
├── backend/
│   ├── main.py (FastAPI application)
│   ├── requirements.txt
│   └── .env
├── .gitignore
└── README.md
```

## 🚀 Quick Start Guide

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- Git

### 1. Backend Setup (Local)

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

Backend will run at: `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

### 2. Frontend Setup (Local)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will run at: `http://localhost:5173`

## ☁️ Deployment Instructions

### Backend Deployment (Render)

1. **Create Render Account**: Go to [render.com](https://render.com)

2. **Create New Web Service**:
   - Connect your GitHub repository
   - Select backend directory
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Environment Variables**:
   ```
   PYTHON_VERSION=3.11.0
   ```

4. **Deploy**: Render will automatically deploy
   - Your backend URL: `https://your-app.onrender.com`

### Frontend Deployment (Vercel)

1. **Update API URL**:
   In `App.jsx`, change:
   ```javascript
   const API_URL = 'https://your-backend-url.onrender.com';
   ```

2. **Create Vercel Account**: Go to [vercel.com](https://vercel.com)

3. **Deploy**:
   ```bash
   npm install -g vercel
   vercel
   ```
   
   Or connect GitHub repository directly through Vercel dashboard

4. **Configure**:
   - Framework Preset: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`

### Alternative: Railway Deployment

**Backend on Railway**:
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Deploy
railway up
```

**Frontend on Netlify**:
1. Connect GitHub repo
2. Build command: `npm run build`
3. Publish directory: `dist`

## 📦 Complete File Contents

### `backend/requirements.txt`
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
numpy==1.26.2
python-multipart==0.0.6
```

### `frontend/package.json`
```json
{
  "name": "optical-designer-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "lucide-react": "^0.263.1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.4.0"
  }
}
```

### `frontend/vite.config.js`
```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

### `frontend/tailwind.config.js`
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

### `frontend/src/index.jsx`
```javascript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

### `frontend/src/index.css`
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

### `frontend/public/index.html`
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Optical Setup Designer</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/index.jsx"></script>
  </body>
</html>
```

### `.gitignore`
```
# Frontend
frontend/node_modules/
frontend/dist/
frontend/.env

# Backend
backend/venv/
backend/__pycache__/
backend/*.pyc
backend/.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

## 🧪 Testing the Application

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Test Simulation
```bash
curl -X POST http://localhost:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.0",
    "timestamp": "2025-10-30T00:00:00Z",
    "components": [
      {
        "id": 1,
        "type": "source",
        "position": {"x": 100, "y": 300},
        "rotation": 0,
        "properties": {"wavelength": 550, "power": 1, "beamAngle": 0}
      }
    ],
    "simulation": {
      "sweepConfig": {
        "startFreq": 400,
        "stopFreq": 700,
        "points": 5
      },
      "rays": []
    }
  }'
```

## 📊 API Endpoints Reference

### `GET /`
Health check and service info

### `GET /health`
Detailed health status

### `POST /api/simulate`
Run full optical simulation
- **Input**: OpticalSetup JSON
- **Output**: SimulationResult with rays, frequency sweep, statistics

### `POST /api/validate`
Validate setup without simulation
- **Input**: OpticalSetup JSON
- **Output**: Validation results with issues and recommendations

## 🔧 Troubleshooting

### CORS Errors
If you get CORS errors, ensure backend CORS middleware is configured:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Backend Connection Issues
Update frontend `API_URL`:
```javascript
const API_URL = process.env.VITE_API_URL || 'http://localhost:8000';
```

Add to Vercel environment variables:
```
VITE_API_URL=https://your-backend.onrender.com
```

### Slow Render Cold Starts
Free tier Render services spin down after inactivity. First request may take 30-60 seconds.

## 📈 Performance Optimization

### Backend
- Use Redis for caching simulation results
- Implement request rate limiting
- Add result pagination for large datasets

### Frontend
- Lazy load components
- Implement virtual scrolling for large component lists
- Use React.memo for expensive renders

## 🔐 Security Considerations

1. **Input Validation**: Backend validates all inputs
2. **Rate Limiting**: Add rate limiting middleware
3. **HTTPS**: Always use HTTPS in production
4. **API Keys**: Consider adding API authentication for production

## 📝 Next Steps

1. ✅ Deploy backend to Render
2. ✅ Deploy frontend to Vercel
3. ✅ Test integration with deployed services
4. 📊 Add more optical components (beam splitters, diffraction gratings)
5. 📈 Implement result visualization charts
6. 💾 Add save/load functionality with database
7. 👥 Add user authentication
8. 🎨 Improve UI/UX with animations

## 🆘 Support & Documentation

- Backend API Docs: `https://your-backend-url.onrender.com/docs`
- Frontend Demo: `https://your-frontend-url.vercel.app`
- GitHub Issues: For bug reports and feature requests

## 📄 License

MIT License - Feel free to use and modify for your needs.