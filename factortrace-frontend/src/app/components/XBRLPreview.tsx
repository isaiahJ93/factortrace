'use client';

import { useState, useEffect } from 'react';
import { FileCode, Copy, Download, CheckCircle } from 'lucide-react';

export function XBRLPreview({ voucherData }: { voucherData: any }) {
  const [xbrlContent, setXbrlContent] = useState('');
  const [copied, setCopied] = useState(false);

  // Generate XBRL preview
  useEffect(() => {
    const generateXBRL = () => {
      const xbrl = `<?xml version="1.0" encoding="UTF-8"?>
<xbrl xmlns="http://www.xbrl.org/2003/instance"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xmlns:esrs="http://xbrl.org/esrs/2024">
  
  <context id="c1">
    <entity>
      <identifier scheme="http://www.lei-identifier.org">${voucherData.lei || 'XXXXXXXXXXXXXXXXXXXX'}</identifier>
    </entity>
    <period>
      <instant>${new Date().toISOString().split('T')[0]}</instant>
    </period>
  </context>
  
  <!-- Emissions Data -->
  <esrs:GHGEmissionsScope1 contextRef="c1" unitRef="tCO2e" decimals="2">
    ${voucherData.scope1?.value || '0.00'}
  </esrs:GHGEmissionsScope1>
  
  <esrs:GHGEmissionsScope2 contextRef="c1" unitRef="tCO2e" decimals="2">
    ${voucherData.scope2?.value || '0.00'}
  </esrs:GHGEmissionsScope2>
  
  <esrs:GHGEmissionsScope3 contextRef="c1" unitRef="tCO2e" decimals="2">
    ${voucherData.scope3?.value || '0.00'}
  </esrs:GHGEmissionsScope3>
  
  <!-- Data Quality -->
  <esrs:DataQualityScore contextRef="c1" decimals="0">
    ${Math.round((voucherData.scope1?.quality + voucherData.scope2?.quality + voucherData.scope3?.quality) / 3) || 0}
  </esrs:DataQualityScore>
  
  <!-- Verification Status -->
  <esrs:VerificationLevel contextRef="c1">
    ${voucherData.verificationLevel || 'none'}
  </esrs:VerificationLevel>
</xbrl>`;
      
      setXbrlContent(xbrl);
    };

    generateXBRL();
  }, [voucherData]);

  const handleCopy = () => {
    navigator.clipboard.writeText(xbrlContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([xbrlContent], { type: 'application/xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `emission-voucher-${Date.now()}.xbrl`;
    a.click();
  };

  return (
    <div className="bg-gray-900 rounded-lg overflow-hidden">
      <div className="bg-gray-800 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileCode className="w-4 h-4 text-gray-400" />
          <span className="text-sm font-medium text-gray-300">XBRL Preview</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="p-1.5 hover:bg-gray-700 rounded transition-colors"
          >
            {copied ? (
              <CheckCircle className="w-4 h-4 text-emerald-400" />
            ) : (
              <Copy className="w-4 h-4 text-gray-400" />
            )}
          </button>
          <button
            onClick={handleDownload}
            className="p-1.5 hover:bg-gray-700 rounded transition-colors"
          >
            <Download className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      </div>
      <div className="p-4 overflow-x-auto">
        <pre className="text-sm text-gray-300 font-mono">
          <code dangerouslySetInnerHTML={{ 
            __html: xbrlContent
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;')
              .replace(/(&lt;\/?)(\w+)/g, '$1<span class="text-blue-400">$2</span>')
              .replace(/([\w-]+)=/g, '<span class="text-purple-400">$1</span>=')
              .replace(/"([^"]*)"/g, '"<span class="text-emerald-400">$1</span>"')
          }} />
        </pre>
      </div>
    </div>
  );
}
