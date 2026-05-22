/**
 * Settings Index Page
 * Redirects to integrations for now (can be expanded to a settings menu later)
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function SettingsPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/settings/integrations');
  }, [router]);

  return (
    <div className="flex items-center justify-center h-64">
      <p className="text-gray-500">Redirecting to settings...</p>
    </div>
  );
}
