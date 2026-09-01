import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { partnerApi, NearestPartnerResponse } from '../api/partnerApi';
import {
  MapPin,
  Navigation,
  Loader2,
  Building,
  Building2,
  Phone,
  Mail,
  Globe,
  AlertCircle,
  Search,
  Info,
  ExternalLink,
  ShieldCheck,
  CheckCircle,
  ZoomIn,
  ZoomOut,
  Lock,
  Unlock,
  RotateCcw,
  Compass
} from 'lucide-react';

interface MapLocatorProps {
  onSelectPartner?: (partnerId: string) => void;
  selectedPartnerId?: string | null;
  schemeId?: string;
  schemeName?: string;
  loanCategory?: string;
}

interface UserLocation {
  lat: number;
  lng: number;
}

interface ActiveOrigin {
  lat: number;
  lng: number;
  label: string;
  isGps: boolean;
}

interface OSRMRouteInfo {
  coordinates: [number, number][]; // Array of [lat, lng] pairs
  distanceKm: number;
  durationMins: number;
}

// In-memory cache for Nominatim PIN/query searches
const geocodeCache = new Map<string, { lat: number; lng: number; displayName: string }>();

// Strict validation helper for coordinate pairs
export const isValidCoord = (lat: any, lng: any): boolean => {
  return (
    typeof lat === 'number' &&
    typeof lng === 'number' &&
    Number.isFinite(lat) &&
    Number.isFinite(lng) &&
    lat >= -90 &&
    lat <= 90 &&
    lng >= -180 &&
    lng <= 180
  );
};

// Haversine distance calculation in kilometers
export const calculateHaversineKm = (lat1: number, lon1: number, lat2: number, lon2: number): number => {
  if (!isValidCoord(lat1, lon1) || !isValidCoord(lat2, lon2)) return 0;
  const R = 6371; // Earth radius in km
  const dLat = (lat2 - lat1) * (Math.PI / 180);
  const dLon = (lon2 - lon1) * (Math.PI / 180);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c * 10) / 10;
};

