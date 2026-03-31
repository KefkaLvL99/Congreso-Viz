// ============================================================
// pages/Comisiones.jsx
// ============================================================
// Página que muestra las comisiones del Senado.
// Al hacer clic en una comisión se expande y muestra
// sus integrantes con sus roles.
// ============================================================

import { useState, useEffect } from 'react'

const API_URL = 'http://localhost:8000'

// ── BADGE DE TIPO ─────────────────────────────────────────────
// Muestra el tipo de comisión con color según categoría
function BadgeTipo({ tipo }) {
  const estilos = {
    'Permanente':  'bg-blue-950 text-blue-400 border-blue-900',
    'Especial':    'bg-amber-950 text-amber-400 border-amber-900',
    'Presupuesto': 'bg-green-950 text-green-400 border-green-900',
  }
  const clase = estilos[tipo] ?? 'bg-gray-800 text-gray-400 border-gray-700'

  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border ${clase}`}>
      {tipo}
    </span>
  )
}

// ── TARJETA DE COMISIÓN ───────────────────────────────────────
function TarjetaComision({ comision }) {
  const [expandida, setExpandida] = useState(false)
  const [detalle, setDetalle]     = useState(null)
  const [cargando, setCargando]   = useState(false)

  // Al expandir, carga el detalle completo con integrantes
  function toggleExpandir() {
    if (!expandida && !detalle) {
      setCargando(true)
      fetch(`${API_URL}/comisiones/${comision.id}`)
        .then(r => r.json())
        .then(data => {
          setDetalle(data)
          setCargando(false)
        })
        .catch(() => setCargando(false))
    }
    setExpandida(!expandida)
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">

      {/* Cabecera — siempre visible */}
      <button
        onClick={toggleExpandir}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-800 transition-colors text-left"
      >
        <div className="flex items-center gap-3 min-w-0">
          {/* Indicador expandido/colapsado */}
          <span className="text-gray-600 text-xs flex-shrink-0">
            {expandida ? '▼' : '▶'}
          </span>
          <span className="text-gray-100 text-sm truncate">
            {comision.nombre}
          </span>
        </div>

        <div className="flex items-center gap-3 flex-shrink-0 ml-4">
          <span className="text-gray-600 text-xs">
            {comision.total_integrantes} integrantes
          </span>
          <BadgeTipo tipo={comision.tipo} />
        </div>
      </button>

      {/* Detalle expandido — integrantes */}
      {expandida && (
        <div className="border-t border-gray-800 px-4 py-3">
          {cargando ? (
            <p className="text-gray-600 text-xs py-2">Cargando integrantes...</p>
          ) : detalle?.integrantes?.length > 0 ? (
            <div className="space-y-2">
              {detalle.integrantes.map((m, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {/* Avatar pequeño */}
                    <div className="w-7 h-7 rounded-full bg-gray-800 flex items-center justify-center text-gray-500 text-xs flex-shrink-0">
                      {m.nombre?.[0]}{m.apellido_paterno?.[0]}
                    </div>
                    <span className="text-gray-300 text-xs">{m.nombre_completo}</span>
                  </div>
                  {/* Rol — solo si tiene función especial */}
                  {m.funcion && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-gray-800 text-gray-500 border border-gray-700">
                      {m.funcion}
                    </span>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-600 text-xs py-2">Sin integrantes registrados</p>
          )}
        </div>
      )}

    </div>
  )
}

// ── COMPONENTE PRINCIPAL ──────────────────────────────────────
export default function Comisiones() {
  const [comisiones, setComisiones] = useState([])
  const [busqueda, setBusqueda]     = useState('')
  const [filtroTipo, setFiltroTipo] = useState('Todos')
  const [cargando, setCargando]     = useState(true)
  const [error, setError]           = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/comisiones/`)
      .then(r => {
        if (!r.ok) throw new Error(`Error HTTP ${r.status}`)
        return r.json()
      })
      .then(data => {
        setComisiones(data.comisiones)
        setCargando(false)
      })
      .catch(err => {
        setError(err.message)
        setCargando(false)
      })
  }, [])

  // Tipos únicos para el filtro
  const tipos = ['Todos', ...new Set(comisiones.map(c => c.tipo).filter(Boolean))]

  // Filtro combinado: tipo + búsqueda por nombre
  const filtradas = comisiones.filter(c => {
    const coincideTipo   = filtroTipo === 'Todos' || c.tipo === filtroTipo
    const coincideNombre = c.nombre?.toLowerCase().includes(busqueda.toLowerCase())
    return coincideTipo && coincideNombre
  })

  if (cargando) return (
    <div className="max-w-6xl mx-auto px-6 py-12 text-center text-gray-500">
      Cargando comisiones...
    </div>
  )

  if (error) return (
    <div className="max-w-6xl mx-auto px-6 py-12 text-center text-red-400">
      Error al cargar datos: {error}
      <p className="text-gray-500 text-sm mt-2">¿Está corriendo el servidor FastAPI en localhost:8000?</p>
    </div>
  )

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">

      {/* Encabezado */}
      <div className="mb-6">
        <h1 className="text-xl font-medium text-gray-100">Comisiones del Senado</h1>
        <p className="text-gray-500 text-sm mt-1">
          {comisiones.length} comisiones · Haz clic para ver integrantes
        </p>
      </div>

      {/* Filtros */}
      <div className="flex gap-3 mb-4 flex-wrap">
        {/* Buscador */}
        <input
          type="text"
          placeholder="Buscar comisión..."
          value={busqueda}
          onChange={e => setBusqueda(e.target.value)}
          className="flex-1 min-w-48 bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-gray-500"
        />
        {/* Filtro por tipo */}
        <div className="flex gap-2">
          {tipos.map(tipo => (
            <button
              key={tipo}
              onClick={() => setFiltroTipo(tipo)}
              className={`text-xs px-3 py-2 rounded-lg border transition-colors ${
                filtroTipo === tipo
                  ? 'bg-gray-700 border-gray-600 text-gray-100'
                  : 'bg-gray-900 border-gray-800 text-gray-500 hover:border-gray-700'
              }`}
            >
              {tipo}
            </button>
          ))}
        </div>
      </div>

      {/* Contador */}
      <p className="text-gray-600 text-xs mb-4">
        {filtradas.length} de {comisiones.length} comisiones
      </p>

      {/* Lista */}
      <div className="space-y-2">
        {filtradas.map(comision => (
          <TarjetaComision key={comision.id} comision={comision} />
        ))}
      </div>

    </div>
  )
}
