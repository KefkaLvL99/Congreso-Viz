// ============================================================
// App.jsx - Rutas y estructura principal
// ============================================================
// Define qué componente mostrar según la URL.
// La Navbar aparece en todas las páginas porque está
// fuera del bloque de rutas.
// ============================================================

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'

// Páginas — las crearemos una por una
// Por ahora usamos placeholders temporales
import Inicio from './pages/Inicio'
import Senadores from './pages/Senadores'
import Comisiones from './pages/Comisiones'
import Diputados from './pages/Diputados'
import Votaciones from './pages/Votaciones'
import Parlamentario from './pages/Parlamentario'
import Busqueda from './pages/Busqueda'
import NotFound from './pages/NotFound'
import Leyes from './pages/Leyes'
//import Gastos from './pages/Gastos'
export default function App() {
  return (
    <BrowserRouter>
      {/* Fondo oscuro para toda la app */}
      <div className="min-h-screen bg-gray-950 text-gray-100">

        {/* Navbar aparece en todas las páginas */}
        <Navbar />

        {/* Contenido según la ruta actual */}
        <Routes>
          <Route path="/"           element={<Inicio />}     />
          <Route path="/senadores"  element={<Senadores />}  />
          <Route path="/comisiones" element={<Comisiones />} />
          <Route path="/diputados" element={<Diputados />} />
          <Route path="/votaciones" element={<Votaciones />} />
          <Route path="/parlamentario/:nombre" element={<Parlamentario />} />
          <Route path="/busqueda" element={<Busqueda />} />
          <Route path="*" element={<NotFound />} />
          <Route path="/leyes" element={<Leyes />} />
          {/*<Route path="/gastos" element={<Gastos />} />*/}
        </Routes>

      </div>
    </BrowserRouter>
  )
}
