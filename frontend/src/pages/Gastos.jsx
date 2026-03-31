// ============================================================
// pages/Gastos.jsx — Ranking gastos con detalle expandible
// ============================================================

import { useState, useEffect } from 'react'

const API_URL = 'http://localhost:8000'

const MESES_NOMBRE = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                      'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

function formatPesos(monto) {
  if (monto >= 1_000_000) return `$${(monto / 1_000_000).toFixed(1)}M`
  if (monto >= 1_000)     return `$${Math.round(monto / 1_000).toLocaleString('es-CL')}K`
  return `$${monto.toLocaleString('es-CL')}`
}

function formatPesosCompleto(monto) {
  return `$${monto.toLocaleString('es-CL')}`
}

// Colores por categoría
const COLORES_CATEGORIA = {
  'TRASLACION':                   'text-orange-400',
  'OFICINAS PARLAMENTARIAS':      'text-blue-400',
  'DIFUSION':                     'text-purple-400',
  'TELEFONIA CELULAR':            'text-green-400',
  'TELEFONIA FIJA':               'text-green-600',
  'ACTIVIDADES REGIONALES':       'text-yellow-400',
  'MATERIALES DE OFICINA':        'text-gray-400',
  'CORRESPONDENCIA':              'text-gray-500',
  'SERVICIOS MENORES SENADORES':  'text-red-400',
}

function colorCategoria(cat) {
  return COLORES_CATEGORIA[cat] ?? 'text-gray-400'
}

