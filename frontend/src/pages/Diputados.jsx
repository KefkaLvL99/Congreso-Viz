// ============================================================
// pages/Diputados.jsx
// ============================================================

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

const API_URL = 'http://localhost:8000'

// Convierte "Camila Flores Oporto" → "Flores O., Camila"
function nombreAFormatoXML(nombreCompleto) {
  if (!nombreCompleto) return nombreCompleto
  const partes = nombreCompleto.trim().split(/\s+/)
  if (partes.length < 2) return nombreCompleto
  const apellidoPaterno = partes[partes.length - 2]
  const apellidoMaterno = partes[partes.length - 1]
  const nombre = partes.slice(0, partes.length - 2).join(' ')
  const inicialMaterno = apellidoMaterno ? apellidoMaterno[0] + '.' : ''
  return `${apellidoPaterno} ${inicialMaterno}, ${nombre}`
}

function TarjetaDiputado({ diputado }) {
  const iniciales = [
    diputado.nombre?.[0],
    diputado.apellido_paterno?.[0],
  ].filter(Boolean).join('')

  const linkVotos = `/parlamentario/${encodeURIComponent(diputado.nombre_completo)}`

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-600 transition-colors">
      <div className="flex items-center gap-4">

        <div className="w-10 h-10 rounded-full bg-blue-950 flex items-center justify-center text-blue-400 text-sm font-medium flex-shrink-0">
          {iniciales}
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-gray-100 text-sm font-medium truncate">
            {diputado.nombre_completo}
          </p>
          <p className="text-gray-500 text-xs mt-0.5">
            {diputado.region} · {diputado.distrito}
          </p>
        </div>

        <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
          <span className="text-xs px-2 py-0.5 rounded-full bg-gray-800 text-gray-400 border border-gray-700">
            {diputado.partido ?? 'Sin partido'}
          </span>
          {diputado.bancada && diputado.bancada !== diputado.partido && (
            <span className="text-xs text-gray-600">{diputado.bancada}</span>
          )}
          <Link
            to={linkVotos}
            className="text-xs text-blue-500 hover:text-blue-300 transition-colors"
          >
            Ver votos →
          </Link>
        </div>

      </div>
    </div>
  )
}

export default function Diputados() {
  const [diputados, setDiputados] = useState([])
  const [busqueda, setBusqueda]   = useState('')
  const [filtroRegion, setFiltroRegion] = useState('Todas')
  const [cargando, setCargando]   = useState(true)
  const [error, setError]         = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/diputados/`)
      .then(r => { if (!r.ok) throw new Error(`Error HTTP ${r.status}`); return r.json() })
      .then(data => { setDiputados(data.diputados); setCargando(false) })
      .catch(err => { setError(err.message); setCargando(false) })
  }, [])

  const regiones = ['Todas', ...new Set(
    diputados.map(d => d.region).filter(Boolean).sort()
  )]

  const filtrados = diputados.filter(d => {
    const texto = busqueda.toLowerCase()
    const coincideNombre = (
      d.nombre_completo?.toLowerCase().includes(texto) ||
      d.partido?.toLowerCase().includes(texto) ||
      d.bancada?.toLowerCase().includes(texto)
    )
    const coincideRegion = filtroRegion === 'Todas' || d.region === filtroRegion
    return coincideNombre && coincideRegion
  })

  if (cargando) return (
    <div className="max-w-6xl mx-auto px-6 py-12 text-center text-gray-500">
      Cargando diputados...
    </div>
  )

  if (error) return (
    <div className="max-w-6xl mx-auto px-6 py-12 text-center text-red-400">
      Error: {error}
    </div>
  )

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">

      <div className="mb-6">
        <h1 className="text-xl font-medium text-gray-100">Diputados vigentes</h1>
        <p className="text-gray-500 text-sm mt-1">
          {diputados.length} diputados · Cámara de Diputadas y Diputados de Chile
        </p>
      </div>

      <div className="relative mb-4">
        <input
          type="text"
          placeholder="Buscar por nombre, partido o bancada..."
          value={busqueda}
          onChange={e => setBusqueda(e.target.value)}
          className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-gray-500"
        />
        {busqueda && (
          <span className="absolute right-3 top-2.5 text-xs text-gray-600">
            {filtrados.length} resultado{filtrados.length !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      <div className="mb-6 overflow-x-auto">
        <div className="flex gap-2 pb-1" style={{ minWidth: 'max-content' }}>
          {regiones.map(region => (
            <button
              key={region}
              onClick={() => setFiltroRegion(region)}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-colors whitespace-nowrap ${
                filtroRegion === region
                  ? 'bg-gray-700 border-gray-600 text-gray-100'
                  : 'bg-gray-900 border-gray-800 text-gray-500 hover:border-gray-700'
              }`}
            >
              {region === 'Todas' ? 'Todas las regiones'
                : region.replace('Región de la ', '').replace('Región de ', '')
                        .replace('Región del ', '').replace('Región ', '')}
            </button>
          ))}
        </div>
      </div>

      <p className="text-gray-600 text-xs mb-4">
        {filtrados.length} de {diputados.length} diputados
      </p>

      {filtrados.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {filtrados.map(d => <TarjetaDiputado key={d.id} diputado={d} />)}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-600">
          No se encontraron diputados con "{busqueda}"
        </div>
      )}

    </div>
  )
}
