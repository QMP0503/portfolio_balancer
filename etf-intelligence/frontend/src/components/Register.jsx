import { useState } from 'react'
import { Link } from 'react-router-dom'
import { register } from '../api'

export default function Register({ onRegister }) {
  const [form, setForm] = useState({ email: '', firstName: '', lastName: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  function set(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(form.email, form.firstName, form.lastName, form.password)
      onRegister()
    } catch (err) {
      setError(err.status === 409 ? 'Email already registered.' : err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-semibold mb-8 text-center">Create Account</h1>

        {error && (
          <div className="mb-4 px-4 py-3 rounded bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="block text-sm font-medium mb-1" htmlFor="firstName">First name</label>
              <input
                id="firstName" type="text" required value={form.firstName} onChange={set('firstName')}
                className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium mb-1" htmlFor="lastName">Last name</label>
              <input
                id="lastName" type="text" required value={form.lastName} onChange={set('lastName')}
                className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1" htmlFor="email">Email</label>
            <input
              id="email" type="email" required value={form.email} onChange={set('email')}
              className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1" htmlFor="password">Password</label>
            <input
              id="password" type="password" required value={form.password} onChange={set('password')}
              className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            type="submit" disabled={loading}
            className="w-full py-2 px-4 rounded bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium transition-colors"
          >
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
          Already have an account?{' '}
          <Link to="/login" className="text-blue-500 hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
