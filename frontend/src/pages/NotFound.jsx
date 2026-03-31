// ============================================================
// pages/NotFound.jsx — Página 404
// ============================================================

import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="max-w-xl mx-auto px-6 py-24 text-center">
      <p className="text-gray-700 text-6xl font-medium mb-4">404</p>
      <h1 className="text-gray-300 text-lg font-medium mb-2">
        Página no encontrada
      </h1>
      <p className="text-gray-600 text-sm mb-8">
        La página que buscas no existe o fue movida.
      </p>
      <Link
        to="/"
        className="text-xs px-5 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-gray-300 hover:border-gray-500 transition-colors"
      >
        ← Volver al inicio
      </Link>
    </div>
  )
}
