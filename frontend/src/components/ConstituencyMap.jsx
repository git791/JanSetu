import { useEffect, useRef, useState } from 'react'
import { setOptions, importLibrary } from '@googlemaps/js-api-loader'
import { MapPin } from 'lucide-react'

const DARK_MAP_STYLES = [
  { elementType: 'geometry', stylers: [{ color: '#0c1220' }] },
  { elementType: 'labels.text.stroke', stylers: [{ color: '#0c1220' }] },
  { elementType: 'labels.text.fill', stylers: [{ color: '#746855' }] },
  {
    featureType: 'administrative.locality',
    elementType: 'labels.text.fill',
    stylers: [{ color: '#d59563' }],
  },
  {
    featureType: 'poi',
    elementType: 'labels.text.fill',
    stylers: [{ color: '#d59563' }],
  },
  {
    featureType: 'poi.park',
    elementType: 'geometry',
    stylers: [{ color: '#0e1f12' }],
  },
  {
    featureType: 'poi.park',
    elementType: 'labels.text.fill',
    stylers: [{ color: '#6b9a76' }],
  },
  {
    featureType: 'road',
    elementType: 'geometry',
    stylers: [{ color: '#1a2540' }],
  },
  {
    featureType: 'road',
    elementType: 'geometry.stroke',
    stylers: [{ color: '#212a37' }],
  },
  {
    featureType: 'road',
    elementType: 'labels.text.fill',
    stylers: [{ color: '#9ca5b3' }],
  },
  {
    featureType: 'road.highway',
    elementType: 'geometry',
    stylers: [{ color: '#746855' }],
  },
  {
    featureType: 'road.highway',
    elementType: 'geometry.stroke',
    stylers: [{ color: '#1f2835' }],
  },
  {
    featureType: 'road.highway',
    elementType: 'labels.text.fill',
    stylers: [{ color: '#f3d19c' }],
  },
  {
    featureType: 'transit',
    elementType: 'geometry',
    stylers: [{ color: '#2f3948' }],
  },
  {
    featureType: 'transit.station',
    elementType: 'labels.text.fill',
    stylers: [{ color: '#d59563' }],
  },
  {
    featureType: 'water',
    elementType: 'geometry',
    stylers: [{ color: '#0b1621' }],
  },
  {
    featureType: 'water',
    elementType: 'labels.text.fill',
    stylers: [{ color: '#515c6d' }],
  },
  {
    featureType: 'water',
    elementType: 'labels.text.stroke',
    stylers: [{ color: '#17263c' }],
  },
]

const getPriorityColor = (score) => {
  if (score >= 70) return { fill: '#EF4444', stroke: '#DC2626' }
  if (score >= 40) return { fill: '#F59E0B', stroke: '#D97706' }
  return { fill: '#10B981', stroke: '#059669' }
}

