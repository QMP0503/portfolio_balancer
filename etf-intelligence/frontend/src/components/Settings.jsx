import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMe, updateMe, changePassword } from '../api'

function Field({ label, type = 'text', value, onChange }) {
  return (
    <div>
      <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
    </div>
  )
}


export default function Settings() {
  const [profile, setProfile] = useState({ email: '', first_name: '', last_name: '' })
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    getMe()
      .then((me) => {
        setProfile(me)
        setFirstName(me.first_name)
        setLastName(me.last_name)
        setEmail(me.email)
      })
      .catch((err) => setError(err.message))
  }, [])

  async function handleSaveProfile(e) {
    e.preventDefault()
    setError('')
    setSuccess('')
    try {
      const updated = await updateMe(email, firstName, lastName)
      setProfile(updated)
      setSuccess('Profile updated.')
    } catch (err) { setError(err.message) }
  }

  async function handleChangePassword(e) {
    e.preventDefault()
    setError('')
    setSuccess('')
    try {
      await changePassword(currentPassword, newPassword)
      setCurrentPassword('')
      setNewPassword('')
      setSuccess('Password changed.')
    } catch (err) { setError(err.message) }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Settings</h1>
        <Link to="/" className="text-sm text-gray-500 hover:underline">← Dashboard</Link>
      </div>

      {error && (
        <div className="mb-4 flex items-center justify-between px-4 py-3 rounded bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-sm">
          <span>{error}</span>
          <button onClick={() => setError('')} className="ml-4 font-bold">×</button>
        </div>
      )}
      {success && (
        <div className="mb-4 px-4 py-3 rounded bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-sm">
          {success}
        </div>
      )}

      {/* Profile */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-3">Profile</h2>
        <form onSubmit={handleSaveProfile} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Field label="First name" value={firstName} onChange={setFirstName} />
            <Field label="Last name" value={lastName} onChange={setLastName} />
          </div>
          <Field label="Email" type="email" value={email} onChange={setEmail} />
          <button type="submit" className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white text-sm">
            Save profile
          </button>
        </form>
      </section>

      {/* Change password */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-3">Change Password</h2>
        <form onSubmit={handleChangePassword} className="space-y-3">
          <Field label="Current password" type="password" value={currentPassword} onChange={setCurrentPassword} />
          <Field label="New password" type="password" value={newPassword} onChange={setNewPassword} />
          <button type="submit" className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white text-sm">
            Change password
          </button>
        </form>
      </section>

      {/* Placeholder for future stock picker */}
      <section>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-3">Tracked Stocks</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">HXQ · VFV · VCN · ZEM — customisation coming soon.</p>
      </section>
    </div>
  )
}
