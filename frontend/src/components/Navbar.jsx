// ============================================================
// components/Navbar.jsx
// ============================================================

import { Link, useLocation } from 'react-router-dom'

const LINKS = [
  { to: '/',          label: 'Inicio'     },
  { to: '/senadores', label: 'Senadores'  },
  { to: '/comisiones',label: 'Comisiones' },
  { to: '/diputados', label: 'Diputados'  },
  { to: '/votaciones',label: 'Votaciones' },
  { to: '/busqueda',  label: 'Buscar'     },
  { to: '/leyes', label: 'Leyes' }
  //{ to: '/gastos', label: 'Gastos' }
]

export default function Navbar() {
  const location = useLocation()

  return (
    <nav className="bg-gray-900 border-b border-gray-800 px-6 py-3">
      <div className="max-w-6xl mx-auto flex items-center justify-between">

        <Link to="/" className="text-gray-100 font-medium text-base tracking-wide">
          Datos Congreso
        </Link>

        <div className="flex items-center gap-6">
          {LINKS.map(link => {
            const activo = location.pathname === link.to
            return (
              <Link
                key={link.to}
                to={link.to}
                className={`text-sm transition-colors ${
                  activo
                    ? 'text-gray-100'
                    : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                {link.label}
              </Link>
            )
          })}
        </div>

      </div>
    </nav>
  )
}