// ── DETALLE EXPANDIBLE ────────────────────────────────────────
function DetalleGastos({ senadorId, ano }) {
  const [detalle, setDetalle] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [vistaActiva, setVistaActiva] = useState('categoria') // 'categoria' | 'mensual'

  useEffect(() => {
    const params = ano ? `?ano=${ano}` : ''
    fetch(`${API_URL}/gastos/senadores/${senadorId}${params}`)
      .then(r => r.json())
      .then(data => { setDetalle(data); setCargando(false) })
      .catch(() => setCargando(false))
  }, [senadorId, ano])

  if (cargando) return (
    <div className="px-4 pb-3 text-gray-600 text-xs">Cargando detalle...</div>
  )
  if (!detalle || !detalle.detalle?.length) return (
    <div className="px-4 pb-3 text-gray-600 text-xs">Sin datos de gastos para este período.</div>
  )

  // Agrupar detalle por año → mes → registros
  const porAnoMes = {}
  for (const d of detalle.detalle) {
    const key = `${d.ano}-${String(d.mes).padStart(2, '0')}`
    if (!porAnoMes[key]) porAnoMes[key] = { ano: d.ano, mes: d.mes, items: [], total: 0 }
    porAnoMes[key].items.push(d)
    porAnoMes[key].total += d.monto
  }
  const periodos = Object.entries(porAnoMes).sort((a, b) => b[0].localeCompare(a[0]))

  return (
    <div className="border-t border-gray-800 bg-gray-950">

      {/* Tabs vista */}
      <div className="flex gap-1 px-4 pt-3 pb-2">
        {['categoria', 'mensual'].map(v => (
          <button key={v} onClick={() => setVistaActiva(v)}
            className={`text-xs px-3 py-1 rounded-lg border transition-colors ${
              vistaActiva === v
                ? 'bg-gray-700 border-gray-600 text-gray-100'
                : 'bg-gray-900 border-gray-800 text-gray-500 hover:border-gray-700'
            }`}>
            {v === 'categoria' ? 'Por categoría' : 'Por mes'}
          </button>
        ))}
        <span className="ml-auto text-gray-500 text-xs self-center">
          Total: <span className="text-gray-300 font-medium">{formatPesosCompleto(detalle.total_gasto)}</span>
        </span>
      </div>

      {/* Vista por categoría */}
      {vistaActiva === 'categoria' && (
        <div className="px-4 pb-4 space-y-1.5">
          {Object.entries(detalle.por_categoria).map(([cat, monto]) => (
            <div key={cat} className="flex items-center justify-between py-1.5 border-b border-gray-800 last:border-0">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full flex-shrink-0 ${colorCategoria(cat).replace('text-', 'bg-')}`} />
                <span className="text-gray-400 text-xs capitalize">{cat.toLowerCase()}</span>
              </div>
              <span className="text-gray-200 text-xs font-medium">{formatPesosCompleto(monto)}</span>
            </div>
          ))}
        </div>
      )}

      {/* Vista por mes */}
      {vistaActiva === 'mensual' && (
        <div className="px-4 pb-4 space-y-3 max-h-80 overflow-y-auto">
          {periodos.map(([key, periodo]) => (
            <div key={key}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-gray-400 text-xs font-medium">
                  {MESES_NOMBRE[periodo.mes]} {periodo.ano}
                </span>
                <span className="text-gray-400 text-xs">{formatPesosCompleto(periodo.total)}</span>
              </div>
              <div className="space-y-1 pl-3 border-l border-gray-800">
                {periodo.items.map((item, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <span className={`text-xs capitalize ${colorCategoria(item.categoria)}`}>
                      {item.categoria.toLowerCase()}
                    </span>
                    <span className="text-gray-500 text-xs">{formatPesosCompleto(item.monto)}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── FILA RANKING ──────────────────────────────────────────────
function FilaRanking({ senador, posicion, maximo, ano }) {
  const [expandido, setExpandido] = useState(false)
  const pct = Math.round((senador.total_gasto / maximo) * 100)

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden hover:border-gray-700 transition-colors">

      <button onClick={() => setExpandido(!expandido)} className="w-full text-left px-4 py-3">
        <div className="flex items-center gap-3">
          {/* Posición */}
          <span className={`text-sm font-medium w-7 flex-shrink-0 text-right ${
            posicion === 1 ? 'text-yellow-400' :
            posicion === 2 ? 'text-gray-400' :
            posicion === 3 ? 'text-orange-600' : 'text-gray-600'
          }`}>{posicion}</span>

          {/* Info + barra */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <p className="text-gray-100 text-sm truncate">{senador.nombre_completo}</p>
              {senador.partido && (
                <span className="text-xs px-1.5 rounded-full border bg-gray-800 text-gray-500 border-gray-700 flex-shrink-0">
                  {senador.partido}
                </span>
              )}
            </div>
            {/* Barra */}
            <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
              <div className="h-full bg-blue-800 rounded-full transition-all" style={{ width: `${pct}%` }} />
            </div>
          </div>

          {/* Monto + flecha */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <span className="text-gray-200 text-sm font-medium">{formatPesos(senador.total_gasto)}</span>
            <span className="text-gray-600 text-xs">{expandido ? '▲' : '▼'}</span>
          </div>
        </div>
      </button>

      {expandido && <DetalleGastos senadorId={senador.senador_id} ano={ano} />}
    </div>
  )
}

// ── COMPONENTE PRINCIPAL ──────────────────────────────────────
export default function Gastos() {
  const [senadores, setSenadores] = useState([])
  const [anios, setAnios]         = useState([])
  const [anioSel, setAnioSel]     = useState(null)
  const [cargando, setCargando]   = useState(true)
  const [busqueda, setBusqueda]   = useState('')

  useEffect(() => {
    setCargando(true)
    const params = anioSel ? `?ano=${anioSel}` : ''
    fetch(`${API_URL}/gastos/senadores${params}`)
      .then(r => r.json())
      .then(data => {
        setSenadores(data.senadores ?? [])
        setAnios(data.anios ?? [])
        setCargando(false)
      })
      .catch(() => setCargando(false))
  }, [anioSel])

  const filtrados = senadores.filter(s =>
    !busqueda ||
    s.nombre_completo?.toLowerCase().includes(busqueda.toLowerCase()) ||
    s.partido?.toLowerCase().includes(busqueda.toLowerCase())
  )

  const maximo = filtrados.length > 0 ? filtrados[0].total_gasto : 1

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">

      <div className="mb-6">
        <h1 className="text-xl font-medium text-gray-100">Gastos operacionales · Senado</h1>
        <p className="text-gray-500 text-sm mt-1">
          Gastos rendidos por senadores vigentes · Fuente: Transparencia Senado de Chile
        </p>
      </div>

      {/* Selector año */}
      {anios.length > 0 && (
        <div className="mb-4 overflow-x-auto">
          <div className="flex gap-2 pb-1" style={{ minWidth: 'max-content' }}>
            <button onClick={() => setAnioSel(null)}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                anioSel === null
                  ? 'bg-gray-700 border-gray-600 text-gray-100'
                  : 'bg-gray-900 border-gray-800 text-gray-500 hover:border-gray-700'
              }`}>Todos</button>
            {anios.map(a => (
              <button key={a} onClick={() => setAnioSel(a)}
                className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                  anioSel === a
                    ? 'bg-gray-700 border-gray-600 text-gray-100'
                    : 'bg-gray-900 border-gray-800 text-gray-500 hover:border-gray-700'
                }`}>{a}</button>
            ))}
          </div>
        </div>
      )}

      {/* Buscador */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Buscar por nombre o partido..."
          value={busqueda}
          onChange={e => setBusqueda(e.target.value)}
          className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-gray-500"
        />
      </div>

      {/* Leyenda categorías */}
      <div className="flex flex-wrap gap-3 mb-4">
        {Object.entries(COLORES_CATEGORIA).slice(0, 5).map(([cat, color]) => (
          <div key={cat} className="flex items-center gap-1">
            <span className={`w-2 h-2 rounded-full ${color.replace('text-', 'bg-')}`} />
            <span className="text-gray-600 text-xs capitalize">{cat.toLowerCase()}</span>
          </div>
        ))}
      </div>

      {cargando ? (
        <div className="text-center py-12 text-gray-500">Cargando gastos...</div>
      ) : filtrados.length > 0 ? (
        <div className="space-y-2">
          {filtrados.map((s, i) => (
            <FilaRanking
              key={s.senador_id}
              senador={s}
              posicion={i + 1}
              maximo={maximo}
              ano={anioSel}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-600">
          No hay datos de gastos{anioSel ? ` para ${anioSel}` : ''}
        </div>
      )}
    </div>
  )
}
