'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Home, FileText, BarChart3, Settings, LogOut, Shield, Database, List, Plus } from 'lucide-react';

export const Navigation = () => {
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem('voucherSession');
    localStorage.removeItem('companyAccess');
    router.push('/login');
  };

  const navItems = [
    { icon: Home, label: 'Dashboard', path: '/dashboard' },
    { icon: List, label: 'Emissions', path: '/emissions' },
    { icon: Plus, label: 'Create Entry', path: '/emissions/create' },
    { icon: BarChart3, label: 'Reports', path: '/reports' },
    { icon: Settings, label: 'Settings', path: '/settings' }
  ];

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-emerald-600" />
            <span className="text-xl font-bold text-gray-900">FactorTrace</span>
          </div>
          
          <div className="flex gap-4">
            {navItems.map((item) => (
              <button
                key={item.label}
                onClick={() => router.push(item.path)}
                className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 hover:text-emerald-600 hover:bg-gray-50 rounded-lg transition-colors"
              >
                <item.icon className="w-4 h-4" />
                {item.label}
              </button>
            ))}
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Database className="w-4 h-4 text-emerald-600" />
            <span>XBRL/iXBRL Ready</span>
          </div>
          
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
};