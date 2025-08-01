'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  ArrowLeft, Plus, Download, Filter, Search, 
  Calendar, MoreVertical, Edit, Trash2, Zap,
  ChevronUp, ChevronDown, FileText, AlertCircle, 
  CheckCircle, BarChart3
} from 'lucide-react';
// import { EvidenceUpload } from '../../components/EvidenceUpload';
import { apiClient } from '../../../lib/api-client';
import { EmissionData, QualityScores } from '../../types/emissions';

export default function EmissionsListPage() {
  const router = useRouter();
  const [emissions, setEmissions] = useState<EmissionData[]>([]);
  const [filteredEmissions, setFilteredEmissions] = useState<EmissionData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [scopeFilter, setScopeFilter] = useState<number | null>(null);
  const [sortBy, setSortBy] = useState<'date' | 'amount'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [error, setError] = useState<string | null>(null);

  // Fetch emissions data
  const fetchEmissions = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient.getEmissions();
      setEmissions(data);
      setFilteredEmissions(data);
    } catch (error) {
      console.error('Error fetching emissions:', error);
      setError('Failed to load emissions data');
      // Use mock data for development
      const mockData: EmissionData[] = [
        {
          id: 1,
          date: '2024-04-15',
          emission_factor_id: 1,
          activity_data: 1000,
          emission_amount: 2.32,
          scope: 1,
          category: 'stationary_combustion',
          activity_type: 'Natural Gas Combustion',
          activity_unit: 'kWh',
          evidence_type: 'invoice',
          document_url: null,
          quality_score: 85,
          description: 'Monthly natural gas usage',
          location: 'Main Office'
        },
        {
          id: 2,
          date: '2024-04-14',
          emission_factor_id: 2,
          activity_data: 5000,
          emission_amount: 2.175,
          scope: 2,
          category: 'purchased_electricity',
          activity_type: 'Grid Electricity',
          activity_unit: 'kWh',
          evidence_type: null,
          document_url: null,
          quality_score: 50,
          description: 'Data center electricity consumption',
          location: 'Data Center'
        },
        {
          id: 3,
          date: '2024-04-13',
          emission_factor_id: 3,
          activity_data: 15000,
          emission_amount: 3.345,
          scope: 3,
          category: 'business_travel',
          activity_type: 'Air Travel',
          activity_unit: 'km',
          evidence_type: 'receipt',
          document_url: '/uploads/receipt123.pdf',
          quality_score: 100,
          description: 'International business trip',
          location: null
        },
      ];
      setEmissions(mockData);
      setFilteredEmissions(mockData);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEmissions();
  }, []);

  // Filter and sort emissions
  useEffect(() => {
    let filtered = [...emissions];

    // Apply scope filter
    if (scopeFilter !== null) {
      filtered = filtered.filter(e => e.scope === scopeFilter);
    }

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(e => 
        e.category?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        e.location?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        e.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        e.activity_type?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      if (sortBy === 'date') {
        const dateA = new Date(a.date).getTime();
        const dateB = new Date(b.date).getTime();
        return sortOrder === 'asc' ? dateA - dateB : dateB - dateA;
      } else {
        return sortOrder === 'asc' ? 
          (a.emission_amount || 0) - (b.emission_amount || 0) : 
          (b.emission_amount || 0) - (a.emission_amount || 0);
      }
    });

    setFilteredEmissions(filtered);
  }, [emissions, scopeFilter, searchTerm, sortBy, sortOrder]);

  const toggleSort = (field: 'date' | 'amount') => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this emission entry?')) {
      try {
        await apiClient.deleteEmission(id);
        setEmissions(emissions.filter(e => e.id !== id));
      } catch (error) {
        console.error('Error deleting emission:', error);
        alert('Failed to delete emission entry');
      }
    }
  };

  const handleScoreUpdate = (emissionId: number, scores: QualityScores) => {
    setEmissions(prev => 
      prev.map(emission => 
        emission.id === emissionId 
          ? { ...emission, quality_score: scores.total_score, evidence_type: scores.evidence_type }
          : emission
      )
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getCategoryLabel = (category: string) => {
    return category?.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ') || 'Unknown';
  };

  const getQualityBadge = (score?: number, evidenceType?: string) => {
    if (!score) return null;

    const color = score >= 90 ? 'bg-green-100 text-green-800' :
                  score >= 70 ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800';

    const icon = score >= 90 ? <CheckCircle className="w-4 h-4" /> :
                 <AlertCircle className="w-4 h-4" />;

    return (
      <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${color}`}>
        {icon}
        {score}%
        {evidenceType && <span className="text-xs opacity-75">({evidenceType})</span>}
      </div>
    );
  };

  const totalEmissions = (filteredEmissions || []).reduce((sum, e) => sum + (e.emission_amount || 0), 0);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => router.push('/dashboard')}
                className="mr-4 p-2 rounded-md hover:bg-gray-100"
              >
                <ArrowLeft className="w-5 h-5 text-gray-600" />
              </button>
              <div className="flex items-center">
                <Zap className="w-6 h-6 text-emerald-500 mr-2" />
                <h1 className="text-xl font-semibold text-gray-900">Emissions</h1>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => router.push('/emissions/quality-export')}
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <BarChart3 className="w-4 h-4 mr-1.5" />
                Quality Report
              </button>
              <button className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                <Download className="w-4 h-4 mr-1.5" />
                Export
              </button>
              <button
                onClick={() => router.push('/emissions/new')}
                className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-emerald-600 hover:bg-emerald-700"
              >
                <Plus className="w-4 h-4 mr-1.5" />
                New Entry
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filters and Search */}
        <div className="bg-white shadow rounded-lg p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search emissions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            {/* Scope Filter */}
            <div>
              <select
                value={scopeFilter || ''}
                onChange={(e) => setScopeFilter(e.target.value ? parseInt(e.target.value) : null)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="">All Scopes</option>
                <option value="1">Scope 1</option>
                <option value="2">Scope 2</option>
                <option value="3">Scope 3</option>
              </select>
            </div>

            {/* Sort Options */}
            <div className="flex space-x-2">
              <button
                onClick={() => toggleSort('date')}
                className={`flex-1 px-3 py-2 border rounded-md text-sm font-medium ${
                  sortBy === 'date' 
                    ? 'border-emerald-500 bg-emerald-50 text-emerald-700' 
                    : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                Date {sortBy === 'date' && (sortOrder === 'asc' ? <ChevronUp className="inline w-4 h-4" /> : <ChevronDown className="inline w-4 h-4" />)}
              </button>
              <button
                onClick={() => toggleSort('amount')}
                className={`flex-1 px-3 py-2 border rounded-md text-sm font-medium ${
                  sortBy === 'amount' 
                    ? 'border-emerald-500 bg-emerald-50 text-emerald-700' 
                    : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                Amount {sortBy === 'amount' && (sortOrder === 'asc' ? <ChevronUp className="inline w-4 h-4" /> : <ChevronDown className="inline w-4 h-4" />)}
              </button>
            </div>

            {/* Summary */}
            <div className="text-right">
              <div className="text-sm text-gray-500">Total Emissions</div>
              <div className="text-lg font-semibold text-gray-900">{totalEmissions.toFixed(2)} tCO₂e</div>
            </div>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center">
            <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
            <span className="text-red-800">{error}</span>
          </div>
        )}

        {/* Emissions List */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto"></div>
            <p className="text-gray-500 mt-4">Loading emissions...</p>
          </div>
        ) : filteredEmissions.length === 0 ? (
          <div className="bg-white shadow rounded-lg p-12 text-center">
            <Zap className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No emissions found</h3>
            <p className="text-gray-500 mb-6">
              {searchTerm || scopeFilter ? 'Try adjusting your filters' : 'Get started by creating your first emission entry'}
            </p>
            <button
              onClick={() => router.push('/emissions/new')}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-emerald-600 hover:bg-emerald-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create First Entry
            </button>
          </div>
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
              {filteredEmissions.map((emission) => (
                <li key={emission.id}>
                  <div className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center flex-1">
                        <div className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center font-semibold text-white
                          ${emission.scope === 1 ? 'bg-blue-500' : emission.scope === 2 ? 'bg-purple-500' : 'bg-pink-500'}`}>
                          S{emission.scope}
                        </div>
                        <div className="ml-4 flex-1">
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                {getCategoryLabel(emission.category || '')}
                              </div>
                              <div className="text-sm text-gray-500">
                                {emission.activity_data} {emission.activity_unit} × Factor #{emission.emission_factor_id} = {emission.emission_amount?.toFixed(2) || '0.00'} tCO₂e
                              </div>
                              <div className="flex items-center mt-1 text-xs text-gray-400 space-x-3">
                                <span>{formatDate(emission.date)}</span>
                                {emission.location && <span>• {emission.location}</span>}
                                {emission.description && <span>• {emission.description}</span>}
                              </div>
                            </div>
                            <div className="ml-4 flex items-center space-x-4">
                              {/* Quality Score Badge */}
                              {getQualityBadge(emission.quality_score, emission.evidence_type)}
                              
                              {/* Evidence Link */}
                              {emission.document_url ? (
                                <a
                                  href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${emission.document_url}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800"
                                >
                                  <FileText className="w-4 h-4" />
                                  <span className="text-sm">View</span>
                                </a>
                              ) : (
                                <span className="text-gray-400 text-sm">No evidence</span>
                              )}
                              
                              {/* Evidence Upload Button */}
                              <EvidenceUpload
                                emissionId={emission.id}
                                factorName={`${getCategoryLabel(emission.category || '')} - ${emission.activity_type || 'Emission'}`}
                                currentScore={emission.quality_score}
                                currentEvidenceType={emission.evidence_type}
                                onScoreUpdate={(scores) => handleScoreUpdate(emission.id, scores)}
                                onUploadComplete={fetchEmissions}
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 ml-4">
                        <div className="text-right mr-4">
                          <div className="text-lg font-semibold text-gray-900">
                            {emission.emission_amount?.toFixed(2) || '0.00'}
                          </div>
                          <div className="text-xs text-gray-500">tCO₂e</div>
                        </div>
                        <div className="relative group">
                          <button className="p-2 rounded-md hover:bg-gray-100">
                            <MoreVertical className="w-5 h-5 text-gray-400" />
                          </button>
                          <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                            <button
                              onClick={() => router.push(`/emissions/${emission.id}/edit`)}
                              className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                            >
                              <Edit className="w-4 h-4 mr-2" />
                              Edit
                            </button>
                            <button
                              onClick={() => handleDelete(emission.id)}
                              className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-gray-100 flex items-center"
                            >
                              <Trash2 className="w-4 h-4 mr-2" />
                              Delete
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </main>
    </div>
  );
}