// ============================================================
// pages/Leyes.jsx — Últimas leyes publicadas
// ============================================================

import { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

function BadgeTipo({ tipo }) {
  const estilos = {
    'Ley':         'bg-green-950 text-green-400 border-green-900',
    'Decreto Ley': 'bg-yellow-950 text-yellow-400 border-yellow-900',
    'Dfl':         'bg-blue-950 text-blue-400 border-blue-900',
  }
  const clase = estilos[tipo] ?? 'bg-gray-800 text-gray-400 border-gray-700'
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border flex-shrink-0 ${clase}`}>
      {tipo}
    </span>
  )
}

function ResumenLey({ ley }) {
  const [resumen, setResumen]   = useState(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError]       = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/leyes/${ley.id_norma}/resumen`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        titulo: ley.titulo,
        numero: ley.numero,
        texto:  ley.texto || ley.titulo,
      })
    })
      .then(r => { if (!r.ok) throw new Error('Error al generar resumen'); return r.json() })
      .then(data => { setResumen(data.resumen); setCargando(false) })
      .catch(err => { setError(err.message); setCargando(false) })
  }, [ley.id_norma])

  if (cargando) return (
    <div className="flex items-center gap-2 py-2">
      <div className="w-3 h-3 rounded-full bg-blue-500 animate-pulse" />
      <span className="text-gray-500 text-xs">Claude está analizando la ley...</span>
    </div>
  )
  if (error) return <div className="text-red-500 text-xs py-1">{error}</div>
  return (
    <div className="space-y-2">
      {resumen.split('\n\n').filter(p => p.trim()).map((p, i) => (
        <p key={i} className="text-gray-300 text-xs leading-relaxed">{p}</p>
      ))}
    </div>
  )
}

function TarjetaLey({ ley }) {
  const [verResumen, setVerResumen] = useState(false)

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden hover:border-gray-700 transition-colors">

      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className="flex-1 min-w-0">
            <p className="text-gray-100 text-sm leading-snug mb-2">
              {ley.titulo || '(Sin título)'}
            </p>
            <div className="flex flex-wrap gap-2 items-center">
              <BadgeTipo tipo={ley.tipo} />
              {ley.numero && (
                <span className="text-gray-400 text-xs font-medium">N° {ley.numero}</span>
              )}
              {ley.fecha_publicacion && (
                <span className="text-gray-600 text-xs">Publicada {ley.fecha_publicacion}</span>
              )}
              {ley.organismos?.length > 0 && (
                <span className="text-gray-600 text-xs">{ley.organismos[0]}</span>
              )}
            </div>
          </div>
          {ley.url && (
            <a href={ley.url} target="_blank" rel="noopener noreferrer"
              className="text-blue-500 hover:text-blue-300 text-xs transition-colors flex-shrink-0 mt-0.5">
              Ver texto ↗
            </a>
          )}
        </div>

        {/* Botón resumen IA */}
        <div className="mt-3">
          <button
            onClick={() => setVerResumen(!verResumen)}
            className={`text-xs px-3 py-1.5 rounded-lg border transition-colors flex items-center gap-1.5 ${
              verResumen
                ? 'bg-blue-950 border-blue-800 text-blue-300'
                : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-500 hover:text-gray-200'
            }`}>
            <span>✦</span>
            <span>{verResumen ? 'Ocultar resumen' : '¿Qué significa esta ley?'}</span>
          </button>
        </div>
      </div>

      {/* Resumen IA */}
      {verResumen && (
        <div className="mx-4 mb-4 p-3 bg-gray-800 border border-gray-700 rounded-lg">
          <p className="text-blue-400 text-xs font-medium mb-2">✦ Explicación por IA (puede ser impreciso)</p>
          <ResumenLey ley={ley} />
        </div>
      )}
    </div>
  )
}

const POR_PAGINA = 10

function PaginatedLeyes({ leyes, busqueda }) {
  const [pagina, setPagina] = useState(0)
  const total_paginas = Math.ceil(leyes.length / POR_PAGINA)
  const paginas = leyes.slice(pagina * POR_PAGINA, (pagina + 1) * POR_PAGINA)

  // Reset página al buscar
  useEffect(() => { setPagina(0) }, [busqueda])

  return (
    <>
      <p className="text-gray-600 text-xs mb-4">
        {leyes.length} ley{leyes.length !== 1 ? 'es' : ''}
        {busqueda ? ` con "${busqueda}"` : ' más recientes'}
        {total_paginas > 1 && ` · Página ${pagina + 1} de ${total_paginas}`}
      </p>

      <div className="space-y-3 mb-6">
        {paginas.map((ley, i) => (
          <TarjetaLey key={i} ley={ley} />
        ))}
      </div>

      {total_paginas > 1 && (
        <div className="flex items-center justify-between">
          <button onClick={() => setPagina(p => Math.max(0, p - 1))} disabled={pagina === 0}
            className="text-xs px-4 py-2 rounded-lg border border-gray-800 text-gray-500 hover:border-gray-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
            ← Anterior
          </button>
          <div className="flex gap-1">
            {Array.from({ length: total_paginas }, (_, i) => (
              <button key={i} onClick={() => setPagina(i)}
                className={`text-xs w-8 h-8 rounded-lg border transition-colors ${
                  pagina === i
                    ? 'bg-gray-700 border-gray-600 text-gray-100'
                    : 'bg-gray-900 border-gray-800 text-gray-500 hover:border-gray-700'
                }`}>{i + 1}</button>
            ))}
          </div>
          <button onClick={() => setPagina(p => Math.min(total_paginas - 1, p + 1))} disabled={pagina === total_paginas - 1}
            className="text-xs px-4 py-2 rounded-lg border border-gray-800 text-gray-500 hover:border-gray-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
            Siguiente →
          </button>
        </div>
      )}
    </>
  )
}

export default function Leyes() {
  const [leyes, setLeyes]       = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError]       = useState(null)
  const [busqueda, setBusqueda] = useState('')

  useEffect(() => {
    setCargando(true)
    fetch(`${API_URL}/leyes/recientes?cantidad=50`)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(data => { setLeyes(data.leyes ?? []); setCargando(false) })
      .catch(err => { setError(err.message); setCargando(false) })
  }, [])

  const filtradas = leyes.filter(l =>
    !busqueda ||
    l.titulo?.toLowerCase().includes(busqueda.toLowerCase()) ||
    l.numero?.includes(busqueda) ||
    l.organismos?.some(o => o.toLowerCase().includes(busqueda.toLowerCase()))
  )

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">

      <div className="mb-6">
        <h1 className="text-xl font-medium text-gray-100">Leyes publicadas</h1>
        <p className="text-gray-500 text-sm mt-1">
          Últimas 50 leyes promulgadas en el Diario Oficial · Fuente: Biblioteca del Congreso Nacional
        </p>
      </div>

      <div className="mb-6">
        <input
          type="text"
          placeholder="Buscar por título, número o ministerio..."
          value={busqueda}
          onChange={e => setBusqueda(e.target.value)}
          className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-gray-500"
        />
      </div>

      {cargando ? (
        <div className="text-center py-12 text-gray-500">Cargando leyes...</div>
      ) : error ? (
        <div className="text-center py-12 text-red-400">{error}</div>
      ) : (
        <PaginatedLeyes leyes={filtradas} busqueda={busqueda} />
      )}
    </div>
  )
}
