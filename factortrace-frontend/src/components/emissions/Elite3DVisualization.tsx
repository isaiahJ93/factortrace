import React, { useRef, useState, useEffect } from 'react';
import * as THREE from 'three';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Text, Box, Sphere } from '@react-three/drei';

// Monte Carlo 3D Particle System
function MonteCarloParticles({ results }) {
  const particlesRef = useRef();
  const [particles] = useState(() => {
    const temp = [];
    const count = 1000;
    
    if (!results?.uncertainty_analysis) return temp;
    
    const { mean, std_dev } = results.uncertainty_analysis;
    
    for (let i = 0; i < count; i++) {
      // Generate particles following normal distribution
      const value = mean + (Math.random() - 0.5) * 2 * std_dev * 3;
      const normalizedValue = (value - mean) / std_dev;
      
      temp.push({
        position: [
          (Math.random() - 0.5) * 10,
          normalizedValue * 2,
          (Math.random() - 0.5) * 10
        ],
        color: normalizedValue > 0 ? '#ef4444' : '#10b981',
        scale: Math.random() * 0.05 + 0.02
      });
    }
    return temp;
  });

  useFrame((state) => {
    if (particlesRef.current) {
      particlesRef.current.rotation.y = state.clock.elapsedTime * 0.1;
    }
  });

  return (
    <group ref={particlesRef}>
      {particles.map((particle, i) => (
        <Sphere key={i} position={particle.position} args={[particle.scale, 8, 8]}>
          <meshBasicMaterial color={particle.color} transparent opacity={0.6} />
        </Sphere>
      ))}
    </group>
  );
}

// 3D Scope Visualization
function ScopeVisualization({ scopeData }) {
  const groupRef = useRef();
  
  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = state.clock.elapsedTime * 0.2;
    }
  });

  const scopeColors = {
    'Scope 1': '#6366f1',
    'Scope 2': '#8b5cf6',
    'Scope 3': '#ec4899'
  };

  return (
    <group ref={groupRef}>
      {scopeData.map((scope, index) => {
        const angle = (index / scopeData.length) * Math.PI * 2;
        const radius = 2;
        const height = scope.value / 5;
        
        return (
          <group key={scope.name} position={[Math.cos(angle) * radius, 0, Math.sin(angle) * radius]}>
            <Box args={[0.8, height, 0.8]} position={[0, height / 2, 0]}>
              <meshStandardMaterial color={scopeColors[scope.name]} metalness={0.6} roughness={0.2} />
            </Box>
            <Text
              position={[0, height + 0.5, 0]}
              fontSize={0.3}
              color="white"
              anchorX="center"
              anchorY="middle"
            >
              {scope.name}
              {'\n'}
              {scope.value.toFixed(1)} tCO2e
            </Text>
          </group>
        );
      })}
    </group>
  );
}

// Main 3D Scene
function Scene({ results, scopeData }) {
  return (
    <>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} />
      <pointLight position={[-10, -10, -10]} color="#8b5cf6" intensity={0.5} />
      
      {results && <MonteCarloParticles results={results} />}
      {scopeData.length > 0 && <ScopeVisualization scopeData={scopeData} />}
      
      <OrbitControls enableZoom={true} enablePan={true} enableRotate={true} />
    </>
  );
}

// Enhanced Dashboard with 3D
export default function Elite3DVisualization({ results }) {
  const getScopeData = () => {
    if (!results?.summary) return [];
    return [
      { name: 'Scope 1', value: results.summary.scope1_emissions / 1000 },
      { name: 'Scope 2', value: results.summary.scope2_location_based / 1000 },
      { name: 'Scope 3', value: results.summary.scope3_emissions / 1000 }
    ];
  };

  return (
    <div className="bg-gray-800/50 backdrop-blur rounded-2xl p-6 border border-gray-700 h-96">
      <h3 className="text-xl font-semibold mb-4 text-white">3D Monte Carlo Visualization</h3>
      <Canvas camera={{ position: [0, 5, 10], fov: 50 }}>
        <Scene results={results} scopeData={getScopeData()} />
      </Canvas>
      <div className="mt-4 text-sm text-gray-400 text-center">
        <p>🟢 Below Mean | 🔴 Above Mean | Drag to rotate</p>
      </div>
    </div>
  );
}

// Animated Uncertainty Range Component
export function UncertaintyWave({ value, lower, upper }) {
  const [animatedValue, setAnimatedValue] = useState(value);
  
  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate uncertainty with smooth animation
      const range = upper - lower;
      const randomValue = lower + Math.random() * range;
      setAnimatedValue(randomValue);
    }, 2000);
    
    return () => clearInterval(interval);
  }, [value, lower, upper]);

  const percentage = ((animatedValue - lower) / (upper - lower)) * 100;
  
  return (
    <div className="relative h-20 bg-gray-700/30 rounded-lg overflow-hidden">
      <div className="absolute inset-0 flex items-center px-4">
        <div className="w-full bg-gray-600 h-2 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-green-400 to-blue-500 transition-all duration-1000 ease-in-out"
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
      <div className="absolute inset-0 flex items-center justify-between px-4 text-xs text-gray-400">
        <span>{(lower/1000).toFixed(1)}</span>
        <span className="text-white font-bold text-base">{(animatedValue/1000).toFixed(2)} tCO2e</span>
        <span>{(upper/1000).toFixed(1)}</span>
      </div>
      <svg className="absolute inset-0 w-full h-full opacity-20">
        <defs>
          <pattern id="wave" x="0" y="0" width="100" height="20" patternUnits="userSpaceOnUse">
            <path d="M0,10 Q25,5 50,10 T100,10" stroke="currentColor" fill="none" className="text-blue-400">
              <animate attributeName="d" 
                values="M0,10 Q25,5 50,10 T100,10;M0,10 Q25,15 50,10 T100,10;M0,10 Q25,5 50,10 T100,10"
                dur="3s" repeatCount="indefinite" />
            </path>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#wave)" />
      </svg>
    </div>
  );
}