import { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const ZONES = [
  { name: 'B.C. Road Town Center', center: [12.8817, 75.0299], radius: 600, risk: 'LOW', color: '#10B981' },
  { name: 'Bantwal Town', center: [12.8936, 74.9947], radius: 800, risk: 'LOW', color: '#10B981' },
  { name: 'Panemangalore', center: [12.8750, 75.0150], radius: 500, risk: 'MODERATE', color: '#F59E0B' },
  { name: 'Melkar Junction', center: [12.8591, 75.0555], radius: 600, risk: 'MODERATE', color: '#F59E0B' },
  { name: 'NH-75 Highway Stretch', center: [12.8700, 75.0400], radius: 700, risk: 'LOW', color: '#10B981' },
  { name: 'Netravathi River Area', center: [12.8900, 75.0100], radius: 500, risk: 'MODERATE', color: '#F59E0B' },
];

const SERVICES = [
  { name: 'Bantwal Police Station', type: 'police', pos: [12.8936, 74.9947], addr: 'Main Road, Bantwal Town', phone: '(08255) 232 333' },
  { name: 'Bantwal Traffic Police', type: 'police', pos: [12.8591, 75.0555], addr: 'Melkar, Bantwal', phone: '(08255) 234 500' },
  { name: 'Taluk General Hospital', type: 'hospital', pos: [12.8920, 74.9960], addr: 'Main Road, Bantwal 574211', phone: '(08255) 232 230' },
  { name: 'Father Muller Hospital', type: 'hospital', pos: [12.8650, 74.8830], addr: 'Thumbe, Mangalore', phone: '(0824) 223 8000' },
  { name: 'KMC Hospital Mangalore', type: 'hospital', pos: [12.8710, 74.8426], addr: 'Ambedkar Circle, Mangalore', phone: '(0824) 244 5858' },
];

const LANDMARKS = [
  { name: 'B.C. Road Bus Stand', pos: [12.8817, 75.0299] },
  { name: 'Sri Karinjeshwara Temple', pos: [12.8650, 75.0900] },
  { name: 'Netravathi River Bridge', pos: [12.8880, 75.0050] },
  { name: 'Bantwal Town Center', pos: [12.8936, 74.9947] },
  { name: 'Panemangalore Heritage', pos: [12.8750, 75.0150] },
  { name: 'Jamalabad Fort Trail', pos: [12.9100, 75.1200] },
];

const MAP_LAYERS = {
  roadmap: {
    name: 'Google Streets',
    url: 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
    maxZoom: 20,
    attribution: '&copy; Google Maps',
  },
  satellite: {
    name: 'Google Satellite',
    url: 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
    maxZoom: 20,
    attribution: '&copy; Google Maps',
  },
  terrain: {
    name: 'Google Terrain',
    url: 'https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
    subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
    maxZoom: 20,
    attribution: '&copy; Google Maps',
  },
  osm: {
    name: 'CartoDB Dark',
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    subdomains: ['a', 'b', 'c', 'd'],
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap',
  },
};

export default function CrimeMapPage() {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const currentTileLayerRef = useRef(null);
  const userMarkerRef = useRef(null);

  const [activeLayer, setActiveLayer] = useState('roadmap');
  const [userPos, setUserPos] = useState([12.8817, 75.0299]);

  // Track GPS location
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (p) => setUserPos([p.coords.latitude, p.coords.longitude]),
        () => setUserPos([12.8817, 75.0299]),
        { timeout: 5000 }
      );
    }
  }, []);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [12.8817, 75.0299],
      zoom: 14,
      zoomControl: false,
    });

    L.control.zoom({ position: 'topright' }).addTo(map);

    // Initial Google Roadmap Layer
    const layerConfig = MAP_LAYERS.roadmap;
    const gLayer = L.tileLayer(layerConfig.url, {
      attribution: layerConfig.attribution,
      maxZoom: layerConfig.maxZoom,
      subdomains: layerConfig.subdomains,
    }).addTo(map);

    currentTileLayerRef.current = gLayer;

    // Safety Risk Zones
    ZONES.forEach((z) => {
      L.circle(z.center, {
        radius: z.radius,
        color: z.color,
        fillColor: z.color,
        fillOpacity: 0.22,
        weight: 2,
        opacity: 0.8,
      })
        .addTo(map)
        .bindPopup(
          `<div style="font-family:sans-serif;font-size:12px;min-width:160px;padding:2px">` +
          `<strong style="color:#111;font-size:13px">${z.name}</strong><br/>` +
          `<span style="color:${z.color};font-weight:bold;font-size:12px">● ${z.risk} RISK ZONE</span><br/>` +
          `<small style="color:#555">B.C. Road, Bantwal Sector</small></div>`
        );
    });

    // Emergency Services Markers
    SERVICES.forEach((s) => {
      const icon = L.divIcon({
        html: `<div style="background:${s.type === 'police' ? '#2563EB' : '#DC2626'};width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:15px;border:2.5px solid #fff;box-shadow:0 3px 10px rgba(0,0,0,0.5)">${s.type === 'police' ? '🛡' : '🏥'}</div>`,
        className: '',
        iconSize: [30, 30],
        iconAnchor: [15, 15],
      });
      L.marker(s.pos, { icon })
        .addTo(map)
        .bindPopup(
          `<div style="font-family:sans-serif;font-size:12px;padding:2px">` +
          `<strong style="color:#111">${s.name}</strong><br/>` +
          `<small style="color:#666">${s.addr}</small><br/>` +
          `<a href="tel:${s.phone}" style="color:#0284c7;font-weight:bold;text-decoration:none;display:inline-block;margin-top:4px">📞 ${s.phone}</a></div>`
        );
    });

    // Local Landmarks
    LANDMARKS.forEach((lm) => {
      const icon = L.divIcon({
        html: `<div style="background:#D97706;width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.3)">⭐</div>`,
        className: '',
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      });
      L.marker(lm.pos, { icon }).addTo(map).bindPopup(
        `<div style="font-family:sans-serif;font-size:12px"><strong>${lm.name}</strong><br/><small style="color:#666">Bantwal Landmark</small></div>`
      );
    });

    // User Location Marker
    const userIcon = L.divIcon({
      html: `<div style="position:relative"><div style="width:18px;height:18px;background:#0284c7;border-radius:50%;border:3px solid #fff;box-shadow:0 0 12px rgba(2,132,199,0.8)"></div><div style="position:absolute;top:-5px;left:-5px;width:28px;height:28px;border-radius:50%;border:2px solid rgba(2,132,199,0.5);animation:ping 1.5s cubic-bezier(0,0,0.2,1) infinite"></div></div>`,
      className: '',
      iconSize: [18, 18],
      iconAnchor: [9, 9],
    });
    userMarkerRef.current = L.marker([12.8817, 75.0299], { icon: userIcon, zIndexOffset: 1000 })
      .addTo(map)
      .bindPopup('<strong style="font-family:sans-serif">📍 You are here (B.C. Road)</strong>');

    mapInstanceRef.current = map;

    // Invalidate size to guarantee rendering even if mounted inside flex container
    const timer1 = setTimeout(() => map.invalidateSize(), 100);
    const timer2 = setTimeout(() => map.invalidateSize(), 500);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update user marker position when GPS changes
  useEffect(() => {
    if (userMarkerRef.current && userPos) {
      userMarkerRef.current.setLatLng(userPos);
    }
  }, [userPos]);

  // Switch Layer
  const switchLayer = (layerKey) => {
    if (!mapInstanceRef.current) return;

    if (currentTileLayerRef.current) {
      mapInstanceRef.current.removeLayer(currentTileLayerRef.current);
    }

    const config = MAP_LAYERS[layerKey] || MAP_LAYERS.roadmap;
    const newLayer = L.tileLayer(config.url, {
      attribution: config.attribution,
      maxZoom: config.maxZoom,
      subdomains: config.subdomains,
    }).addTo(mapInstanceRef.current);

    currentTileLayerRef.current = newLayer;
    setActiveLayer(layerKey);
  };

  const locateUser = () => {
    if (mapInstanceRef.current && userPos) {
      mapInstanceRef.current.flyTo(userPos, 15, { duration: 1 });
    }
  };

  return (
    <div className="flex flex-col h-full w-full relative select-none flex-1 min-h-0">
      {/* Top Header */}
      <div className="h-14 bg-surface-container-low flex items-center justify-between px-4 border-b border-outline-variant/20 shrink-0 z-20">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-secondary/15 flex items-center justify-center">
            <span className="material-symbols-outlined text-secondary text-lg">explore</span>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <h1 className="text-sm font-grotesk font-bold text-on-surface uppercase tracking-wider">
                Google Maps
              </h1>
              <span className="text-[9px] px-1.5 py-0.2 bg-secondary/20 text-secondary font-mono font-bold rounded">
                LIVE
              </span>
            </div>
            <p className="text-[9px] text-outline">B.C. Road, Bantwal, Karnataka 574219</p>
          </div>
        </div>

        {/* Locate Me */}
        <button
          onClick={locateUser}
          title="Center on my location"
          className="w-9 h-9 rounded-xl bg-surface-container flex items-center justify-center hover:bg-surface-container-high text-secondary transition-colors"
        >
          <span className="material-symbols-outlined text-lg">my_location</span>
        </button>
      </div>

      {/* Map Style Selector Bar */}
      <div className="bg-surface-container px-3 py-1.5 flex items-center justify-between text-xs font-mono border-b border-outline-variant/20 z-10 shrink-0">
        <div className="flex items-center gap-1 text-[10px] text-outline uppercase font-semibold">
          <span className="material-symbols-outlined text-xs text-secondary">layers</span>
          <span>Layer:</span>
        </div>
        <div className="flex items-center gap-1">
          {[
            { id: 'roadmap', label: 'Streets' },
            { id: 'satellite', label: 'Satellite' },
            { id: 'terrain', label: 'Terrain' },
            { id: 'osm', label: 'Dark' },
          ].map((style) => (
            <button
              key={style.id}
              onClick={() => switchLayer(style.id)}
              className={`px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase transition-all ${
                activeLayer === style.id
                  ? 'bg-secondary text-on-secondary shadow-md'
                  : 'bg-surface-container-high text-outline hover:text-on-surface'
              }`}
            >
              {style.label}
            </button>
          ))}
        </div>
      </div>

      {/* Map Container - fills exact available space without overflowing into BottomNav */}
      <div className="flex-1 w-full relative min-h-0 overflow-hidden">
        <div
          ref={mapContainerRef}
          className="absolute inset-0 w-full h-full"
          style={{ background: '#0d1322' }}
        />

        {/* Legend Overlay */}
        <div className="absolute bottom-3 left-3 z-[1000] bg-surface-container/95 backdrop-blur-md rounded-xl p-3 border border-outline-variant/30 shadow-2xl">
          <p className="text-[9px] text-outline font-bold uppercase mb-1.5 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse" />
            Bantwal Safety Zones
          </p>
          <div className="space-y-1">
            {[
              { color: '#10B981', label: 'Low Risk Zone' },
              { color: '#F59E0B', label: 'Moderate Risk Zone' },
            ].map((l) => (
              <div key={l.label} className="flex items-center gap-2">
                <span style={{ background: l.color }} className="w-2.5 h-2.5 rounded-full inline-block" />
                <span className="text-[10px] text-on-surface font-medium">{l.label}</span>
              </div>
            ))}
            <div className="border-t border-outline-variant/20 mt-1.5 pt-1.5 space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs">🛡</span>
                <span className="text-[10px] text-on-surface">Police Station</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs">🏥</span>
                <span className="text-[10px] text-on-surface">Hospital</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
