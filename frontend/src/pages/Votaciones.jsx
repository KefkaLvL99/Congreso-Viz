// ============================================================
// pages/Votaciones.jsx — Vista agrupada por proyecto
// ============================================================

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

function BadgeResultado({ resultado, small = false }) {
  const estilos = {
    'Aprobado':  'bg-green-950 text-green-400 border-green-900',
    'Rechazado': 'bg-red-950 text-red-400 border-red-900',
    'Empate':    'bg-yellow-950 text-yellow-400 border-yellow-900',
  }
  const clase = estilos[resultado] ?? 'bg-gray-800 text-gray-400 border-gray-700'
  return (
    <span className={`${small ? 'text-xs px-1.5 py-0' : 'text-xs px-2 py-0.5'} rounded-full border flex-shrink-0 ${clase}`}>
      {resultado}
    </span>
  )
}

function BadgeCamara({ camara }) {
  const es_camara = camara === 'C.Diputados'
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border flex-shrink-0 ${
      es_camara
        ? 'bg-blue-950 text-blue-400 border-blue-900'
        : 'bg-purple-950 text-purple-400 border-purple-900'
    }`}>
      {es_camara ? 'Cámara' : 'Senado'}
    </span>
  )
}

function ResumenIA({ boletin }) {
  const [resumen, setResumen]   = useState(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError]       = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/resumen/${boletin}`)
      .then(r => { if (!r.ok) throw new Error('Error al generar resumen'); return r.json() })
      .then(data => { setResumen(data.resumen); setCargando(false) })
      .catch(err => { setError(err.message); setCargando(false) })
  }, [boletin])

  if (cargando) return (
    <div className="flex items-center gap-2 py-3">
      <div className="w-3 h-3 rounded-full bg-blue-500 animate-pulse" />
      <span className="text-gray-500 text-xs">Claude está analizando el proyecto...</span>
    </div>
  )
  if (error) return <div className="text-red-500 text-xs py-2">{error}</div>
  return (
    <div className="space-y-2">
      {resumen.split('\n\n').filter(p => p.trim()).map((parrafo, i) => (
        <p key={i} className="text-gray-300 text-xs leading-relaxed">{parrafo}</p>
      ))}
    </div>
  )
}