export default function ConstituencyMap({ clusters = [], onClusterSelect }) {
  const mapRef = useRef(null)
  const mapInstance = useRef(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const circlesRef = useRef([])
  const infoWindowRef = useRef(null)

  useEffect(() => {
    const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY
    if (!apiKey) {
      setError('Google Maps API key not configured.')
      setIsLoading(false)
      return
    }

    setOptions({
      key: apiKey,
      version: 'weekly',
    })

    importLibrary('maps')
      .then((maps) => {
        if (!mapRef.current) return
        const map = new maps.Map(mapRef.current, {
          center: { lat: 12.9716, lng: 77.5946 },
          zoom: 13,
          styles: DARK_MAP_STYLES,
          disableDefaultUI: false,
          zoomControl: true,
          mapTypeControl: false,
          streetViewControl: false,
          fullscreenControl: true,
        })
        mapInstance.current = map
        infoWindowRef.current = new maps.InfoWindow()
        setIsLoading(false)
      })
      .catch((e) => {
        console.error('Map load error:', e)
        setError('Failed to load Google Maps.')
        setIsLoading(false)
      })
  }, [])

  // Draw/update circles whenever clusters change
  useEffect(() => {
    if (!mapInstance.current || isLoading) return

    Promise.all([importLibrary('maps'), importLibrary('core')]).then(([maps, core]) => {
      const bounds = new core.LatLngBounds()
      let hasValidCoordinates = false

      // Remove old circles
      circlesRef.current.forEach((c) => c.setMap(null))
      circlesRef.current = []

      clusters.forEach((cluster) => {
        if (!cluster.lat || !cluster.lng) return
        hasValidCoordinates = true
        bounds.extend({ lat: cluster.lat, lng: cluster.lng })

        const { fill, stroke } = getPriorityColor(cluster.priority_score)
        const radius = 150 + (cluster.demand_count / 312) * 300 // 150–450m

        const circle = new maps.Circle({
          strokeColor: stroke,
          strokeOpacity: 0.8,
          strokeWeight: 2,
          fillColor: fill,
          fillOpacity: 0.25,
          map: mapInstance.current,
          center: { lat: cluster.lat, lng: cluster.lng },
          radius,
        })

        circle.addListener('click', () => {
          const content = `
            <div style="
              background:#111827;
              color:#F9FAFB;
              border-radius:10px;
              padding:12px 16px;
              font-family:Inter,sans-serif;
              max-width:240px;
              border:1px solid rgba(99,102,241,0.3);
            ">
              <p style="font-size:13px;font-weight:700;margin:0 0 4px">${cluster.name}</p>
              <p style="font-size:11px;color:#9CA3AF;margin:0 0 6px">📍 ${cluster.location} · ${cluster.ward_id}</p>
              <div style="display:flex;gap:12px;font-size:12px">
                <span style="color:#818CF8">Score: <b>${cluster.priority_score}</b></span>
                <span style="color:#9CA3AF">${cluster.demand_count} citizens</span>
              </div>
            </div>
          `
          infoWindowRef.current.setContent(content)
          infoWindowRef.current.setPosition({ lat: cluster.lat, lng: cluster.lng })
          infoWindowRef.current.open(mapInstance.current)
          if (onClusterSelect) onClusterSelect(cluster)
        })

        circlesRef.current.push(circle)
      })

      if (hasValidCoordinates) {
        mapInstance.current.fitBounds(bounds)
      }
    })
  }, [clusters, isLoading, onClusterSelect])

  return (
    <div className="relative w-full h-full rounded-2xl overflow-hidden" style={{ minHeight: 360 }}>
      {isLoading && (
        <div
          className="absolute inset-0 flex flex-col items-center justify-center z-10 rounded-2xl"
          style={{ background: 'rgba(13,21,41,0.95)' }}
        >
          <div className="flex flex-col items-center gap-3">
            <div className="relative">
              <div
                className="w-12 h-12 rounded-full border-2 border-indigo-500/30 animate-pulse"
                style={{ background: 'rgba(99,102,241,0.1)' }}
              />
              <MapPin size={20} className="text-indigo-400 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
            </div>
            <p className="text-sm text-gray-400 animate-pulse">Loading constituency map…</p>
          </div>
        </div>
      )}

      {error && (
        <div
          className="absolute inset-0 flex flex-col items-center justify-center z-10 rounded-2xl"
          style={{ background: 'rgba(13,21,41,0.95)' }}
        >
          <MapPin size={32} className="text-indigo-400 mb-3" />
          <p className="text-sm text-gray-400 text-center px-8">{error}</p>
          <p className="text-xs text-gray-600 mt-2 text-center px-8">
            Add VITE_GOOGLE_MAPS_API_KEY to your .env file to enable map
          </p>
          {/* Fallback: show cluster list */}
          <div className="mt-4 w-full px-4 space-y-1 max-h-48 overflow-y-auto">
            {clusters.slice(0, 6).map((c) => (
              <button
                key={c.id}
                onClick={() => onClusterSelect && onClusterSelect(c)}
                className="w-full text-left px-3 py-2 rounded-lg text-xs text-gray-300 hover:bg-white/5 transition-colors flex justify-between"
              >
                <span className="truncate">{c.name}</span>
                <span className="text-indigo-400 font-bold ml-2">{c.priority_score}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      <div ref={mapRef} className="w-full h-full" style={{ minHeight: 360 }} />
    </div>
  )
}
