const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000'

export { API_BASE_URL }

export async function createRide({ riderName, origin, destination, trustedContact }) {
  const response = await fetch(`${API_BASE_URL}/api/rides`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      rider_name: riderName,
      origin,
      destination,
      trusted_contact: trustedContact,
    }),
  })

  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.error || 'Unable to start your ride. Please try again.')
  return data
}

export async function simulateSafetyIncident(rideId) {
  const response = await fetch(`${API_BASE_URL}/api/rides/${rideId}/simulate-safety-incident`, { method: 'POST' })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.error || 'Unable to start the incident simulation.')
  return data
}

async function postRideAction(path, rideId, body) {
  const response = await fetch(`${API_BASE_URL}/api/rides/${rideId}/${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.error || 'Unable to complete the safety action.')
  return data
}

export function respondToCheckin(rideId, response) {
  return postRideAction('check-ins/respond', rideId, { response })
}

export function triggerSos(rideId) {
  return postRideAction('sos', rideId)
}