function DetalleVotos({ votacionId }) {
  const [detalle, setDetalle]   = useState(null)
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    fetch(`${API_URL}/votaciones/${votacionId}/detalle`)
      .then(r => r.json())
      .then(data => { setDetalle(data); setCargando(false) })
      .catch(() => setCargando(false))
  }, [votacionId])

  if (cargando) return <div className="text-gray-600 text-xs py-2">Cargando...</div>
  if (!detalle || detalle.total_registros === 0) return (
    <div className="text-gray-600 text-xs py-2">Sin detalle de votos individuales</div>
  )

  const grupos = [
    { label: 'A favor',    key: 'si',         color: 'text-green-400' },
    { label: 'En contra',  key: 'no',         color: 'text-red-400'   },
    { label: 'Abstención', key: 'abstencion', color: 'text-yellow-400'},
    { label: 'Pareo',      key: 'pareo',      color: 'text-gray-400'  },
  ]

  return (
    <div className="mt-2 space-y-2">
      {grupos.map(g => {
        const votos = detalle.detalle[g.key] ?? []
        if (votos.length === 0) return null
        return (
          <div key={g.key}>
            <p className={`text-xs font-medium mb-1 ${g.color}`}>{g.label} ({votos.length})</p>
            <div className="flex flex-wrap gap-1">
              {votos.map((nombre, i) => (
                <Link key={i} to={`/parlamentario/${encodeURIComponent(nombre)}`}
                  className="text-xs px-2 py-0.5 bg-gray-800 text-gray-400 rounded border border-gray-700 hover:border-gray-500 hover:text-gray-200 transition-colors">
                  {nombre}
                </Link>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function FilaVotacion({ vot }) {
  const [expandida, setExpandida] = useState(false)
  const tema = vot.tema && vot.tema.length > 120 ? vot.tema.slice(0, 120) + '...' : vot.tema

  return (
    <div className="border-t border-gray-800">
      <div className="flex items-start gap-3 py-2.5 px-4">
        <span className="text-gray-600 text-xs flex-shrink-0 w-20 pt-0.5">{vot.fecha}</span>
        <div className="flex-1 min-w-0">
          <p className="text-gray-300 text-xs leading-snug">{tema}</p>
          {vot.tipo_votacion && <span className="text-gray-600 text-xs">{vot.tipo_votacion}</span>}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="text-green-600 text-xs">{vot.votos_si}</span>
          <span className="text-gray-700 text-xs">—</span>
          <span className="text-red-600 text-xs">{vot.votos_no}</span>
          <BadgeResultado resultado={vot.resultado} small />
        </div>
        {vot.tiene_detalle && (
          <button onClick={() => setExpandida(!expandida)}
            className="text-gray-700 hover:text-gray-400 text-xs transition-colors flex-shrink-0"
            title="Ver quién votó qué">
            {expandida ? '▲' : '▼'}
          </button>
        )}
      </div>
      {expandida && (
        <div className="px-4 pb-3 ml-20">
          <DetalleVotos votacionId={vot.id} />
        </div>
      )}
    </div>
  )
}

function TarjetaProyecto({ proyecto }) {
  const [expandido, setExpandido]   = useState(false)
  const [verResumen, setVerResumen] = useState(false)

  const resultados       = proyecto.votaciones.map(v => v.resultado)
  const hayRechazado     = resultados.includes('Rechazado')
  const todoAprobado     = resultados.every(r => r === 'Aprobado')
  const resultadoGeneral = todoAprobado ? 'Aprobado' : (hayRechazado ? 'Rechazado' : 'Mixto')

  const urlBoletin = proyecto.boletin
    ? `https://tramitacion.senado.cl/appsenado/templates/tramitacion/index.php?boletin_ini=${proyecto.boletin}`
    : null

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden hover:border-gray-700 transition-colors">
      <button onClick={() => setExpandido(!expandido)} className="w-full text-left px-4 py-3">
        <div className="flex items-start gap-3">
          <span className="text-gray-600 text-xs flex-shrink-0 pt-1">{expandido ? '▼' : '▶'}</span>
          <div className="flex-1 min-w-0">
            <p className="text-gray-100 text-sm leading-snug">{proyecto.titulo || '(Sin título)'}</p>
            <div className="flex flex-wrap gap-2 mt-1.5 items-center">
              {urlBoletin ? (
                <a href={urlBoletin} target="_blank" rel="noopener noreferrer"
                  className="text-blue-500 hover:text-blue-300 text-xs transition-colors"
                  onClick={e => e.stopPropagation()}>
                  Boletín {proyecto.boletin} ↗
                </a>
              ) : proyecto.boletin ? (
                <span className="text-gray-600 text-xs">Boletín {proyecto.boletin}</span>
              ) : null}
              <span className="text-gray-600 text-xs">{proyecto.ultima_fecha}</span>
              <BadgeCamara camara={proyecto.camara} />
              {proyecto.estado === 'En tramitación' && (
                <span className="text-xs px-1.5 py-0 rounded-full border bg-yellow-950 text-yellow-500 border-yellow-900">
                  En tramitación
                </span>
              )}
            </div>
          </div>
          <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
            <BadgeResultado resultado={resultadoGeneral} />
            <span className="text-gray-600 text-xs">
              {proyecto.total_votaciones} votación{proyecto.total_votaciones !== 1 ? 'es' : ''}
            </span>
          </div>
        </div>
      </button>

      {proyecto.boletin && (
        <div className="px-4 pb-3 flex items-center gap-3">
          <button onClick={e => { e.stopPropagation(); setVerResumen(!verResumen) }}
            className={`text-xs px-3 py-1.5 rounded-lg border transition-colors flex items-center gap-1.5 ${
              verResumen
                ? 'bg-blue-950 border-blue-800 text-blue-300'
                : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-500 hover:text-gray-200'
            }`}>
            <span>✦</span>
            <span>{verResumen ? 'Ocultar resumen' : '¿Qué significa esto?'}</span>
          </button>
        </div>
      )}

      {verResumen && proyecto.boletin && (
        <div className="mx-4 mb-4 p-3 bg-gray-800 border border-gray-700 rounded-lg">
          <p className="text-blue-400 text-xs font-medium mb-2">✦ Explicación realizada por IA (Podría ser impreciso)</p>
          <ResumenIA boletin={proyecto.boletin} />
        </div>
      )}

      {expandido && (
        <div className="bg-gray-950">
          {proyecto.votaciones.map(vot => <FilaVotacion key={vot.id} vot={vot} />)}
        </div>
      )}
    </div>
  )
}

export default function Votaciones() {
  const [proyectos, setProyectos]               = useState([])
  const [anios, setAnios]                       = useState([])
  const [anioSeleccionado, setAnioSeleccionado] = useState(undefined)
  const [filtroCamara, setFiltroCamara]         = useState('Todas')
  const [filtroTramitacion, setFiltroTramitacion] = useState(false)
  const [busqueda, setBusqueda]                 = useState('')
  const [cargando, setCargando]                 = useState(true)
  const [error, setError]                       = useState(null)
  const [pagina, setPagina]                     = useState(0)
  const [total, setTotal]                       = useState(0)

  const LIMITE = 20

  // Cargar años primero
  useEffect(() => {
    fetch(`${API_URL}/votaciones/anios`)
      .then(r => r.json())
      .then(data => {
        const lista = data.anios ?? []
        setAnios(lista)
        // Setear año inicial — null significa "sin setear aún" (undefined)
        // Ahora lo seteamos a primer año disponible
        setAnioSeleccionado(lista.length > 0 ? lista[0] : null)
      })
      .catch(() => setAnioSeleccionado(null))
  }, [])

  // Cargar votaciones solo cuando anioSeleccionado ya fue seteado (no undefined)
  useEffect(() => {
    if (anioSeleccionado === undefined) return  // aún cargando años
    setCargando(true)
    const params = new URLSearchParams({ limite: LIMITE, offset: pagina * LIMITE })
    if (anioSeleccionado)        params.append('anio',        anioSeleccionado)
    if (filtroCamara !== 'Todas') params.append('camara',      filtroCamara)
    if (filtroTramitacion)        params.append('tramitacion', 'true')

    fetch(`${API_URL}/votaciones/agrupadas?${params}`)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(data => {
        setProyectos(data.proyectos ?? [])
        setTotal(data.total_proyectos ?? 0)
        setCargando(false)
      })
      .catch(err => { setError(err.message); setCargando(false) })
  }, [pagina, filtroCamara, anioSeleccionado, filtroTramitacion])

  const filtrados = proyectos.filter(p =>
    !busqueda || p.titulo?.toLowerCase().includes(busqueda.toLowerCase()) ||
    p.boletin?.toLowerCase().includes(busqueda.toLowerCase())
  )

  if (error) return (
    <div className="max-w-6xl mx-auto px-6 py-12 text-center text-red-400">Error: {error}</div>
  )

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">

      <div className="mb-4">
        <h1 className="text-xl font-medium text-gray-100">Votaciones del Congreso</h1>
        <p className="text-gray-500 text-sm mt-1">
          {total} proyectos{anioSeleccionado ? ` en ${anioSeleccionado}` : ''} · Senado y Cámara
        </p>
      </div>

      {/* Aviso de desfase */}
      <div className="mb-6 p-3 bg-gray-800 border border-gray-700 rounded-lg">
        <p className="text-gray-500 text-xs">
          ℹ️ Los datos provienen de las APIs oficiales del Senado y la Cámara de Diputados.
          Las votaciones pueden tener un desfase de publicación según los plazos de cada institución.
          Para información en tiempo real visita{' '}
          <a href="https://www.senado.cl" target="_blank" rel="noopener noreferrer"
            className="text-blue-500 hover:text-blue-300 transition-colors">senado.cl</a>
          {' '}o{' '}
          <a href="https://www.camara.cl" target="_blank" rel="noopener noreferrer"
            className="text-blue-500 hover:text-blue-300 transition-colors">camara.cl</a>
        </p>
      </div>

      {/* Selector de año */}
      {anios.length > 0 && (
        <div className="mb-4 overflow-x-auto">
          <div className="flex gap-2 pb-1" style={{ minWidth: 'max-content' }}>
            <button onClick={() => { setAnioSeleccionado(null); setPagina(0) }}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                anioSeleccionado === null
                  ? 'bg-gray-700 border-gray-600 text-gray-100'
                  : 'bg-gray-900 border-gray-800 text-gray-500 hover:border-gray-700'
              }`}>Todos</button>
            {anios.map(a => (
              <button key={a} onClick={() => { setAnioSeleccionado(a); setPagina(0) }}
                className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                  anioSeleccionado === a
                    ? 'bg-gray-700 border-gray-600 text-gray-100'
                    : 'bg-gray-900 border-gray-800 text-gray-500 hover:border-gray-700'
                }`}>{a}</button>
            ))}
          </div>
        </div>
      )}

      {/* Filtros */}
      <div className="flex gap-3 mb-6 flex-wrap">
        <input type="text" placeholder="Buscar por título o boletín..."
          value={busqueda} onChange={e => setBusqueda(e.target.value)}
          className="flex-1 min-w-48 bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-gray-500"
        />
        <div className="flex gap-2 flex-wrap">
          {['Todas', 'Senado', 'C.Diputados'].map(c => (
            <button key={c} onClick={() => { setFiltroCamara(c); setPagina(0) }}
              className={`text-xs px-3 py-2 rounded-lg border transition-colors ${
                filtroCamara === c
                  ? 'bg-gray-700 border-gray-600 text-gray-100'
                  : 'bg-gray-900 border-gray-800 text-gray-500 hover:border-gray-700'
              }`}>{c === 'C.Diputados' ? 'Cámara' : c}</button>
          ))}
          <div className="w-px bg-gray-800 mx-1" />
          <button onClick={() => { setFiltroTramitacion(!filtroTramitacion); setPagina(0) }}
            className={`text-xs px-3 py-2 rounded-lg border transition-colors ${
              filtroTramitacion
                ? 'bg-yellow-950 border-yellow-900 text-yellow-400'
                : 'bg-gray-900 border-gray-800 text-gray-500 hover:border-gray-700'
            }`}>En tramitación</button>
        </div>
      </div>

      {cargando ? (
        <div className="text-center py-12 text-gray-500">Cargando votaciones...</div>
      ) : filtrados.length > 0 ? (
        <>
          <div className="space-y-3 mb-6">
            {filtrados.map(p => (
              <TarjetaProyecto key={`${p.boletin}-${p.ultima_fecha}`} proyecto={p} />
            ))}
          </div>
          <div className="flex items-center justify-between">
            <button onClick={() => setPagina(p => Math.max(0, p - 1))} disabled={pagina === 0}
              className="text-xs px-4 py-2 rounded-lg border border-gray-800 text-gray-500 hover:border-gray-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
              ← Anterior
            </button>
            <span className="text-gray-600 text-xs">
              Página {pagina + 1} de {Math.ceil(total / LIMITE)}
            </span>
            <button onClick={() => setPagina(p => p + 1)} disabled={(pagina + 1) * LIMITE >= total}
              className="text-xs px-4 py-2 rounded-lg border border-gray-800 text-gray-500 hover:border-gray-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
              Siguiente →
            </button>
          </div>
        </>
      ) : (
        <div className="text-center py-12 text-gray-600">
          No hay proyectos{anioSeleccionado ? ` en ${anioSeleccionado}` : ''}
          {filtroTramitacion ? ' en tramitación' : ''}
          {busqueda ? ` con "${busqueda}"` : ''}
        </div>
      )}
    </div>
  )
}
