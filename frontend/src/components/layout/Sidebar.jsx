import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { fetchHealthCheck } from '../../services/api';

const navSections = [
  {
    label: 'CORE COMMAND',
    color: 'bg-primary',
    items: [
      { path: '/', icon: 'dashboard', label: 'Executive Overview' },
      { path: '/crime-risk-map', icon: 'map', label: 'Crime Risk AI Map' },
      { path: '/tourist-safety', icon: 'shield', label: 'Tourist Safety Guardian' },
    ],
  },
  {
    label: 'AGENTS & DISPATCH',
    color: 'bg-secondary',
    items: [
      { path: '/incident-prioritization', icon: 'warning', label: 'Incident Prioritization' },
    ],
  },
];

export default function Sidebar() {
  const [healthStatus, setHealthStatus] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function check() {
      try {
        const res = await fetchHealthCheck();
        if (!cancelled) {
          setHealthStatus(res?.status === 'OK' ? 'CONNECTED' : 'DISCONNECTED');
        }
      } catch {
        if (!cancelled) {
          setHealthStatus('DISCONNECTED');
        }
      }
    }
    check();
    const interval = setInterval(check, 30000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <aside className="fixed left-0 top-0 h-full w-72 bg-surface-container-low/95 backdrop-blur-xl z-50 flex flex-col justify-between shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
      <div className="flex flex-col flex-1 overflow-y-auto">
        {/* Logo Header */}
        <div className="h-16 px-space-md flex items-center justify-between bg-surface-container-lowest/80">
          <div className="flex items-center gap-space-sm">
            <div className="h-8 w-8 bg-primary/20 flex items-center justify-center">
              <span className="material-symbols-outlined text-primary text-lg">security</span>
            </div>
            <div className="flex flex-col">
              <span className="font-grotesk text-[18px] font-semibold uppercase tracking-wider text-primary leading-6">
                SENTINEL
              </span>
              <span className="font-mono text-[9px] font-semibold uppercase tracking-widest text-secondary leading-3">
                SURVEILLANCE DECK
              </span>
            </div>
          </div>
          <div className="h-2 w-2 bg-secondary animate-pulse" />
        </div>

        {/* Clearance Badge */}
        <div className="p-space-md flex items-center justify-between bg-surface-container/60">
          <div className="flex items-center gap-space-xs">
            <span className="material-symbols-outlined text-secondary text-base">verified_user</span>
            <span className="font-mono text-[9px] font-semibold uppercase tracking-wider text-on-surface-variant">
              ACCESS STATUS
            </span>
          </div>
          <span className="font-mono text-[9px] font-semibold px-space-xs py-0.5 bg-surface-variant text-secondary font-bold">
            AUTHORIZED
          </span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-space-sm py-space-md space-y-space-md">
          {navSections.map((section) => (
            <div key={section.label} className="space-y-space-xs">
              <div className="px-space-xs py-1 flex items-center gap-space-xs">
                <span className={`w-1.5 h-1.5 ${section.color}`} />
                <span className="font-mono text-[9px] font-semibold uppercase tracking-widest text-outline">
                  {section.label}
                </span>
              </div>
              <div className="space-y-0.5">
                {section.items.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    end={item.path === '/'}
                    className={({ isActive }) =>
                      `flex items-center gap-space-sm px-space-md py-space-sm transition-colors uppercase tracking-wider ${
                        isActive
                          ? 'bg-primary-container text-on-primary-container font-bold'
                          : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface font-mono text-[11px] font-semibold'
                      }`
                    }
                  >
                    <span className="material-symbols-outlined text-lg">{item.icon}</span>
                    <span className="text-[11px]">{item.label}</span>
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>
      </div>

      {/* Footer Telemetry */}
      <div className="p-space-md bg-surface-container-lowest/90 flex flex-col gap-space-xs">
        <div className="flex items-center justify-between text-on-surface-variant font-mono text-[9px] font-semibold">
          <span className="flex items-center gap-1">
            <span
              className={`w-1.5 h-1.5 ${
                healthStatus === 'CONNECTED' ? 'bg-secondary' : 'bg-outline'
              }`}
            />
            BACKEND LINK
          </span>
          <span
            className={`font-bold ${
              healthStatus === 'CONNECTED' ? 'text-secondary' : 'text-outline'
            }`}
          >
            {healthStatus || 'CHECKING...'}
          </span>
        </div>
        <div className="flex items-center justify-between text-on-surface-variant font-mono text-[9px] font-semibold">
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 bg-primary" />
            PREDICTION ENGINE
          </span>
          <span className="font-bold text-outline">STANDBY</span>
        </div>
      </div>
    </aside>
  );
}