// Helper to generate custom colored Leaflet DivIcon pins
const createPartnerIcon = (type: string, category: string = '', index: number, isSelected: boolean) => {
  let color = '#4f46e5'; // default indigo
  if (category === 'AUTHORIZED_SCHEME_PARTNER') color = '#2563eb'; // blue
  else if (category === 'IMPLEMENTING_ASSISTANCE_CENTRE') color = '#059669'; // emerald
  else if (category === 'NEARBY_FINANCIAL_SERVICE_POINT') color = '#d97706'; // amber
  else if (type === 'PSB') color = '#2563eb'; // blue
  else if (type === 'RRB') color = '#16a34a'; // green
  else if (type === 'NBFC_MFI') color = '#9333ea'; // purple
  else if (type === 'SCA') color = '#ea580c'; // orange
  else if (type === 'COOPERATIVE_BANK' || type === 'COOPERATIVE_SOCIETY') color = '#0d9488'; // teal
  else color = '#475569'; // slate

  const scale = isSelected ? 1.25 : 1.0;
  const size = Math.round(32 * scale);

  return L.divIcon({
    className: 'custom-partner-pin',
    html: `
      <div style="
        background-color: ${color};
        width: ${size}px;
        height: ${size}px;
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        display: flex;
        align-items: center;
        justify-content: center;
        border: 2px solid #ffffff;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.35);
        cursor: pointer;
        transition: transform 0.2s ease;
      ">
        <span style="
          transform: rotate(45deg);
          color: #ffffff;
          font-weight: 800;
          font-size: ${isSelected ? '13px' : '11px'};
          font-family: system-ui, sans-serif;
        ">${index}</span>
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size],
    popupAnchor: [0, -size],
  });
};

// User Location Pulse Icon (GPS)
const userLocationIcon = L.divIcon({
  className: 'custom-user-pin',
  html: `
    <div style="position: relative; width: 24px; height: 24px;">
      <div style="
        position: absolute;
        width: 24px;
        height: 24px;
        background-color: rgba(234, 88, 12, 0.4);
        border-radius: 50%;
        animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
      "></div>
      <div style="
        position: absolute;
        width: 14px;
        height: 14px;
        top: 5px;
        left: 5px;
        background-color: #ea580c;
        border: 2px solid #ffffff;
        border-radius: 50%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.4);
      "></div>
    </div>
  `,
  iconSize: [24, 24],
  iconAnchor: [12, 12],
  popupAnchor: [0, -12],
});

// Search Location Pin Icon (Non-GPS)
const searchLocationIcon = L.divIcon({
  className: 'custom-search-pin',
  html: `
    <div style="
      background-color: #334155;
      width: 28px;
      height: 28px;
      border-radius: 50% 50% 50% 0;
      transform: rotate(-45deg);
      display: flex;
      align-items: center;
      justify-content: center;
      border: 2px solid #ffffff;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.35);
    ">
      <span style="transform: rotate(45deg); color: #ffffff; font-size: 11px; font-weight: bold;">📍</span>
    </div>
  `,
  iconSize: [28, 28],
  iconAnchor: [14, 28],
  popupAnchor: [0, -28],
});

// ─────────────────────────────────────────────────────────────
// Map Interaction & Gesture Controller
// ─────────────────────────────────────────────────────────────
const MapInteractionHandler: React.FC<{
  isScrollZoomUnlocked: boolean;
  onShowScrollHint: () => void;
  recenterTrigger: number;
  origin: ActiveOrigin | null;
  partners: NearestPartnerResponse[];
  routeCoords: [number, number][];
}> = ({
  isScrollZoomUnlocked,
  onShowScrollHint,
  recenterTrigger,
  origin,
  partners,
  routeCoords,
}) => {
  const map = useMap();

  // Manage scroll-wheel zoom permission safely
  useEffect(() => {
    if (isScrollZoomUnlocked) {
      map.scrollWheelZoom.enable();
    } else {
      map.scrollWheelZoom.disable();
    }
  }, [isScrollZoomUnlocked, map]);

  // Intercept wheel events to allow normal page scrolling + Ctrl+Wheel zoom support
  useEffect(() => {
    const container = map.getContainer();

    const handleWheel = (e: WheelEvent) => {
      if (e.ctrlKey || e.metaKey) {
        // User is holding Ctrl or Cmd: allow map zooming
        if (!map.scrollWheelZoom.enabled()) {
          map.scrollWheelZoom.enable();
        }
      } else {
        // User is normal scrolling: let page scroll freely, and show hint
        if (!isScrollZoomUnlocked) {
          if (map.scrollWheelZoom.enabled()) {
            map.scrollWheelZoom.disable();
          }
          onShowScrollHint();
        }
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.key === 'Control' || e.key === 'Meta') {
        if (!isScrollZoomUnlocked && map.scrollWheelZoom.enabled()) {
          map.scrollWheelZoom.disable();
        }
      }
    };

    container.addEventListener('wheel', handleWheel, { passive: true });
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      container.removeEventListener('wheel', handleWheel);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [map, isScrollZoomUnlocked, onShowScrollHint]);

  // Handle defensive bounds recalculation & animations
  const fitMapBounds = useCallback(() => {
    try {
      // 1. If valid OSRM driving route exists with 2+ valid points, fit to route
      if (Array.isArray(routeCoords) && routeCoords.length >= 2) {
        const validRoute = routeCoords.filter(
          (pt) => Array.isArray(pt) && pt.length >= 2 && isValidCoord(pt[0], pt[1])
        );
        if (validRoute.length >= 2) {
          const bounds = L.latLngBounds(validRoute.map((pt) => [pt[0], pt[1]]));
          if (bounds.isValid()) {
            map.fitBounds(bounds, { padding: [40, 40], maxZoom: 13 });
            return;
          }
        }
      }

      // 2. Collect all valid geographic points (origin + partners)
      const validPoints: [number, number][] = [];
      if (origin && isValidCoord(origin.lat, origin.lng)) {
        validPoints.push([origin.lat, origin.lng]);
      }

      if (Array.isArray(partners)) {
        partners.forEach((p) => {
          if (p && p.partner && typeof p.partner.latitude === 'number' && typeof p.partner.longitude === 'number' && isValidCoord(p.partner.latitude, p.partner.longitude)) {
            validPoints.push([p.partner.latitude, p.partner.longitude]);
          }
        });
      }

      // Multiple points: fit bounds
      if (validPoints.length > 1) {
        const bounds = L.latLngBounds(validPoints);
        if (bounds.isValid()) {
          map.fitBounds(bounds, { padding: [40, 40], maxZoom: 12 });
          return;
        }
      }

      // Single point: fly to point safely
      if (validPoints.length === 1) {
        map.flyTo([validPoints[0][0], validPoints[0][1]], 11, { duration: 0.8 });
        return;
      }

      // Fallback: Default pan to national center
      if (origin && isValidCoord(origin.lat, origin.lng)) {
        map.flyTo([origin.lat, origin.lng], 10, { duration: 0.8 });
      } else {
        map.setView([22.5937, 78.9629], 5);
      }
    } catch (err) {
      console.warn('Map bounds animation safe guard caught:', err);
    }
  }, [origin, partners, routeCoords, map]);

  useEffect(() => {
    const timer = setTimeout(() => {
      try {
        map.invalidateSize();
      } catch (e) {
        // ignore
      }
    }, 150);
    return () => clearTimeout(timer);
  }, [map]);

  useEffect(() => {
    fitMapBounds();
  }, [fitMapBounds, recenterTrigger]);

  return null;
};

// ─────────────────────────────────────────────────────────────
// Map Control Buttons Component (In-Map HUD)
// ─────────────────────────────────────────────────────────────
const MapHudControls: React.FC<{
  isScrollZoomUnlocked: boolean;
  onToggleScrollZoom: () => void;
  onRecenter: () => void;
}> = ({ isScrollZoomUnlocked, onToggleScrollZoom, onRecenter }) => {
  const map = useMap();
  const { t } = useTranslation();

  return (
    <div className="absolute top-4 right-4 z-[25] flex flex-col gap-2 shadow-lg">
      {/* Zoom In Button */}
      <button
        type="button"
        onClick={() => map.zoomIn()}
        className="w-9 h-9 bg-white hover:bg-slate-50 text-slate-700 rounded-xl border border-slate-200 flex items-center justify-center shadow-xs transition hover:scale-105 active:scale-95"
        title={t('map.zoomIn', 'Zoom in')}
        aria-label={t('map.zoomIn', 'Zoom in')}
      >
        <ZoomIn className="w-4 h-4" />
      </button>

      {/* Zoom Out Button */}
      <button
        type="button"
        onClick={() => map.zoomOut()}
        className="w-9 h-9 bg-white hover:bg-slate-50 text-slate-700 rounded-xl border border-slate-200 flex items-center justify-center shadow-xs transition hover:scale-105 active:scale-95"
        title={t('map.zoomOut', 'Zoom out')}
        aria-label={t('map.zoomOut', 'Zoom out')}
      >
        <ZoomOut className="w-4 h-4" />
      </button>

      {/* Recenter View Button */}
      <button
        type="button"
        onClick={onRecenter}
        className="w-9 h-9 bg-white hover:bg-slate-50 text-slate-700 rounded-xl border border-slate-200 flex items-center justify-center shadow-xs transition hover:scale-105 active:scale-95"
        title={t('map.recenter', 'Recenter and Fit All Locations')}
        aria-label={t('map.recenterAria', 'Recenter map')}
      >
        <RotateCcw className="w-4 h-4 text-sky-600" />
      </button>

      {/* Scroll Zoom Lock/Unlock Toggle */}
      <button
        type="button"
        onClick={onToggleScrollZoom}
        className={`w-9 h-9 rounded-xl border flex items-center justify-center shadow-xs transition hover:scale-105 active:scale-95 ${
          isScrollZoomUnlocked
            ? 'bg-amber-500 text-white border-amber-600 ring-2 ring-amber-200'
            : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200'
        }`}
        title={isScrollZoomUnlocked ? t('map.scrollZoomUnlocked', 'Scroll Zoom Unlocked (Mouse wheel zooms map)') : t('map.scrollZoomLocked', 'Scroll Zoom Locked (Normal page scroll)')}
        aria-label={t('map.toggleScrollZoom', 'Toggle scroll zoom')}
      >
        {isScrollZoomUnlocked ? <Unlock className="w-4 h-4" /> : <Lock className="w-4 h-4 text-slate-500" />}
      </button>
    </div>
  );
};

export const MapLocator: React.FC<MapLocatorProps> = ({
  onSelectPartner,
  selectedPartnerId: initialSelectedId = null,
  schemeId,
  schemeName,
  loanCategory,
}) => {
  const { t } = useTranslation();

  // Authoritative GPS Location State
  const [gpsLocation, setGpsLocation] = useState<UserLocation | null>(null);
  const [isGpsActive, setIsGpsActive] = useState<boolean>(false);

  // Search Area Location State
  const [searchLocation, setSearchLocation] = useState<{ lat: number; lng: number; label: string } | null>(null);
  const [pinCode, setPinCode] = useState('');

  const [isLoading, setIsLoading] = useState(false);
  const [isLocating, setIsLocating] = useState(false);
  const [partners, setPartners] = useState<NearestPartnerResponse[]>([]);
  const [selectedPartnerId, setSelectedPartnerId] = useState<string | null>(initialSelectedId);
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState<string>('ALL');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Filtered partners based on selected category tab
  const filteredPartners = useMemo(() => {
    let list = partners;
    if (selectedCategoryFilter === 'AUTHORIZED_SCHEME_PARTNER') {
      list = list.filter(p => p.partner && p.partner.partner_category === 'AUTHORIZED_SCHEME_PARTNER');
    } else if (selectedCategoryFilter === 'IMPLEMENTING_ASSISTANCE_CENTRE') {
      list = list.filter(p => p.partner && p.partner.partner_category === 'IMPLEMENTING_ASSISTANCE_CENTRE');
    } else if (selectedCategoryFilter === 'NEARBY_FINANCIAL_SERVICE_POINT') {
      list = list.filter(p => p.partner && p.partner.partner_category === 'NEARBY_FINANCIAL_SERVICE_POINT');
    } else if (selectedCategoryFilter === 'TRAINING_HANDHOLDING_CENTRE') {
      list = list.filter(p => p.partner && (
        p.partner.institution_type === 'RSETI_TRAINING_INSTITUTE' ||
        p.partner.partner_type === 'RSETI_TRAINING_INSTITUTE' ||
        (p.service_type && p.service_type.includes('TRAINING')) ||
        (p.partner.service_type && p.partner.service_type.includes('TRAINING'))
      ));
    } else if (selectedCategoryFilter === 'VERIFIED') {
      list = list.filter(p => p.partner && p.partner.verification_status === 'VERIFIED_OFFICIAL');
    }
    return list;
  }, [partners, selectedCategoryFilter]);

  // OSRM Driving Route State
  const [routeInfo, setRouteInfo] = useState<OSRMRouteInfo | null>(null);
  const [routeStatus, setRouteStatus] = useState<string | null>(null);

  // Map Interaction State
  const [isScrollZoomUnlocked, setIsScrollZoomUnlocked] = useState<boolean>(false);
  const [showScrollHint, setShowScrollHint] = useState<boolean>(false);
  const [recenterTrigger, setRecenterTrigger] = useState<number>(0);
  const hintTimeoutRef = useRef<any>(null);

  const triggerScrollHint = useCallback(() => {
    setShowScrollHint(true);
    if (hintTimeoutRef.current) clearTimeout(hintTimeoutRef.current);
    hintTimeoutRef.current = setTimeout(() => {
      setShowScrollHint(false);
    }, 1800);
  }, []);

  // Active Origin: GPS location if active, otherwise geocoded search location
  const activeOrigin: ActiveOrigin | null = useMemo(() => {
    if (isGpsActive && gpsLocation && isValidCoord(gpsLocation.lat, gpsLocation.lng)) {
      return {
        lat: gpsLocation.lat,
        lng: gpsLocation.lng,
        label: 'your current location',
        isGps: true,
      };
    }
    if (searchLocation && isValidCoord(searchLocation.lat, searchLocation.lng)) {
      return {
        lat: searchLocation.lat,
        lng: searchLocation.lng,
        label: searchLocation.label,
        isGps: false,
      };
    }
    return null;
  }, [isGpsActive, gpsLocation, searchLocation]);

  // Recalculate partner distances and sort based on the authoritative active origin
  const processAndSetPartners = useCallback(
    (rawPartners: NearestPartnerResponse[], originLat: number, originLng: number) => {
      const validPartners = (Array.isArray(rawPartners) ? rawPartners : [])
        .filter((item) => item && item.partner && typeof item.partner.latitude === 'number' && typeof item.partner.longitude === 'number' && isValidCoord(item.partner.latitude, item.partner.longitude))
        .map((item) => {
          const pLat = item.partner.latitude as number;
          const pLng = item.partner.longitude as number;
          const distKm = calculateHaversineKm(
            originLat,
            originLng,
            pLat,
            pLng
          );
          return {
            ...item,
            distance_km: distKm,
          };
        });

      // Sort by distance from active origin
      validPartners.sort((a, b) => a.distance_km - b.distance_km);

      setPartners(validPartners);
      if (validPartners.length > 0) {
        setSelectedPartnerId(validPartners[0].partner.partner_id);
        if (onSelectPartner) onSelectPartner(validPartners[0].partner.partner_id);
        setErrorMsg(null);
      } else {
        setSelectedPartnerId(null);
        if (schemeId) {
          setErrorMsg('No verified channel partner is currently mapped to this scheme in this area. Please apply directly through the official government portal.');
        } else {
          setErrorMsg('No verified channel partner was found matching this criteria.');
        }
      }
    },
    [schemeId, onSelectPartner]
  );

  // Fetch partners based on current state
  const fetchPartnersForCurrentState = useCallback(async () => {
    setIsLoading(true);
    setErrorMsg(null);

    let queryLat = 28.6139;
    let queryLng = 77.2090;
    let queryRadius = 2500;

    if (activeOrigin && isValidCoord(activeOrigin.lat, activeOrigin.lng)) {
      queryLat = activeOrigin.lat;
      queryLng = activeOrigin.lng;
      queryRadius = 350;
    }

    try {
      const data = await partnerApi.getNearestPartners(
        queryLat,
        queryLng,
        queryRadius,
        schemeId,
        loanCategory
      );
      processAndSetPartners(data, queryLat, queryLng);
    } catch (err: any) {
      console.error('Failed to load nearest partners:', err);
      setErrorMsg(err?.response?.data?.detail || 'Unable to connect to partner directory service.');
    } finally {
      setIsLoading(false);
    }
  }, [schemeId, loanCategory, activeOrigin, processAndSetPartners]);

  // Trigger partner fetch on mount or when schemeId / loanCategory changes
  useEffect(() => {
    fetchPartnersForCurrentState();
  }, [schemeId, loanCategory]);

  // Request high-accuracy GPS User Location
  const handleUseCurrentLocation = () => {
    if (!navigator.geolocation) {
      setErrorMsg('Geolocation is not supported by your browser.');
      return;
    }

    setIsLocating(true);
    setErrorMsg(null);

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;

        if (isValidCoord(lat, lng)) {
          setGpsLocation({ lat, lng });
          setIsGpsActive(true);
          setSearchLocation(null);

          try {
            setIsLoading(true);
            const data = await partnerApi.getNearestPartners(lat, lng, 350, schemeId, loanCategory);
            processAndSetPartners(data, lat, lng);
            setRecenterTrigger((prev) => prev + 1);
          } catch (err: any) {
            setErrorMsg(err?.response?.data?.detail || 'Failed to fetch nearest partners.');
          } finally {
            setIsLoading(false);
            setIsLocating(false);
          }
        } else {
          setErrorMsg('Received invalid GPS coordinates from browser.');
          setIsLocating(false);
        }
      },
      (err) => {
        setIsLocating(false);
        if (err.code === err.PERMISSION_DENIED) {
          setErrorMsg('Location permission denied. Please allow location access or search by state/PIN code.');
        } else {
          setErrorMsg('Unable to retrieve your location. Please enter your state or PIN code.');
        }
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  };

  // Search by PIN Code or City/State Name
  const handlePinSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanInput = pinCode.trim();
    if (!cleanInput) {
      setErrorMsg('Please enter a valid PIN code, district, or state name.');
      return;
    }

    setIsLoading(true);
    setErrorMsg(null);

    let searchLat: number | null = null;
    let searchLng: number | null = null;
    let searchLabel: string = cleanInput;

    if (geocodeCache.has(cleanInput)) {
      const cached = geocodeCache.get(cleanInput)!;
      searchLat = cached.lat;
      searchLng = cached.lng;
      searchLabel = cached.displayName;
    } else {
      try {
        const isSixDigitPin = /^\d{6}$/.test(cleanInput);
        const queryParam = isSixDigitPin ? `${cleanInput}, India` : `${cleanInput}, India`;

        const response = await fetch(
          `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(queryParam)}&format=json&addressdetails=1&limit=1&countrycodes=in`,
          {
            headers: {
              'User-Agent': 'YojnaSetu-GovScheme-Platform/1.0 (sih26092-locator@yojnasetu.gov.in)',
            },
          }
        );

        if (response.ok) {
          const results = await response.json();
          if (results && results.length > 0) {
            const lat = parseFloat(results[0].lat);
            const lng = parseFloat(results[0].lon);
            if (isValidCoord(lat, lng)) {
              searchLat = lat;
              searchLng = lng;
              searchLabel = results[0].display_name;
              geocodeCache.set(cleanInput, { lat, lng, displayName: searchLabel });
            }
          }
        }
      } catch (err) {
        setErrorMsg('Network error while searching location. Please check your internet connection.');
        setIsLoading(false);
        return;
      }
    }

    if (!isValidCoord(searchLat, searchLng)) {
      setErrorMsg(`Could not locate "${cleanInput}". Please try a nearby PIN code or district name.`);
      setIsLoading(false);
      return;
    }

    setSearchLocation({ lat: searchLat!, lng: searchLng!, label: cleanInput });

    const effectiveOriginLat = isGpsActive && gpsLocation ? gpsLocation.lat : searchLat!;
    const effectiveOriginLng = isGpsActive && gpsLocation ? gpsLocation.lng : searchLng!;

    try {
      const data = await partnerApi.getNearestPartners(searchLat!, searchLng!, 500, schemeId, loanCategory);
      processAndSetPartners(data, effectiveOriginLat, effectiveOriginLng);
      setRecenterTrigger((prev) => prev + 1);
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.detail || 'Failed to fetch nearby partners.');
    } finally {
      setIsLoading(false);
    }
  };

  // OSRM Turn-by-Turn Driving Route Calculation
  useEffect(() => {
    const selectedPartner = partners.find((p) => p.partner && p.partner.partner_id === selectedPartnerId);
    if (
      !activeOrigin ||
      !isValidCoord(activeOrigin.lat, activeOrigin.lng) ||
      !selectedPartner ||
      !isValidCoord(selectedPartner.partner.latitude, selectedPartner.partner.longitude)
    ) {
      setRouteInfo(null);
      setRouteStatus(null);
      return;
    }

    const fetchOSRMRoute = async () => {
      setRouteStatus('Calculating driving route from active origin...');
      try {
        const uLng = activeOrigin.lng;
        const uLat = activeOrigin.lat;
        const pLng = selectedPartner.partner.longitude;
        const pLat = selectedPartner.partner.latitude;

        const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${uLng},${uLat};${pLng},${pLat}?overview=full&geometries=geojson`;
        const res = await fetch(osrmUrl);
        if (res.ok) {
          const data = await res.json();
          if (data.code === 'Ok' && data.routes && data.routes.length > 0) {
            const route = data.routes[0];
            if (Array.isArray(route.geometry?.coordinates) && route.geometry.coordinates.length >= 2) {
              const coordinates: [number, number][] = [];
              for (const pt of route.geometry.coordinates) {
                if (Array.isArray(pt) && pt.length >= 2 && isValidCoord(pt[1], pt[0])) {
                  coordinates.push([pt[1], pt[0]]);
                }
              }
              if (coordinates.length >= 2) {
                const distanceKm = Math.round((route.distance / 1000) * 10) / 10;
                const durationMins = Math.round(route.duration / 60);

                setRouteInfo({
                  coordinates,
                  distanceKm,
                  durationMins,
                });
                setRouteStatus(null);
                return;
              }
            }
          }
        }
        setRouteInfo(null);
        setRouteStatus('Route unavailable for this long-distance route.');
      } catch (e) {
        setRouteInfo(null);
        setRouteStatus('Route unavailable right now.');
      }
    };

    fetchOSRMRoute();
  }, [activeOrigin, selectedPartnerId, partners]);

  const handlePartnerSelect = (partnerId: string) => {
    setSelectedPartnerId(partnerId);
    if (onSelectPartner) onSelectPartner(partnerId);
  };

  const handleOpenGoogleMapsNavigation = (e: React.MouseEvent, partner: any) => {
    e.stopPropagation();
    if (
      partner &&
      typeof partner.latitude === 'number' &&
      typeof partner.longitude === 'number' &&
      Number.isFinite(partner.latitude) &&
      Number.isFinite(partner.longitude) &&
      partner.coordinates_verified === true
    ) {
      const lat = partner.latitude;
      const lng = partner.longitude;
      const navUrl = `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(`${lat},${lng}`)}`;
      window.open(navUrl, '_blank', 'noopener,noreferrer');
    }
  };

  const selectedPartnerObj = useMemo(() => {
    return partners.find((p) => p.partner && p.partner.partner_id === selectedPartnerId) || null;
  }, [partners, selectedPartnerId]);

  const mapCenterCoords: [number, number] =
    activeOrigin && isValidCoord(activeOrigin.lat, activeOrigin.lng)
      ? [activeOrigin.lat, activeOrigin.lng]
      : [22.5937, 78.9629];

  return (
    <div className="bg-white rounded-3xl shadow-xl overflow-hidden border border-slate-200 flex flex-col md:flex-row h-auto md:h-[720px] relative isolate z-0 w-full">
      {/* ─────────────────────────────────────────────────────────────
          LEFT PANEL: Controls, Filters & Partner List
      ───────────────────────────────────────────────────────────── */}
      <div className="w-full md:w-5/12 flex flex-col border-r border-slate-200 min-h-[420px] md:h-full bg-white relative z-10">
        {/* Search Header */}
        <div className="p-5 border-b border-slate-200 bg-white space-y-3">
          <div className="flex items-center gap-2.5">
            <div className="bg-indigo-50 p-2.5 rounded-2xl text-indigo-600 border border-indigo-100">
              <MapPin className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-extrabold text-slate-900 text-sm">{t('partnerLocator.title', 'Channel Partner Locator')}</h3>
              <p className="text-[11px] text-slate-500">
                {schemeId ? t('partnerLocator.authorizedPartnersFor', 'Authorized channel partners for {{scheme}}', { scheme: schemeName || schemeId }) : t('partnerLocator.officialAgencies', 'Official NSFDC channelizing agencies & banks')}
              </p>
            </div>
          </div>

          <div className="space-y-2.5">
            <button
              onClick={handleUseCurrentLocation}
              disabled={isLocating || isLoading}
              className={`w-full px-4 py-2.5 rounded-xl font-bold text-xs flex items-center justify-center gap-2 transition shadow-sm disabled:opacity-50 ${
                isGpsActive
                  ? 'bg-emerald-600 hover:bg-emerald-700 text-white ring-2 ring-emerald-300'
                  : 'bg-indigo-600 hover:bg-indigo-700 text-white'
              }`}
            >
              {isLocating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Navigation className="w-4 h-4" />}
              {isGpsActive ? `✓ ${t('partnerLocator.currentGpsActive', 'Current GPS Location Active')}` : t('partnerLocator.useCurrentLocation', 'Use My Current Location')}
            </button>

            <div className="relative flex items-center justify-center py-0.5">
              <div className="border-t border-slate-200 w-full" />
              <span className="bg-white px-2 text-[10px] font-extrabold text-slate-400 uppercase tracking-wider absolute">
                {t('partnerLocator.orFilterArea', 'or filter / search area')}
              </span>
            </div>

            <form onSubmit={handlePinSearch} className="flex gap-2">
              <input
                type="text"
                placeholder={t('partnerLocator.searchPlaceholder', 'Enter state, PIN or city (e.g. Gorakhpur, Lucknow)')}
                value={pinCode}
                onChange={(e) => setPinCode(e.target.value)}
                className="flex-1 px-3.5 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-indigo-500 outline-none font-medium transition"
              />
              <button
                type="submit"
                disabled={isLoading}
                className="bg-slate-800 text-white px-4 py-2 rounded-xl hover:bg-slate-700 transition font-bold text-xs flex items-center gap-1 shadow-sm"
              >
                {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
                {t('partnerLocator.search', 'Search')}
              </button>
            </form>

            {/* Quick Demo City Focus */}
            <div className="flex items-center gap-2 text-[11px] pt-0.5">
              <span className="text-slate-400 font-semibold text-[10px] uppercase tracking-wider">{t('partnerLocator.quickFocus', 'Quick Focus:')}</span>
              <div className="flex flex-wrap gap-1.5">
                {[
                  { name: 'Gorakhpur', lat: 26.7606, lng: 83.3732 },
                  { name: 'Lucknow', lat: 26.8467, lng: 80.9462 },
                  { name: 'Varanasi', lat: 25.3176, lng: 82.9739 },
                  { name: 'Kanpur', lat: 26.4499, lng: 80.3319 },
                  { name: 'Prayagraj', lat: 25.4358, lng: 81.8463 }
                ].map(city => (
                  <button
                    key={city.name}
                    type="button"
                    onClick={() => {
                      setPinCode(city.name);
                      setSearchLocation({ lat: city.lat, lng: city.lng, label: city.name });
                      partnerApi.getNearestPartners(city.lat, city.lng, 250, schemeId, loanCategory).then(data => {
                        processAndSetPartners(data, city.lat, city.lng);
                        setRecenterTrigger(prev => prev + 1);
                      });
                    }}
                    className={`px-2 py-0.5 rounded-lg text-[10px] font-bold border transition ${
                      pinCode.toLowerCase() === city.name.toLowerCase()
                        ? 'bg-sky-100 text-sky-800 border-sky-300'
                        : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    {city.name}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Active Origin Status Banner */}
          {activeOrigin && (
            <div>
              {activeOrigin.isGps ? (
                <div className="flex items-center gap-2 text-[11px] text-emerald-900 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-xl font-medium shadow-xs">
                  <Navigation className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>{t('partnerLocator.distGps', 'Distances computed from your GPS location')}</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-[11px] text-slate-800 bg-slate-100 border border-slate-200 px-3 py-1.5 rounded-xl font-medium shadow-xs">
                  <MapPin className="w-3.5 h-3.5 text-slate-600 shrink-0" />
                  <span>{t('partnerLocator.distCustom', 'Distances computed from {{label}}', { label: activeOrigin.label })}</span>
                </div>
              )}
            </div>
          )}

          {/* Category Filter Tabs */}
          <div className="space-y-1 pt-1">
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none text-[11px]">
              {[
                { id: 'ALL', label: t('partnerLocator.categoryAll', 'All Partners') },
                { id: 'AUTHORIZED_SCHEME_PARTNER', label: t('partnerLocator.categoryAuthorized', 'Authorized Partners') },
                { id: 'IMPLEMENTING_ASSISTANCE_CENTRE', label: t('partnerLocator.categoryAssistance', 'Assistance Centres') },
                { id: 'TRAINING_HANDHOLDING_CENTRE', label: t('partnerLocator.categoryTraining', 'Training / EDP') },
                { id: 'NEARBY_FINANCIAL_SERVICE_POINT', label: t('partnerLocator.categoryFinancial', 'Financial Institutions') },
              ].map(tab => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setSelectedCategoryFilter(tab.id)}
                  className={`px-3 py-1 rounded-full whitespace-nowrap font-bold transition text-[10px] shrink-0 ${
                    selectedCategoryFilter === tab.id
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200 border border-slate-200'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Scheme Filter Header Badge */}
          {schemeId && (
            <div className="bg-indigo-50/80 border border-indigo-200 rounded-xl p-2.5 text-xs text-indigo-950 shadow-xs">
              <div className="flex items-center justify-between font-bold text-indigo-900 text-[11px] mb-0.5">
                <span className="flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                  {t('partnerLocator.partnersForScheme', 'Partners for: {{scheme}}', { scheme: schemeName || schemeId })}
                </span>
                <span className="bg-indigo-200/80 text-indigo-900 px-2 py-0.5 rounded-full font-extrabold text-[10px]">
                  {filteredPartners.length} {t('partnerLocator.authorized', 'Authorized')}
                </span>
              </div>
              <p className="text-[10px] text-indigo-700 leading-tight">
                {t('partnerLocator.verifiedDesc', 'Only displaying verified partners officially authorized to deliver this scheme.')}
              </p>
            </div>
          )}
        </div>

        {/* Scrollable Partner List */}
        <div className="flex-1 overflow-y-auto p-4 bg-slate-50 space-y-3">
          {errorMsg && (
            <div
              className={`p-4 rounded-xl flex items-start gap-2.5 text-xs border shadow-sm ${
                errorMsg.includes('government portal')
                  ? 'bg-blue-50 text-blue-900 border-blue-200'
                  : 'bg-amber-50 text-amber-900 border-amber-200'
              }`}
            >
              <AlertCircle
                className={`w-4 h-4 shrink-0 mt-0.5 ${
                  errorMsg.includes('government portal') ? 'text-blue-600' : 'text-amber-600'
                }`}
              />
              <div className="space-y-1">
                <span className="font-semibold">{errorMsg}</span>
                {errorMsg.includes('government portal') && (
                  <p className="text-[11px] text-blue-700">
                    {t('partnerLocator.applyPortalNotice', 'Click "Apply on Official Portal" above to submit your application directly on the ministry portal.')}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Route Summary Banner */}
          {routeInfo && selectedPartnerObj && (
            <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-3 text-xs text-indigo-900 flex items-center justify-between shadow-xs">
              <div>
                <span className="font-bold text-indigo-800">{t('partnerLocator.drivingRoute', 'OSRM Driving Route:')}</span>
                <span className="ml-1 font-medium">
                  {routeInfo.distanceKm.toLocaleString()} km • ~
                  {routeInfo.durationMins >= 60
                    ? `${Math.floor(routeInfo.durationMins / 60)} hr ${routeInfo.durationMins % 60} min`
                    : `${routeInfo.durationMins} mins`}
                </span>
              </div>
              <span className="text-[10px] bg-indigo-200/70 text-indigo-800 px-2 py-0.5 rounded-full font-bold">
                {t('partnerLocator.driving', 'Driving')}
              </span>
            </div>
          )}
          {routeStatus && !routeInfo && (
            <div className="text-[11px] text-slate-500 italic bg-white p-2 rounded-lg border border-slate-200 text-center">
              {routeStatus}
            </div>
          )}

          {/* No Partners Found State */}
          {filteredPartners.length === 0 && !isLoading && (
            <div className="p-6 bg-white rounded-2xl border border-slate-200 text-center space-y-3 my-4">
              <div className="w-12 h-12 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center mx-auto">
                <AlertCircle className="w-6 h-6" />
              </div>
              <h4 className="font-bold text-slate-900 text-sm">
                {t('partnerLocator.noPartnerTitle', 'No verified authorized partner was found for this scheme in this area.')}
              </h4>
              <p className="text-xs text-slate-600 max-w-md mx-auto leading-relaxed">
                {t('partnerLocator.noPartnerDesc', 'Submissions for this scheme are handled directly via the official government portal or statutory district office.')}
              </p>
              <div className="pt-2 flex flex-col sm:flex-row justify-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedCategoryFilter('ALL');
                    setPinCode('Gorakhpur');
                    handlePinSearch({ preventDefault: () => {} } as any);
                  }}
                  className="text-xs text-sky-600 font-bold hover:underline py-1"
                >
                  {t('partnerLocator.browseGorakhpur', 'Browse verified Gorakhpur & UP centres →')}
                </button>
              </div>
            </div>
          )}

          {filteredPartners.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-[10px] font-extrabold text-slate-500 uppercase px-1 tracking-wider">
                {schemeId
                  ? t('partnerLocator.authorizedPartners', 'Authorized Channel Partners ({{count}})', { count: filteredPartners.length })
                  : t('partnerLocator.recommendedPartners', 'Recommended Channel Partners ({{count}})', { count: filteredPartners.length })}
              </h4>
              {filteredPartners.map((p, idx) => {
                const partner = p.partner;
                if (!partner) return null;
                const isSelected = selectedPartnerId === partner.partner_id;

                const category = partner.partner_category || 'AUTHORIZED_SCHEME_PARTNER';

                return (
                  <div
                    key={partner.partner_id}
                    className={`p-3.5 rounded-2xl border-2 cursor-pointer transition-all ${
                      isSelected
                        ? 'border-indigo-600 bg-white shadow-md ring-4 ring-indigo-50'
                        : 'border-slate-200 bg-white hover:border-indigo-300 shadow-xs hover:shadow'
                    }`}
                    onClick={() => handlePartnerSelect(partner.partner_id)}
                  >
                    {/* Header Row: Number + Name + Distance */}
                    <div className="flex justify-between items-start mb-1.5">
                      <div className="font-bold text-slate-900 flex items-start gap-2 pr-2 text-xs">
                        <span className="bg-slate-800 text-white w-5 h-5 rounded-full flex items-center justify-center text-[10px] shrink-0 mt-0.5 font-bold">
                          {idx + 1}
                        </span>
                        <span className="leading-snug">{partner.name}</span>
                      </div>
                      <div className="text-[11px] font-bold text-indigo-700 bg-indigo-100 px-2 py-0.5 rounded-full whitespace-nowrap shrink-0">
                        {p.distance_km.toLocaleString()} {t('partnerLocator.kmAway', 'km away')}
                      </div>
                    </div>

                    {/* Trust Category Badges */}
                    <div className="ml-7 mb-2 flex flex-wrap gap-1.5">
                      {category === 'AUTHORIZED_SCHEME_PARTNER' && (
                        <span className="inline-flex items-center gap-1 text-[10px] font-extrabold text-blue-800 bg-blue-50 border border-blue-200 px-2.5 py-0.5 rounded-full">
                          <ShieldCheck className="w-3 h-3 text-blue-600 shrink-0" />
                          {t('partnerLocator.badgeAuthorized', 'OFFICIALLY VERIFIED SCHEME PARTNER')}
                        </span>
                      )}
                      {category === 'IMPLEMENTING_ASSISTANCE_CENTRE' && (
                        <span className="inline-flex items-center gap-1 text-[10px] font-extrabold text-emerald-800 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full">
                          <Building2 className="w-3 h-3 text-emerald-600 shrink-0" />
                          {t('partnerLocator.badgeAssistance', 'GOVERNMENT ASSISTANCE CENTRE')}
                        </span>
                      )}
                      {category === 'NEARBY_FINANCIAL_SERVICE_POINT' && (
                        <span className="inline-flex items-center gap-1 text-[10px] font-extrabold text-amber-800 bg-amber-50 border border-amber-200 px-2.5 py-0.5 rounded-full">
                          <Building className="w-3 h-3 text-amber-600 shrink-0" />
                          {t('partnerLocator.badgeFinancial', 'FINANCIAL INSTITUTION (GENERAL ROUTE)')}
                        </span>
                      )}
                      {partner.institution_type && (
                        <span className="text-[10px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full">
                          {partner.institution_type.replace(/_/g, ' ')}
                        </span>
                      )}
                    </div>

                    {/* Address & District */}
                    {partner.address && (
                      <div className="text-[11px] text-slate-600 ml-7 flex items-start gap-1.5 mb-1.5 font-medium leading-relaxed">
                        <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                        <span>{partner.address}</span>
                      </div>
                    )}

                    {/* Contact Pills: Phone, Email, Website, Official Source */}
                    <div className="ml-7 flex flex-wrap gap-1.5 mb-2">
                      {partner.phone && (
                        <a
                          href={`tel:${partner.phone}`}
                          onClick={(e) => e.stopPropagation()}
                          className="inline-flex items-center gap-1 text-[10px] font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 px-2.5 py-0.5 rounded-md transition"
                        >
                          <Phone className="w-3 h-3 text-slate-500" />
                          {partner.phone}
                        </a>
                      )}
                      {partner.email && (
                        <a
                          href={`mailto:${partner.email}`}
                          onClick={(e) => e.stopPropagation()}
                          className="inline-flex items-center gap-1 text-[10px] font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 px-2.5 py-0.5 rounded-md transition"
                        >
                          <Mail className="w-3 h-3 text-slate-500" />
                          {partner.email}
                        </a>
                      )}
                      {partner.website && (
                        <a
                          href={partner.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="inline-flex items-center gap-1 text-[10px] font-bold text-sky-700 bg-sky-50 hover:bg-sky-100 px-2.5 py-0.5 rounded-md transition border border-sky-100"
                        >
                          <Globe className="w-3 h-3 text-sky-500" />
                          {t('partnerLocator.website', 'Website')}
                        </a>
                      )}
                      {partner.source_url && (
                        <a
                          href={partner.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="inline-flex items-center gap-1 text-[10px] font-bold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 px-2.5 py-0.5 rounded-md transition border border-indigo-100"
                        >
                          <ExternalLink className="w-3 h-3 text-indigo-500" />
                          {t('partnerLocator.officialSource', 'Official Source')}
                        </a>
                      )}
                    </div>

                    {/* Schemes Supported */}
                    {partner.supported_schemes && partner.supported_schemes.length > 0 && (
                      <div className="ml-7 text-[10px] text-slate-600 mb-1.5">
                        <span className="font-bold text-slate-700">{t('partnerLocator.schemesSupported', 'Schemes Supported')}: </span>
                        <span className="text-slate-600">{partner.supported_schemes.slice(0, 3).join(', ')}</span>
                        {partner.supported_schemes.length > 3 && (
                          <span className="font-semibold text-indigo-600 ml-1">+{partner.supported_schemes.length - 3} more</span>
                        )}
                      </div>
                    )}

                    {/* Scheme Authorization and Capacity */}
                    <div className="ml-7 space-y-1 mb-2">
                      {p.is_scheme_matched ? (
                        <div className="flex items-center gap-1.5 text-[11px] text-emerald-800 font-semibold bg-emerald-50/80 border border-emerald-200 px-2.5 py-1 rounded-lg">
                          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                          ✓ {t('map.authorizedForScheme', 'Authorized for selected scheme')}
                          {p.service_type ? ` (${p.service_type.replace(/_/g, ' ')})` : ''}
                        </div>
                      ) : schemeId ? (
                        <div className="flex items-center gap-1.5 text-[11px] text-amber-800 bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-lg">
                          <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                          {t('map.authPending', '⚠ Scheme-specific authorization not confirmed')}
                        </div>
                      ) : null}

                      <div className="text-[10px] text-slate-500">
                        <span>{t('partnerLocator.lastVerified', 'Last verified')}: </span>
                        <span className="font-semibold text-slate-700">{partner.last_verified_date || '2026-09-01'}</span>
                      </div>
                    </div>

                    {/* Action Row: Radio Select + Navigate */}
                    <div className="flex justify-between items-center mt-2 pt-2 border-t border-slate-100 ml-7 gap-2">
                      <div className="flex items-center gap-1.5">
                        <input
                          type="radio"
                          checked={isSelected}
                          readOnly
                          className="w-3.5 h-3.5 text-indigo-600 border-slate-300 focus:ring-indigo-600 cursor-pointer"
                        />
                        <span className="text-[11px] font-bold text-slate-800">{t('map.selectPartner', 'Select Partner')}</span>
                      </div>

                      {isValidCoord(partner.latitude, partner.longitude) && (
                        <a
                          href={`https://www.google.com/maps/dir/?api=1&destination=${partner.latitude},${partner.longitude}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="text-[10px] text-white bg-slate-800 hover:bg-slate-700 px-2.5 py-1 rounded-lg font-bold transition flex items-center gap-1 shadow-xs hover:shadow"
                          title={`Navigate to ${partner.latitude}, ${partner.longitude}`}
                        >
                          <ExternalLink className="w-3 h-3 text-sky-400" /> {t('partnerLocator.getDirections', 'Get Directions')}
                        </a>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          RIGHT PANEL: Interactive Leaflet Map
      ───────────────────────────────────────────────────────────── */}
      <div className="w-full md:w-7/12 min-h-[460px] md:min-h-[720px] h-[480px] md:h-full relative bg-slate-100 overflow-hidden isolate z-0">
        {/* Scroll Zoom Overlay Hint (Appears on accidental wheel scroll without Ctrl) */}
        {showScrollHint && (
          <div className="absolute inset-0 z-[35] bg-slate-950/60 backdrop-blur-xs flex items-center justify-center pointer-events-none transition-opacity duration-300">
            <div className="bg-slate-900 text-white text-xs font-bold px-4 py-2.5 rounded-2xl shadow-2xl border border-slate-700 flex items-center gap-2">
              <Compass className="w-4 h-4 text-sky-400 animate-spin" />
              <span>{t('map.ctrlScrollHint', 'Use Ctrl + scroll to zoom map')}</span>
            </div>
          </div>
        )}

        <MapContainer
          center={mapCenterCoords}
          zoom={5}
          scrollWheelZoom={false}
          zoomControl={false}
          className="h-full w-full relative z-0"
          style={{ height: '100%', width: '100%', minHeight: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Gesture & Interaction Handler */}
          <MapInteractionHandler
            isScrollZoomUnlocked={isScrollZoomUnlocked}
            onShowScrollHint={triggerScrollHint}
            recenterTrigger={recenterTrigger}
            origin={activeOrigin}
            partners={filteredPartners}
            routeCoords={routeInfo?.coordinates || []}
          />

          {/* In-Map Custom HUD Controls */}
          <MapHudControls
            isScrollZoomUnlocked={isScrollZoomUnlocked}
            onToggleScrollZoom={() => setIsScrollZoomUnlocked(!isScrollZoomUnlocked)}
            onRecenter={() => setRecenterTrigger((prev) => prev + 1)}
          />

          {/* Active Origin Marker */}
          {activeOrigin && isValidCoord(activeOrigin.lat, activeOrigin.lng) && (
            <Marker
              position={[activeOrigin.lat, activeOrigin.lng]}
              icon={activeOrigin.isGps ? userLocationIcon : searchLocationIcon}
            >
              <Popup>
                <div className="p-1 text-slate-800 text-xs font-semibold">
                  {activeOrigin.isGps ? (
                    <div className="flex items-center gap-1 text-emerald-800">
                      <Navigation className="w-3.5 h-3.5 text-emerald-600" /> Your Current GPS Location
                    </div>
                  ) : (
                    <div className="flex items-center gap-1 text-slate-800">
                      <MapPin className="w-3.5 h-3.5 text-slate-600" /> Searched Area: {activeOrigin.label}
                    </div>
                  )}
                  <div className="text-[10px] text-slate-500 font-normal mt-0.5">
                    ({activeOrigin.lat.toFixed(4)}, {activeOrigin.lng.toFixed(4)})
                  </div>
                </div>
              </Popup>
            </Marker>
          )}

          {/* OSRM Route Polyline */}
          {routeInfo && Array.isArray(routeInfo.coordinates) && routeInfo.coordinates.length > 1 && (
            <Polyline
              positions={routeInfo.coordinates}
              pathOptions={{
                color: '#4f46e5',
                weight: 5,
                opacity: 0.85,
                lineCap: 'round',
                lineJoin: 'round',
              }}
            />
          )}

          {/* Partner Markers */}
          {filteredPartners.map((p, idx) => {
            const partner = p.partner;
            if (!partner || typeof partner.latitude !== 'number' || typeof partner.longitude !== 'number' || !isValidCoord(partner.latitude, partner.longitude)) return null;
            const isSelected = selectedPartnerId === partner.partner_id;

            return (
              <Marker
                key={partner.partner_id}
                position={[partner.latitude, partner.longitude]}
                icon={createPartnerIcon(partner.partner_type, partner.partner_category || '', idx + 1, isSelected)}
                eventHandlers={{
                  click: () => handlePartnerSelect(partner.partner_id),
                }}
              >
                <Popup>
                  <div className="p-1.5 min-w-[210px] text-slate-800">
                    <div className="font-extrabold text-xs mb-1 text-slate-900 leading-snug">
                      {idx + 1}. {partner.name}
                    </div>
                    <div className="text-[11px] text-slate-500 mb-1 flex items-center gap-1 font-medium">
                      <Building className="w-3 h-3 text-slate-400" /> {partner.institution_type || partner.partner_type}
                    </div>
                    {partner.address && (
                      <div className="text-[10px] text-slate-600 mb-1.5 font-normal line-clamp-2">
                        {partner.address}
                      </div>
                    )}
                    {p.is_scheme_matched ? (
                      <div className="text-[10px] text-emerald-700 font-bold bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded mb-1.5 flex items-center gap-1">
                        <ShieldCheck className="w-3 h-3 text-emerald-600 shrink-0" /> Scheme Authorized
                      </div>
                    ) : null}
                    <div className="text-indigo-600 font-bold text-xs bg-indigo-50 inline-block px-2 py-0.5 rounded mb-2">
                      {p.distance_km.toLocaleString()} km away
                    </div>
                    {isValidCoord(partner.latitude, partner.longitude) && (
                      <div className="pt-2 border-t border-slate-100">
                        <a
                          href={`https://www.google.com/maps/dir/?api=1&destination=${partner.latitude},${partner.longitude}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="w-full text-[10px] text-white bg-slate-800 hover:bg-slate-700 px-2.5 py-1.5 rounded-lg font-bold transition flex items-center justify-center gap-1.5 shadow-xs"
                        >
                          <ExternalLink className="w-3 h-3 text-sky-400" /> {t('partnerLocator.getDirections', 'Get Directions')}
                        </a>
                      </div>
                    )}
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
};
