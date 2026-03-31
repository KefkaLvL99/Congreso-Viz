// ============================================================
// pages/Busqueda.jsx — Buscador unificado de parlamentarios
// ============================================================

import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

const MODOS = [
  { key: 'nombre',  label: 'Por nombre',  placeholder: 'Ej: Flores, Macaya, Yasna...' },
  { key: 'partido', label: 'Por partido', placeholder: 'Ej: UDI, RN, PS, Frente Amplio...' },
  { key: 'region',  label: 'Por región',  placeholder: 'Ej: Valparaíso, Maule, Biobío...' },
]

function BadgeCamara({ camara }) {
  const esSenado = camara === 'Senado'
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border flex-shrink-0 ${
      esSenado
        ? 'bg-purple-950 text-purple-400 border-purple-900'
        : 'bg-blue-950 text-blue-400 border-blue-900'
    }`}>
      {esSenado ? 'Senado' : 'Cámara'}
    </span>
  )
}

function TarjetaParlamentario({ resultado }) {
  const iniciales = resultado.nombre_completo
    ?.split(/\s+/).filter(Boolean).slice(0, 2).map(p => p[0]).join('') || '?'

  return (
    <Link
      to={`/parlamentario/${encodeURIComponent(resultado.nombre_xml)}`}
      className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-600 transition-colors flex items-center gap-4"
    >
      <div className="w-10 h-10 rounded-full bg-blue-950 flex items-center justify-center text-blue-400 text-sm font-medium flex-shrink-0">
        {iniciales}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-gray-100 text-sm font-medium truncate">{resultado.nombre_completo}</p>
        <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-0.5">
          {resultado.partido && (
            <span className="text-gray-500 text-xs">{resultado.partido}</span>
          )}
          {resultado.region && (
            <span className="text-gray-600 text-xs truncate">{resultado.region}</span>
          )}
        </div>
      </div>
      <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
        <BadgeCamara camara={resultado.camara} />
        {resultado.territorio && (
          <span className="text-gray-600 text-xs">{resultado.territorio}</span>
        )}
      </div>
    </Link>
  )
}

export default function Busqueda() {
  const [query, setQuery]       = useState('')
  const [modo, setModo]         = useState('nombre')
  const [resultados, setResultados] = useState([])
  const [cargando, setCargando] = useState(false)
  const [buscado, setBuscado]   = useState(false)
  const inputRef = useRef(null)

  useEffect(() => { inputRef.current?.focus() }, [])

  // Reset al cambiar modo
  useEffect(() => {
    setQuery('')
    setResultados([])
    setBuscado(false)
    inputRef.current?.focus()
  }, [modo])

  // Búsqueda con debounce
  useEffect(() => {
    if (query.trim().length < 2) {
      setResultados([])
      setBuscado(false)
      return
    }

    const timer = setTimeout(() => {
      setCargando(true)
      fetch(`${API_URL}/busqueda/?q=${encodeURIComponent(query.trim())}&modo=${modo}`)
        .then(r => r.json())
        .then(data => {
          setResultados(data.resultados ?? [])
          setBuscado(true)
          setCargando(false)
        })
        .catch(() => setCargando(false))
    }, 300)

    return () => clearTimeout(timer)
  }, [query, modo])

  const modoActual = MODOS.find(m => m.key === modo)

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">

      <div className="mb-6">
        <h1 className="text-xl font-medium text-gray-100">Buscar parlamentario</h1>
        <p className="text-gray-500 text-sm mt-1">
          Senadores y diputados vigentes
        </p>
      </div>

      {/* Selector de modo */}
      <div className="flex gap-2 mb-4">
        {MODOS.map(m => (
          <button
            key={m.key}
            onClick={() => setModo(m.key)}
            className={`text-xs px-4 py-2 rounded-lg border transition-colors ${
              modo === m.key
                ? 'bg-gray-700 border-gray-600 text-gray-100'
                : 'bg-gray-900 border-gray-800 text-gray-500 hover:border-gray-700 hover:text-gray-300'
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="relative mb-6">
        <input
          ref={inputRef}
          type="text"
          placeholder={modoActual?.placeholder}
          value={query}
          onChange={e => setQuery(e.target.value)}
          className="w-full bg-gray-900 border border-gray-700 rounded-xl px-5 py-3.5 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-gray-500 transition-colors"
        />
        {cargando && (
          <div className="absolute right-4 top-3.5">
            <div className="w-4 h-4 rounded-full border-2 border-gray-600 border-t-gray-300 animate-spin" />
          </div>
        )}
        {query && !cargando && (
          <button
            onClick={() => setQuery('')}
            className="absolute right-4 top-3.5 text-gray-600 hover:text-gray-400 transition-colors"
          >
            ✕
          </button>
        )}
      </div>

      {/* Contador */}
      {buscado && !cargando && (
        <p className="text-gray-600 text-xs mb-4">
          {resultados.length > 0
            ? `${resultados.length} resultado${resultados.length !== 1 ? 's' : ''} para "${query}"`
            : `Sin resultados para "${query}"`
          }
        </p>
      )}

      {/* Resultados */}
      {resultados.length > 0 && (
        <div className="space-y-2">
          {resultados.map((r, i) => (
            <TarjetaParlamentario key={i} resultado={r} />
          ))}
        </div>
      )}

      {buscado && resultados.length === 0 && !cargando && (
        <div className="text-center py-12">
          <p className="text-gray-600 text-sm">No se encontraron resultados para "{query}"</p>
          <p className="text-gray-700 text-xs mt-1">
            {modo === 'partido' && 'Prueba con siglas como UDI, RN, PS, PC, PPD...'}
            {modo === 'nombre'  && 'Prueba con apellido o nombre completo'}
            {modo === 'region'  && 'Prueba con el nombre de la región sin "Región de"'}
          </p>
        </div>
      )}

      {!buscado && !cargando && (
        <div className="text-center py-12 text-gray-700 text-sm">
          Escribe al menos 2 caracteres para buscar
        </div>
      )}

    </div>
  )
}
