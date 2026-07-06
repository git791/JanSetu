import { Routes, Route, Navigate, NavLink, useLocation } from 'react-router-dom'
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X, Send, LayoutDashboard, Globe, FlaskConical } from 'lucide-react'
import CitizenSubmit from './pages/CitizenSubmit'
import MPDashboard from './pages/MPDashboard'
import PublicTransparency from './pages/PublicTransparency'
import WhatIfSimulator from './pages/WhatIfSimulator'

const NAV_LINKS = [
  { to: '/submit', label: 'Submit', icon: Send },
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/public', label: 'Public Tracker', icon: Globe },
  { to: '/simulate', label: 'Simulator', icon: FlaskConical },
]

function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)
  const location = useLocation()

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-30"
      style={{
        background: 'rgba(10,15,30,0.85)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(99,102,241,0.15)',
      }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <NavLink to="/submit" className="flex items-center gap-2 no-underline">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center font-black text-sm"
              style={{ background: 'linear-gradient(135deg, #6366F1, #8B5CF6)' }}
            >
              JS
            </div>
            <span className="gradient-text text-xl font-extrabold tracking-tight">
              JanSetu
            </span>
            <span
              className="hidden sm:block text-xs px-2 py-0.5 rounded-full font-medium"
              style={{
                background: 'rgba(99,102,241,0.15)',
                color: '#818CF8',
                border: '1px solid rgba(99,102,241,0.25)',
              }}
            >
              AI Intelligence
            </span>
          </NavLink>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-1">
            {NAV_LINKS.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 no-underline ${
                    isActive
                      ? 'text-white'
                      : 'text-gray-400 hover:text-white hover:bg-white/5'
                  }`
                }
                style={({ isActive }) =>
                  isActive
                    ? { background: 'rgba(99,102,241,0.2)', color: '#818CF8' }
                    : {}
                }
              >
                <Icon size={15} />
                {label}
              </NavLink>
            ))}
          </div>

          {/* Mobile hamburger */}
          <button
            className="md:hidden p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
            onClick={() => setMenuOpen((o) => !o)}
            aria-label="Toggle menu"
          >
            {menuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            style={{
              background: 'rgba(10,15,30,0.98)',
              borderTop: '1px solid rgba(99,102,241,0.12)',
            }}
          >
            <div className="px-4 py-3 space-y-1">
              {NAV_LINKS.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  onClick={() => setMenuOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 no-underline ${
                      isActive ? 'text-indigo-300' : 'text-gray-400'
                    }`
                  }
                  style={({ isActive }) =>
                    isActive
                      ? { background: 'rgba(99,102,241,0.15)' }
                      : {}
                  }
                >
                  <Icon size={16} />
                  {label}
                </NavLink>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  )
}

export default function App() {
  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      <Navbar />
      <main className="pt-16">
        <Routes>
          <Route path="/" element={<Navigate to="/submit" replace />} />
          <Route path="/submit" element={<CitizenSubmit />} />
          <Route path="/dashboard" element={<MPDashboard />} />
          <Route path="/public" element={<PublicTransparency />} />
          <Route path="/simulate" element={<WhatIfSimulator />} />
        </Routes>
      </main>
    </div>
  )
}
