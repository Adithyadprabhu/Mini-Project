import { useState, useEffect } from 'react';
import { fetchOverview, fetchIncidents } from '../services/api';

export default function ExecutiveOverview() {
  const [data, setData] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const [overviewRes, incidentsRes] = await Promise.allSettled([
          fetchOverview(),
          fetchIncidents(),
        ]);

        if (cancelled) return;

        if (overviewRes.status === 'fulfilled' && overviewRes.value) {
          setData(overviewRes.value);
        } else {
          setData(null);
        }

        if (incidentsRes.status === 'fulfilled' && incidentsRes.value?.incidents) {
          setIncidents(incidentsRes.value.incidents);
        } else {
          setIncidents([]);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Backend connection unavailable');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadData();
    return () => {
      cancelled = true;
    };
  }, []);

  const kpis = data?.kpis || null;
  const weather = data?.weather || null;

  const kpiCards = [
    {
      label: 'TOTAL INCIDENTS (24H)',
      icon: 'emergency',
      value: kpis?.totalIncidents24h !== undefined ? String(kpis.totalIncidents24h) : '—',
      delta: kpis?.incidentsChange !== undefined ? `${kpis.incidentsChange > 0 ? '+' : ''}${kpis.incidentsChange}%` : null,
      deltaColor: 'text-secondary',
      valueColor: 'text-on-surface',
      accentColor: 'bg-secondary',
      sub: kpis ? 'Recorded 24h incidents' : 'No data available',
    },
    {
      label: 'HIGH-RISK / CRITICAL ZONES',
      icon: 'fmd_bad',
      iconColor: 'text-tertiary',
      value: kpis?.highRiskZones !== undefined ? String(kpis.highRiskZones) : '—',
      delta: kpis?.highRiskZones ? 'ACTIVE' : null,
      deltaColor: 'text-tertiary',
      valueColor: 'text-tertiary',
      accentColor: 'bg-tertiary-container',
      sub: kpis ? 'High-risk sectors flagged' : 'No data available',
    },
    {
      label: 'ACTIVE UNITS DEPLOYED',
      icon: 'local_police',
      iconColor: 'text-primary',
      value: kpis?.activeUnits !== undefined ? String(kpis.activeUnits) : '—',
      delta: null,
      valueColor: 'text-primary',
      accentColor: 'bg-primary',
      sub: kpis ? 'Units on field' : 'No emergency units available',
    },
    {
      label: 'MONITORED TOURISTS',
      icon: 'travel_explore',
      iconColor: 'text-secondary',
      value: kpis?.monitoredTourists !== undefined ? kpis.monitoredTourists.toLocaleString() : '—',
      delta: kpis?.touristsChange !== undefined ? `${kpis.touristsChange > 0 ? '+' : ''}${kpis.touristsChange}%` : null,
      deltaColor: 'text-secondary',
      valueColor: 'text-on-surface',
      accentColor: 'bg-secondary',
      sub: kpis ? 'Registered active visitors' : 'No visitor data available',
    },
    {
      label: 'AI INCIDENT ACCURACY',
      icon: 'neurology',
      iconColor: 'text-primary',
      value: kpis?.aiAccuracy !== undefined ? `${kpis.aiAccuracy}%` : '—',
      delta: kpis?.aiAccuracy ? 'CONF' : null,
      deltaColor: 'text-secondary',
      valueColor: 'text-primary',
      accentColor: 'bg-primary-container',
      sub: kpis ? 'Model Validation Score' : 'Prediction service unavailable',
    },
  ];

  const criticalIncident = incidents.find((i) => i.priority === 'critical');

  return (
    <div className="flex flex-col w-full">
      {/* ── Command Operations Header Bar ─────────────────────────── */}
      <div className="bg-surface-container-lowest/90 px-space-md py-space-sm flex flex-wrap items-center justify-between gap-y-space-xs">
        <div className="flex items-center gap-space-md">
          <div className="flex items-center gap-space-xs">
            <span className={`w-2.5 h-2.5 ${data ? 'bg-secondary animate-ping' : 'bg-outline'}`} />
            <span className="font-grotesk text-headline-sm uppercase tracking-wider text-on-surface">
              EXECUTIVE COMMAND MATRIX
            </span>
          </div>
          <div className="hidden md:flex items-center gap-space-xs px-space-xs py-0.5 bg-surface-container text-on-surface-variant font-mono text-label-sm">
            <span className="text-secondary font-bold">GRID LOC:</span>
            <span>ZONE-ATL-DT // EPSG:2240</span>
          </div>
          <div className="flex items-center gap-space-xs px-space-xs py-0.5 bg-surface-container-high text-primary font-mono text-label-sm">
            <span className={`w-1.5 h-1.5 ${data ? 'bg-primary' : 'bg-outline'}`} />
            <span>{data ? 'BACKEND LINK ACTIVE' : 'AWAITING BACKEND CONNECTION'}</span>
          </div>
        </div>
        {/* Action Toolbar */}
        <div className="flex flex-wrap items-center gap-space-xs">
          <button className="px-space-sm py-1 bg-surface-container-high hover:bg-surface-variant text-on-surface font-mono text-label-sm uppercase tracking-wider transition-colors flex items-center gap-1">
            <span className="material-symbols-outlined text-sm text-secondary">campaign</span>
            <span>Broadcast Advisory</span>
          </button>
          <button className="px-space-sm py-1 bg-surface-container-high hover:bg-surface-variant text-error font-mono text-label-sm uppercase tracking-wider transition-colors flex items-center gap-1">
            <span className="material-symbols-outlined text-sm text-error">lock</span>
            <span>Lockdown Geofence</span>
          </button>
          <button className="px-space-sm py-1 bg-primary text-on-primary font-mono text-label-sm uppercase tracking-wider font-bold hover:bg-surface-tint transition-colors flex items-center gap-1">
            <span className="material-symbols-outlined text-sm">download</span>
            <span>Export Briefing</span>
          </button>
        </div>
      </div>

      {/* ── Realtime Emergency Alert Ticker ────────────────────────── */}
      <div className="bg-surface-container-low px-space-md py-1.5 flex flex-wrap items-center justify-between gap-space-sm">
        <div className="flex items-center gap-space-sm flex-1 min-w-[280px]">
          <div
            className={`px-space-xs py-0.5 ${
              criticalIncident
                ? 'bg-tertiary-container text-on-tertiary-container animate-pulse'
                : 'bg-surface-container-high text-outline'
            } font-mono text-label-sm font-bold uppercase tracking-widest flex items-center gap-1`}
          >
            <span className="material-symbols-outlined text-xs">
              {criticalIncident ? 'warning' : 'info'}
            </span>
            {criticalIncident ? 'CRITICAL ALERT' : 'SYSTEM STATUS'}
          </div>
          <div className="flex items-center gap-space-xs font-mono text-body-sm text-on-surface truncate">
            {criticalIncident ? (
              <>
                <span className="text-tertiary font-bold">[{criticalIncident.id}]</span>
                <span className="text-on-surface-variant">{criticalIncident.location}:</span>
                <span className="text-on-surface font-semibold truncate">
                  {criticalIncident.title}
                </span>
              </>
            ) : (
              <span className="text-on-surface-variant font-mono">
                No active emergency alerts — System monitoring
              </span>
            )}
          </div>
        </div>
      </div>

      {/* ── Main Dashboard Content ────────────────────────────────── */}
      <div className="p-space-md md:p-space-lg flex flex-col gap-space-md">
        {loading && (
          <div className="p-space-md bg-surface-container-low flex items-center justify-center gap-2 text-secondary font-mono text-label-sm">
            <span className="w-2 h-2 bg-secondary animate-ping" />
            <span>FETCHING LIVE BACKEND TELEMETRY...</span>
          </div>
        )}

        {error && (
          <div className="p-space-md bg-surface-container-low border-l-4 border-error flex items-center justify-between text-error font-mono text-label-sm">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-base">cloud_off</span>
              <span>Backend connection unavailable: {error}</span>
            </div>
            <span className="text-outline uppercase">Showing empty state</span>
          </div>
        )}

        {/* ── KPI Summary Row (5 Cards) ───────────────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-space-sm">
          {kpiCards.map((card, i) => (
            <div
              key={i}
              className="bg-surface-container-low/85 backdrop-blur-md p-space-md flex flex-col justify-between gap-space-sm relative overflow-hidden"
            >
              <div className={`absolute top-0 left-0 w-1 h-full ${card.accentColor}`} />
              <div className="flex items-center justify-between">
                <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
                  {card.label}
                </span>
                <span className={`material-symbols-outlined text-base ${card.iconColor || 'text-secondary'}`}>
                  {card.icon}
                </span>
              </div>
              <div>
                <div className="flex items-baseline gap-space-xs">
                  <span className={`font-grotesk text-headline-xl font-bold ${card.valueColor}`}>
                    {card.value}
                  </span>
                  {card.delta && (
                    <span className={`font-mono text-label-md font-bold ${card.deltaColor}`}>
                      {card.delta}
                    </span>
                  )}
                </div>
                <span className="font-mono text-body-sm text-outline">{card.sub}</span>
              </div>
            </div>
          ))}
        </div>

        {/* ── Main Grid: Tactical GIS (7 cols) + Telemetry (5 cols) ── */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-md">
          {/* ── LEFT: Tactical GIS Map Panel ───────────────────────── */}
          <div className="lg:col-span-7 bg-surface-container-low/95 flex flex-col relative overflow-hidden">
            {/* Map Header Controls */}
            <div className="p-space-sm bg-surface-container flex flex-wrap items-center justify-between gap-space-xs">
              <div className="flex items-center gap-space-xs">
                <span className="material-symbols-outlined text-secondary text-base">radar</span>
                <span className="font-grotesk text-headline-sm uppercase text-on-surface">
                  ATLANTA METRO TACTICAL GIS
                </span>
              </div>
              <div className="flex items-center gap-space-xs font-mono text-label-sm text-outline">
                <span>CARTOGRAPHIC GRID: EPSG:2240</span>
              </div>
            </div>

            {/* Tactical Canvas */}
            <div className="relative w-full h-[480px] bg-surface-container-lowest overflow-hidden flex items-center justify-center">
              {/* Map base road grid */}
              <div className="w-full h-full bg-surface-container-lowest opacity-40 filter contrast-125 saturate-50 flex items-center justify-center">
                <svg className="w-full h-full" viewBox="0 0 800 480" fill="none">
                  {/* Grid lines */}
                  {Array.from({ length: 9 }).map((_, i) => (
                    <line key={`h${i}`} x1="0" y1={i * 60} x2="800" y2={i * 60} stroke="#242a3a" strokeWidth="0.5" />
                  ))}
                  {Array.from({ length: 11 }).map((_, i) => (
                    <line key={`v${i}`} x1={i * 80} y1="0" x2={i * 80} y2="480" stroke="#242a3a" strokeWidth="0.5" />
                  ))}
                  {/* Real road arterial corridors */}
                  <line x1="400" y1="0" x2="400" y2="480" stroke="#242a3a" strokeWidth="2" />
                  <line x1="0" y1="240" x2="800" y2="240" stroke="#242a3a" strokeWidth="2" />
                  <line x1="200" y1="0" x2="600" y2="480" stroke="#1e2538" strokeWidth="1" />
                </svg>
              </div>

              {/* Tactical HUD Overlay */}
              <div className="absolute inset-0 pointer-events-none flex flex-col justify-between p-space-sm">
                <div className="flex items-start justify-between font-mono text-label-sm text-outline">
                  <div className="bg-surface/80 p-1 flex flex-col">
                    <span className="text-secondary font-bold">NW: 33.7634° N, 84.3951° W</span>
                    <span>CENTER: CENTENNIAL OLYMPIC PARK HUB</span>
                  </div>
                  <div className="bg-surface/80 p-1 flex flex-col text-right">
                    <span>ELEVATION: 1,050 FT</span>
                    <span>GEO-BOUNDS: ATLANTA METRO SECTOR 5</span>
                  </div>
                </div>

                {/* Empty State Banner */}
                <div className="self-center bg-surface-container-high/90 px-space-md py-space-sm border border-outline-variant flex flex-col items-center gap-1 shadow-lg pointer-events-auto">
                  <span className="material-symbols-outlined text-outline text-2xl">location_off</span>
                  <span className="font-mono text-label-sm text-on-surface uppercase font-bold">
                    No Live GPS Tracking Data Available
                  </span>
                  <span className="font-mono text-body-sm text-outline">
                    Connect backend dispatch &amp; consent-verified tourist location feeds
                  </span>
                </div>

                {/* Bottom Legend */}
                <div className="flex flex-wrap items-center justify-between gap-space-xs bg-surface/90 p-space-xs pointer-events-auto">
                  <div className="flex items-center gap-space-sm font-mono text-label-sm">
                    <div className="flex items-center gap-1">
                      <span className="w-3 h-3 bg-tertiary-container" />
                      <span className="text-on-surface">CRITICAL INCIDENT</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="w-3 h-3 bg-secondary" />
                      <span className="text-on-surface">TOURIST ZONE</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="w-3 h-3 bg-primary" />
                      <span className="text-on-surface">DISPATCH PATROL</span>
                    </div>
                  </div>
                  <div className="font-mono text-label-sm text-outline">
                    <span>LIVE CAD STREAM: AWAITING SYNC</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Geofence Zone Status Bar */}
            <div className="p-space-sm bg-surface-container flex items-center justify-center font-mono text-label-sm text-outline">
              <span>No zone risk assessment data available from prediction service</span>
            </div>
          </div>

          {/* ── RIGHT: Telemetry & AI Stream Panel (5 cols) ────────── */}
          <div className="lg:col-span-5 flex flex-col gap-space-md">
            {/* Widget 1: Environmental Telemetry */}
            <div className="bg-surface-container-low/95 p-space-md flex flex-col gap-space-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-space-xs">
                  <span className="material-symbols-outlined text-secondary text-base">thermostat</span>
                  <span className="font-grotesk text-headline-sm uppercase text-on-surface">
                    ENVIRONMENTAL TELEMETRY
                  </span>
                </div>
                <span className="px-space-xs py-0.5 bg-surface-container text-outline font-mono text-label-sm">
                  {weather ? 'ACTIVE' : 'NO SENSOR DATA'}
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-space-xs pt-space-xs">
                {[
                  { label: 'ATLANTA METRO', value: weather?.temp || '—', sub: weather?.condition || 'No data' },
                  { label: 'HUMIDITY', value: weather?.humidity || '—', sub: 'No data' },
                  { label: 'SURFACE WIND', value: weather?.wind || '—', sub: 'No data' },
                  { label: 'OPTICAL VIS', value: weather?.opticalVis || '—', sub: 'No data' },
                ].map((w, i) => (
                  <div key={i} className="bg-surface-container p-space-xs flex flex-col">
                    <span className="font-mono text-label-sm text-outline uppercase">{w.label}</span>
                    <span className="font-grotesk text-headline-md font-bold text-on-surface">{w.value}</span>
                    <span className="font-mono text-body-sm text-on-surface-variant">{w.sub}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Widget 2: AI Incident Prioritization Stream */}
            <div className="bg-surface-container-low/95 p-space-md flex flex-col gap-space-sm flex-1">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-space-xs">
                  <span className="material-symbols-outlined text-primary text-base">emergency_home</span>
                  <span className="font-grotesk text-headline-sm uppercase text-on-surface">
                    AI INCIDENT PRIORITIZATION
                  </span>
                </div>
                <div className="flex items-center gap-1 font-mono text-label-sm text-outline">
                  <span>QUEUE ({incidents.length})</span>
                </div>
              </div>
              <div className="flex flex-col gap-space-xs">
                {incidents.length === 0 ? (
                  <div className="p-space-lg bg-surface-container text-center font-mono text-label-sm text-outline">
                    No active incidents reported
                  </div>
                ) : (
                  incidents.map((inc) => (
                    <div
                      key={inc.id}
                      className="bg-surface-container p-space-xs flex items-center justify-between gap-space-sm hover:bg-surface-container-high transition-colors"
                    >
                      <div className="flex items-center gap-space-xs min-w-0">
                        <span className="w-1.5 h-10 bg-primary shrink-0" />
                        <div className="flex flex-col min-w-0">
                          <div className="flex items-center gap-space-xs">
                            <span className="px-1 py-0 bg-primary/20 text-primary font-mono text-label-sm font-bold">
                              {inc.priority || 'P-3'}
                            </span>
                            <span className="font-mono text-label-md text-on-surface font-bold truncate">
                              {inc.title}
                            </span>
                          </div>
                          <span className="font-mono text-body-sm text-outline truncate">{inc.location}</span>
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        <span className="font-mono text-label-md text-primary font-bold">
                          SEV: {inc.severity || '—'}
                        </span>
                        <span className="block font-mono text-label-sm text-outline">{inc.time || '—'}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Widget 3: Predictive Incident Peaks */}
            <div className="bg-surface-container-low/95 p-space-md flex flex-col gap-space-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-space-xs">
                  <span className="material-symbols-outlined text-secondary text-base">monitoring</span>
                  <span className="font-grotesk text-headline-sm uppercase text-on-surface">
                    PREDICTIVE INCIDENT FORECAST
                  </span>
                </div>
                <span className="font-mono text-label-sm text-outline">MODEL STANDBY</span>
              </div>
              <div className="h-28 w-full bg-surface-container p-2 flex flex-col items-center justify-center text-center">
                <span className="material-symbols-outlined text-outline text-2xl mb-1">query_stats</span>
                <span className="font-mono text-label-sm text-outline uppercase font-semibold">
                  Prediction service unavailable
                </span>
                <span className="font-mono text-body-sm text-outline">
                  Awaiting ML temporal risk forecast model execution
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* ── Bottom Section: CCTV / Safe Passages / Command Console ── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-space-md">
          {/* Card A: CCTV / Sensors */}
          <div className="bg-surface-container-low/95 p-space-md flex flex-col gap-space-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-space-xs">
                <span className="material-symbols-outlined text-secondary text-base">photo_camera_front</span>
                <span className="font-grotesk text-headline-sm uppercase text-on-surface">
                  OPTICAL CCTVs // SENSORS
                </span>
              </div>
              <span className="font-mono text-label-sm text-outline">0 CONNECTED</span>
            </div>
            <div className="p-space-md bg-surface-container flex flex-col items-center justify-center text-center h-28">
              <span className="material-symbols-outlined text-outline text-2xl mb-1">videocam_off</span>
              <span className="font-mono text-label-sm text-outline uppercase">
                No active video stream feeds connected
              </span>
            </div>
          </div>

          {/* Card B: Tourist Safe Passages */}
          <div className="bg-surface-container-low/95 p-space-md flex flex-col gap-space-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-space-xs">
                <span className="material-symbols-outlined text-primary text-base">route</span>
                <span className="font-grotesk text-headline-sm uppercase text-on-surface">
                  TOURIST SAFE PASSAGES
                </span>
              </div>
              <span className="font-mono text-label-sm text-outline">0 ROUTES</span>
            </div>
            <div className="p-space-md bg-surface-container flex flex-col items-center justify-center text-center h-28">
              <span className="material-symbols-outlined text-outline text-2xl mb-1">alt_route</span>
              <span className="font-mono text-label-sm text-outline uppercase">
                No verified route data available
              </span>
            </div>
          </div>

          {/* Card C: Command Console */}
          <div className="bg-surface-container-low/95 p-space-md flex flex-col justify-between gap-space-xs">
            <div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-space-xs">
                  <span className="material-symbols-outlined text-secondary text-base">security</span>
                  <span className="font-grotesk text-headline-sm uppercase text-on-surface">
                    COMMAND CONSOLE
                  </span>
                </div>
                <span className="font-mono text-label-sm text-outline">SYSTEM CONSOLE</span>
              </div>
              <div className="pt-space-xs space-y-1 font-mono text-label-sm">
                <div className="flex justify-between text-on-surface-variant">
                  <span>MARTA TRANSIT POLICE LINK:</span>
                  <span className="text-outline">NOT CONNECTED</span>
                </div>
                <div className="flex justify-between text-on-surface-variant">
                  <span>ATLANTA TOURIST APP BROADCAST:</span>
                  <span className="text-outline">AWAITING GATEWAY</span>
                </div>
                <div className="flex justify-between text-on-surface-variant">
                  <span>CAD INTEGRATION (911):</span>
                  <span className="text-outline">AWAITING STREAM</span>
                </div>
              </div>
            </div>
            <div className="pt-2 flex items-center gap-space-xs">
              <button className="flex-1 py-1.5 bg-surface-container-high hover:bg-surface-variant text-on-surface font-mono text-label-sm uppercase font-bold tracking-wider flex items-center justify-center gap-1 transition-colors">
                <span className="material-symbols-outlined text-sm">notifications_active</span>
                <span>SEND MASS ADVISORY</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
