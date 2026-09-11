import { useEffect, useState } from 'react'
import { io } from 'socket.io-client'
import Map from './components/Map.jsx'
import { vijayawadaDemoRoute } from './data/routes.js'
import { API_BASE_URL, createRide, respondToCheckin, simulateSafetyIncident, triggerSos } from './services/api.js'

const initialUpdate = { risk_score: 15, risk_level: 'SAFE', status: 'active', signals: [{ signal: 'Journey appears normal.' }], high_risk_threshold: 75 }

function Header({ go }) { return <header className="border-b border-slate-200 bg-white"><div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4"><div><b className="text-xl">SafeRoute</b><p className="text-xs text-slate-500">Ride with confidence</p></div><button onClick={() => go('guardian')} className="rounded-lg px-3 py-2 text-sm font-semibold text-sky-700">Guardian</button></div></header> }
function RideMap({ update }) { const actualRoute = update?.actual_route?.map(p => [p.latitude, p.longitude]) || []; const point = update?.current_location; return <Map {...vijayawadaDemoRoute} vehiclePosition={point ? [point.latitude, point.longitude] : vijayawadaDemoRoute.vehiclePosition} actualRoute={actualRoute} className="h-72 rounded-2xl border border-sky-100 sm:h-96" /> }
function Status({ update }) { const signals = update?.signals?.map(s => s.signal) || ['Journey appears normal.']; const high = update?.risk_score >= update?.high_risk_threshold; return <div className="space-y-5"><section className={`rounded-2xl border p-5 ${high ? 'border-rose-200 bg-rose-50' : 'border-emerald-100 bg-emerald-50'}`}><div className="flex justify-between"><div><p className="text-sm font-semibold">Current risk score</p><p className="text-4xl font-black">{update?.risk_score ?? 15}<span className="text-lg">/100</span></p></div><span className={`h-fit rounded-full px-3 py-1 text-xs font-bold text-white ${high ? 'bg-rose-600' : 'bg-emerald-600'}`}>{update?.risk_level ?? 'SAFE'}</span></div><p className="mt-3 text-sm font-medium">{signals.at(-1)}</p></section><section className="rounded-2xl border bg-white p-5"><h2 className="font-bold">Detected safety signals</h2><ul className="mt-3 space-y-2 text-sm">{signals.map(s => <li key={s}>• {s}</li>)}</ul></section></div> }
function CheckIn({ onRespond }) { return <section className="rounded-2xl border border-amber-200 bg-amber-50 p-4 shadow-sm"><p className="font-bold text-amber-900">Are you safe?</p><p className="mt-1 text-sm text-amber-800">Your guardian may be notified if you cannot respond.</p><div className="mt-3 grid gap-2 sm:grid-cols-3"><button onClick={() => onRespond('safe')} className="rounded-xl bg-emerald-600 p-3 font-bold text-white">I&apos;m Safe</button><button onClick={() => onRespond('help')} className="rounded-xl bg-rose-600 p-3 font-bold text-white">I Need Help</button><button onClick={() => onRespond('cannot_respond')} className="rounded-xl border border-amber-300 bg-white p-3 font-bold text-amber-900">I Can&apos;t Respond</button></div></section> }
function SafetyAlert({ alert }) { if (!alert) return null; const location = alert.current_location; return <section className="mb-6 rounded-2xl border-2 border-rose-300 bg-rose-50 p-5 text-rose-950 shadow-sm"><p className="text-sm font-black uppercase tracking-wide">Possible safety incident detected</p><h2 className="mt-1 text-xl font-bold">{alert.rider_name} · {alert.risk_level} · {alert.risk_score}/100</h2><p className="mt-2 text-sm font-medium">{alert.message}</p><p className="mt-2 text-sm">Detected anomalies: {alert.signals?.join(', ') || 'None reported'}</p><p className="text-sm">Current location: {location ? `${Number(location.latitude).toFixed(5)}, ${Number(location.longitude).toFixed(5)}` : 'Unavailable'}</p><p className="text-sm">Timestamp: {alert.timestamp ? new Date(alert.timestamp).toLocaleString() : 'Unavailable'}</p><div className="mt-4 grid gap-2 sm:grid-cols-3"><button onClick={() => window.alert(`Call ${alert.rider_name}`)} className="rounded-xl border border-rose-300 bg-white p-3 font-bold">Call Rider</button><button onClick={() => window.alert('Live location is shown on the map.')} className="rounded-xl border border-rose-300 bg-white p-3 font-bold">Open Live Location</button><button onClick={() => window.alert('Prototype only: this does not contact 112.')} className="rounded-xl bg-rose-700 p-3 font-bold text-white">Emergency / 112</button></div></section> }
function Home({ start, go }) { const [form, setForm] = useState({ name: '', start: '', destination: '', contact: '' }); const [error, setError] = useState(''); const input = (label, key) => <label className="block"><span className="mb-1 block text-sm font-semibold">{label}</span><input required value={form[key]} onChange={e => setForm({ ...form, [key]: e.target.value })} className="w-full rounded-xl border p-3" /></label>; const submit = async e => { e.preventDefault(); setError(''); try { await start(form) } catch (x) { setError(x.message || 'Unable to start your ride. Please try again.') } }; return <main className="min-h-screen bg-slate-50"><Header go={go}/><div className="mx-auto grid max-w-5xl gap-10 px-5 py-16 lg:grid-cols-2"><section><p className="font-bold text-sky-700">PROACTIVE RIDE SAFETY</p><h1 className="mt-4 text-5xl font-black">Safety that doesn&apos;t wait for an SOS.</h1></section><form onSubmit={submit} className="space-y-4 rounded-3xl border bg-white p-7 shadow"><h2 className="text-2xl font-bold">Start a safe ride</h2>{input('Your name', 'name')}{input('Starting location', 'start')}{input('Destination', 'destination')}{input('Trusted contact', 'contact')}{error && <p role="alert" className="text-sm text-rose-700">{error}</p>}<button className="w-full rounded-xl bg-sky-600 p-4 font-bold text-white">Start Safe Ride →</button></form></div></main> }
function Active({ ride, update, simulate, running, go, checkIn, onCheckin, onSos }) { const high = update.risk_score >= update.high_risk_threshold; return <main className="min-h-screen bg-slate-50"><Header go={go}/><div className="mx-auto max-w-6xl px-5 py-7"><section className={`mb-6 flex items-center justify-between rounded-2xl p-5 text-white ${high ? 'bg-rose-700' : 'bg-slate-950'}`}><div><p className="text-sm font-bold">{high ? 'HIGH-RISK JOURNEY' : 'JOURNEY IN PROGRESS'}</p><h1 className="text-2xl font-bold">Heading to {ride.destination}</h1><p className="text-sm">Status: {update.status}</p></div><div className="flex gap-2"><button onClick={onSos} className="rounded-xl bg-rose-500 px-4 py-3 font-black text-white">SOS</button><button disabled={running} onClick={simulate} className="rounded-xl bg-white px-4 py-3 font-bold text-slate-900 disabled:opacity-60">{running ? 'Simulation running…' : 'Simulate Safety Incident'}</button></div></section>{checkIn && <div className="mb-6"><CheckIn onRespond={onCheckin}/></div>}<div className="grid gap-6 lg:grid-cols-[1.35fr_.85fr]"><section><RideMap update={update}/><p className="mt-3 rounded-xl border bg-white p-3 text-sm">Journey status: <b>{update.status}</b></p></section><Status update={update}/></div></div></main> }
function Guardian({ ride, update, go, alert }) { const high = update.risk_score >= update.high_risk_threshold; const location = update.current_location; return <main className="min-h-screen bg-slate-50"><Header go={go}/><div className="mx-auto max-w-6xl px-5 py-7"><SafetyAlert alert={alert}/><section className={`mb-6 rounded-2xl p-5 ${high ? 'bg-rose-50 text-rose-800' : 'bg-sky-50 text-sky-800'}`}><p className="text-sm font-black">{high ? 'HIGH-RISK JOURNEY' : 'RIDING NOW'}</p><h1 className="text-2xl font-bold">{ride?.name || 'No active rider'}</h1></section><div className="grid gap-6 lg:grid-cols-[1.35fr_.85fr]"><section><RideMap update={update}/><div className="mt-4 rounded-2xl border bg-white p-4 text-sm"><p><b>Current location:</b> {location ? `${location.latitude.toFixed(5)}, ${location.longitude.toFixed(5)}` : 'Awaiting location'}</p><p><b>Expected route:</b> blue line</p><p><b>Actual route:</b> orange dashed line</p><p><b>Timestamp:</b> {update.timestamp ? new Date(update.timestamp).toLocaleString() : '—'}</p></div></section><div><Status update={update}/><section className="mt-6 rounded-2xl border bg-white p-5"><h2 className="font-bold">Emergency actions</h2><div className="mt-4 grid gap-3"><button className="rounded-xl border p-3 font-semibold">Check in with rider</button><button className="rounded-xl bg-rose-600 p-3 font-bold text-white">Emergency help</button></div></section></div></div></div></main> }
function getStoredRide() { try { return JSON.parse(window.localStorage.getItem('saferoute.activeRide')) } catch { return null } }

function App() {
	const [view, setView] = useState('home')
	const [ride, setRide] = useState(getStoredRide)
	const [update, setUpdate] = useState(initialUpdate)
	const [running, setRunning] = useState(false)
	const [checkIn, setCheckIn] = useState(null)
	const [alert, setAlert] = useState(null)

	useEffect(() => {
		const socket = io(API_BASE_URL, { transports: ['polling'] })
		const rideId = () => ride?.id || getStoredRide()?.id
		const matchesRide = data => data.ride_id === rideId()
		const mergeRisk = data => {
			if (!matchesRide(data)) return
			setUpdate(previous => ({ ...previous, ...data, signals: data.signals.map(signal => typeof signal === 'string' ? { signal } : signal) }))
		}
		const receiveLocation = data => {
			if (!matchesRide(data)) return
			setUpdate(previous => ({ ...previous, current_location: data.location, actual_route: data.actual_route, timestamp: data.timestamp }))
		}
		const receiveAlert = data => mergeRisk(data)
		const receiveSafetyAlert = data => {
			if (!matchesRide(data)) return
			setAlert(data)
			setCheckIn(null)
			setRunning(false)
		}
		const receiveCheckin = data => {
			if (matchesRide(data)) setCheckIn(data)
		}
		const receiveStoredRide = event => {
			if (!event.newValue) return
			try { setRide(JSON.parse(event.newValue)) } catch { /* Ignore malformed local state. */ }
		}

		socket.on('location_update', receiveLocation)
		socket.on('risk_update', mergeRisk)
		socket.on('safety_alert', receiveSafetyAlert)
		socket.on('check_in_requested', receiveCheckin)
		window.addEventListener('storage', receiveStoredRide)
		return () => {
			socket.off('location_update', receiveLocation)
			socket.off('risk_update', mergeRisk)
			socket.off('safety_alert', receiveSafetyAlert)
			socket.off('check_in_requested', receiveCheckin)
			window.removeEventListener('storage', receiveStoredRide)
			socket.disconnect()
		}
	}, [ride?.id])

	const start = async form => {
		const created = await createRide({ riderName: form.name, origin: form.start, destination: form.destination, trustedContact: form.contact })
		const nextRide = { ...form, id: created.ride_id }
		setRide(nextRide)
		window.localStorage.setItem('saferoute.activeRide', JSON.stringify(nextRide))
		setUpdate({ ...initialUpdate, ...created })
		setView('active')
	}
	const simulate = async () => {
		try { setRunning(true); await simulateSafetyIncident(ride.id) } catch (x) { setRunning(false); window.alert(x.message) }
	}
	const respond = async response => {
		try { await respondToCheckin(ride.id, response); setCheckIn(null) } catch (x) { window.alert(x.message) }
	}
	const onSos = async () => {
		try { const created = await triggerSos(ride.id); setAlert(created) } catch (x) { window.alert(x.message) }
	}
	if (view === 'guardian') return <Guardian ride={ride} update={update} alert={alert} go={setView}/>
	if (view === 'active' && ride) return <Active ride={ride} update={update} simulate={simulate} running={running} checkIn={checkIn} onCheckin={respond} onSos={onSos} go={setView}/>
	return <Home start={start} go={setView}/>
}
export default App
