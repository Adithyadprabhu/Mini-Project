import { useState, useEffect, useCallback } from 'react';
import { fetchCrimeRiskPrediction } from '../services/api';

const TIME_WINDOWS = [
  { value: 'current', label: 'CURRENT LIVE WINDOW' },
  { value: 'tonight', label: 'TONIGHT PEAK HOURS' },
  { value: 'event', label: 'EVENT DENSITY WINDOW' },
  { value: 'custom', label: 'CUSTOM ML INFERENCE QUERY' },
];

const LOCATIONS = [
  { value: 'five-points', label: 'FIVE POINTS / WOODRUFF PARK (ZONE 5)' },
  { value: 'centennial', label: 'CENTENNIAL OLYMPIC PARK' },
  { value: 'midtown', label: 'PIEDMONT PARK / MIDTOWN' },
  { value: 'battery', label: 'THE BATTERY / TRUIST PARK' },
  { value: 'west-end', label: 'WEST END TRANSIT CORRIDOR' },
];

export default function CrimeRiskMap() {
  const [timeWindow, setTimeWindow] = useState('current');
  const [location, setLocation] = useState('five-points');
  const [layers, setLayers] = useState({
    heatmap: true,
    incidents: true,
    tourists: true,
    units: true,
  });
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(true);
  const [mlRunning, setMlRunning] = useState(false);
  const [toast, setToast] = useState(null);

  const showToast = useCallback((title, body, icon = 'info') => {
    setToast({ title, body, icon });
    setTimeout(() => setToast(null), 4200);
  }, []);

  const toggleLayer = (layer) => {
    setLayers((prev) => ({ ...prev, [layer]: !prev[layer] }));
  };

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        setLoading(true);
        const res = await fetchCrimeRiskPrediction({ timeWindow, location });
        if (!cancelled) {
          setPrediction(res?.prediction || null);
        }
      } catch {
        if (!cancelled) {
          setPrediction(null);
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
  }, [timeWindow, location]);

  const runML = async () => {
    setMlRunning(true);
    try {
      const res = await fetchCrimeRiskPrediction({ timeWindow, location });
      if (res?.prediction) {
        setPrediction(res.prediction);
        showToast('ML INFERENCE RECEIVED', 'Updated spatial risk prediction from backend service.', 'neurology');
      } else {
        setPrediction(null);
        showToast('PREDICTION SERVICE UNAVAILABLE', 'Backend ML prediction service is not connected.', 'warning');
      }
    } catch {
      setPrediction(null);
      showToast('CONNECTION ERROR', 'Failed to communicate with prediction service.', 'error');
    } finally {
      setMlRunning(false);
    }
  };

  const currentLocationLabel = LOCATIONS.find((l) => l.value === location)?.label || location.toUpperCase();

  return (
    <div className="flex flex-col w-full text-on-surface select-none pb-12">
      {/* Sub-header Breadcrumb & Operational Alert Tape */}
      <div className="w-full bg-surface-container-lowest px-space-md py-2 flex flex-wrap items-center justify-between gap-y-2">
        <div className="flex items-center gap-space-sm font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold">
          <span className="text-outline uppercase tracking-widest">GRID-REF:</span>
          <span className="text-primary font-bold">ATL-33.7490°N / 84.3880°W</span>
          <span className="text-outline-variant">|</span>
          <span className="text-outline uppercase tracking-widest">SECTOR:</span>
          <span className="text-secondary font-bold">ATLANTA METRO GIS</span>
          <span className="text-outline-variant">|</span>
          <span className="text-outline uppercase tracking-widest">MODEL STATUS:</span>
          <span className="flex items-center gap-1 text-outline">
            <span className={`w-1.5 h-1.5 ${prediction ? 'bg-secondary animate-pulse' : 'bg-outline'}`} />
            {prediction ? 'MODEL SYNCHRONIZED' : 'MODEL STANDBY'}
          </span>
        </div>
        <div className="flex items-center gap-space-sm font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold">
          <span className="bg-surface-variant px-space-xs py-0.5 text-on-surface-variant uppercase tracking-wider">
            CARTOGRAPHIC BOUNDS: ZONE 5
          </span>
        </div>
      </div>

      {/* Predictive Query & Simulation Control Bar */}
      <section className="p-space-md bg-surface-container-low/90 backdrop-blur-md">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-md items-center">
          {/* Temporal Simulation Window */}
          <div className="lg:col-span-4 flex flex-col gap-1">
            <label className="font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold uppercase tracking-widest text-outline flex items-center justify-between">
              <span>TEMPORAL QUERY WINDOW</span>
              <span className="text-secondary">UTC-5 EST</span>
            </label>
            <div className="flex items-center bg-surface-container-lowest px-space-sm py-1.5 gap-space-xs">
              <span className="material-symbols-outlined text-secondary text-base">schedule</span>
              <select
                className="bg-transparent font-mono text-[11px] leading-[14px] tracking-[0.1em] font-semibold text-on-surface uppercase tracking-wider w-full focus:outline-none cursor-pointer"
                value={timeWindow}
                onChange={(e) => {
                  setTimeWindow(e.target.value);
                  showToast('TEMPORAL WINDOW UPDATED', `Query window set to: ${e.target.options[e.target.selectedIndex].text}`, 'schedule');
                }}
              >
                {TIME_WINDOWS.map((tw) => (
                  <option key={tw.value} value={tw.value} className="bg-surface-container-highest text-on-surface">
                    {tw.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Spatial Target Sector */}
          <div className="lg:col-span-4 flex flex-col gap-1">
            <label className="font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold uppercase tracking-widest text-outline flex items-center justify-between">
              <span>SPATIAL TARGET SECTOR</span>
              <span className="text-primary">APD METRO SECTOR</span>
            </label>
            <div className="flex items-center bg-surface-container-lowest px-space-sm py-1.5 gap-space-xs">
              <span className="material-symbols-outlined text-primary text-base">my_location</span>
              <select
                className="bg-transparent font-mono text-[11px] leading-[14px] tracking-[0.1em] font-semibold text-on-surface uppercase tracking-wider w-full focus:outline-none cursor-pointer"
                value={location}
                onChange={(e) => {
                  setLocation(e.target.value);
                  showToast('MAP RETARGETED', `Query targeted to: ${e.target.options[e.target.selectedIndex].text}`, 'center_focus_strong');
                }}
              >
                {LOCATIONS.map((loc) => (
                  <option key={loc.value} value={loc.value} className="bg-surface-container-highest text-on-surface">
                    {loc.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* ML Trigger & Model Badge */}
          <div className="lg:col-span-4 flex flex-col justify-end gap-1">
            <div className="flex items-center justify-between font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold text-outline">
              <span>AI PREDICTION INFERENCE</span>
              <span className="text-outline tracking-widest">
                {prediction ? 'RESULTS ACTIVE' : 'AWAITING RUN'}
              </span>
            </div>
            <div className="flex items-center gap-space-xs">
              <button
                onClick={runML}
                disabled={mlRunning}
                className="flex-1 bg-primary text-on-primary font-mono text-[11px] leading-[14px] tracking-[0.1em] font-bold uppercase tracking-wider py-2 px-space-md flex items-center justify-center gap-space-xs hover:bg-secondary-fixed-dim transition-all active:scale-[0.99]"
              >
                <span className={`material-symbols-outlined text-base ${mlRunning ? 'animate-spin' : ''}`}>
                  neurology
                </span>
                <span>{mlRunning ? 'QUERYING ML SERVICE...' : 'RUN PREDICTIVE ML'}</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Main Tactical Workspace: Grid Layout */}
      <div className="p-space-md grid grid-cols-1 xl:grid-cols-12 gap-space-md">
        {/* Column 1-8: Tactical Map Visualizer Canvas */}
        <div className="xl:col-span-8 flex flex-col gap-space-md">
          {/* Interactive Tactical Map Screen */}
          <div className="relative w-full h-[620px] bg-surface-container-lowest overflow-hidden flex flex-col shadow-2xl">
            {/* HUD Vertex Crosshairs */}
            <div className="absolute top-2 left-2 text-secondary font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold pointer-events-none z-30">+ NW 33.762</div>
            <div className="absolute top-2 right-2 text-secondary font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold pointer-events-none z-30">+ NE 84.372</div>
            <div className="absolute bottom-2 left-2 text-secondary font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold pointer-events-none z-30">+ SW 33.738</div>
            <div className="absolute bottom-2 right-2 text-secondary font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold pointer-events-none z-30">+ SE 84.399</div>

            {/* Tactical Canvas Overlay / Scanline Grid */}
            <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px] opacity-35 pointer-events-none z-10" />
            <div className="absolute inset-0 bg-gradient-to-b from-surface/50 via-transparent to-surface/80 pointer-events-none z-10" />

            {/* Interactive Layers / Controls Bar (Floating Top-Left) */}
            <div className="absolute top-4 left-4 z-30 flex flex-wrap items-center gap-1.5 bg-surface-container-low/95 backdrop-blur-md p-1.5 shadow-lg max-w-[92%]">
              <span className="font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold text-outline px-1.5 uppercase tracking-widest">LAYERS:</span>
              <button
                onClick={() => toggleLayer('heatmap')}
                className={`px-2 py-1 font-mono text-[9px] leading-[12px] tracking-[0.12em] font-bold flex items-center gap-1 transition-colors ${
                  layers.heatmap ? 'bg-surface-container-high text-secondary' : 'opacity-50 bg-surface-variant text-outline'
                }`}
              >
                <span className="w-2 h-2 bg-secondary" />
                RISK HEATMAP
              </button>
              <button
                onClick={() => toggleLayer('incidents')}
                className={`px-2 py-1 font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold flex items-center gap-1 transition-colors ${
                  layers.incidents ? 'bg-surface-container-high text-on-surface' : 'opacity-50 bg-surface-variant text-outline'
                }`}
              >
                <span className="material-symbols-outlined text-xs text-error">warning</span>
                INCIDENTS
              </button>
              <button
                onClick={() => toggleLayer('tourists')}
                className={`px-2 py-1 font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold flex items-center gap-1 transition-colors ${
                  layers.tourists ? 'bg-surface-container-high text-primary' : 'opacity-50 bg-surface-variant text-outline'
                }`}
              >
                <span className="material-symbols-outlined text-xs">group</span>
                TOURIST ZONES
              </button>
              <button
                onClick={() => toggleLayer('units')}
                className={`px-2 py-1 font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold flex items-center gap-1 transition-colors ${
                  layers.units ? 'bg-surface-container-high text-on-surface-variant' : 'opacity-50 bg-surface-variant text-outline'
                }`}
              >
                <span className="material-symbols-outlined text-xs text-secondary-fixed">local_police</span>
                PATROL UNITS
              </button>
            </div>

            {/* Tactical HUD Camera & Viewport Tools (Floating Top-Right) */}
            <div className="absolute top-4 right-4 z-30 flex items-center gap-1 bg-surface-container-low/95 backdrop-blur-md p-1">
              <button className="w-7 h-7 flex items-center justify-center bg-surface-container hover:bg-surface-container-high text-secondary" title="Reset View">
                <span className="material-symbols-outlined text-sm">explore</span>
              </button>
            </div>

            {/* SVG Tactical GIS Vector Canvas */}
            <div className="relative w-full h-full">
              <svg className="w-full h-full object-cover" fill="none" viewBox="0 0 1000 680" xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <pattern id="tacticalGrid" width="40" height="40" patternUnits="userSpaceOnUse">
                    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#242a3a" strokeWidth="0.75" />
                  </pattern>
                </defs>

                {/* Base Grid & Dark Territory Fill */}
                <rect fill="#090e1a" width="1000" height="680" />
                <rect fill="url(#tacticalGrid)" width="1000" height="680" opacity="0.8" />

                {/* Actual Atlanta Geographic Road & Transit Network */}
                <path d="M 680,120 Q 730,150 720,210 Q 710,250 760,290" fill="none" stroke="#003640" strokeWidth="6" opacity="0.6" />

                {/* Major Arterials: I-75 / I-85 Connector */}
                <path d="M 380,0 Q 420,240 450,330 T 560,680" fill="none" stroke="#2f3445" strokeLinecap="round" strokeWidth="12" />
                <path d="M 380,0 Q 420,240 450,330 T 560,680" fill="none" stroke="#4cd7f6" strokeDasharray="6,6" strokeWidth="1.5" opacity="0.4" />
                <text fill="#8c909f" fontFamily="JetBrains Mono" fontSize="10" transform="rotate(72 395 160)" x="395" y="160">I-75/85 DOWNTOWN CONNECTOR</text>

                {/* North Ave NW */}
                <line stroke="#242a3a" strokeWidth="3" x1="80" x2="920" y1="180" y2="180" />
                <text fill="#8c909f" fontFamily="JetBrains Mono" fontSize="9" x="110" y="172">NORTH AVE NW (TECH CORRIDOR)</text>

                {/* Peachtree Street */}
                <path d="M 620,30 L 490,260 L 460,420 L 430,650" fill="none" stroke="#33394a" strokeWidth="4" />
                <text fill="#adc6ff" fontFamily="JetBrains Mono" fontSize="10" transform="rotate(60 545 150)" x="545" y="150">PEACHTREE ST NE</text>

                {/* Martin Luther King Jr Dr */}
                <line stroke="#242a3a" strokeWidth="3" x1="90" x2="880" y1="520" y2="520" />
                <text fill="#8c909f" fontFamily="JetBrains Mono" fontSize="9" x="120" y="512">MLK JR DR SW / STATE CAPITOL</text>

                {/* Marietta St NW */}
                <line stroke="#242a3a" strokeWidth="2" x1="160" x2="520" y1="280" y2="440" />
                <text fill="#8c909f" fontFamily="JetBrains Mono" fontSize="9" transform="rotate(24 210 325)" x="210" y="325">MARIETTA ST NW</text>

                {/* Ponce De Leon Ave */}
                <line stroke="#242a3a" strokeWidth="2" x1="580" x2="960" y1="120" y2="120" />
                <text fill="#8c909f" fontFamily="JetBrains Mono" fontSize="9" x="680" y="112">PONCE DE LEON AVE NE</text>
              </svg>

              {/* Informational Center Overlay */}
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none p-4">
                <div className="bg-surface-container-high/90 border border-outline-variant p-space-md flex flex-col items-center gap-1 shadow-2xl max-w-md text-center pointer-events-auto">
                  <span className="material-symbols-outlined text-outline text-3xl">map</span>
                  <span className="font-mono text-label-sm font-bold text-on-surface uppercase">
                    ATLANTA GEOGRAPHIC RISK MESH
                  </span>
                  <p className="font-mono text-body-sm text-outline">
                    {loading
                      ? 'Connecting to spatial inference pipeline...'
                      : prediction
                      ? 'Spatial prediction overlay loaded from connected ML backend.'
                      : 'Prediction service unavailable. Base cartography displayed without simulated data.'}
                  </p>
                </div>
              </div>
            </div>

            {/* Floating Tactical Map Bottom Legend & Telemetry Overlay */}
            <div className="absolute bottom-3 left-3 right-3 z-30 flex flex-wrap items-center justify-between gap-2 bg-surface-container-lowest/90 backdrop-blur-md px-space-md py-2">
              <div className="flex items-center flex-wrap gap-space-md font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold">
                <span className="text-outline uppercase tracking-wider">RISK THRESHOLDS:</span>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 bg-emerald-500" />
                  <span className="text-on-surface">LOW (&lt;25%)</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 bg-yellow-500" />
                  <span className="text-on-surface">MED (25-50%)</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 bg-amber-600" />
                  <span className="text-on-surface">HIGH (50-75%)</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 bg-tertiary-container" />
                  <span className="text-error font-bold">CRITICAL (&gt;75%)</span>
                </div>
              </div>
              <div className="font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold text-outline">
                <span>GEOGRAPHIC REF: EPSG:2240 ATLANTA</span>
              </div>
            </div>
          </div>

          {/* Real-time Multi-Zone Comparison Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-space-sm">
            {['DOWNTOWN', 'MIDTOWN', 'OLD FOURTH WARD', 'BUCKHEAD'].map((name) => (
              <div key={name} className="bg-surface-container p-space-sm flex flex-col gap-1">
                <div className="flex items-center justify-between text-outline font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold">
                  <span>{name}</span>
                  <span className="text-outline font-bold">
                    {prediction?.zones?.[name]?.risk !== undefined ? `${prediction.zones[name].risk}%` : '—'}
                  </span>
                </div>
                <div className="font-grotesk text-[14px] leading-[18px] text-outline font-semibold">
                  {prediction?.zones?.[name]?.level || 'No prediction data'}
                </div>
                <div className="w-full bg-surface-variant h-1 overflow-hidden">
                  <div
                    className="bg-primary h-full"
                    style={{ width: `${prediction?.zones?.[name]?.risk || 0}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Column 9-12: Spatial Risk Prediction Inspector Panel */}
        <div className="xl:col-span-4 flex flex-col gap-space-md">
          {/* Spatial Risk Prediction Inspector Card */}
          <div className="bg-surface-container-low p-space-md flex flex-col gap-space-md shadow-xl relative overflow-hidden">
            {/* Header Classification Tag */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-space-xs font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold">
                <span className="w-2 h-2 bg-primary" />
                <span className="text-primary font-bold tracking-widest uppercase">SPATIAL TARGET AUDIT</span>
              </div>
              <span className="font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold px-space-xs py-0.5 bg-surface-container-high text-outline">
                {prediction ? 'ANALYZED' : 'AWAITING ML'}
              </span>
            </div>

            {/* Selected Location Details Header */}
            <div className="flex flex-col gap-0.5">
              <span className="font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold text-outline uppercase tracking-widest">
                FOCAL INSPECTOR
              </span>
              <h2 className="font-grotesk text-[20px] leading-[26px] font-semibold text-on-surface uppercase tracking-tight">
                {currentLocationLabel}
              </h2>
            </div>

            {/* Radial Risk Gauge & Summary Metric */}
            <div className="bg-surface-container-lowest p-space-md flex items-center justify-between gap-space-md">
              <div className="flex flex-col gap-1">
                <span className="font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold text-outline uppercase tracking-wider">
                  PREDICTED RISK INDEX
                </span>
                <div className="flex items-baseline gap-1">
                  <span className="font-grotesk text-[40px] leading-[48px] font-bold text-on-surface">
                    {prediction?.riskIndex !== undefined ? `${prediction.riskIndex}%` : '—'}
                  </span>
                  <span className="font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold text-outline uppercase font-bold tracking-wider">
                    {prediction?.riskLevel || 'NO DATA'}
                  </span>
                </div>
                <p className="font-mono text-[11px] leading-[16px] tracking-[0.02em] text-on-surface-variant max-w-[200px] leading-tight">
                  {prediction
                    ? `Confidence interval: ${prediction.confidence}%`
                    : 'Prediction service unavailable. Connect ML model backend for genuine risk outputs.'}
                </p>
              </div>

              {/* Gauge Placeholder */}
              <div className="relative w-24 h-24 flex items-center justify-center shrink-0">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="40" fill="transparent" stroke="#242a3a" strokeWidth="8" />
                  {prediction?.riskIndex !== undefined && (
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      fill="transparent"
                      stroke="#4cd7f6"
                      strokeWidth="8"
                      strokeDasharray="251.2"
                      strokeDashoffset={251.2 - (251.2 * prediction.riskIndex) / 100}
                    />
                  )}
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                  <span className="material-symbols-outlined text-outline text-lg">analytics</span>
                </div>
              </div>
            </div>

            {/* Contributing Factors AI Breakdown */}
            <div className="flex flex-col gap-space-xs">
              <div className="flex items-center justify-between font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold text-outline uppercase tracking-wider pb-1">
                <span>CONTRIBUTING FACTORS BREAKDOWN</span>
                <span className="text-outline">ML WEIGHT</span>
              </div>
              <div className="p-space-md bg-surface-container text-center font-mono text-label-sm text-outline">
                Prediction service unavailable — No contributing factors to display
              </div>
            </div>

            {/* Recommended Preventative Action Dispatch Box */}
            <div className="bg-surface-container-highest p-space-md flex flex-col gap-space-xs">
              <div className="flex items-center justify-between font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold">
                <span className="text-secondary font-bold uppercase tracking-wider flex items-center gap-1">
                  <span className="material-symbols-outlined text-sm">auto_mode</span>
                  RECOMMENDATION DIRECTIVE
                </span>
              </div>
              <p className="font-mono text-[11px] leading-[16px] text-on-surface-variant">
                {prediction?.recommendation || 'Awaiting ML risk predictions to generate preventative guidance.'}
              </p>
            </div>
          </div>

          {/* Field Sector Feed Micro-Card */}
          <div className="bg-surface-container-low p-space-md flex flex-col gap-space-xs">
            <div className="flex items-center justify-between font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold text-outline">
              <span>SURVEILLANCE CAM FEED</span>
              <span className="text-outline uppercase">OFFLINE</span>
            </div>
            <div className="relative w-full h-32 bg-surface-container-lowest flex items-center justify-center text-center p-4">
              <div className="flex flex-col items-center gap-1 text-outline">
                <span className="material-symbols-outlined text-2xl">videocam_off</span>
                <span className="font-mono text-label-sm">No camera feed connected</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Full-Width Bottom Intelligence Module */}
      <section className="p-space-md">
        <div className="bg-surface-container-low p-space-md flex flex-col gap-space-md shadow-xl">
          {/* Chart Header Controls */}
          <div className="flex flex-wrap items-center justify-between gap-y-2">
            <div className="flex flex-col">
              <div className="flex items-center gap-space-xs font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold text-secondary">
                <span className="material-symbols-outlined text-sm">ssid_chart</span>
                <span className="uppercase tracking-widest font-bold">TEMPORAL PREDICTIVE TRAJECTORY</span>
              </div>
              <h3 className="font-grotesk text-[18px] leading-[24px] tracking-[0.02em] font-semibold text-on-surface uppercase tracking-tight">
                CRIME BASELINE VS. MODEL FORECAST
              </h3>
            </div>
          </div>

          {/* Chart Canvas */}
          <div className="w-full h-48 bg-surface-container-lowest p-space-sm relative flex items-center justify-center text-center">
            <div className="flex flex-col items-center gap-2 text-outline">
              <span className="material-symbols-outlined text-3xl">show_chart</span>
              <span className="font-mono text-label-sm font-semibold uppercase">
                No forecast data available
              </span>
              <span className="font-mono text-body-sm max-w-sm">
                Connect actual Atlanta historical crime datasets and forecasting pipeline to visualize temporal risk curves.
              </span>
            </div>
          </div>

          {/* Actionable Insights Footer Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-space-sm pt-1">
            <div className="p-space-sm bg-surface-container flex items-center gap-space-sm">
              <span className="material-symbols-outlined text-outline text-2xl">alarm_on</span>
              <div className="flex flex-col">
                <span className="font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold text-outline uppercase">
                  PREDICTED RISK CREST
                </span>
                <span className="font-grotesk text-[16px] leading-[22px] font-semibold text-outline">
                  —
                </span>
              </div>
            </div>
            <div className="p-space-sm bg-surface-container flex items-center gap-space-sm">
              <span className="material-symbols-outlined text-outline text-2xl">groups</span>
              <div className="flex flex-col">
                <span className="font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold text-outline uppercase">
                  PROJECTED VISITOR EXPOSURE
                </span>
                <span className="font-grotesk text-[16px] leading-[22px] font-semibold text-outline">
                  —
                </span>
              </div>
            </div>
            <div className="p-space-sm bg-surface-container flex items-center gap-space-sm">
              <span className="material-symbols-outlined text-outline text-2xl">shield</span>
              <div className="flex flex-col">
                <span className="font-mono text-[9px] leading-[12px] tracking-[0.12em] font-semibold text-outline uppercase">
                  OPTIMAL PATROL WINDOW
                </span>
                <span className="font-grotesk text-[16px] leading-[22px] font-semibold text-outline">
                  —
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Toast Notification */}
      <div
        className={`fixed bottom-6 right-6 z-50 transition-all duration-300 bg-surface-container-high p-space-md max-w-md shadow-2xl flex items-start gap-space-sm ${
          toast ? 'translate-y-0 opacity-100' : 'translate-y-24 opacity-0 pointer-events-none'
        }`}
      >
        <span className="material-symbols-outlined text-secondary text-2xl">{toast?.icon || 'check_circle'}</span>
        <div className="flex flex-col">
          <span className="font-mono text-[9px] leading-[12px] tracking-[0.12em] font-bold uppercase tracking-wider text-secondary">
            {toast?.title}
          </span>
          <p className="font-mono text-[11px] leading-[16px] tracking-[0.02em] text-on-surface">{toast?.body}</p>
        </div>
      </div>
    </div>
  );
}
