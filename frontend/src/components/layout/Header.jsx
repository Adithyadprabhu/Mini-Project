import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { fetchHealthCheck } from '../../services/api';

export default function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const [time, setTime] = useState(() => new Date());
  const [systemOnline, setSystemOnline] = useState(null);
  const [profileOpen, setProfileOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [audioAlerts, setAudioAlerts] = useState(true);

  const role = location.pathname.includes('tourist')
    ? 'tourist'
    : location.pathname.includes('incident')
    ? 'officer'
    : 'admin';

  const profileRef = useRef(null);
  const notifRef = useRef(null);

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function checkHealth() {
      try {
        const res = await fetchHealthCheck();
        if (!cancelled) {
          setSystemOnline(res?.status === 'OK');
        }
      } catch {
        if (!cancelled) {
          setSystemOnline(false);
        }
      }
    }

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  // Close popovers on click outside
  useEffect(() => {
    function handleClickOutside(e) {
      if (profileRef.current && !profileRef.current.contains(e.target)) {
        setProfileOpen(false);
      }
      if (notifRef.current && !notifRef.current.contains(e.target)) {
        setNotificationsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleRoleChange = (newRole) => {
    if (newRole === 'tourist') {
      navigate('/tourist-safety');
    } else if (newRole === 'officer') {
      navigate('/incident-prioritization');
    } else {
      navigate('/');
    }
  };

  const formatTime = (d) => {
    return d.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZone: 'America/New_York',
    });
  };

  const getRoleDisplayName = (r) => {
    switch (r) {
      case 'officer':
        return 'PATROL OFFICER';
      case 'tourist':
        return 'TOURIST PORTAL';
      case 'admin':
      default:
        return 'COMMAND OPERATOR';
    }
  };

  return (
    <header className="fixed top-0 left-72 right-0 h-16 bg-surface/90 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.04)] z-40 flex items-center justify-between px-space-lg">
      <div className="flex items-center gap-space-lg overflow-x-auto py-1">
        {/* Network Status */}
        <div className="flex items-center gap-space-xs px-space-sm py-1 bg-surface-container">
          <span
            className={`w-2 h-2 ${
              systemOnline === true
                ? 'bg-secondary animate-pulse'
                : systemOnline === false
                ? 'bg-error'
                : 'bg-outline'
            }`}
          />
          <span
            className={`font-mono text-[9px] font-semibold uppercase font-bold tracking-widest ${
              systemOnline === true
                ? 'text-secondary'
                : systemOnline === false
                ? 'text-error'
                : 'text-outline'
            }`}
          >
            {systemOnline === true
              ? 'BACKEND ONLINE'
              : systemOnline === false
              ? 'BACKEND OFFLINE'
              : 'CHECKING STATUS...'}
          </span>
        </div>

        {/* GPS */}
        <div className="flex items-center gap-space-xs text-on-surface-variant font-mono text-[9px] font-semibold">
          <span className="material-symbols-outlined text-sm text-outline">satellite_alt</span>
          <span>GPS: —</span>
        </div>

        {/* Time */}
        <div className="flex items-center gap-space-xs text-on-surface-variant font-mono text-[9px] font-semibold">
          <span className="material-symbols-outlined text-sm text-outline">schedule</span>
          <span>ATL: {formatTime(time)} EST</span>
        </div>

        {/* Weather */}
        <div className="hidden lg:flex items-center gap-space-xs text-on-surface-variant font-mono text-[9px] font-semibold">
          <span className="material-symbols-outlined text-sm text-outline">partly_cloudy_day</span>
          <span>WEATHER: —</span>
        </div>
      </div>

      <div className="flex items-center gap-space-md relative">
        {/* Search */}
        <div className="hidden xl:flex items-center bg-surface-container px-space-sm py-1 gap-space-sm cursor-pointer hover:bg-surface-container-high transition-colors">
          <span className="material-symbols-outlined text-base text-outline">search</span>
          <span className="font-mono text-[9px] font-semibold text-outline">SEARCH DISPATCH / LOC / CAD</span>
          <span className="px-1.5 py-0.5 bg-surface-variant text-on-surface-variant font-mono text-[9px] font-semibold font-bold">
            CTRL+K
          </span>
        </div>

        {/* Role Selector */}
        <div className="flex items-center bg-surface-container-high px-space-xs py-1">
          <span className="material-symbols-outlined text-sm text-secondary mr-1">shield_person</span>
          <select
            value={role}
            onChange={(e) => handleRoleChange(e.target.value)}
            className="bg-transparent font-mono text-[9px] font-semibold text-on-surface uppercase tracking-wider focus:outline-none cursor-pointer pr-1"
          >
            <option value="admin" className="bg-surface-container-highest text-on-surface">Admin Command</option>
            <option value="officer" className="bg-surface-container-highest text-on-surface">Police Officer</option>
            <option value="tourist" className="bg-surface-container-highest text-on-surface">Tourist Portal</option>
          </select>
        </div>

        {/* Notifications */}
        <div ref={notifRef} className="relative">
          <button
            onClick={() => {
              setNotificationsOpen((prev) => !prev);
              setProfileOpen(false);
            }}
            title="Notifications"
            className="relative flex items-center justify-center p-2 bg-surface-container hover:bg-surface-container-high transition-colors cursor-pointer"
          >
            <span className="material-symbols-outlined text-on-surface-variant text-lg">notifications</span>
            <span className="absolute -top-1 -right-1 px-1 bg-surface-container-high text-outline font-mono text-[9px] font-semibold font-bold">
              0
            </span>
          </button>

          {/* Notifications Dropdown */}
          {notificationsOpen && (
            <div className="absolute right-0 top-12 w-72 bg-surface-container-low border border-outline-variant/40 shadow-2xl z-50 p-space-md flex flex-col gap-space-xs">
              <div className="flex items-center justify-between pb-1 border-b border-outline-variant/30">
                <span className="font-mono text-[10px] font-bold uppercase text-on-surface tracking-wider">
                  SYSTEM NOTIFICATIONS
                </span>
                <span className="font-mono text-[9px] text-outline">ALL CLEAR</span>
              </div>
              <div className="py-4 text-center text-outline font-mono text-[10px]">
                No active notifications or alerts
              </div>
            </div>
          )}
        </div>

        {/* User Profile Button */}
        <div ref={profileRef} className="relative">
          <button
            onClick={() => {
              setProfileOpen((prev) => !prev);
              setNotificationsOpen(false);
            }}
            title="Operator Profile"
            className={`flex items-center gap-space-sm pl-space-xs p-1 cursor-pointer transition-colors ${
              profileOpen ? 'bg-surface-container-high' : 'hover:bg-surface-container'
            }`}
          >
            <div className="flex-col text-right hidden sm:flex">
              <span className="font-mono text-[9px] font-semibold font-bold uppercase tracking-wider text-on-surface">
                {getRoleDisplayName(role)}
              </span>
              <span className="font-mono text-[9px] font-semibold uppercase tracking-widest text-secondary flex items-center justify-end gap-1">
                <span className="w-1.5 h-1.5 bg-secondary animate-pulse" />
                ACTIVE SESSION
              </span>
            </div>
            <div className="w-8 h-8 bg-surface-container-high hover:bg-surface-container-highest flex items-center justify-center text-secondary transition-colors">
              <span className="material-symbols-outlined text-sm">person</span>
            </div>
          </button>

          {/* User Profile Popover / Dropdown Menu */}
          {profileOpen && (
            <div className="absolute right-0 top-12 w-80 bg-surface-container-low border border-outline-variant/50 shadow-2xl z-50 p-space-md flex flex-col gap-space-sm font-mono text-[11px] animate-fadeIn">
              {/* Profile Card Header */}
              <div className="flex items-center gap-space-sm pb-space-xs border-b border-outline-variant/30">
                <div className="w-10 h-10 bg-primary/20 text-primary flex items-center justify-center">
                  <span className="material-symbols-outlined text-xl">shield_person</span>
                </div>
                <div className="flex flex-col">
                  <span className="font-bold text-on-surface uppercase text-[12px]">
                    {getRoleDisplayName(role)}
                  </span>
                  <span className="text-secondary text-[9px] uppercase tracking-wider font-semibold">
                    ACCESS TIER: ALPHA-9 TACTICAL
                  </span>
                </div>
              </div>

              {/* Session Diagnostics */}
              <div className="space-y-1.5 py-1 text-[9px] text-on-surface-variant">
                <div className="flex justify-between">
                  <span className="text-outline">OPERATIONAL ROLE:</span>
                  <span className="text-on-surface font-bold uppercase">{role}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-outline">BACKEND STATUS:</span>
                  <span className={`font-bold ${systemOnline ? 'text-secondary' : 'text-outline'}`}>
                    {systemOnline ? 'CONNECTED' : 'DISCONNECTED'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-outline">TERMINAL STATION:</span>
                  <span className="text-on-surface">DT-COMMAND-01</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-outline">GEODETIC DATUM:</span>
                  <span className="text-on-surface">EPSG:2240 (ATLANTA)</span>
                </div>
              </div>

              {/* Preferences */}
              <div className="pt-space-xs border-t border-outline-variant/30 flex items-center justify-between">
                <span className="text-[10px] text-outline uppercase font-semibold">AUDIO DISPATCH ALERTS</span>
                <button
                  onClick={() => setAudioAlerts((prev) => !prev)}
                  className={`px-2 py-0.5 font-mono text-[9px] font-bold uppercase transition-colors ${
                    audioAlerts ? 'bg-secondary text-on-secondary' : 'bg-surface-container-highest text-outline'
                  }`}
                >
                  {audioAlerts ? 'ENABLED' : 'MUTED'}
                </button>
              </div>

              {/* Quick Actions */}
              <div className="pt-space-xs border-t border-outline-variant/30 flex items-center gap-space-xs">
                <button
                  onClick={() => {
                    handleRoleChange('admin');
                    setProfileOpen(false);
                  }}
                  className="flex-1 py-1.5 bg-surface-container-high hover:bg-surface-variant text-on-surface text-[9px] font-bold uppercase tracking-wider text-center transition-colors"
                >
                  RESET VIEW
                </button>
                <button
                  onClick={() => setProfileOpen(false)}
                  className="flex-1 py-1.5 bg-primary text-on-primary hover:bg-primary-container text-[9px] font-bold uppercase tracking-wider text-center transition-colors"
                >
                  CLOSE
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
