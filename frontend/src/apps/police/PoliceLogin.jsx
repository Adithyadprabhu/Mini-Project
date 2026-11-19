import { useState } from 'react';
import { useAuth } from '../../context/useAuth';

export default function PoliceLogin() {
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
        throw new Error('Officer identification and security credentials required');
      }
      await login(email.trim(), password, 'police');
    } catch (err) {
      setError(err.message || 'Authentication rejected. Invalid police patrol credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface flex flex-col justify-center items-center p-6 select-none relative overflow-hidden font-mono">
      {/* Background Grid */}
      <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px] opacity-25 pointer-events-none" />

      <div className="w-full max-w-md bg-surface-container-low border-2 border-secondary/40 shadow-2xl p-8 relative z-10">
        {/* Police Badge Header */}
        <div className="flex items-center justify-between pb-4 border-b border-outline-variant/30 mb-6">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-secondary animate-pulse" />
            <span className="font-grotesk text-lg font-bold text-on-surface uppercase tracking-wider">
              APD // PATROL DISPATCH
            </span>
          </div>
          <span className="text-[10px] bg-secondary/20 text-secondary px-2 py-0.5 font-bold uppercase">
            ZONE 5 TACTICAL
          </span>
        </div>

        <div className="mb-6">
          <div className="flex items-center gap-2 mb-1">
            <span className="material-symbols-outlined text-secondary text-2xl">local_police</span>
            <h2 className="font-grotesk text-xl font-bold uppercase text-on-surface">
              Officer Patrol Login
            </h2>
          </div>
          <p className="text-xs text-outline">
            Secure mobile terminal access for active Atlanta Police patrol cruisers, foot units, and CAD dispatch responders.
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-error-container/30 border border-error/50 text-error text-xs flex items-center gap-2">
            <span className="material-symbols-outlined text-sm shrink-0">emergency</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="block text-[10px] text-outline uppercase font-semibold mb-1">
              Officer Email / Unit ID
            </label>
            <div className="flex items-center bg-surface-container px-3 py-2 border border-outline-variant/30 focus-within:border-secondary transition-colors">
              <span className="material-symbols-outlined text-outline text-base mr-2">badge</span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="police@yourdomain.com"
                className="bg-transparent text-xs text-on-surface w-full focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-[10px] text-outline uppercase font-semibold mb-1">
              Officer Security PIN / Password
            </label>
            <div className="flex items-center bg-surface-container px-3 py-2 border border-outline-variant/30 focus-within:border-secondary transition-colors">
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
            className="w-full mt-2 py-3 bg-secondary hover:bg-secondary-fixed text-on-secondary font-bold uppercase tracking-wider text-xs transition-all flex items-center justify-center gap-2 shadow-lg disabled:opacity-50"
          >
            {submitting ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-on-secondary border-t-transparent rounded-full animate-spin" />
                <span>Verifying Duty Roster...</span>
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-sm">radio</span>
                <span>Check In To Patrol</span>
              </>
            )}
          </button>
        </form>

        {/* Credentials Helper Box */}
        <div className="mt-5 p-3 bg-surface-container/80 border border-outline-variant/40 text-[10px] space-y-1.5">
          <div className="text-secondary font-bold uppercase tracking-wider flex items-center gap-1.5">
            <span className="material-symbols-outlined text-xs">local_police</span>
            <span>Default Officer Credentials</span>
          </div>
          <div className="flex justify-between text-on-surface-variant font-mono text-[10px]">
            <span className="text-outline">Email:</span>
            <span className="text-on-surface font-bold select-all">police@yourdomain.com</span>
          </div>
          <div className="flex justify-between text-on-surface-variant font-mono text-[10px]">
            <span className="text-outline">Password:</span>
            <span className="text-on-surface font-bold select-all">Police@Sentinel2026!</span>
          </div>
          <div className="flex justify-between text-on-surface-variant font-mono text-[10px]">
            <span className="text-outline">Badge ID:</span>
            <span className="text-on-surface font-bold select-all">APD-504</span>
          </div>
          <button
            type="button"
            onClick={() => {
              setEmail('police@yourdomain.com');
              setPassword('Police@Sentinel2026!');
            }}
            className="w-full mt-2 py-1.5 bg-surface-container-high hover:bg-surface-variant text-secondary text-[9px] font-bold uppercase transition-colors"
          >
            Auto-Fill Officer Credentials
          </button>
        </div>

        <div className="mt-6 pt-4 border-t border-outline-variant/20 flex items-center justify-between text-[9px] text-outline">
          <span>PRECINCT: ZONE 5 HQ</span>
          <span>APD-CAD NET: SYNCED</span>
        </div>
      </div>
    </div>
  );
}
