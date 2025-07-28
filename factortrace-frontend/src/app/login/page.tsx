'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();
  const [voucherCode, setVoucherCode] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [error, setError] = useState('');

  const demoVouchers = [
    { code: 'VT-DEMO1', description: 'Demo Account' },
    { code: 'VT-TECH1', description: 'Tech Sector Demo' },
    { code: 'VT-ACME1', description: 'ACME Corp Demo' },
    { code: 'ELITE-2024', description: 'Elite Access' }
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsValidating(true);

    try {
      // Add logging
      console.log('Starting login process with code:', voucherCode);
      
      // Simulate validation
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Set all required auth tokens
      console.log('Setting auth tokens...');
      localStorage.setItem('voucherSession', voucherCode);
      localStorage.setItem('companyAccess', 'true');
      sessionStorage.setItem('voucherSession', voucherCode);
      
      // Verify tokens were set
      console.log('Tokens set:', {
        localStorage: localStorage.getItem('companyAccess'),
        sessionStorage: sessionStorage.getItem('voucherSession')
      });
      
      // Try redirect
      console.log('Attempting redirect to /dashboard...');
      
      // Use window.location as fallback if router.push doesn't work
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 100);
      
      router.push('/dashboard');
      
    } catch (err) {
      console.error('Login error:', err);
      setError('Invalid voucher code. Please try again.');
    } finally {
      setIsValidating(false);
    }
  };

  const handleDemoClick = (code: string) => {
    setVoucherCode(code);
    setError('');
  };

  // Add a direct access button for testing
  const handleDirectAccess = () => {
    console.log('Direct access clicked');
    localStorage.setItem('voucherSession', 'DIRECT-ACCESS');
    localStorage.setItem('companyAccess', 'true');
    sessionStorage.setItem('voucherSession', 'DIRECT-ACCESS');
    window.location.href = '/dashboard';
  };

  return (
    <>
      <style jsx>{`
        * {
          box-sizing: border-box;
          margin: 0;
          padding: 0;
        }
        
        @keyframes blob {
          0% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
          100% { transform: translate(0px, 0px) scale(1); }
        }
        
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
      
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(to bottom right, #111827, #1f2937, #111827)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1rem',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Background blobs */}
        <div style={{
          position: 'absolute',
          top: '-10rem',
          right: '-10rem',
          width: '20rem',
          height: '20rem',
          backgroundColor: '#10b981',
          borderRadius: '50%',
          mixBlendMode: 'multiply',
          filter: 'blur(60px)',
          opacity: 0.2,
          animation: 'blob 7s infinite'
        }} />
        <div style={{
          position: 'absolute',
          bottom: '-10rem',
          left: '-10rem',
          width: '20rem',
          height: '20rem',
          backgroundColor: '#3b82f6',
          borderRadius: '50%',
          mixBlendMode: 'multiply',
          filter: 'blur(60px)',
          opacity: 0.2,
          animation: 'blob 7s infinite 2s'
        }} />

        <div style={{
          position: 'relative',
          width: '100%',
          maxWidth: '28rem',
          zIndex: 10
        }}>
          {/* Logo and Title */}
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <div style={{
              width: '4rem',
              height: '4rem',
              backgroundColor: '#10b981',
              borderRadius: '50%',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1rem'
            }}>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
              </svg>
            </div>
            <h1 style={{
              fontSize: '2.25rem',
              fontWeight: 'bold',
              color: 'white',
              marginBottom: '0.5rem'
            }}>FactorTrace</h1>
            <p style={{ color: '#9ca3af' }}>Elite Emissions Reporting Portal</p>
          </div>

          {/* Main Card */}
          <div style={{
            backgroundColor: 'rgba(31, 41, 55, 0.5)',
            backdropFilter: 'blur(12px)',
            borderRadius: '1rem',
            padding: '2rem',
            border: '1px solid rgba(55, 65, 81, 0.5)',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
          }}>
            <h2 style={{
              fontSize: '1.5rem',
              fontWeight: '600',
              color: 'white',
              marginBottom: '1.5rem'
            }}>Enter Your Voucher Code</h2>
            
            <p style={{
              color: '#9ca3af',
              marginBottom: '2rem',
              lineHeight: '1.5'
            }}>
              Use the voucher code provided by your sustainability team to access the emissions reporting system.
            </p>

            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{
                  display: 'block',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  color: '#d1d5db',
                  marginBottom: '0.5rem'
                }}>Voucher Code</label>
                
                <div style={{ position: 'relative' }}>
                  <div style={{
                    position: 'absolute',
                    left: '0.75rem',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: '#6b7280'
                  }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                      <path d="M7 11V7a5 5 0 0110 0v4"></path>
                    </svg>
                  </div>
                  
                  <input
                    type="text"
                    value={voucherCode}
                    onChange={(e) => setVoucherCode(e.target.value.toUpperCase())}
                    placeholder="VT-XXXXX or ELITE-2024"
                    required
                    style={{
                      width: '100%',
                      padding: '0.75rem 1rem 0.75rem 2.5rem',
                      backgroundColor: 'rgba(55, 65, 81, 0.5)',
                      border: '1px solid #4b5563',
                      borderRadius: '0.5rem',
                      color: 'white',
                      fontSize: '1rem',
                      outline: 'none',
                      transition: 'all 0.2s'
                    }}
                    onFocus={(e) => {
                      e.target.style.borderColor = '#10b981';
                      e.target.style.boxShadow = '0 0 0 3px rgba(16, 185, 129, 0.1)';
                    }}
                    onBlur={(e) => {
                      e.target.style.borderColor = '#4b5563';
                      e.target.style.boxShadow = 'none';
                    }}
                  />
                </div>
                
                <p style={{
                  marginTop: '0.5rem',
                  fontSize: '0.75rem',
                  color: '#6b7280'
                }}>
                  Format: VT-XXXXX (e.g., VT-DEMO1) or simple codes (e.g., ELITE-2024)
                </p>
              </div>

              {error && (
                <div style={{
                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.5)',
                  borderRadius: '0.5rem',
                  padding: '0.75rem',
                  marginBottom: '1.5rem'
                }}>
                  <p style={{ fontSize: '0.875rem', color: '#f87171' }}>{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={isValidating || !voucherCode}
                style={{
                  width: '100%',
                  backgroundColor: '#10b981',
                  color: 'white',
                  padding: '0.75rem 1rem',
                  borderRadius: '0.5rem',
                  fontWeight: '500',
                  fontSize: '1rem',
                  border: 'none',
                  cursor: isValidating || !voucherCode ? 'not-allowed' : 'pointer',
                  opacity: isValidating || !voucherCode ? 0.5 : 1,
                  transition: 'all 0.2s',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem'
                }}
                onMouseEnter={(e) => {
                  if (!isValidating && voucherCode) {
                    e.currentTarget.style.backgroundColor = '#059669';
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#10b981';
                }}
              >
                {isValidating ? (
                  <>
                    <div style={{
                      width: '1.25rem',
                      height: '1.25rem',
                      border: '2px solid rgba(255, 255, 255, 0.3)',
                      borderTopColor: 'white',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite'
                    }} />
                    Validating...
                  </>
                ) : (
                  <>
                    Access Dashboard
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="5" y1="12" x2="19" y2="12"></line>
                      <polyline points="12 5 19 12 12 19"></polyline>
                    </svg>
                  </>
                )}
              </button>
            </form>

            {/* Features */}
            <div style={{
              marginTop: '2rem',
              paddingTop: '2rem',
              borderTop: '1px solid #374151',
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '1rem',
              textAlign: 'center'
            }}>
              <div>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2" style={{ margin: '0 auto 0.5rem' }}>
                  <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                  <polyline points="9 22 9 12 15 12 15 22"></polyline>
                </svg>
                <p style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Company-wide Access</p>
              </div>
              <div>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2" style={{ margin: '0 auto 0.5rem' }}>
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                </svg>
                <p style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Secure & Compliant</p>
              </div>
              <div>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2" style={{ margin: '0 auto 0.5rem' }}>
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                  <circle cx="9" cy="7" r="4"></circle>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                </svg>
                <p style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Multi-user Support</p>
              </div>
            </div>
          </div>

          {/* Demo Vouchers */}
          <div style={{
            marginTop: '2rem',
            backgroundColor: 'rgba(31, 41, 55, 0.3)',
            backdropFilter: 'blur(8px)',
            borderRadius: '0.75rem',
            padding: '1.5rem',
            border: '1px solid rgba(55, 65, 81, 0.5)'
          }}>
            <h3 style={{
              fontSize: '0.875rem',
              fontWeight: '500',
              color: '#d1d5db',
              marginBottom: '1rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" strokeWidth="2">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
              </svg>
              Demo Voucher Codes
            </h3>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '0.75rem'
            }}>
              {demoVouchers.map((voucher) => (
                <button
                  key={voucher.code}
                  onClick={() => handleDemoClick(voucher.code)}
                  style={{
                    backgroundColor: 'rgba(55, 65, 81, 0.5)',
                    border: '1px solid #4b5563',
                    borderRadius: '0.5rem',
                    padding: '0.75rem 1rem',
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(55, 65, 81, 0.8)';
                    e.currentTarget.style.borderColor = '#6b7280';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(55, 65, 81, 0.5)';
                    e.currentTarget.style.borderColor = '#4b5563';
                  }}
                >
                  <p style={{
                    fontSize: '0.875rem',
                    fontFamily: 'monospace',
                    color: '#34d399',
                    marginBottom: '0.25rem'
                  }}>{voucher.code}</p>
                  <p style={{
                    fontSize: '0.75rem',
                    color: '#6b7280'
                  }}>{voucher.description}</p>
                </button>
              ))}
            </div>
            
            <p style={{
              fontSize: '0.75rem',
              color: '#6b7280',
              textAlign: 'center',
              marginTop: '1rem'
            }}>Click any code to use it</p>
          </div>

          {/* Debug button - REMOVE IN PRODUCTION */}
          <div style={{
            marginTop: '1rem',
            textAlign: 'center'
          }}>
            <button
              onClick={handleDirectAccess}
              style={{
                fontSize: '0.75rem',
                color: '#ef4444',
                textDecoration: 'underline',
                background: 'none',
                border: 'none',
                cursor: 'pointer'
              }}
            >
              Debug: Direct Dashboard Access
            </button>
          </div>

          {/* Footer */}
          <div style={{
            marginTop: '2rem',
            textAlign: 'center'
          }}>
            <p style={{
              fontSize: '0.875rem',
              color: '#6b7280'
            }}>
              Need a voucher code? Contact your sustainability officer or{' '}
              <a 
                href="#" 
                style={{
                  color: '#34d399',
                  textDecoration: 'underline'
                }}
                onMouseEnter={(e) => e.currentTarget.style.color = '#6ee7b7'}
                onMouseLeave={(e) => e.currentTarget.style.color = '#34d399'}
              >
                request access
              </a>
            </p>
          </div>
        </div>
      </div>
    </>
  );
}