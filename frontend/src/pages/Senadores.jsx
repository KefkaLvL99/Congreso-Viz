// ============================================================
// pages/Senadores.jsx
// ============================================================

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

// Convierte "Camila Flores Oporto" → "Flores O., Camila"
// para buscar en el endpoint de parlamentarios
function nombreAFormatoXML(nombreCompleto) {
  if (!nombreCompleto) return nombreCompleto
  const partes = nombreCompleto.trim().split(/\s+/)
  if (partes.length < 2) return nombreCompleto
  // Últimas 2 palabras son apellidos, el resto es nombre
  const apellidoPaterno = partes[partes.length - 2]
  const apellidoMaterno = partes[partes.length - 1]
  const nombre = partes.slice(0, partes.length - 2).join(' ')
  const inicialMaterno = apellidoMaterno ? apellidoMaterno[0] + '.' : ''
  return `${apellidoPaterno} ${inicialMaterno}, ${nombre}`
}

function TarjetaSenador({ senador }) {
  const iniciales = [
    senador.nombre?.[0],
    senador.apellido_paterno?.[0],
  ].filter(Boolean).join('')

  const linkVotos = `/parlamentario/${encodeURIComponent(
    nombreAFormatoXML(senador.nombre_completo)
  )}`

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-600 transition-colors">
      <div className="flex items-center gap-4">

        <div className="w-10 h-10 rounded-full bg-blue-950 flex items-center justify-center text-blue-400 text-sm font-medium flex-shrink-0">
          {iniciales}
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-gray-100 text-sm font-medium truncate">
            {senador.nombre_completo}
          </p>
          <p className="text-gray-500 text-xs mt-0.5">
            {senador.region} · Circ. {senador.circunscripcion}
          </p>
        </div>

        <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
          <span className="text-xs px-2 py-0.5 rounded-full bg-gray-800 text-gray-400 border border-gray-700">
            {senador.partido ?? 'Sin partido'}
          </span>
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

export default function Senadores() {
  const [senadores, setSenadores] = useState([])
  const [busqueda, setBusqueda]   = useState('')
  const [cargando, setCargando]   = useState(true)
  const [error, setError]         = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/senadores/`)
      .then(r => { if (!r.ok) throw new Error(`Error HTTP ${r.status}`); return r.json() })
      .then(data => { setSenadores(data.senadores); setCargando(false) })
      .catch(err => { setError(err.message); setCargando(false) })
  }, [])

  const filtrados = senadores.filter(s => {
    const texto = busqueda.toLowerCase()
    return (
      s.nombre_completo?.toLowerCase().includes(texto) ||
      s.partido?.toLowerCase().includes(texto) ||
      s.region?.toLowerCase().includes(texto)
    )
  })

  if (cargando) return (
    <div className="max-w-6xl mx-auto px-6 py-12 text-center text-gray-500">
      Cargando senadores...
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
        <h1 className="text-xl font-medium text-gray-100">Senadores vigentes</h1>
        <p className="text-gray-500 text-sm mt-1">
          {senadores.length} senadores · Senado de Chile
        </p>
      </div>

      <div className="relative mb-6">
        <input
          type="text"
          placeholder="Buscar por nombre, partido o región..."
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

      {filtrados.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {filtrados.map(s => <TarjetaSenador key={s.id} senador={s} />)}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-600">
          No se encontraron senadores con "{busqueda}"
        </div>
      )}

    </div>
  )
}
