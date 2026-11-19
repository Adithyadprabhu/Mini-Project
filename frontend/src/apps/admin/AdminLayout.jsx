import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../../context/useAuth';

export default function AdminLayout({ basePath = '' }) {
  const { user, logout } = useAuth();
  const [profileOpen, setProfileOpen] = useState(false);

  const navItems = [
    { path: `${basePath}/`, icon: 'dashboard', label: 'Executive Overview', exact: true },
    { path: `${basePath}/crime-risk-map`, icon: 'map', label: 'Crime Risk AI Map' },
    { path: `${basePath}/incidents`, icon: 'insights', label: 'Incident Oversight' },
  ];

  return (
    <div className="min-h-screen bg-surface flex">
      {/* Admin Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-72 bg-surface-container-low/95 border-r border-outline-variant/30 backdrop-blur-xl z-50 flex flex-col justify-between shadow-2xl select-none">
        <div className="flex flex-col flex-1 overflow-y-auto">
          {/* Logo Header */}
          <div className="h-16 px-space-md flex items-center justify-between bg-surface-container-lowest/80 border-b border-outline-variant/30">
            <div className="flex items-center gap-space-sm">
              <div className="h-8 w-8 bg-primary/20 text-primary flex items-center justify-center">
                <span className="material-symbols-outlined text-lg">admin_panel_settings</span>
              </div>
              <div className="flex flex-col">
                <span className="font-grotesk text-base font-bold uppercase tracking-wider text-primary leading-tight">
                  ADMIN COMMAND
                </span>
                <span className="font-mono text-[9px] font-semibold uppercase tracking-widest text-outline">
                  CITYWIDE OVERSIGHT
                </span>
              </div>
            </div>
            <div className="h-2 w-2 bg-primary rounded-full animate-pulse" />
          </div>

          {/* Access Badge */}
          <div className="p-space-md flex items-center justify-between bg-surface-container/60 border-b border-outline-variant/20">
            <div className="flex items-center gap-1.5 font-mono text-[9px] text-outline uppercase font-semibold">
              <span className="material-symbols-outlined text-primary text-sm">verified_user</span>
              <span>CLEARANCE: ALPHA-9</span>
            </div>
            <span className="font-mono text-[9px] px-1.5 py-0.5 bg-primary/20 text-primary font-bold">
              SUPERVISOR
            </span>
          </div>

          {/* Nav Links */}
          <nav className="p-space-md space-y-1 font-mono">
            <div className="text-[9px] font-semibold text-outline uppercase tracking-wider px-2 py-1">
              COMMAND MATRIX
            </div>
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.exact}
                className={({ isActive }) =>
                  `flex items-center gap-space-sm px-space-md py-2.5 transition-colors uppercase tracking-wider text-xs font-semibold ${
                    isActive
                      ? 'bg-primary-container text-on-primary-container font-bold shadow-md'
                      : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
                  }`
                }
              >
                <span className="material-symbols-outlined text-lg">{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>
        </div>

        {/* Footer Admin Status */}
        <div className="p-space-md bg-surface-container-lowest/90 border-t border-outline-variant/30 flex flex-col gap-1 text-[9px] font-mono text-outline">
          <div className="flex justify-between items-center">
            <span>OPERATOR:</span>
            <span className="text-on-surface font-bold uppercase truncate max-w-[140px]">
              {user?.name || 'Administrator'}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span>TERMINAL:</span>
            <span className="text-primary font-bold">ADM-CORE-DT</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="pl-72 flex-1 flex flex-col min-h-screen">
        {/* Header Bar */}
        <header className="h-16 bg-surface/90 backdrop-blur-xl border-b border-outline-variant/30 flex items-center justify-between px-space-lg sticky top-0 z-40">
          <div className="flex items-center gap-space-md font-mono text-[10px] text-outline">
            <div className="flex items-center gap-1.5 px-2 py-1 bg-surface-container">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              <span className="text-primary font-bold uppercase">ADMINISTRATIVE MATRIX ONLINE</span>
            </div>
            <span>STATION: KATL-METRO</span>
          </div>

          <div className="flex items-center gap-space-md relative">
            <button
              onClick={() => setProfileOpen((prev) => !prev)}
              className="flex items-center gap-2 p-1.5 bg-surface-container-high hover:bg-surface-variant transition-colors"
            >
              <span className="material-symbols-outlined text-primary text-base">person</span>
              <span className="font-mono text-xs font-bold uppercase text-on-surface">
                {user?.name?.split(' ')[0] || 'Admin'}
              </span>
              <span className="material-symbols-outlined text-outline text-xs">expand_more</span>
            </button>

            {profileOpen && (
              <div className="absolute right-0 top-12 w-64 bg-surface-container-low border border-outline-variant/50 shadow-2xl p-4 font-mono text-xs space-y-3 z-50 animate-fadeIn">
                <div className="border-b border-outline-variant/30 pb-2">
                  <div className="font-bold text-on-surface">{user?.name}</div>
                  <div className="text-[10px] text-outline">{user?.email}</div>
                  <div className="text-[9px] text-primary font-bold mt-1">ROLE: COMMAND ADMINISTRATOR</div>
                </div>
                <button
                  onClick={logout}
                  className="w-full py-2 bg-error-container hover:bg-error text-on-error font-bold uppercase text-[10px] flex items-center justify-center gap-1.5 transition-colors"
                >
                  <span className="material-symbols-outlined text-sm">logout</span>
                  <span>End Administrator Session</span>
                </button>
              </div>
            )}
          </div>
        </header>

        <main className="flex-1 bg-surface">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
