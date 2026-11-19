import { useState } from 'react';
import { useAuth } from '../../context/useAuth';

export default function AdminLogin() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      if (!email.trim() || !password) {
        throw new Error('Command administrator credentials required');
      }
      await login(email.trim(), password, 'admin');
    } catch (err) {
      setError(err.message || 'Authentication rejected. Invalid command administrative credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface flex flex-col justify-center items-center p-6 select-none relative overflow-hidden">
      {/* Background Cartography Grid Overlay */}
      <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px] opacity-25 pointer-events-none" />

      <div className="w-full max-w-md bg-surface-container-low border border-outline-variant/40 shadow-2xl p-8 relative z-10 font-mono">
        {/* Terminal Header Bar */}
        <div className="flex items-center justify-between pb-4 border-b border-outline-variant/30 mb-6">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-primary" />
            <span className="font-grotesk text-lg font-bold text-on-surface uppercase tracking-wider">
              SENTINEL // ADMIN COMMAND
            </span>
          </div>
          <span className="text-[10px] bg-surface-container-high text-primary px-2 py-0.5 font-bold">
            TIER-1 ACCESS
          </span>
        </div>

        <div className="mb-6">
          <h2 className="font-grotesk text-xl font-bold uppercase text-on-surface">
            Command Center Authentication
          </h2>
          <p className="text-xs text-outline mt-1">
            Authorized administrative access for spatial analytics, district GIS oversight, and citywide incident coordination.
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-error-container/30 border border-error/50 text-error text-xs flex items-center gap-2">
            <span className="material-symbols-outlined text-sm shrink-0">gpp_bad</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="block text-[10px] text-outline uppercase font-semibold mb-1">
              Admin Identification / Email
            </label>
            <div className="flex items-center bg-surface-container px-3 py-2 border border-outline-variant/30 focus-within:border-primary transition-colors">
              <span className="material-symbols-outlined text-outline text-base mr-2">admin_panel_settings</span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@yourdomain.com"
                className="bg-transparent text-xs text-on-surface w-full focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-[10px] text-outline uppercase font-semibold mb-1">
              Security Key / Password
            </label>
            <div className="flex items-center bg-surface-container px-3 py-2 border border-outline-variant/30 focus-within:border-primary transition-colors">
              <span className="material-symbols-outlined text-outline text-base mr-2">key</span>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="bg-transparent text-xs text-on-surface w-full focus:outline-none"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full mt-2 py-3 bg-primary hover:bg-primary-container text-on-primary font-bold uppercase tracking-wider text-xs transition-all flex items-center justify-center gap-2 shadow-lg disabled:opacity-50"
          >
            {submitting ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-on-primary border-t-transparent rounded-full animate-spin" />
                <span>Verifying Clearance...</span>
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-sm">lock_open</span>
                <span>Authenticate Session</span>
              </>
            )}
          </button>
        </form>

        {/* Credentials Helper Box */}
        <div className="mt-5 p-3 bg-surface-container/80 border border-outline-variant/40 text-[10px] space-y-1.5">
          <div className="text-primary font-bold uppercase tracking-wider flex items-center gap-1.5">
            <span className="material-symbols-outlined text-xs">key</span>
            <span>Default Administrator Credentials</span>
          </div>
          <div className="flex justify-between text-on-surface-variant font-mono text-[10px]">
            <span className="text-outline">Email:</span>
            <span className="text-on-surface font-bold select-all">admin@yourdomain.com</span>
          </div>
          <div className="flex justify-between text-on-surface-variant font-mono text-[10px]">
            <span className="text-outline">Password:</span>
            <span className="text-on-surface font-bold select-all">Admin@Sentinel2026!</span>
          </div>
          <button
            type="button"
            onClick={() => {
              setEmail('admin@yourdomain.com');
              setPassword('Admin@Sentinel2026!');
            }}
            className="w-full mt-2 py-1.5 bg-surface-container-high hover:bg-surface-variant text-primary text-[9px] font-bold uppercase transition-colors"
          >
            Auto-Fill Admin Credentials
          </button>
        </div>

        <div className="mt-6 pt-4 border-t border-outline-variant/20 flex items-center justify-between text-[9px] text-outline">
          <span>PORTAL ID: ADM-HQ-01</span>
          <span>GEODETIC REF: EPSG:2240</span>
        </div>
      </div>
    </div>
  );
}
