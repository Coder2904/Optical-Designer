import React, { useState, useRef, useEffect } from 'react';
import { Download, Trash2, Plus, Play, Settings, Upload, Zap, Link2 } from 'lucide-react';

const GRID_SIZE = 60;
const CANVAS_WIDTH = 960;
const CANVAS_HEIGHT = 720;
const PORT_RADIUS = 8;
const API_URL = 'https://optical-designer-hpqt.onrender.com';

const COMPONENT_TYPES = {
  laser: { 
    name: 'Laser', 
    color: '#fbbf24', 
    icon: '◉',
    ports: [{ id: 'out', x: 30, y: 0, type: 'output' }],
    width: 40,
    height: 40
  },
  mirror: { 
    name: 'Mirror', 
    color: '#60a5fa', 
    icon: '|',
    ports: [
      { id: 'in', x: -20, y: 0, type: 'input' },
      { id: 'out', x: 0, y: -20, type: 'output' }
    ],
    width: 40,
    height: 40
  },
  beamsplitter: { 
    name: 'Beam Splitter', 
    color: '#a78bfa', 
    icon: '⊕',
    ports: [
      { id: 'in', x: -25, y: 0, type: 'input' },
      { id: 'out1', x: 25, y: 0, type: 'output' },
      { id: 'out2', x: 0, y: 25, type: 'output' },
      { id: 'out3', x: 0, y: -25, type: 'output' }
    ],
    width: 50,
    height: 50
  },
  lens: { 
    name: 'Lens', 
    color: '#34d399', 
    icon: '()',
    ports: [
      { id: 'in', x: -30, y: 0, type: 'input' },
      { id: 'out', x: 30, y: 0, type: 'output' }
    ],
    width: 40,
    height: 50
  },
  photodetector: { 
    name: 'Photo-detector', 
    color: '#f87171', 
    icon: '□',
    ports: [
      { id: 'in', x: -20, y: 0, type: 'input' }
    ],
    width: 40,
    height: 40
  }
};

