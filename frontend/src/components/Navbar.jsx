// ============================================================
// components/Navbar.jsx
// ============================================================

import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

const LINKS = [
  { to: '/',          label: 'Inicio'     },
  { to: '/senadores', label: 'Senadores'  },
  { to: '/comisiones',label: 'Comisiones' },
  { to: '/diputados', label: 'Diputados'  },
  { to: '/votaciones',label: 'Votaciones' },
  { to: '/leyes',     label: 'Leyes'      },
  { to: '/busqueda',  label: 'Buscar'     },
]

export default function Navbar() {
  const location  = useLocation()
  const [abierto, setAbierto] = useState(false)

  return (
    <nav className="bg-gray-900 border-b border-gray-800 px-4 py-3">
      <div className="max-w-6xl mx-auto flex items-center justify-between">

        {/* Logo */}
        <Link to="/" className="text-gray-100 font-medium text-base tracking-wide"
          onClick={() => setAbierto(false)}>
          Congreso Viz
        </Link>

        {/* Menú hamburguesa — solo móvil */}
        <button
          className="md:hidden text-gray-400 hover:text-gray-200 transition-colors"
          onClick={() => setAbierto(!abierto)}
          aria-label="Menú"
        >
          {abierto ? (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          )}
        </button>

        {/* Links desktop */}
        <div className="hidden md:flex items-center gap-6">
          {LINKS.map(link => {
            const activo = location.pathname === link.to
            return (
              <Link key={link.to} to={link.to}
                className={`text-sm transition-colors ${
                  activo ? 'text-gray-100' : 'text-gray-500 hover:text-gray-300'
                }`}>
                {link.label}
              </Link>
            )
          })}
        </div>
      </div>

      {/* Menú móvil desplegable */}
      {abierto && (
        <div className="md:hidden mt-3 border-t border-gray-800 pt-3 flex flex-col gap-1">
          {LINKS.map(link => {
            const activo = location.pathname === link.to
            return (
              <Link key={link.to} to={link.to}
                onClick={() => setAbierto(false)}
                className={`px-2 py-2 rounded-lg text-sm transition-colors ${
                  activo
                    ? 'text-gray-100 bg-gray-800'
                    : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800'
                }`}>
                {link.label}
              </Link>
            )
          })}
        </div>
      )}
    </nav>
  )
}
