// ============================================================
// pages/Inicio.jsx
// ============================================================

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

const API_URL = 'http://localhost:8000'

function Metrica({ label, valor, sub }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <p className="text-gray-600 text-xs mb-1">{label}</p>
      <p className="text-gray-100 text-2xl font-medium">{valor}</p>
      {sub && <p className="text-gray-600 text-xs mt-1">{sub}</p>}
    </div>
  )
}

function BarraPartido({ partido, cantidad, total }) {
  const porcentaje = Math.round((cantidad / total) * 100)
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-gray-400 text-xs">{partido}</span>
        <span className="text-gray-600 text-xs">{cantidad}</span>
      </div>
      <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div className="h-full bg-blue-800 rounded-full" style={{ width: `${porcentaje}%` }} />
      </div>
    </div>
  )
}

function BadgeResultado({ resultado }) {
  const estilos = {
    'Aprobado':  'bg-green-950 text-green-400 border-green-900',
    'Rechazado': 'bg-red-950 text-red-400 border-red-900',
    'Empate':    'bg-yellow-950 text-yellow-400 border-yellow-900',
  }
  const clase = estilos[resultado] ?? 'bg-gray-800 text-gray-400 border-gray-700'
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border flex-shrink-0 ${clase}`}>
      {resultado}
    </span>
  )
}

function BadgeCamara({ camara }) {
  const esCamara = camara === 'C.Diputados'
  return (
    <span className={`text-xs px-1.5 py-0 rounded-full border flex-shrink-0 ${
      esCamara
        ? 'bg-blue-950 text-blue-400 border-blue-900'
        : 'bg-purple-950 text-purple-400 border-purple-900'
    }`}>
      {esCamara ? 'Cámara' : 'Senado'}
    </span>
  )
}

export default function Inicio() {
  const [senadores, setSenadores]                 = useState([])
  const [comisiones, setComisiones]               = useState([])
  const [diputados, setDiputados]                 = useState([])
  const [totalVotaciones, setTotalVotaciones]     = useState(0)
  const [ultimasVotaciones, setUltimasVotaciones] = useState([])
  const [cargando, setCargando]                   = useState(true)

  useEffect(() => {
    Promise.all([
      fetch(`${API_URL}/senadores/`).then(r => r.json()),
      fetch(`${API_URL}/comisiones/`).then(r => r.json()),
      fetch(`${API_URL}/diputados/`).then(r => r.json()),
      fetch(`${API_URL}/votaciones/?limite=1`).then(r => r.json()),
      fetch(`${API_URL}/votaciones/recientes`).then(r => r.json()),
    ])
      .then(([dataSen, dataCom, dataDip, dataVot, dataRecientes]) => {
        setSenadores(dataSen.senadores ?? [])
        setComisiones(dataCom.comisiones ?? [])
        setDiputados(dataDip.diputados ?? [])
        setTotalVotaciones(dataVot.total ?? 0)
        setUltimasVotaciones(dataRecientes.votaciones ?? [])
        setCargando(false)
      })
      .catch(() => setCargando(false))
  }, [])

  const porPartido = senadores.reduce((acc, s) => {
    const partido = s.partido ?? 'Sin partido'
    acc[partido] = (acc[partido] ?? 0) + 1
    return acc
  }, {})

  const topPartidos = Object.entries(porPartido)
    .sort((a, b) => b[1] - a[1])

  if (cargando) return (
    <div className="max-w-6xl mx-auto px-6 py-12 text-center text-gray-500">
      Cargando...
    </div>
  )

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">

      <div className="mb-8">
        <h1 className="text-xl font-medium text-gray-100">Congreso Nacional de Chile</h1>
        <p className="text-gray-500 text-sm mt-1">
          Datos abiertos del Congreso — actualizados automáticamente cada 6 horas
        </p>
      </div>

      {/* Métricas */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
        <Metrica label="Senadores"  valor={senadores.length}  sub="vigentes"    />
        <Metrica label="Diputados"  valor={diputados.length}  sub="vigentes"    />
        <Metrica label="Comisiones" valor={comisiones.length} sub="activas"     />
        <Metrica label="Votaciones" valor={totalVotaciones}   sub="registradas" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">

        {/* Distribución por partido — Senado */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
          <h2 className="text-gray-300 text-sm font-medium mb-4">
            Distribución por partido · Senado
          </h2>
          <div className="space-y-3">
            {topPartidos.map(([partido, cantidad]) => (
              <BarraPartido
                key={partido}
                partido={partido}
                cantidad={cantidad}
                total={senadores.length}
              />
            ))}
          </div>
        </div>

        {/* Accesos directos */}
        <div className="flex flex-col gap-3">

          <Link to="/busqueda"
            className="bg-gray-800 border border-gray-700 rounded-lg p-5 hover:border-gray-500 transition-colors group">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-100 text-sm font-medium">🔍 Buscar parlamentario</p>
                <p className="text-gray-500 text-xs mt-1">Por nombre, partido o región · Senado y Cámara</p>
              </div>
              <span className="text-gray-700 group-hover:text-gray-400 transition-colors">→</span>
            </div>
          </Link>

          <Link to="/senadores"
            className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-600 transition-colors group">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-100 text-sm font-medium">Senadores</p>
                <p className="text-gray-500 text-xs mt-1">{senadores.length} vigentes</p>
              </div>
              <span className="text-gray-700 group-hover:text-gray-400 transition-colors">→</span>
            </div>
          </Link>

          <Link to="/diputados"
            className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-600 transition-colors group">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-100 text-sm font-medium">Diputados</p>
                <p className="text-gray-500 text-xs mt-1">{diputados.length} vigentes</p>
              </div>
              <span className="text-gray-700 group-hover:text-gray-400 transition-colors">→</span>
            </div>
          </Link>

          <Link to="/comisiones"
            className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-600 transition-colors group">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-100 text-sm font-medium">Comisiones</p>
                <p className="text-gray-500 text-xs mt-1">{comisiones.length} activas</p>
              </div>
              <span className="text-gray-700 group-hover:text-gray-400 transition-colors">→</span>
            </div>
          </Link>

          <Link to="/votaciones"
            className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-600 transition-colors group">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-100 text-sm font-medium">Votaciones</p>
                <p className="text-gray-500 text-xs mt-1">{totalVotaciones} registradas</p>
              </div>
              <span className="text-gray-700 group-hover:text-gray-400 transition-colors">→</span>
            </div>
          </Link>

        </div>
      </div>

      {/* Últimas votaciones */}
      {ultimasVotaciones.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-gray-300 text-sm font-medium">Votaciones recientes</h2>
            <Link to="/votaciones" className="text-gray-600 text-xs hover:text-gray-400 transition-colors">
              Ver todas →
            </Link>
          </div>
          <div className="space-y-2">
            {ultimasVotaciones.slice(0, 6).map((v, i) => (
              <div key={i} className="flex items-start gap-3 py-2 border-t border-gray-800 first:border-0">
                <div className="flex-1 min-w-0">
                  <p className="text-gray-300 text-xs leading-snug truncate">{v.titulo}</p>
                  <div className="flex gap-2 mt-0.5">
                    <span className="text-gray-600 text-xs">{v.fecha}</span>
                    <BadgeCamara camara={v.camara} />
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className="text-green-600 text-xs">{v.votos_si}</span>
                  <span className="text-gray-700 text-xs">—</span>
                  <span className="text-red-600 text-xs">{v.votos_no}</span>
                  <BadgeResultado resultado={v.resultado} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  )
}
