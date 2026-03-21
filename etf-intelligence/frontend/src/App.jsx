import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import { getPortfolios } from './api'
import Dashboard from './components/Dashboard'
import Login from './components/Login'
import Register from './components/Register'
import Settings from './components/Settings'

function AuthGuard({ isLoggedIn, children }) {
  if (isLoggedIn === null) return null // still checking
  if (!isLoggedIn) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(null)

  useEffect(() => {
    getPortfolios()
      .then(() => setIsLoggedIn(true))
      .catch((err) => {
        if (err.status === 401) setIsLoggedIn(false)
        else setIsLoggedIn(false)
      })
  }, [])

  return (
    <ThemeProvider>
      <div className="min-h-screen bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100">
        <BrowserRouter>
          <Routes>
            <Route
              path="/login"
              element={
                isLoggedIn ? (
                  <Navigate to="/" replace />
                ) : (
                  <Login onLogin={() => setIsLoggedIn(true)} />
                )
              }
            />
            <Route
              path="/"
              element={
                <AuthGuard isLoggedIn={isLoggedIn}>
                  <Dashboard onLogout={() => setIsLoggedIn(false)} />
                </AuthGuard>
              }
            />
            <Route
              path="/register"
              element={
                isLoggedIn ? (
                  <Navigate to="/" replace />
                ) : (
                  <Register onRegister={() => setIsLoggedIn(true)} />
                )
              }
            />
            <Route
              path="/settings"
              element={
                <AuthGuard isLoggedIn={isLoggedIn}>
                  <Settings />
                </AuthGuard>
              }
            />
          </Routes>
        </BrowserRouter>
      </div>
    </ThemeProvider>
  )
}
