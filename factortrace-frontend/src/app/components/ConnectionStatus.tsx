// src/app/components/ConnectionStatus.tsx
'use client';

import { useEffect, useState } from 'react';
import { Wifi, WifiOff, Database, Shield, Activity, AlertCircle, CheckCircle } from 'lucide-react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface BackendFeatures {
  xbrl?: boolean;
  cbam_compliance?: boolean;
  uncertainty_analysis?: boolean;
  [key: string]: any;
}

interface ConnectionInfo {
  status: 'checking' | 'connected' | 'disconnected' | 'error';
  message?: string;
  version?: string;
  features?: BackendFeatures;
}

export const ConnectionStatus = ({ 
  variant = 'detailed', // 'simple' | 'detailed'
  position = 'bottom-right' // 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'
}: {
  variant?: 'simple' | 'detailed';
  position?: string;
}) => {
  const [isOnline, setIsOnline] = useState(true);
  const [connectionInfo, setConnectionInfo] = useState<ConnectionInfo>({
    status: 'checking'
  });
  const [lastChecked, setLastChecked] = useState(new Date());
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    // Check browser online status
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    
    setIsOnline(navigator.onLine);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    // Check backend connection
    checkBackendConnection();
    
    // Check every 30 seconds
    const interval = setInterval(checkBackendConnection, 30000);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(interval);
    };
  }, []);

  const checkBackendConnection = async () => {
    if (!navigator.onLine) {
      setConnectionInfo({ status: 'disconnected', message: 'No internet connection' });
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/`, {
        method: 'GET',
        mode: 'cors',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setConnectionInfo({
          status: 'connected',
          message: data.message || 'API Connected',
          version: data.version,
          features: data.features || {}
        });
      } else {
        setConnectionInfo({
          status: 'error',
          message: `API Error (${response.status})`
        });
      }
      setLastChecked(new Date());
    } catch (error) {
      setConnectionInfo({
        status: 'disconnected',
        message: 'Cannot reach API server'
      });
    }
  };

  const getPositionClasses = () => {
    const positions: Record<string, string> = {
      'bottom-right': 'bottom-4 right-4',
      'bottom-left': 'bottom-4 left-4',
      'top-right': 'top-20 right-4',
      'top-left': 'top-20 left-4'
    };
    return positions[position] || positions['bottom-right'];
  };

  const getStatusColor = () => {
    if (!isOnline) return { bg: 'bg-red-50', text: 'text-red-700', icon: 'text-red-600' };
    
    switch (connectionInfo.status) {
      case 'connected':
        return { bg: 'bg-emerald-50', text: 'text-emerald-700', icon: 'text-emerald-600' };
      case 'checking':
        return { bg: 'bg-yellow-50', text: 'text-yellow-700', icon: 'text-yellow-600' };
      case 'error':
        return { bg: 'bg-orange-50', text: 'text-orange-700', icon: 'text-orange-600' };
      default:
        return { bg: 'bg-red-50', text: 'text-red-700', icon: 'text-red-600' };
    }
  };

  const getStatusIcon = () => {
    if (!isOnline) return <WifiOff className="w-4 h-4" />;
    
    switch (connectionInfo.status) {
      case 'connected':
        return <Wifi className="w-4 h-4" />;
      case 'checking':
        return <Wifi className="w-4 h-4 animate-pulse" />;
      case 'error':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <WifiOff className="w-4 h-4" />;
    }
  };

  const getStatusText = () => {
    if (!isOnline) return 'Offline';
    
    switch (connectionInfo.status) {
      case 'connected':
        return 'API Connected';
      case 'checking':
        return 'Connecting...';
      case 'error':
        return 'API Error';
      default:
        return 'API Disconnected';
    }
  };

  const colors = getStatusColor();

  // Simple variant
  if (variant === 'simple') {
    return (
      <div className={`fixed ${getPositionClasses()} z-50`}>
        <div className={`px-4 py-2 rounded-lg shadow-lg flex items-center gap-2 transition-all ${colors.bg} ${colors.text}`}>
          <span className={colors.icon}>{getStatusIcon()}</span>
          <span className="text-sm font-medium">{getStatusText()}</span>
        </div>
      </div>
    );
  }

  // Detailed variant
  return (
    <div className={`fixed ${getPositionClasses()} z-50`}>
      <div 
        className="bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden cursor-pointer"
        onClick={() => setShowDetails(!showDetails)}
      >
        <div className={`px-4 py-3 flex items-center gap-3 ${colors.bg}`}>
          <div className="relative">
            <span className={colors.icon}>{getStatusIcon()}</span>
            {connectionInfo.status === 'checking' && (
              <div className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-yellow-500 animate-ping" />
            )}
          </div>
          
          <div className="flex-1">
            <p className={`text-sm font-medium ${colors.text}`}>{getStatusText()}</p>
            {connectionInfo.message && (
              <p className="text-xs text-gray-600 mt-0.5">{connectionInfo.message}</p>
            )}
          </div>
          
          {connectionInfo.status === 'connected' && (
            <CheckCircle className={`w-4 h-4 ${colors.icon}`} />
          )}
        </div>
        
        {/* Expandable details section */}
        {showDetails && connectionInfo.status === 'connected' && (
          <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
            {connectionInfo.version && (
              <p className="text-xs text-gray-600 mb-2">
                Version: {connectionInfo.version}
              </p>
            )}
            
            {connectionInfo.features && Object.keys(connectionInfo.features).length > 0 && (
              <div className="space-y-1">
                <p className="text-xs font-medium text-gray-700 mb-1">Active Features:</p>
                <div className="flex flex-wrap gap-2">
                  {connectionInfo.features.xbrl && (
                    <div className="flex items-center gap-1 text-xs text-emerald-600 bg-emerald-50 px-2 py-1 rounded">
                      <Database className="w-3 h-3" />
                      <span>XBRL</span>
                    </div>
                  )}
                  {connectionInfo.features.cbam_compliance && (
                    <div className="flex items-center gap-1 text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                      <Shield className="w-3 h-3" />
                      <span>CBAM</span>
                    </div>
                  )}
                  {connectionInfo.features.uncertainty_analysis && (
                    <div className="flex items-center gap-1 text-xs text-purple-600 bg-purple-50 px-2 py-1 rounded">
                      <Activity className="w-3 h-3" />
                      <span>Monte Carlo</span>
                    </div>
                  )}
                </div>
              </div>
            )}
            
            <p className="text-xs text-gray-500 mt-2">
              Last checked: {lastChecked.toLocaleTimeString()}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

// Export with default props for backward compatibility
export default ConnectionStatus;