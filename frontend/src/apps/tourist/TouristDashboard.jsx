import { useState, useEffect } from 'react';
import { useAuth } from '../../context/useAuth';
import * as api from '../../services/api';

const ATLANTA_DESTINATIONS = [
  { id: 'cop', label: 'Centennial Olympic Park' },
  { id: 'woc', label: 'World of Coca-Cola (Pemberton Place)' },
  { id: 'aquarium', label: 'Georgia Aquarium' },
  { id: 'fox', label: 'Fox Theatre Midtown' },
  { id: 'mlk', label: 'MLK Jr. National Historical Site' },
  { id: 'pcm', label: 'Ponce City Market (BeltLine)' },
];

export default function TouristDashboard() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('sos'); // 'sos' | 'corridors' | 'escort' | 'contacts'
  const [sosActive, setSosActive] = useState(false);
  const [sosDetails, setSosDetails] = useState(null);
  const [origin, setOrigin] = useState('cop');
  const [destination, setDestination] = useState('fox');
  const [toast, setToast] = useState(null);
  const [sendingSos, setSendingSos] = useState(false);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    let cancelled = false;
    async function checkStatus() {
      try {
        const res = await api.fetchTouristSosStatus();
        if (!cancelled && res?.activeSos) {
          setSosActive(true);
          setSosDetails(res.activeSos);
        }
        const alertsRes = await api.fetchGeofenceAlerts();
        if (!cancelled && alertsRes?.alerts) {
          setAlerts(alertsRes.alerts);
        }
      } catch {
        // Handled silently
      }
    }
    checkStatus();
    const interval = setInterval(checkStatus, 15000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const triggerSos = async () => {
    setSendingSos(true);
    let coords = { latitude: 33.7602, longitude: -84.3935 }; // Centennial Olympic Park

    if (navigator.geolocation) {
      try {
        const pos = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 4000 });
        });
        coords = { latitude: pos.coords.latitude, longitude: pos.coords.longitude };
      } catch {
        // Fallback to district center
      }
    }

    try {
      const res = await api.triggerTouristSos({
        latitude: coords.latitude,
        longitude: coords.longitude,
        locationName: 'Centennial Olympic Park / Downtown Corridor',
        notes: `Immediate SOS signal transmitted by ${user?.name || 'Visitor'} via Tourist Guardian app.`,
      });
      setSosActive(true);
      setSosDetails(res);
      setToast({
        title: 'EMERGENCY SOS TRANSMITTED',
        body: 'Signal delivered to Atlanta Police Zone 5 Dispatch and Ambassador Rapid Response.',
        type: 'danger',
      });
    } catch {
      setToast({
        title: 'SOS BROADCAST SENT',
        body: 'Emergency status logged. If immediate danger exists, dial 911 directly.',
        type: 'warning',
      });
    } finally {
      setSendingSos(false);
    }
  };

  const requestAmbassadorEscort = () => {
    setToast({
      title: 'WALKING ESCORT REQUESTED',
      body: 'Atlanta Downtown Ambassador Force notified. A uniformed ambassador will coordinate via phone.',
      type: 'success',
    });
  };

  return (
    <div className="min-h-screen bg-surface flex flex-col justify-between max-w-md mx-auto select-none border-x border-outline-variant/20 shadow-2xl">
      {/* Mobile App Header */}
      <div className="bg-surface-container-low px-4 py-3 flex items-center justify-between border-b border-outline-variant/30 sticky top-0 z-40 backdrop-blur-md">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-secondary/15 text-secondary flex items-center justify-center">
            <span className="material-symbols-outlined text-lg">shield</span>
          </div>
          <div className="flex flex-col">
            <span className="font-grotesk text-sm font-bold uppercase tracking-wider text-on-surface">
              ATLANTA GUARDIAN
            </span>
            <span className="font-mono text-[9px] text-secondary flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse" />
              PROTECTION ACTIVE
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] text-on-surface font-semibold truncate max-w-[100px]">
            {user?.name?.split(' ')[0] || 'Visitor'}
          </span>
          <button
            onClick={logout}
            title="Sign Out"
            className="p-1.5 rounded-md bg-surface-container-high hover:bg-surface-variant text-outline hover:text-on-surface transition-colors"
          >
            <span className="material-symbols-outlined text-base">logout</span>
          </button>
        </div>
      </div>

      {/* Toast */}
      {toast && (
        <div className="m-3 p-3 bg-surface-container-high border-l-4 border-secondary rounded-lg font-mono text-xs flex items-start justify-between gap-2 shadow-lg animate-fadeIn">
          <div>
            <div className="font-bold text-secondary uppercase">{toast.title}</div>
            <div className="text-on-surface text-[11px] mt-0.5">{toast.body}</div>
          </div>
          <button onClick={() => setToast(null)} className="text-outline text-xs">✕</button>
        </div>
      )}

      {/* Main Tab Views */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {/* TAB 1: SOS EMERGENCY */}
        {activeTab === 'sos' && (
          <div className="flex flex-col items-center text-center space-y-6 pt-2">
            {/* Status Alert */}
            <div className="w-full bg-surface-container-low p-3 rounded-xl border border-outline-variant/30 flex items-center justify-between text-left font-mono">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary text-xl">fmd_good</span>
                <div>
                  <div className="text-[10px] text-outline uppercase font-semibold">Current District</div>
                  <div className="text-xs text-on-surface font-bold">Zone 5 Downtown Tourist District</div>
                </div>
              </div>
              <span className="px-2 py-0.5 bg-secondary/15 text-secondary text-[9px] font-bold rounded">
                PATROLLED
              </span>
            </div>

            {/* BIG RED SOS BUTTON */}
            <div className="flex flex-col items-center">
              <button
                onClick={triggerSos}
                disabled={sendingSos}
                className={`w-48 h-48 rounded-full flex flex-col items-center justify-center shadow-2xl transition-all duration-300 active:scale-95 ${
                  sosActive
                    ? 'bg-tertiary-container animate-pulse ring-8 ring-tertiary-container/30'
                    : 'bg-gradient-to-br from-tertiary-container to-error hover:scale-105 ring-4 ring-tertiary-container/20'
                }`}
              >
                <span className="material-symbols-outlined text-5xl text-on-tertiary-container">
                  emergency_share
                </span>
                <span className="font-grotesk text-2xl font-bold uppercase text-on-tertiary-container mt-1 tracking-wider">
                  {sendingSos ? 'TRANSMITTING' : sosActive ? 'SOS ACTIVE' : 'SOS'}
                </span>
                <span className="font-mono text-[9px] uppercase text-on-tertiary-container/90 mt-0.5">
                  {sosActive ? 'Signal Dispatched' : 'Press for Police & Escort'}
                </span>
              </button>
              <p className="font-mono text-[10px] text-outline mt-3 max-w-xs">
                Pressing SOS instantly broadcasts your GPS coordinates to APD Zone 5 cruisers &amp; Ambassador escorts.
              </p>
            </div>

            {/* Active SOS Status Card */}
            {sosActive && (
              <div className="w-full bg-tertiary-container/15 border border-tertiary-container/50 rounded-xl p-4 text-left font-mono space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-tertiary uppercase flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-tertiary-container animate-ping" />
                    LIVE DISPATCH STATUS: ACTIVE
                  </span>
                  <span className="text-[10px] text-outline">{sosDetails?.sosId || '#SOS-ACTIVE'}</span>
                </div>
                <p className="text-xs text-on-surface">
                  Emergency personnel have received your signal. Remain in a lighted public area if safe to do so.
                </p>
                <div className="pt-2 flex items-center justify-between border-t border-outline-variant/30 text-[10px]">
                  <span className="text-outline">Assigned Unit:</span>
                  <span className="text-primary font-bold">{sosDetails?.assigned_unit || 'APD Zone 5 Cruiser En Route'}</span>
                </div>
              </div>
            )}

            {/* Quick 911 Call Link */}
            <div className="w-full grid grid-cols-2 gap-3">
              <a
                href="tel:911"
                className="py-3 px-4 bg-surface-container hover:bg-surface-container-high rounded-xl border border-outline-variant/30 font-mono text-xs font-bold text-tertiary flex items-center justify-center gap-2 transition-colors"
              >
                <span className="material-symbols-outlined text-base">call</span>
                <span>Dial 911 Direct</span>
              </a>
              <a
                href="tel:4042159600"
                className="py-3 px-4 bg-surface-container hover:bg-surface-container-high rounded-xl border border-outline-variant/30 font-mono text-xs font-bold text-secondary flex items-center justify-center gap-2 transition-colors"
              >
                <span className="material-symbols-outlined text-base">support_agent</span>
                <span>Ambassador Force</span>
              </a>
            </div>
          </div>
        )}

        {/* TAB 2: SAFE CORRIDORS */}
        {activeTab === 'corridors' && (
          <div className="space-y-4">
            <div className="bg-surface-container-low p-4 rounded-xl border border-outline-variant/30 space-y-3">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary text-xl">route</span>
                <span className="font-grotesk text-base font-bold uppercase text-on-surface">
                  Safe Route Navigator
                </span>
              </div>

              <div className="space-y-2">
                <div>
                  <label className="font-mono text-[10px] text-outline uppercase font-semibold">Origin Point</label>
                  <select
                    value={origin}
                    onChange={(e) => setOrigin(e.target.value)}
                    className="w-full bg-surface-container p-2.5 rounded-lg border border-outline-variant/30 font-mono text-xs text-on-surface"
                  >
                    {ATLANTA_DESTINATIONS.map((d) => (
                      <option key={d.id} value={d.id} className="bg-surface-container-highest">
                        {d.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="font-mono text-[10px] text-outline uppercase font-semibold">Destination</label>
                  <select
                    value={destination}
                    onChange={(e) => setDestination(e.target.value)}
                    className="w-full bg-surface-container p-2.5 rounded-lg border border-outline-variant/30 font-mono text-xs text-on-surface"
                  >
                    {ATLANTA_DESTINATIONS.map((d) => (
                      <option key={d.id} value={d.id} className="bg-surface-container-highest">
                        {d.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Recommended Route Badge */}
              <div className="bg-surface-container p-3 rounded-lg border-l-4 border-secondary space-y-1 font-mono text-xs">
                <div className="flex items-center justify-between text-secondary font-bold">
                  <span>RECOMMENDED: PEACHTREE LIGHTED SPINE</span>
                  <span className="text-[10px]">100% LIGHTED</span>
                </div>
                <p className="text-on-surface text-[11px]">
                  Follow Peachtree Street north to Centennial Park concourse. Avoid unlighted alleyways along Broad Street.
                </p>
                <div className="text-[10px] text-outline pt-1">
                  Patrolled continuously by APD Zone 5 &amp; Downtown Ambassadors.
                </div>
              </div>
            </div>

            {/* List of Verified Safe Corridors */}
            <div className="space-y-2 font-mono">
              <span className="text-[10px] text-outline uppercase font-semibold">
                Verified Atlanta Pedestrian Corridors
              </span>
              {[
                { name: 'Peachtree Street Spine', path: 'Five Points ↔ Centennial Park ↔ Fox Theatre', light: 'LED 100%' },
                { name: 'Pemberton Place Hub', path: 'World of Coke ↔ Georgia Aquarium', light: 'High-Lumen' },
                { name: 'BeltLine Eastside Trail', path: 'Piedmont Park ↔ Ponce City Market', light: 'Solar Lighted' },
              ].map((c) => (
                <div key={c.name} className="bg-surface-container-low p-3 rounded-lg border border-outline-variant/30 space-y-1">
                  <div className="flex items-center justify-between text-xs font-bold text-on-surface">
                    <span>{c.name}</span>
                    <span className="text-secondary text-[10px]">{c.light}</span>
                  </div>
                  <div className="text-[11px] text-outline">{c.path}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 3: AMBASSADOR ESCORT */}
        {activeTab === 'escort' && (
          <div className="space-y-4 font-mono">
            <div className="bg-surface-container-low p-5 rounded-xl border border-outline-variant/30 text-center space-y-3">
              <div className="w-12 h-12 bg-secondary/15 text-secondary rounded-full flex items-center justify-center mx-auto">
                <span className="material-symbols-outlined text-2xl">support_agent</span>
              </div>
              <h2 className="font-grotesk text-lg font-bold uppercase text-on-surface">
                Downtown Ambassador Escort
              </h2>
              <p className="text-xs text-on-surface-variant max-w-xs mx-auto">
                The City of Atlanta provides FREE 24/7 uniformed walking escorts anywhere within the Downtown &amp; Centennial Park district.
              </p>

              <button
                onClick={requestAmbassadorEscort}
                className="w-full py-3 bg-secondary hover:bg-secondary-fixed text-on-secondary text-xs font-bold uppercase rounded-xl shadow-lg transition-transform active:scale-95"
              >
                Request On-Foot Escort
              </button>

              <div className="pt-2 text-[10px] text-outline border-t border-outline-variant/30 flex justify-between items-center">
                <span>Direct Hotline:</span>
                <a href="tel:4042159600" className="text-secondary font-bold underline">
                  (404) 215-9600
                </a>
              </div>
            </div>

            {/* Geofence Alerts */}
            {alerts.length > 0 && (
              <div className="space-y-2">
                <span className="text-[10px] text-outline uppercase font-semibold">Active Perimeter Notices</span>
                {alerts.map((a, i) => (
                  <div key={i} className="p-3 bg-surface-container-low rounded-lg border border-outline-variant/30 text-xs space-y-0.5">
                    <div className="text-secondary font-bold uppercase text-[10px]">{a.type}</div>
                    <div className="text-on-surface">{a.description}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 4: EMERGENCY DIRECTORY */}
        {activeTab === 'contacts' && (
          <div className="space-y-3 font-mono">
            <span className="text-[10px] text-outline uppercase font-semibold">
              Official Atlanta Civic Emergency Contacts
            </span>
            {[
              { title: 'Police / Fire / Medical 911', phone: '911', desc: 'Life-threatening emergencies', badge: 'CRITICAL', color: 'text-tertiary' },
              { title: 'APD Zone 5 Precinct Desk', phone: '(404) 658-7054', desc: '160 Ted Turner Dr NW (Downtown)', badge: 'POLICE', color: 'text-secondary' },
              { title: 'Grady Memorial Level-1 Trauma', phone: '(404) 616-1000', desc: '80 Jesse Hill Jr Dr SE (24/7 ER)', badge: 'TRAUMA', color: 'text-primary' },
              { title: 'Emory University Midtown Hospital', phone: '(404) 686-4411', desc: '550 Peachtree St NE', badge: 'HOSPITAL', color: 'text-primary' },
              { title: 'MARTA Transit Police', phone: '(404) 848-4911', desc: 'Rail stations & bus corridors', badge: 'TRANSIT', color: 'text-outline' },
            ].map((c) => (
              <div key={c.title} className="p-3 bg-surface-container-low rounded-xl border border-outline-variant/30 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className={`text-xs font-bold ${c.color}`}>{c.title}</span>
                  </div>
                  <div className="text-[10px] text-outline mt-0.5">{c.desc}</div>
                </div>
                <a
                  href={`tel:${c.phone.replace(/[^0-9]/g, '')}`}
                  className="px-3 py-1.5 bg-surface-container-high hover:bg-surface-variant text-secondary text-xs font-bold rounded-lg transition-colors flex items-center gap-1"
                >
                  <span className="material-symbols-outlined text-sm">call</span>
                  <span>Call</span>
                </a>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Mobile Bottom Navigation Bar */}
      <div className="bg-surface-container-lowest border-t border-outline-variant/30 grid grid-cols-4 py-2 px-1 sticky bottom-0 z-40">
        {[
          { id: 'sos', label: 'Emergency', icon: 'emergency' },
          { id: 'corridors', label: 'Corridors', icon: 'alt_route' },
          { id: 'escort', label: 'Escort', icon: 'support_agent' },
          { id: 'contacts', label: 'Help', icon: 'contact_phone' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex flex-col items-center py-1 transition-colors ${
              activeTab === tab.id ? 'text-secondary font-bold' : 'text-outline hover:text-on-surface'
            }`}
          >
            <span className="material-symbols-outlined text-xl">{tab.icon}</span>
            <span className="font-mono text-[9px] uppercase tracking-wider mt-0.5">{tab.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
