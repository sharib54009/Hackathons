import { divIcon } from 'leaflet'
import { MapContainer, Marker, Polyline, TileLayer, Tooltip } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

// divIcon avoids Leaflet's default image-path issue in Vite builds.
const vehicleIcon = divIcon({
  className: 'saferoute-marker',
  html: '<span class="saferoute-marker__vehicle" aria-hidden="true">●</span>',
  iconSize: [28, 28], iconAnchor: [14, 14],
})
const destinationIcon = divIcon({
  className: 'saferoute-marker',
  html: '<span class="saferoute-marker__destination" aria-hidden="true">⌖</span>',
  iconSize: [34, 34], iconAnchor: [17, 34],
})

function Map({ center, vehiclePosition, destination, route = [], actualRoute = [], zoom = 13, className = '' }) {
  return <MapContainer center={center} zoom={zoom} scrollWheelZoom className={`saferoute-map ${className}`}>
    <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
    {route.length > 1 && <Polyline positions={route} pathOptions={{ color: '#0284c7', weight: 5, opacity: 0.85 }} />}
    {actualRoute.length > 1 && <Polyline positions={actualRoute} pathOptions={{ color: '#f97316', weight: 5, opacity: 0.9, dashArray: '8 8' }} />}
    {vehiclePosition && <Marker position={vehiclePosition} icon={vehicleIcon}><Tooltip direction="top" offset={[0, -14]}>Current vehicle position</Tooltip></Marker>}
    {destination?.position && <Marker position={destination.position} icon={destinationIcon}><Tooltip direction="top" offset={[0, -30]}>{destination.name || 'Destination'}</Tooltip></Marker>}
  </MapContainer>
}

export default Map
