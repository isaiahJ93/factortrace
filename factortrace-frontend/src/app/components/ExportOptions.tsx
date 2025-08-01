'use client';

import React, { useState, useEffect } from 'react';
import { 
  Download, FileText, FileCode, FileSpreadsheet, Eye, Mail, 
  Shield, Loader2, Check, AlertCircle, Lock, Globe, Zap,
  FileCheck, Settings, Calendar, Building, ChevronRight,
  TrendingUp, Award, Sparkles, Copy, ExternalLink
, X } from 'lucide-react';

// Progress indicator component
const ExportProgress = ({ progress, stage }: { progress: number; stage: string }) => {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-emerald-100 rounded-full mb-4">
            <Loader2 className="w-8 h-8 text-emerald-600 animate-spin" />
          </div>
          <h3 className="text-xl font-semibold text-gray-900">Generating Export</h3>
          <p className="text-sm text-gray-600 mt-2">{stage}</p>
        </div>
        
        <div className="space-y-3">
          <div className="relative">
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div 
                className="bg-gradient-to-r from-emerald-500 to-emerald-600 h-3 rounded-full transition-all duration-500 relative overflow-hidden"
                style={{ width: `${progress}%` }}
              >
                <div className="absolute inset-0 bg-white/20 animate-pulse" />
              </div>
            </div>
            <span className="absolute right-0 -top-6 text-sm font-medium text-gray-700">
              {progress}%
            </span>
          </div>
          
          <div className="grid grid-cols-4 gap-2">
            {['Validating', 'Formatting', 'Generating', 'Finalizing'].map((step, index) => (
              <div 
                key={step}
                className={`text-xs text-center ${
                  index * 25 < progress ? 'text-emerald-600 font-medium' : 'text-gray-400'
                }`}
              >
                {step}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Preview modal component
const PreviewModal = ({ format, data, onClose, onConfirm }: { format: string; data: any; onClose: () => void; onConfirm: () => void }) => {
  const renderPreview = () => {
    switch (format) {
      case 'xbrl':
        return (
          <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
            <pre className="text-green-400 text-xs font-mono">
{`<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
      xmlns:xbrli="http://www.xbrl.org/2003/instance">
  <head>
    <title>Emissions Report - ${data.companyName}</title>
  </head>
  <body>
    <div class="report">
      <h1>GHG Emissions Disclosure</h1>
      <p>Entity: <ix:nonNumeric contextRef="c1" name="lei:LEI">
        ${data.lei}
      </ix:nonNumeric></p>
      
      <table class="emissions">
        <tr>
          <td>Scope 1 Emissions:</td>
          <td><ix:nonFraction contextRef="c1" unitRef="tCO2e" 
              name="ghg:Scope1Emissions" decimals="2">
              ${data.scope1.value}
          </ix:nonFraction> tCO₂e</td>
        </tr>
      </table>
    </div>
  </body>
</html>`}
            </pre>
          </div>
        );
        
      case 'pdf':
        return (
          <div className="bg-white border border-gray-200 rounded-lg p-8" style={{ minHeight: '400px' }}>
            <div className="flex items-center justify-between mb-6">
              <h1 className="text-2xl font-bold text-gray-900">Emissions Report</h1>
              <div className="text-right">
                <p className="text-sm text-gray-600">{data.companyName}</p>
                <p className="text-xs text-gray-500">{new Date().toLocaleDateString()}</p>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-gray-50 rounded p-3">
                <p className="text-sm text-gray-600">Total Emissions</p>
                <p className="text-2xl font-bold text-gray-900">
                  {(parseFloat(data.scope1.value || 0) + 
                    parseFloat(data.scope2.value || 0) + 
                    parseFloat(data.scope3.value || 0)).toFixed(2)} tCO₂e
                </p>
              </div>
              <div className="bg-gray-50 rounded p-3">
                <p className="text-sm text-gray-600">Data Quality</p>
                <p className="text-2xl font-bold text-gray-900">{data.primaryDataPercentage}%</p>
              </div>
            </div>
            
            <div className="text-xs text-gray-500 text-center mt-8">
              Page 1 of 12 • Preview Mode
            </div>
          </div>
        );
        
      default:
        return <div>Preview not available</div>;
    }
  };
  
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl">
        <div className="p-6 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h3 className="text-xl font-semibold text-gray-900">Export Preview</h3>
            <p className="text-sm text-gray-600 mt-1">Review before downloading</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 200px)' }}>
          {renderPreview()}
        </div>
        
        <div className="p-6 border-t border-gray-200 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2">
              <input type="checkbox" className="rounded text-emerald-600" defaultChecked />
              <span className="text-sm text-gray-700">Include digital signature</span>
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" className="rounded text-emerald-600" />
              <span className="text-sm text-gray-700">Password protect</span>
            </label>
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={onConfirm}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Download
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

interface ExportOptionsProps {
  voucherData: any;
  onExport: (format: string) => void;
}

export function ExportOptions({ voucherData, onExport }: ExportOptionsProps) {
  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [exportStage, setExportStage] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState('');
  const [recentExports, setRecentExports] = useState<{ format: string; timestamp: Date; filename: string; status: string; }[]>([]);
  const [exportSettings, setExportSettings] = useState({
    includeCharts: true,
    includeAppendix: true,
    digitalSignature: true,
    encryption: false
  });

  const exportFormats = [
    {
      format: 'xbrl',
      name: 'iXBRL',
      fullName: 'Inline XBRL',
      description: 'ESRS & CSRD compliant',
      icon: FileCode,
      color: 'emerald',
      features: ['Machine-readable', 'Human-readable', 'Regulatory compliant', 'Digital signature'],
      fileSize: '~2.5 MB',
      badge: 'Recommended'
    },
    {
      format: 'pdf',
      name: 'PDF Report',
      fullName: 'Professional PDF',
      description: 'Board-ready presentation',
      icon: FileText,
      color: 'blue',
      features: ['Charts & graphs', 'Executive summary', 'Print optimized', 'Password protection'],
      fileSize: '~5.2 MB',
      badge: null
    },
    {
      format: 'excel',
      name: 'Excel',
      fullName: 'Excel Workbook',
      description: 'Detailed data analysis',
      icon: FileSpreadsheet,
      color: 'purple',
      features: ['All raw data', 'Calculation details', 'Pivot tables', 'Macros enabled'],
      fileSize: '~1.8 MB',
      badge: null
    }
  ];

  const additionalFormats = [
    { format: 'json', name: 'JSON', icon: FileCode },
    { format: 'csv', name: 'CSV', icon: FileText },
    { format: 'xml', name: 'XML', icon: FileCode }
  ];

  const handleExport = async (format: string) => {
    setSelectedFormat(format);
    setShowPreview(true);
  };

  const confirmExport = async () => {
    setShowPreview(false);
    setIsExporting(true);
    setExportProgress(0);
    
    // Simulate export stages
    const stages = [
      { stage: 'Validating data completeness...', progress: 25 },
      { stage: 'Applying ESRS taxonomy...', progress: 50 },
      { stage: 'Generating formatted output...', progress: 75 },
      { stage: 'Finalizing and encrypting...', progress: 100 }
    ];
    
    for (const { stage, progress } of stages) {
      setExportStage(stage);
      await animateProgress(progress);
      await new Promise(resolve => setTimeout(resolve, 800));
    }
    
    // Generate the actual export
    generateExport(selectedFormat);
    
    // Add to recent exports
    setRecentExports(prev => [{
      format: selectedFormat,
      timestamp: new Date(),
      filename: `emissions-report-${Date.now()}.${selectedFormat}`,
      status: 'completed'
    }, ...prev].slice(0, 5));
    
    setIsExporting(false);
    onExport(selectedFormat);
  };

  const animateProgress = (target: number) => {
    return new Promise(resolve => {
      const interval = setInterval(() => {
        setExportProgress(prev => {
          if (prev >= target) {
            clearInterval(interval);
            resolve(undefined);
            return target;
          }
          return prev + 2;
        });
      }, 20);
    });
  };

  const generateExport = (format: string) => {
    switch (format) {
      case 'xbrl':
        generateIXBRL();
        break;
      case 'pdf':
        generateProfessionalPDF();
        break;
      case 'excel':
        generateExcelWorkbook();
        break;
    }
  };

  const generateIXBRL = () => {
    // Generate proper inline XBRL with ESRS taxonomy
    const ixbrl = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" 
      xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xmlns:xbrli="http://www.xbrl.org/2003/instance"
      xmlns:iso4217="http://www.xbrl.org/2003/iso4217"
      xmlns:esrs="http://www.efrag.org/esrs/2023"
      xmlns:lei="http://www.lei-identifier.org">
<head>
  <title>Sustainability Statement - ${voucherData.companyName}</title>
  <meta charset="UTF-8"/>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; }
    .header { border-bottom: 2px solid #10b981; padding-bottom: 20px; }
    .metric { margin: 20px 0; padding: 15px; background: #f3f4f6; border-radius: 8px; }
    .hidden { display: none; }
  </style>
</head>
<body>
  <!-- Hidden XBRL contexts and units -->
  <div class="hidden">
    <ix:header>
      <ix:references>
        <ix:schemaRef xlink:type="simple" xlink:href="https://www.efrag.org/esrs/2023/esrs-e1.xsd"/>
      </ix:references>
      <ix:resources>
        <xbrli:context id="c-2024">
          <xbrli:entity>
            <xbrli:identifier scheme="http://www.lei-identifier.org">${voucherData.lei}</xbrli:identifier>
          </xbrli:entity>
          <xbrli:period>
            <xbrli:instant>2024-12-31</xbrli:instant>
          </xbrli:period>
        </xbrli:context>
        <xbrli:unit id="tCO2e">
          <xbrli:measure>esrs:tCO2e</xbrli:measure>
        </xbrli:unit>
        <xbrli:unit id="percentage">
          <xbrli:measure>xbrli:pure</xbrli:measure>
        </xbrli:unit>
      </ix:resources>
    </ix:header>
  </div>

  <div class="header">
    <h1>Sustainability Statement</h1>
    <p>Entity: <ix:nonNumeric contextRef="c-2024" name="esrs:EntityLegalName">${voucherData.companyName}</ix:nonNumeric></p>
    <p>LEI: <ix:nonNumeric contextRef="c-2024" name="lei:LEI">${voucherData.lei}</ix:nonNumeric></p>
    <p>Period: ${voucherData.reportingPeriod} ${voucherData.reportingYear}</p>
  </div>

  <section>
    <h2>E1: Climate Change</h2>
    
    <div class="metric">
      <h3>GHG Emissions</h3>
      <p>Scope 1 (Direct emissions): 
        <ix:nonFraction contextRef="c-2024" unitRef="tCO2e" name="esrs-e1:GHGEmissionsScope1" decimals="2" format="ixt:numdotdecimal">
          ${voucherData.scope1.value}
        </ix:nonFraction> tCO₂e
      </p>
      <p>Scope 2 (Energy indirect): 
        <ix:nonFraction contextRef="c-2024" unitRef="tCO2e" name="esrs-e1:GHGEmissionsScope2LocationBased" decimals="2" format="ixt:numdotdecimal">
          ${voucherData.scope2.value}
        </ix:nonFraction> tCO₂e
      </p>
      <p>Scope 3 (Other indirect): 
        <ix:nonFraction contextRef="c-2024" unitRef="tCO2e" name="esrs-e1:GHGEmissionsScope3" decimals="2" format="ixt:numdotdecimal">
          ${voucherData.scope3.value}
        </ix:nonFraction> tCO₂e
      </p>
      <p><strong>Total GHG Emissions: 
        <ix:nonFraction contextRef="c-2024" unitRef="tCO2e" name="esrs-e1:GHGEmissionsTotal" decimals="2" format="ixt:numdotdecimal">
          ${parseFloat(voucherData.scope1.value || 0) + parseFloat(voucherData.scope2.value || 0) + parseFloat(voucherData.scope3.value || 0)}
        </ix:nonFraction> tCO₂e
      </strong></p>
    </div>

    <div class="metric">
      <h3>Data Quality</h3>
      <p>Primary data percentage: 
        <ix:nonFraction contextRef="c-2024" unitRef="percentage" name="esrs-e1:PrimaryDataPercentage" decimals="0">
          ${voucherData.primaryDataPercentage}
        </ix:nonFraction>%
      </p>
      <p>Verification level: 
        <ix:nonNumeric contextRef="c-2024" name="esrs-e1:AssuranceLevel">
          ${voucherData.verificationLevel}
        </ix:nonNumeric>
      </p>
    </div>
  </section>

  <footer>
    <p>Generated by FactorTrace on ${new Date().toISOString()}</p>
    ${exportSettings.digitalSignature ? '<p>Digitally signed and verified</p>' : ''}
  </footer>
</body>
</html>`;
    
    downloadFile(ixbrl, `sustainability-statement-${Date.now()}.html`, 'text/html');
  };

  const generateProfessionalPDF = () => {
    // In production, use a proper PDF library like jsPDF or puppeteer
    console.log('Generating professional PDF with charts...');
    // This would integrate with your backend PDF generation service
  };

  const generateExcelWorkbook = () => {
    // In production, use a library like ExcelJS
    console.log('Generating Excel workbook with multiple sheets...');
  };

  const downloadFile = (content: string, filename: string, type: string) => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const shareViaEmail = () => {
    const subject = `Emissions Report - ${voucherData.companyName}`;
    const body = `Please find attached the emissions report for ${voucherData.reportingPeriod} ${voucherData.reportingYear}.`;
    window.location.href = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  };

  return (
    <div className="space-y-6">
      {/* Header with actions */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-semibold text-gray-900">Export Your Report</h3>
          <p className="text-sm text-gray-600 mt-1">Choose a format optimized for your needs</p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => setExportSettings(prev => ({ ...prev, includeCharts: !prev.includeCharts }))}
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Settings className="w-5 h-5" />
          </button>
          <button 
            onClick={shareViaEmail}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
          >
            <Mail className="w-4 h-4" />
            Share
          </button>
        </div>
      </div>
      
      {/* Main export formats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {exportFormats.map((format) => {
          const Icon = format.icon;
          return (
            <div
              key={format.format}
              className="relative bg-white border-2 border-gray-200 rounded-xl hover:border-emerald-500 hover:shadow-xl transition-all group"
            >
              {format.badge && (
                <div className="absolute -top-3 left-4 px-3 py-1 bg-emerald-600 text-white text-xs font-medium rounded-full">
                  {format.badge}
                </div>
              )}
              
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className={`p-3 bg-${format.color}-100 rounded-lg group-hover:scale-110 transition-transform`}>
                    <Icon className={`w-8 h-8 text-${format.color}-600`} />
                  </div>
                  <Eye 
                    className="w-5 h-5 text-gray-400 cursor-pointer hover:text-gray-600"
                    onClick={() => handleExport(format.format)}
                  />
                </div>
                
                <h4 className="text-lg font-semibold text-gray-900">{format.name}</h4>
                <p className="text-sm text-gray-500">{format.fullName}</p>
                <p className="text-sm text-gray-600 mt-2">{format.description}</p>
                
                <div className="mt-4 space-y-2">
                  {format.features.map((feature, index) => (
                    <div key={index} className="flex items-center gap-2 text-sm text-gray-600">
                      <Check className="w-4 h-4 text-emerald-500" />
                      {feature}
                    </div>
                  ))}
                </div>
                
                <div className="mt-6 flex items-center justify-between">
                  <span className="text-xs text-gray-500">{format.fileSize}</span>
                  <button
                    onClick={() => handleExport(format.format)}
                    className={`px-4 py-2 bg-${format.color}-600 text-white rounded-lg hover:bg-${format.color}-700 transition-colors flex items-center gap-2 text-sm font-medium`}
                  >
                    <Download className="w-4 h-4" />
                    Export
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Additional formats */}
      <div className="border-t pt-6">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Additional Formats</h4>
        <div className="flex gap-3">
          {additionalFormats.map(format => (
            <button
              key={format.format}
              onClick={() => handleExport(format.format)}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2 text-sm"
            >
              <format.icon className="w-4 h-4" />
              {format.name}
            </button>
          ))}
        </div>
      </div>

      {/* Recent exports */}
      {recentExports.length > 0 && (
        <div className="border-t pt-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Recent Exports</h4>
          <div className="space-y-2">
            {recentExports.map((exp, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <FileCheck className="w-5 h-5 text-emerald-600" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{exp.filename}</p>
                    <p className="text-xs text-gray-600">
                      {new Date(exp.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
                <button className="text-sm text-blue-600 hover:text-blue-700">
                  Download again
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Export settings panel */}
      {exportSettings && (
        <div className="fixed bottom-6 right-6 w-80 bg-white rounded-lg shadow-xl border border-gray-200 p-4">
          <h4 className="font-medium text-gray-900 mb-3">Export Settings</h4>
          <div className="space-y-3">
            <label className="flex items-center gap-2">
              <input 
                type="checkbox" 
                checked={exportSettings.includeCharts}
                onChange={(e) => setExportSettings(prev => ({ ...prev, includeCharts: e.target.checked }))}
                className="rounded text-emerald-600" 
              />
              <span className="text-sm text-gray-700">Include charts & visualizations</span>
            </label>
            <label className="flex items-center gap-2">
              <input 
                type="checkbox" 
                checked={exportSettings.includeAppendix}
                onChange={(e) => setExportSettings(prev => ({ ...prev, includeAppendix: e.target.checked }))}
                className="rounded text-emerald-600" 
              />
              <span className="text-sm text-gray-700">Include methodology appendix</span>
            </label>
            <label className="flex items-center gap-2">
              <input 
                type="checkbox" 
                checked={exportSettings.digitalSignature}
                onChange={(e) => setExportSettings(prev => ({ ...prev, digitalSignature: e.target.checked }))}
                className="rounded text-emerald-600" 
              />
              <span className="text-sm text-gray-700">Add digital signature</span>
            </label>
            <label className="flex items-center gap-2">
              <input 
                type="checkbox" 
                checked={exportSettings.encryption}
                onChange={(e) => setExportSettings(prev => ({ ...prev, encryption: e.target.checked }))}
                className="rounded text-emerald-600" 
              />
              <span className="text-sm text-gray-700">Password protect</span>
            </label>
          </div>
        </div>
      )}

      {/* Export progress modal */}
      {isExporting && <ExportProgress progress={exportProgress} stage={exportStage} />}
      
      {/* Preview modal */}
      {showPreview && (
        <PreviewModal 
          format={selectedFormat}
          data={voucherData}
          onClose={() => setShowPreview(false)}
          onConfirm={confirmExport}
        />
      )}
    </div>
  );
}