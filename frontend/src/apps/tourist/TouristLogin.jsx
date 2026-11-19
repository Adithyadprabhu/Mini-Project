import { useState } from 'react';
import { useAuth } from '../../context/useAuth';

export default function TouristLogin() {
  const { login, register } = useAuth();
  const [tab, setTab] = useState('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [forgotMsg, setForgotMsg] = useState(false);

  const handleSignIn = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (!email.trim() || !password) throw new Error('Email and password are required');
      await login(email.trim(), password, 'tourist');
    } catch (err) {
      setError(err.message || 'Sign in failed. Please check your credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError(null);
    if (!name.trim() || !email.trim() || !password) {
      setError('Please fill in all required fields.');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setSubmitting(true);
    try {
      await register({ email: email.trim(), password, name: name.trim(), phone: phone.trim(), role: 'tourist' });
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const inputClass =
    'w-full bg-surface-container border border-outline-variant/30 rounded-xl px-4 py-3 text-sm text-on-surface focus:outline-none focus:border-secondary transition-colors';

  return (
    <div className="min-h-screen bg-surface flex flex-col justify-center items-center p-6 relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(76,215,246,0.06)_0%,_transparent_70%)] pointer-events-none" />

      <div className="w-full max-w-sm relative z-10 space-y-6">
        {/* Branding */}
        <div className="text-center space-y-2">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-secondary/10 flex items-center justify-center mb-4">
            <span className="material-symbols-outlined text-secondary text-4xl">shield</span>
          </div>
          <h1 className="font-grotesk text-2xl font-bold text-on-surface uppercase tracking-wider">
            Tourist Guardian
          </h1>
          <p className="text-xs text-secondary font-semibold">B.C. Road, Bantwal, Karnataka</p>
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-outline-variant/30">
          <button
            onClick={() => { setTab('signin'); setError(null); }}
            className={`flex-1 py-3 text-sm font-semibold transition-colors ${
              tab === 'signin'
                ? 'text-secondary border-b-2 border-secondary'
                : 'text-outline hover:text-on-surface-variant'
            }`}
          >
            Sign In
          </button>
          <button
            onClick={() => { setTab('register'); setError(null); }}
            className={`flex-1 py-3 text-sm font-semibold transition-colors ${
              tab === 'register'
                ? 'text-secondary border-b-2 border-secondary'
                : 'text-outline hover:text-on-surface-variant'
            }`}
          >
            Register
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-error-container/20 border border-error/30 rounded-xl p-3 flex items-center gap-2">
            <span className="material-symbols-outlined text-error text-sm">error</span>
            <p className="text-xs text-error">{error}</p>
          </div>
        )}

        {/* Sign In Form */}
        {tab === 'signin' && (
          <form onSubmit={handleSignIn} className="space-y-4">
            <div className="relative">
              <span className="material-symbols-outlined text-outline text-lg absolute left-3 top-1/2 -translate-y-1/2">mail</span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email address"
                className={`${inputClass} pl-10`}
              />
            </div>
            <div className="relative">
              <span className="material-symbols-outlined text-outline text-lg absolute left-3 top-1/2 -translate-y-1/2">lock</span>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                className={`${inputClass} pl-10`}
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="w-full py-3.5 bg-secondary hover:bg-secondary/80 text-on-secondary rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-50 shadow-lg shadow-secondary/20 active:scale-95"
            >
              {submitting ? (
                <span className="w-4 h-4 border-2 border-on-secondary border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <span className="material-symbols-outlined text-sm">login</span>
                  Sign In
                </>
              )}
            </button>
            <button
              type="button"
              onClick={() => setForgotMsg(true)}
              className="w-full text-center text-xs text-outline hover:text-secondary transition-colors"
            >
              Forgot Password?
            </button>
            {forgotMsg && (
              <p className="text-center text-[10px] text-secondary">Contact help@atlantaguardian.com for assistance</p>
            )}
          </form>
        )}

        {/* Register Form */}
        {tab === 'register' && (
          <form onSubmit={handleRegister} className="space-y-3">
            <div className="relative">
              <span className="material-symbols-outlined text-outline text-lg absolute left-3 top-1/2 -translate-y-1/2">person</span>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Full Name"
                className={`${inputClass} pl-10`}
              />
            </div>
            <div className="relative">
              <span className="material-symbols-outlined text-outline text-lg absolute left-3 top-1/2 -translate-y-1/2">mail</span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email address"
                className={`${inputClass} pl-10`}
              />
            </div>
            <div className="relative">
              <span className="material-symbols-outlined text-outline text-lg absolute left-3 top-1/2 -translate-y-1/2">phone</span>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="Phone number (optional)"
                className={`${inputClass} pl-10`}
              />
            </div>
            <div className="relative">
              <span className="material-symbols-outlined text-outline text-lg absolute left-3 top-1/2 -translate-y-1/2">lock</span>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password (8+ characters)"
                className={`${inputClass} pl-10`}
              />
            </div>
            <div className="relative">
              <span className="material-symbols-outlined text-outline text-lg absolute left-3 top-1/2 -translate-y-1/2">lock</span>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm Password"
                className={`${inputClass} pl-10`}
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="w-full py-3.5 bg-secondary hover:bg-secondary/80 text-on-secondary rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-50 shadow-lg shadow-secondary/20 active:scale-95"
            >
              {submitting ? (
                <span className="w-4 h-4 border-2 border-on-secondary border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <span className="material-symbols-outlined text-sm">person_add</span>
                  Create Account
                </>
              )}
            </button>
          </form>
        )}

        {/* Footer */}
        <div className="text-center space-y-1 pt-2">
          <div className="flex items-center justify-center gap-1.5">
            <span className="material-symbols-outlined text-tactical-green text-xs">lock</span>
            <span className="text-[10px] text-outline">Secure & Private</span>
          </div>
          <p className="text-[9px] text-outline/50">Your safety is our priority</p>
        </div>
      </div>
    </div>
  );
}