const OpticalDesigner = () => {
  const [components, setComponents] = useState([]);
  const [connections, setConnections] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [dragging, setDragging] = useState(null);
  const [connecting, setConnecting] = useState(null);
  const [hoveredPort, setHoveredPort] = useState(null);
  const [rays, setRays] = useState([]);
  const [showRays, setShowRays] = useState(false);
  const [sweepConfig, setSweepConfig] = useState({
    startFreq: 400,
    stopFreq: 700,
    points: 10
  });
  const [simulationResult, setSimulationResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const canvasRef = useRef(null);

  const addComponent = (type) => {
    const newComponent = {
      id: Date.now(),
      type,
      x: 120,
      y: 120,
      angle: 0,
      properties: getDefaultProperties(type)
    };
    setComponents([...components, newComponent]);
  };

  const getDefaultProperties = (type) => {
    switch(type) {
      case 'laser':
        return { wavelength: 550, power: 1 };
      case 'mirror':
        return { reflectivity: 0.95, roc: 1000 };
      case 'beamsplitter':
        return { reflectivity: 0.5, transmissivity: 0.5 };
      case 'lens':
        return { focalLength: 100 };
      case 'photodetector':
        return { sensitivity: 1 };
      default:
        return {};
    }
  };

  const deleteComponent = (id) => {
    setComponents(components.filter(c => c.id !== id));
    setConnections(connections.filter(c => c.fromComp !== id && c.toComp !== id));
    if (selectedId === id) setSelectedId(null);
  };

  const updateComponent = (id, updates) => {
    setComponents(components.map(c => 
      c.id === id ? { ...c, ...updates } : c
    ));
  };

  const updateProperty = (id, property, value) => {
    setComponents(components.map(c => 
      c.id === id ? { 
        ...c, 
        properties: { ...c.properties, [property]: parseFloat(value) || 0 }
      } : c
    ));
  };

  const getPortWorldPosition = (component, port) => {
    const angle = component.angle * Math.PI / 180;
    const cos = Math.cos(angle);
    const sin = Math.sin(angle);
    
    return {
      x: component.x + port.x * cos - port.y * sin,
      y: component.y + port.x * sin + port.y * cos,
      portId: port.id
    };
  };

  const findPortAtPosition = (x, y) => {
    for (const comp of components) {
      const compType = COMPONENT_TYPES[comp.type];
      for (const port of compType.ports) {
        const worldPos = getPortWorldPosition(comp, port);
        const dist = Math.sqrt((x - worldPos.x) ** 2 + (y - worldPos.y) ** 2);
        if (dist < PORT_RADIUS * 2) {
          return { component: comp, port, worldPos };
        }
      }
    }
    return null;
  };

  const handleMouseDown = (e, id) => {
    if (e.button !== 0) return;
    
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Check if clicking on a port
    const portInfo = findPortAtPosition(x, y);
    if (portInfo) {
      if (portInfo.port.type === 'output') {
        setConnecting({
          fromComp: portInfo.component.id,
          fromPort: portInfo.port.id,
          startX: portInfo.worldPos.x,
          startY: portInfo.worldPos.y,
          currentX: x,
          currentY: y
        });
      }
      return;
    }
    
    // Otherwise drag component
    setSelectedId(id);
    const component = components.find(c => c.id === id);
    setDragging({
      id,
      offsetX: x - component.x,
      offsetY: y - component.y
    });
  };

  const handleMouseMove = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Update hovered port
    const portInfo = findPortAtPosition(x, y);
    setHoveredPort(portInfo);
    
    if (connecting) {
      setConnecting({ ...connecting, currentX: x, currentY: y });
    } else if (dragging) {
      const newX = Math.round((x - dragging.offsetX) / GRID_SIZE) * GRID_SIZE;
      const newY = Math.round((y - dragging.offsetY) / GRID_SIZE) * GRID_SIZE;
      updateComponent(dragging.id, { x: newX, y: newY });
    }
  };

  const handleMouseUp = (e) => {
    if (connecting) {
      const rect = canvasRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      const portInfo = findPortAtPosition(x, y);
      if (portInfo && portInfo.port.type === 'input') {
        // Create connection
        const newConnection = {
          id: Date.now(),
          fromComp: connecting.fromComp,
          fromPort: connecting.fromPort,
          toComp: portInfo.component.id,
          toPort: portInfo.port.id
        };
        
        // Check if connection already exists
        const exists = connections.some(c => 
          c.fromComp === newConnection.fromComp && 
          c.fromPort === newConnection.fromPort &&
          c.toComp === newConnection.toComp && 
          c.toPort === newConnection.toPort
        );
        
        if (!exists) {
          setConnections([...connections, newConnection]);
        }
      }
      setConnecting(null);
    }
    setDragging(null);
  };

  const deleteConnection = (connId) => {
    setConnections(connections.filter(c => c.id !== connId));
  };

  const runBackendSimulation = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const setup = {
        version: '1.0',
        timestamp: new Date().toISOString(),
        components: components.map(c => ({
          id: c.id,
          type: c.type,
          position: { x: c.x, y: c.y },
          rotation: c.angle,
          properties: c.properties
        })),
        connections: connections.map(c => ({
          id: c.id,
          from: { componentId: c.fromComp, port: c.fromPort },
          to: { componentId: c.toComp, port: c.toPort }
        })),
        simulation: {
          sweepConfig,
          rays: []
        }
      };

      const response = await fetch(`${API_URL}/api/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(setup)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setSimulationResult(result);
      setRays(result.rays || []);
      setShowRays(true);
      
    } catch (err) {
      setError(err.message);
      console.error('Simulation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const exportJSON = () => {
    const setup = {
      version: '1.0',
      timestamp: new Date().toISOString(),
      components: components.map(c => ({
        id: c.id,
        type: c.type,
        position: { x: c.x, y: c.y },
        rotation: c.angle,
        properties: c.properties
      })),
      connections: connections.map(c => ({
        id: c.id,
        from: { componentId: c.fromComp, port: c.fromPort },
        to: { componentId: c.toComp, port: c.toPort }
      })),
      simulation: {
        sweepConfig,
        rays: showRays ? rays : []
      },
      results: simulationResult
    };
    
    const blob = new Blob([JSON.stringify(setup, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `optical_setup_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const importJSON = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const setup = JSON.parse(e.target.result);
        setComponents(setup.components.map(c => ({
          id: c.id,
          type: c.type,
          x: c.position.x,
          y: c.position.y,
          angle: c.rotation,
          properties: c.properties
        })));
        
        if (setup.connections) {
          setConnections(setup.connections.map(c => ({
            id: c.id,
            fromComp: c.from.componentId,
            fromPort: c.from.port,
            toComp: c.to.componentId,
            toPort: c.to.port
          })));
        }
        
        if (setup.simulation) {
          setSweepConfig(setup.simulation.sweepConfig);
        }
      } catch (err) {
        setError('Invalid JSON file');
      }
    };
    reader.readAsText(file);
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    
    // Draw grid
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= CANVAS_WIDTH; i += GRID_SIZE) {
      ctx.beginPath();
      ctx.moveTo(i, 0);
      ctx.lineTo(i, CANVAS_HEIGHT);
      ctx.stroke();
    }
    for (let i = 0; i <= CANVAS_HEIGHT; i += GRID_SIZE) {
      ctx.beginPath();
      ctx.moveTo(0, i);
      ctx.lineTo(CANVAS_WIDTH, i);
      ctx.stroke();
    }
    
    // Draw connections
    connections.forEach(conn => {
      const fromComp = components.find(c => c.id === conn.fromComp);
      const toComp = components.find(c => c.id === conn.toComp);
      if (!fromComp || !toComp) return;
      
      const fromType = COMPONENT_TYPES[fromComp.type];
      const toType = COMPONENT_TYPES[toComp.type];
      const fromPort = fromType.ports.find(p => p.id === conn.fromPort);
      const toPort = toType.ports.find(p => p.id === conn.toPort);
      
      const fromPos = getPortWorldPosition(fromComp, fromPort);
      const toPos = getPortWorldPosition(toComp, toPort);
      
      ctx.strokeStyle = '#6366f1';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(fromPos.x, fromPos.y);
      ctx.lineTo(toPos.x, toPos.y);
      ctx.stroke();
      
      // Draw arrow
      const angle = Math.atan2(toPos.y - fromPos.y, toPos.x - fromPos.x);
      const arrowSize = 10;
      ctx.fillStyle = '#6366f1';
      ctx.beginPath();
      ctx.moveTo(toPos.x, toPos.y);
      ctx.lineTo(
        toPos.x - arrowSize * Math.cos(angle - Math.PI / 6),
        toPos.y - arrowSize * Math.sin(angle - Math.PI / 6)
      );
      ctx.lineTo(
        toPos.x - arrowSize * Math.cos(angle + Math.PI / 6),
        toPos.y - arrowSize * Math.sin(angle + Math.PI / 6)
      );
      ctx.closePath();
      ctx.fill();
    });
    
    // Draw temporary connection line
    if (connecting) {
      ctx.strokeStyle = '#6366f1';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      ctx.moveTo(connecting.startX, connecting.startY);
      ctx.lineTo(connecting.currentX, connecting.currentY);
      ctx.stroke();
      ctx.setLineDash([]);
    }
    
    // Draw rays
    if (showRays && rays.length > 0) {
      rays.forEach(ray => {
        const hue = ((ray.wavelength - 380) / (750 - 380)) * 270;
        ctx.strokeStyle = `hsla(${hue}, 100%, 50%, ${Math.min(ray.intensity, 1)})`;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ray.path.forEach((point, i) => {
          if (i === 0) ctx.moveTo(point.x, point.y);
          else ctx.lineTo(point.x, point.y);
        });
        ctx.stroke();
      });
    }
    
    // Draw components
    components.forEach(comp => {
      const isSelected = comp.id === selectedId;
      const compType = COMPONENT_TYPES[comp.type];
      
      ctx.save();
      ctx.translate(comp.x, comp.y);
      ctx.rotate(comp.angle * Math.PI / 180);
      
      ctx.fillStyle = compType.color;
      ctx.strokeStyle = isSelected ? '#000' : '#666';
      ctx.lineWidth = isSelected ? 3 : 2;
      
      switch(comp.type) {
        case 'laser':
          ctx.beginPath();
          ctx.arc(0, 0, 15, 0, Math.PI * 2);
          ctx.fill();
          ctx.stroke();
          for (let i = 0; i < 8; i++) {
            const angle = (i / 8) * Math.PI * 2;
            ctx.beginPath();
            ctx.moveTo(Math.cos(angle) * 18, Math.sin(angle) * 18);
            ctx.lineTo(Math.cos(angle) * 25, Math.sin(angle) * 25);
            ctx.stroke();
          }
          break;
        case 'mirror':
          ctx.beginPath();
          ctx.moveTo(-5, -25);
          ctx.lineTo(-5, 25);
          ctx.lineTo(5, 25);
          ctx.lineTo(5, -25);
          ctx.closePath();
          ctx.fill();
          ctx.stroke();
          break;
        case 'beamsplitter':
          ctx.beginPath();
          ctx.moveTo(0, -25);
          ctx.lineTo(25, 0);
          ctx.lineTo(0, 25);
          ctx.lineTo(-25, 0);
          ctx.closePath();
          ctx.fill();
          ctx.stroke();
          // Draw diagonal line
          ctx.beginPath();
          ctx.moveTo(-20, -20);
          ctx.lineTo(20, 20);
          ctx.stroke();
          break;
        case 'lens':
          ctx.beginPath();
          ctx.arc(-10, 0, 25, -Math.PI/2, Math.PI/2);
          ctx.arc(10, 0, 25, Math.PI/2, -Math.PI/2);
          ctx.closePath();
          ctx.fill();
          ctx.stroke();
          break;
        case 'photodetector':
          ctx.fillRect(-20, -20, 40, 40);
          ctx.strokeRect(-20, -20, 40, 40);
          break;
      }
      
      // Draw ports
      compType.ports.forEach(port => {
        ctx.fillStyle = port.type === 'input' ? '#ef4444' : '#10b981';
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(port.x, port.y, PORT_RADIUS, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
      });
      
      ctx.restore();
      
      // Draw label
      ctx.fillStyle = '#000';
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(compType.name, comp.x, comp.y + 45);
    });
    
    // Highlight hovered port
    if (hoveredPort) {
      const pos = hoveredPort.worldPos;
      ctx.strokeStyle = '#fbbf24';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, PORT_RADIUS + 3, 0, Math.PI * 2);
      ctx.stroke();
    }
  }, [components, connections, selectedId, connecting, hoveredPort, rays, showRays]);

  const selectedComponent = components.find(c => c.id === selectedId);

  return (
    <div className="w-full h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Optical Setup Designer</h1>
          <p className="text-xs text-gray-500">Port-based optical system with connections</p>
        </div>
        <div className="flex gap-2">
          <label className="flex items-center gap-2 px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 transition cursor-pointer">
            <Upload size={16} />
            Import
            <input type="file" accept=".json" onChange={importJSON} className="hidden" />
          </label>
          <button
            onClick={runBackendSimulation}
            disabled={loading || components.length === 0}
            className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition disabled:opacity-50"
          >
            <Zap size={16} />
            {loading ? 'Simulating...' : 'Simulate'}
          </button>
          <button
            onClick={exportJSON}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition"
          >
            <Download size={16} />
            Export
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-2 text-sm">
          {error}
        </div>
      )}

      <div className="flex-1 flex overflow-hidden">
        {/* Toolbar */}
        <div className="w-56 bg-white border-r border-gray-200 p-4 overflow-y-auto">
          <h2 className="font-semibold text-gray-700 mb-3">Components</h2>
          {Object.entries(COMPONENT_TYPES).map(([type, info]) => (
            <button
              key={type}
              onClick={() => addComponent(type)}
              className="w-full mb-2 p-3 bg-gray-100 hover:bg-gray-200 rounded flex items-center gap-2 transition text-left"
            >
              <span className="text-2xl">{info.icon}</span>
              <div>
                <div className="text-sm font-medium">{info.name}</div>
                <div className="text-xs text-gray-500">{info.ports.length} ports</div>
              </div>
            </button>
          ))}
          
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h2 className="font-semibold text-gray-700 mb-2">Instructions</h2>
            <div className="text-xs text-gray-600 space-y-2">
              <p>• Drag components to position</p>
              <p>• Click output port (green) and drag to input port (red)</p>
              <p>• Select component to edit properties</p>
            </div>
          </div>

          {connections.length > 0 && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h2 className="font-semibold text-gray-700 mb-2 flex items-center gap-2">
                <Link2 size={16} />
                Connections ({connections.length})
              </h2>
              <div className="space-y-1">
                {connections.map(conn => {
                  const fromComp = components.find(c => c.id === conn.fromComp);
                  const toComp = components.find(c => c.id === conn.toComp);
                  return (
                    <div key={conn.id} className="text-xs bg-gray-50 p-2 rounded flex justify-between items-center">
                      <span className="truncate">
                        {COMPONENT_TYPES[fromComp?.type]?.name} → {COMPONENT_TYPES[toComp?.type]?.name}
                      </span>
                      <button
                        onClick={() => deleteConnection(conn.id)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Canvas */}
        <div className="flex-1 overflow-auto p-8 bg-gray-100">
          <canvas
            ref={canvasRef}
            width={CANVAS_WIDTH}
            height={CANVAS_HEIGHT}
            onMouseDown={(e) => {
              const rect = canvasRef.current.getBoundingClientRect();
              const x = e.clientX - rect.left;
              const y = e.clientY - rect.top;
              const clicked = components.find(c => {
                const dist = Math.sqrt((x - c.x) ** 2 + (y - c.y) ** 2);
                return dist < 30;
              });
              if (clicked) {
                handleMouseDown(e, clicked.id);
              } else {
                setSelectedId(null);
              }
            }}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            className="bg-white shadow-lg cursor-crosshair"
          />
        </div>

        {/* Properties Panel */}
        <div className="w-64 bg-white border-l border-gray-200 p-4 overflow-y-auto">
          <h2 className="font-semibold text-gray-700 mb-3">Properties</h2>
          {selectedComponent ? (
            <div className="space-y-3">
              <div className="pb-3 border-b border-gray-200">
                <p className="text-sm font-medium text-gray-600">
                  {COMPONENT_TYPES[selectedComponent.type].name}
                </p>
                <p className="text-xs text-gray-400">ID: {selectedComponent.id}</p>
              </div>
              
              <div>
                <label className="text-xs text-gray-600">Position X</label>
                <input
                  type="number"
                  value={selectedComponent.x}
                  onChange={(e) => updateComponent(selectedComponent.id, { x: parseFloat(e.target.value) })}
                  className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                  step={GRID_SIZE}
                />
              </div>
              
              <div>
                <label className="text-xs text-gray-600">Position Y</label>
                <input
                  type="number"
                  value={selectedComponent.y}
                  onChange={(e) => updateComponent(selectedComponent.id, { y: parseFloat(e.target.value) })}
                  className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                  step={GRID_SIZE}
                />
              </div>
              
              <div>
                <label className="text-xs text-gray-600">Rotation (deg)</label>
                <input
                  type="number"
                  value={selectedComponent.angle}
                  onChange={(e) => updateComponent(selectedComponent.id, { angle: parseFloat(e.target.value) })}
                  className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                  step="45"
                />
              </div>
              
              <div className="pt-3 border-t border-gray-200">
                <p className="text-xs font-medium text-gray-600 mb-2">Properties</p>
                {Object.entries(selectedComponent.properties).map(([key, value]) => (
                  <div key={key} className="mb-2">
                    <label className="text-xs text-gray-600 capitalize">
                      {key === 'roc' ? 'RoC (mm)' : key.replace(/([A-Z])/g, ' $1')}
                    </label>
                    <input
                      type="number"
                      value={value}
                      onChange={(e) => updateProperty(selectedComponent.id, key, e.target.value)}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                      step="0.01"
                    />
                  </div>
                ))}
              </div>
              
              <button
                onClick={() => deleteComponent(selectedComponent.id)}
                className="w-full mt-4 flex items-center justify-center gap-2 px-3 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition"
              >
                <Trash2 size={14} />
                Delete
              </button>
            </div>
          ) : (
            <p className="text-sm text-gray-400 text-center mt-8">
              Select a component to edit properties
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default OpticalDesigner;