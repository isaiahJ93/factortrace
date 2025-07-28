'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter();
  
  useEffect(() => {
    const access = localStorage.getItem('companyAccess');
    if (!access) {
      router.push('/login');
    }
  }, [router]);

  return (
    <>
      {children}
    </>
  );
}