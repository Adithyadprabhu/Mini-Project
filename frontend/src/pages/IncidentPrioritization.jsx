import { useState, useEffect } from 'react';
import { fetchIncidents, dispatchIncident } from '../services/api';

export default function IncidentPrioritization() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');
  const [dispatched, setDispatched] = useState({});

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setLoading(true);
        setError(null);
        const res = await fetchIncidents();
        if (!cancelled) {
          setIncidents(res?.incidents || []);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Backend connection unavailable');
          setIncidents([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleDispatch = async (incidentId) => {
    try {
      const res = await dispatchIncident(incidentId);
      if (res?.success) {
        setDispatched((prev) => ({ ...prev, [incidentId]: true }));
      }
    } catch (err) {
      console.error('Dispatch failed:', err);
    }
  };

  const filteredIncidents = incidents.filter((inc) => {
    if (filter === 'all') return true;
    return inc.priority === filter;
  });

  const counts = {
    all: incidents.length,
    critical: incidents.filter((i) => i.priority === 'critical').length,
    high: incidents.filter((i) => i.priority === 'high').length,
    medium: incidents.filter((i) => i.priority === 'medium').length,
    low: incidents.filter((i) => i.priority === 'low').length,
  };

  const getPriorityStyle = (priority) => {
    switch (priority) {
      case 'critical':
        return {
          border: 'border-tertiary-container',
          dot: 'bg-tertiary-container',
          text: 'text-tertiary-container',
          badgeBg: 'bg-tertiary-container',
          badgeText: 'text-on-tertiary-container',
          label: 'CRITICAL P-1',
        };
      case 'high':
        return {
          border: 'border-secondary',
          dot: 'bg-secondary',
          text: 'text-secondary',
          badgeBg: 'bg-secondary/20',
          badgeText: 'text-secondary',
          label: 'HIGH P-2',
        };
      case 'medium':
        return {
          border: 'border-primary',
          dot: 'bg-primary',
          text: 'text-primary',
          badgeBg: 'bg-primary/20',
          badgeText: 'text-primary',
          label: 'MED P-3',
        };
      default:
        return {
          border: 'border-outline-variant',
          dot: 'bg-outline',
          text: 'text-outline',
          badgeBg: 'bg-surface-variant',
          badgeText: 'text-on-surface-variant',
          label: 'LOW P-4',
        };
    }
  };

  return (
    <div className="flex flex-col w-full text-on-surface select-none pb-12">
      {/* Multi-Agent Orchestration Banner */}
      <section className="w-full bg-surface-container-lowest px-space-md py-space-sm border-b border-outline-variant/30 flex flex-col xl:flex-row xl:items-center xl:justify-between gap-space-sm">
        <div className="flex items-center gap-space-md">
          <div className="flex items-center gap-space-xs">
            <span className={`inline-block w-2.5 h-2.5 ${incidents.length > 0 ? 'bg-secondary animate-ping' : 'bg-outline'}`} />
            <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-secondary font-bold">
              MULTI-AGENT DISPATCH TRIAGE
            </span>
          </div>
          <span className="text-outline font-mono text-[9px] font-semibold">|</span>
          <div className="flex items-center gap-space-xs font-mono text-[9px] font-semibold text-on-surface-variant">
            <span className="text-outline">STREAM:</span>
            <span className="text-outline">CAD 911 INTEGRATION</span>
          </div>
        </div>

        {/* 3 Agent Pills */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-space-xs xl:w-2/3">
          {[
            { name: 'SEVERITY CLASSIFIER', detail: 'Awaiting CAD 911 Stream', color: 'border-secondary' },
            { name: 'RESOURCE ALLOCATOR', detail: 'Vector Routing Standby', color: 'border-primary' },
            { name: 'GEOFENCE SENTINEL', detail: 'Perimeter Monitoring', color: 'border-tertiary' },
          ].map((agent) => (
            <div key={agent.name} className={`flex items-center justify-between px-space-sm py-1 bg-surface-container-low border-l-2 ${agent.color}`}>
              <div className="truncate">
                <div className="font-mono text-[9px] font-semibold uppercase font-bold text-on-surface truncate">
                  {agent.name}
                </div>
                <div className="font-mono text-[9px] font-semibold text-outline truncate">
                  {agent.detail}
                </div>
              </div>
              <span className="font-mono text-[9px] font-semibold uppercase px-1.5 py-0.5 bg-surface-container-high text-outline ml-1">
                STANDBY
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Main Content */}
      <div className="p-space-md xl:p-space-lg grid grid-cols-1 xl:grid-cols-12 gap-space-md">
        {/* Left: Incident Queue (7 cols) */}
        <div className="xl:col-span-7 flex flex-col gap-space-md">
          {/* Header & Filter */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between bg-surface-container-low p-space-md border-b-2 border-outline-variant/40 gap-space-sm">
            <div className="flex items-center gap-space-sm">
              <div className="w-8 h-8 bg-surface-container-high flex items-center justify-center text-secondary">
                <span className="material-symbols-outlined text-lg">electric_bolt</span>
              </div>
              <div>
                <h1 className="font-grotesk text-[18px] font-semibold uppercase tracking-wider text-on-surface">
                  INCIDENT DISPATCH QUEUE
                </h1>
                <p className="font-mono text-[9px] font-semibold text-outline">
                  TRIAGE ENGINE // LIVE CAD STREAM
                </p>
              </div>
            </div>
            <div className="inline-flex bg-surface-container-lowest p-0.5">
              {[
                { key: 'all', label: `ALL (${counts.all})`, color: 'text-on-surface' },
                { key: 'critical', label: `CRIT (${counts.critical})`, color: 'text-tertiary' },
                { key: 'high', label: `HIGH (${counts.high})`, color: 'text-secondary' },
                { key: 'medium', label: `MED (${counts.medium})`, color: 'text-primary' },
                { key: 'low', label: `LOW (${counts.low})`, color: 'text-outline' },
              ].map((btn) => (
                <button
                  key={btn.key}
                  onClick={() => setFilter(btn.key)}
                  className={`px-space-sm py-1 font-mono text-[9px] font-semibold uppercase font-bold transition-colors ${
                    filter === btn.key ? `${btn.color} bg-surface-container-high` : `${btn.color} hover:bg-surface-container`
                  }`}
                >
                  {btn.label}
                </button>
              ))}
            </div>
          </div>

          {loading && (
            <div className="p-space-lg bg-surface-container text-center font-mono text-label-sm text-secondary flex items-center justify-center gap-2">
              <span className="w-2 h-2 bg-secondary animate-ping" />
              <span>FETCHING ACTIVE INCIDENTS FROM CAD BACKEND...</span>
            </div>
          )}

          {error && (
            <div className="p-space-md bg-surface-container-low border-l-4 border-error text-error font-mono text-label-sm">
              Backend connection unavailable: {error}
            </div>
          )}

          {!loading && filteredIncidents.length === 0 && (
            <div className="p-space-xl bg-surface-container text-center flex flex-col items-center justify-center gap-2">
              <span className="material-symbols-outlined text-outline text-4xl">inbox</span>
              <span className="font-grotesk text-headline-sm uppercase text-on-surface">
                No Active Incidents
              </span>
              <span className="font-mono text-body-sm text-outline max-w-sm">
                No active incidents currently reported in the dispatch triage feed.
              </span>
            </div>
          )}

          {/* Incident Cards */}
          {filteredIncidents.map((inc) => {
            const style = getPriorityStyle(inc.priority);
            return (
              <div
                key={inc.id}
                className={`relative bg-surface-container p-space-md border-l-4 ${style.border} flex flex-col gap-space-sm`}
              >
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-space-xs border-b border-outline-variant/30 pb-space-xs">
                  <div className="flex items-center gap-space-xs">
                    <span className={`inline-block w-2 h-2 ${style.dot}`} />
                    <span className={`font-mono text-[11px] font-semibold font-bold ${style.text} uppercase tracking-wider`}>
                      {inc.id} // {inc.title}
                    </span>
                    <span className={`px-1.5 py-0.5 ${style.badgeBg} ${style.badgeText} font-mono text-[9px] font-semibold font-bold uppercase`}>
                      {style.label}
                    </span>
                  </div>
                  <div className="flex items-center gap-space-sm font-mono text-[9px] font-semibold text-outline">
                    <span>{inc.time || 'RECENT'}</span>
                    <span className={`${style.text} font-bold`}>
                      SEVERITY {inc.severity || '—'}/100
                    </span>
                  </div>
                </div>

                {/* Detail Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-space-sm py-1">
                  <div className="flex flex-col">
                    <span className="font-mono text-[9px] font-semibold text-outline uppercase">LOCATION</span>
                    <span className="font-mono text-[13px] text-on-surface font-semibold">{inc.location}</span>
                    <span className="font-mono text-[9px] font-semibold text-outline">{inc.zone || 'Zone 5'}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="font-mono text-[9px] font-semibold text-outline uppercase">UNIT ASSIGNMENT</span>
                    <span className="font-mono text-[13px] font-bold text-primary">{inc.unit || 'AWAITING DISPATCH'}</span>
                    <span className="font-mono text-[9px] font-semibold text-secondary">{inc.eta || '—'}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="font-mono text-[9px] font-semibold text-outline uppercase">THREAT ASSESSMENT</span>
                    <span className="font-mono text-[13px] text-on-surface">{inc.threat || 'Standard Priority'}</span>
                    <span className="font-mono text-[9px] font-semibold text-outline">{inc.threatNote || '—'}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="pt-space-xs flex flex-wrap items-center justify-between gap-space-sm bg-surface-container-lowest/60 p-space-sm">
                  <span className="text-outline font-mono text-[9px] font-semibold">
                    STATUS: {dispatched[inc.id] || inc.dispatched ? 'DISPATCHED' : 'PENDING'}
                  </span>
                  <button
                    onClick={() => handleDispatch(inc.id)}
                    className={`px-space-md py-1.5 font-mono text-[9px] font-semibold uppercase font-bold tracking-wider transition-all flex items-center gap-1 shadow-md ${
                      dispatched[inc.id] || inc.dispatched
                        ? 'bg-surface-container-high text-secondary'
                        : 'bg-primary hover:bg-primary-container text-on-primary'
                    }`}
                  >
                    <span className="material-symbols-outlined text-sm">
                      {dispatched[inc.id] || inc.dispatched ? 'check_circle' : 'emergency'}
                    </span>
                    <span>{dispatched[inc.id] || inc.dispatched ? 'DISPATCHED ✓' : 'DISPATCH UNIT'}</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right: Dispatch Map & Fleet (5 cols) */}
        <div className="xl:col-span-5 flex flex-col gap-space-md">
          {/* Dispatch Map */}
          <div className="bg-surface-container relative flex flex-col overflow-hidden">
            <div className="p-space-sm bg-surface-container-high flex items-center justify-between border-b border-outline-variant/30">
              <div className="flex items-center gap-space-xs">
                <span className="material-symbols-outlined text-base text-secondary">explore</span>
                <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-on-surface font-bold">
                  VECTOR DISPATCH MAP
                </span>
              </div>
              <div className="flex items-center gap-space-xs font-mono text-[9px] font-semibold">
                <span className="text-outline uppercase">GIS GRID: ACTIVE</span>
              </div>
            </div>
            <div className="relative w-full h-80 bg-surface-container-lowest overflow-hidden flex items-center justify-center">
              {/* Grid overlay */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none" xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <pattern id="tac-grid-inc" patternUnits="userSpaceOnUse" width="40" height="40">
                    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(76, 215, 246, 0.1)" strokeWidth="0.5" />
                    <circle cx="20" cy="20" r="0.75" fill="rgba(76, 215, 246, 0.2)" />
                  </pattern>
                </defs>
                <rect fill="url(#tac-grid-inc)" width="100%" height="100%" />
              </svg>

              {/* Informational Center Label */}
              <div className="p-space-md bg-surface-container-high/90 border border-outline-variant flex flex-col items-center gap-1 text-center shadow-lg pointer-events-auto">
                <span className="material-symbols-outlined text-outline text-2xl">near_me_disabled</span>
                <span className="font-mono text-label-sm font-bold text-on-surface uppercase">
                  No Active Map Incidents
                </span>
                <span className="font-mono text-body-sm text-outline">
                  Awaiting CAD 911 incident coordinates
                </span>
              </div>
            </div>
            <div className="p-space-sm bg-surface-container-low border-t border-outline-variant/30 flex items-center justify-between text-on-surface-variant font-mono text-[9px] font-semibold">
              <span className="text-outline">
                Routing optimization engine standby.
              </span>
            </div>
          </div>

          {/* Fleet Allocation Matrix */}
          <div className="bg-surface-container flex flex-col">
            <div className="p-space-sm bg-surface-container-high flex items-center justify-between border-b border-outline-variant/30">
              <div className="flex items-center gap-space-xs">
                <span className="material-symbols-outlined text-base text-primary">groups</span>
                <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-on-surface font-bold">
                  FLEET ALLOCATION MATRIX
                </span>
              </div>
              <span className="font-mono text-[9px] font-semibold text-outline">0 UNITS ACTIVE</span>
            </div>
            <div className="p-space-lg bg-surface-container-lowest text-center font-mono text-label-sm text-outline">
              No emergency units available
            </div>
          </div>

          {/* Live Metrics Strip */}
          <div className="bg-surface-container-low p-space-md flex flex-col gap-space-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-space-xs">
                <span className="material-symbols-outlined text-base text-secondary">monitoring</span>
                <span className="font-grotesk text-[18px] font-semibold uppercase text-on-surface">
                  RESPONSE METRICS
                </span>
              </div>
              <span className="font-mono text-[9px] font-semibold text-outline">CAD ANALYTICS</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-space-xs">
              {[
                { label: 'AVG RESPONSE', value: '—' },
                { label: 'DISPATCHED', value: String(Object.keys(dispatched).length) },
                { label: 'RESOLVED', value: '—' },
                { label: 'PENDING', value: String(filteredIncidents.length) },
              ].map((m) => (
                <div key={m.label} className="bg-surface-container p-space-sm flex flex-col">
                  <span className="font-mono text-[9px] font-semibold text-outline uppercase">{m.label}</span>
                  <span className="font-grotesk text-[22px] font-semibold text-on-surface font-bold">{m.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
