/**
 * jsPDF Extensions
 * ================
 * 
 * Adds missing methods to jsPDF for premium PDF generation:
 * - setGlobalAlpha: For transparency effects (shadows, overlays)
 * - arc: For drawing circular arcs (progress indicators, decorative elements)
 * 
 * This file must be imported AFTER jsPDF but BEFORE using these methods.
 */

import { jsPDF } from 'jspdf';

// Add setGlobalAlpha support for transparency effects
(jsPDF as any).API.setGlobalAlpha = function(alpha: number) {
  if (alpha >= 0 && alpha <= 1) {
    // Store the alpha value for use in drawing operations
    this.internal.globalAlpha = alpha;
    
    // Apply alpha to subsequent drawing operations
    if (alpha < 1) {
      // Set the graphics state with transparency
      this.internal.write(`${alpha} gs`);
    }
  }
  return this;
};

// Add arc method for drawing circular arcs
(jsPDF as any).API.arc = function(
  x: number, 
  y: number, 
  radius: number, 
  startAngle: number, 
  endAngle: number, 
  counterclockwise?: boolean, 
  style?: string
) {
  // Convert angles from degrees to radians
  const start = startAngle * Math.PI / 180;
  const end = endAngle * Math.PI / 180;
  
  // Handle full circle case
  if (Math.abs(endAngle - startAngle) >= 360) {
    this.circle(x, y, radius, style || 'S');
    return this;
  }
  
  // Draw using lines to approximate the arc
  const steps = Math.max(30, Math.ceil(Math.abs(end - start) * radius / 2)); // More steps for larger arcs
  const angleStep = (end - start) / steps;
  
  // Save current line width
  const currentLineWidth = this.internal.getLineWidth();
  this.setLineWidth(currentLineWidth);
  
  // Build the path
  const path: string[] = [];
  
  for (let i = 0; i <= steps; i++) {
    const angle = start + (i * angleStep);
    const px = x + radius * Math.cos(angle);
    const py = y + radius * Math.sin(angle);
    
    if (i === 0) {
      // Move to the first point
      path.push(`${this.internal.f2(px)} ${this.internal.f2(py)} m`);
    } else {
      // Line to subsequent points
      path.push(`${this.internal.f2(px)} ${this.internal.f2(py)} l`);
    }
  }
  
  // Apply the style
  if (style === 'F') {
    // Fill - close the path and fill
    path.push('h f');
  } else if (style === 'FD' || style === 'DF') {
    // Fill and stroke
    path.push('h B');
  } else {
    // Default to stroke
    path.push('S');
  }
  
  // Write the path to the PDF
  this.internal.write(path.join(' '));
  
  return this;
};

// Ensure globalAlpha is reset when creating a new page
const originalAddPage = (jsPDF as any).API.addPage;
(jsPDF as any).API.addPage = function(...args: any[]) {
  // Reset globalAlpha when adding a new page
  if (this.internal.globalAlpha && this.internal.globalAlpha !== 1) {
    this.setGlobalAlpha(1);
  }
  return originalAddPage.apply(this, args);
};

// Helper method to convert from jsPDF coordinates to PDF coordinates
(jsPDF as any).API.internal.f2 = function(num: number) {
  return (num).toFixed(2);
};

// Export to ensure the extensions are loaded
export default {};