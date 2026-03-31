// ============================================================
// pages/Parlamentario.jsx
// ============================================================

import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'

const API_URL = 'http://localhost:8000'

function BadgeVoto({ seleccion }) {
  const estilos = {
    'Si':         'bg-green-950 text-green-400 border-green-900',
    'No':         'bg-red-950 text-red-400 border-red-900',
    'Abstencion': 'bg-yellow-950 text-yellow-400 border-yellow-900',
    'Pareo':      'bg-gray-800 text-gray-500 border-gray-700',
  }
  const labels = {
    'Si': 'A favor', 'No': 'En contra',
    'Abstencion': 'Abstención', 'Pareo': 'Pareo',
  }
  const clase = estilos[seleccion] ?? 'bg-gray-800 text-gray-400 border-gray-700'
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border flex-shrink-0 ${clase}`}>
      {labels[seleccion] ?? seleccion}
    </span>
  )
}

function Estadistica({ label, valor, color }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-3 text-center">
      <p className={`text-xl font-medium ${color}`}>{valor}</p>
      <p className="text-gray-600 text-xs mt-0.5">{label}</p>
    </div>
  )
}

function InfoRow({ label, valor }) {
  if (!valor) return null
  return (
    <div className="flex items-start gap-3 py-2 border-b border-gray-800 last:border-0">
      <span className="text-gray-600 text-xs w-24 flex-shrink-0 pt-0.5">{label}</span>
      <span className="text-gray-300 text-xs">{valor}</span>
    </div>
  )
}

// Agrupa votos por boletín
function agruparPorBoletin(historial) {
  const grupos = {}
  for (const v of historial) {
    const key = v.boletin || v.votacion_id
    if (!grupos[key]) {
      grupos[key] = {
        boletin:  v.boletin,
        titulo:   v.titulo,
        camara:   v.camara,
        votaciones: [],
      }
    }
    grupos[key].votaciones.push(v)
  }
  return Object.values(grupos)
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
    <div className="flex items-center gap-2 py-2">
      <div className="w-3 h-3 rounded-full bg-blue-500 animate-pulse" />
      <span className="text-gray-500 text-xs">Claude está analizando el proyecto...</span>
    </div>
  )
  if (error) return <div className="text-red-500 text-xs py-1">{error}</div>
  return (
    <div className="space-y-1.5">
      {resumen.split('\n\n').filter(p => p.trim()).map((parrafo, i) => (
        <p key={i} className="text-gray-300 text-xs leading-relaxed">{parrafo}</p>
      ))}
    </div>
  )
}

function TarjetaProyecto({ grupo }) {
  const [expandido, setExpandido]   = useState(false)
  const [verResumen, setVerResumen] = useState(false)

  const urlBoletin = grupo.boletin
    ? `https://tramitacion.senado.cl/appsenado/templates/tramitacion/index.php?boletin_ini=${grupo.boletin}`
    : null

  // Voto más reciente para mostrar en resumen
  const votoReciente = grupo.votaciones[0]

  // Determinar resultado general del parlamentario en este proyecto
  const selecciones = grupo.votaciones.map(v => v.seleccion)
  const mayoriaSeleccion = selecciones.reduce((acc, s) => {
    acc[s] = (acc[s] || 0) + 1
    return acc
  }, {})
  const seleccionPrincipal = Object.entries(mayoriaSeleccion)
    .sort((a, b) => b[1] - a[1])[0]?.[0]

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden hover:border-gray-700 transition-colors">
      <div className="px-4 py-3 flex items-start gap-3">
        {/* Info proyecto */}
        <div className="flex-1 min-w-0">
          <p className="text-gray-100 text-sm leading-snug">
            {grupo.titulo || '(Sin título)'}
          </p>
          <div className="flex flex-wrap gap-2 mt-1.5 items-center">
            {urlBoletin ? (
              <a href={urlBoletin} target="_blank" rel="noopener noreferrer"
                className="text-blue-500 hover:text-blue-300 text-xs transition-colors">
                Boletín {grupo.boletin} ↗
              </a>
            ) : grupo.boletin ? (
              <span className="text-gray-600 text-xs">Boletín {grupo.boletin}</span>
            ) : null}
            <span className="text-gray-600 text-xs">
              {grupo.camara === 'C.Diputados' ? 'Cámara' : grupo.camara}
            </span>
            <span className="text-gray-600 text-xs">{votoReciente?.fecha}</span>
            {grupo.votaciones.length > 1 && (
              <span className="text-gray-600 text-xs">
                {grupo.votaciones.length} votaciones
              </span>
            )}
          </div>
        </div>

        {/* Voto del parlamentario */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <BadgeVoto seleccion={seleccionPrincipal} />
          {grupo.votaciones.length > 1 && (
            <button
              onClick={() => setExpandido(!expandido)}
              className="text-gray-600 hover:text-gray-400 text-xs transition-colors"
            >
              {expandido ? '▲' : '▼'}
            </button>
          )}
        </div>
      </div>

      {/* Botón resumen IA */}
      {grupo.boletin && (
        <div className="px-4 pb-3">
          <button
            onClick={() => setVerResumen(!verResumen)}
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

      {/* Resumen IA */}
      {verResumen && grupo.boletin && (
        <div className="mx-4 mb-3 p-3 bg-gray-800 border border-gray-700 rounded-lg">
          <p className="text-blue-400 text-xs font-medium mb-2">✦ Explicación por IA (puede ser impreciso)</p>
          <ResumenIA boletin={grupo.boletin} />
        </div>
      )}

      {/* Detalle de cada votación si hay más de una */}
      {expandido && grupo.votaciones.length > 1 && (
        <div className="border-t border-gray-800 bg-gray-950">
          {grupo.votaciones.map((v, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-2 border-b border-gray-800 last:border-0">
              <span className="text-gray-600 text-xs w-20 flex-shrink-0">{v.fecha}</span>
              <p className="text-gray-400 text-xs flex-1 truncate">{v.tema || v.tipo_votacion || 'Votación'}</p>
              <BadgeVoto seleccion={v.seleccion} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function Parlamentario() {
  const { nombre } = useParams()
  const nombreDecoded = decodeURIComponent(nombre)

  const [datos, setDatos]       = useState(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError]       = useState(null)
  const [pagina, setPagina]     = useState(0)

  const LIMITE = 50  // traer más para agrupar bien

  useEffect(() => {
    setCargando(true)
    const params = new URLSearchParams({ limite: LIMITE, offset: pagina * LIMITE })
    fetch(`${API_URL}/parlamentarios/${encodeURIComponent(nombreDecoded)}/votos?${params}`)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(data => { setDatos(data); setCargando(false) })
      .catch(err => { setError(err.message); setCargando(false) })
  }, [nombreDecoded, pagina])

  if (cargando) return (
    <div className="max-w-4xl mx-auto px-6 py-12 text-center text-gray-500">
      Cargando perfil...
    </div>
  )

  if (error || !datos) return (
    <div className="max-w-4xl mx-auto px-6 py-12 text-center text-red-400">
      No se encontró información para "{nombreDecoded}"
    </div>
  )

  const { estadisticas, historial, total_votos } = datos
  const iniciales = datos.parlamentario
    ?.split(/[\s,]+/).filter(Boolean).slice(0, 2).map(p => p[0]).join('') || '?'

  const territorio = datos.camara === 'Senado'
    ? datos.circunscripcion ? `Circunscripción ${datos.circunscripcion}` : null
    : datos.distrito || null

  const grupos = agruparPorBoletin(historial)

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">

      <Link to="/" className="text-gray-600 text-xs hover:text-gray-400 transition-colors mb-6 inline-block">
        ← Inicio
      </Link>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">

        {/* Perfil */}
        <div className="md:col-span-1 bg-gray-900 border border-gray-800 rounded-lg p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-full bg-blue-950 flex items-center justify-center text-blue-400 text-base font-medium flex-shrink-0">
              {iniciales}
            </div>
            <div>
              <h1 className="text-gray-100 text-sm font-medium leading-snug">
                {datos.parlamentario}
              </h1>
              <p className="text-gray-600 text-xs mt-0.5">{total_votos} votos registrados</p>
            </div>
          </div>
          <div className="space-y-0">
            <InfoRow label="Cámara"     valor={datos.camara} />
            <InfoRow label="Partido"    valor={datos.partido} />
            {datos.bancada && datos.bancada !== datos.partido && (
              <InfoRow label="Bancada"  valor={datos.bancada} />
            )}
            <InfoRow label="Región"     valor={datos.region} />
            <InfoRow label="Territorio" valor={territorio} />
          </div>
        </div>

        {/* Estadísticas */}
        <div className="md:col-span-2">
          <h2 className="text-gray-400 text-xs font-medium mb-3">Resumen de votaciones</h2>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <Estadistica label="A favor"    valor={estadisticas.si}         color="text-green-400" />
            <Estadistica label="En contra"  valor={estadisticas.no}         color="text-red-400"   />
            <Estadistica label="Abstención" valor={estadisticas.abstencion} color="text-yellow-400"/>
            <Estadistica label="Pareo"      valor={estadisticas.pareo}      color="text-gray-500"  />
          </div>
          {(estadisticas.si + estadisticas.no) > 0 && (
            <div>
              <p className="text-gray-600 text-xs mb-1">Tendencia de voto</p>
              <div className="h-2 bg-gray-800 rounded-full overflow-hidden flex">
                <div className="h-full bg-green-800"
                  style={{ width: `${Math.round(estadisticas.si / (estadisticas.si + estadisticas.no + estadisticas.abstencion) * 100)}%` }} />
                <div className="h-full bg-red-900"
                  style={{ width: `${Math.round(estadisticas.no / (estadisticas.si + estadisticas.no + estadisticas.abstencion) * 100)}%` }} />
                <div className="h-full bg-yellow-900"
                  style={{ width: `${Math.round(estadisticas.abstencion / (estadisticas.si + estadisticas.no + estadisticas.abstencion) * 100)}%` }} />
              </div>
              <div className="flex gap-4 mt-1">
                <span className="text-green-600 text-xs">A favor</span>
                <span className="text-red-600 text-xs">En contra</span>
                <span className="text-yellow-700 text-xs">Abstención</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Historial agrupado por proyecto */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-gray-400 text-sm font-medium">
          Historial de votaciones
          <span className="text-gray-600 font-normal ml-2">({grupos.length} proyectos)</span>
        </h2>
      </div>

      <div className="space-y-2 mb-6">
        {grupos.map((grupo, i) => (
          <TarjetaProyecto key={i} grupo={grupo} />
        ))}
      </div>

      {total_votos > LIMITE && (
        <div className="flex items-center justify-between">
          <button onClick={() => setPagina(p => Math.max(0, p - 1))} disabled={pagina === 0}
            className="text-xs px-4 py-2 rounded-lg border border-gray-800 text-gray-500 hover:border-gray-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
            ← Anterior
          </button>
          <span className="text-gray-600 text-xs">
            Página {pagina + 1} de {Math.ceil(total_votos / LIMITE)}
          </span>
          <button onClick={() => setPagina(p => p + 1)} disabled={(pagina + 1) * LIMITE >= total_votos}
            className="text-xs px-4 py-2 rounded-lg border border-gray-800 text-gray-500 hover:border-gray-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
            Siguiente →
          </button>
        </div>
      )}

    </div>
  )
}
