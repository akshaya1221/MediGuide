import { ArrowRight, FileCheck2, ShieldCheck, Sparkles, Stethoscope } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function AuthPage() {
  const { user, login, register } = useAuth()
  const [mode, setMode] = useState<'login'|'register'>('login')
  const [form, setForm] = useState({ fullName: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  if (user) return <Navigate to="/" replace/>
  async function submit(event: FormEvent) {
    event.preventDefault(); setError(''); setBusy(true)
    try { mode === 'login' ? await login(form.email, form.password) : await register(form.fullName, form.email, form.password) }
    catch (err) { setError(err instanceof Error ? err.message : 'Could not sign in') }
    finally { setBusy(false) }
  }
  return <div className="min-h-screen bg-sand lg:grid lg:grid-cols-[1.1fr_.9fr]"><section className="relative hidden overflow-hidden bg-teal-900 p-14 text-white lg:flex lg:flex-col"><div className="absolute -right-36 -top-36 h-96 w-96 rounded-full bg-teal-500/20"/><div className="flex items-center gap-3 text-xl font-bold"><span className="grid h-11 w-11 place-items-center rounded-xl bg-white/10"><Stethoscope/></span>MediGuide AI</div><div className="my-auto max-w-xl"><p className="mb-4 text-sm font-bold uppercase tracking-[.2em] text-teal-100">Your records, explained</p><h1 className="text-5xl font-extrabold leading-tight">Turn difficult medical records into a clear plan for your next conversation.</h1><p className="mt-6 text-lg leading-8 text-teal-100">Upload a report, trace every explanation to its source, organize follow-ups, and prepare better questions for your doctor.</p><div className="mt-10 grid gap-4 sm:grid-cols-3">{[[FileCheck2,'Source grounded'],[Sparkles,'Plain language'],[ShieldCheck,'Safety first']].map(([Icon,label]) => { const I=Icon as typeof FileCheck2; return <div key={label as string} className="rounded-2xl bg-white/10 p-4"><I className="mb-3 text-teal-100"/><p className="font-semibold">{label as string}</p></div>})}</div></div><p className="text-xs text-teal-100">MediGuide does not diagnose, prescribe, or replace professional medical advice.</p></section><section className="grid place-items-center p-6"><div className="w-full max-w-md"><div className="mb-8 flex items-center gap-3 lg:hidden"><span className="grid h-10 w-10 place-items-center rounded-xl bg-teal-700 text-white"><Stethoscope/></span><span className="font-extrabold">MediGuide AI</span></div><h2 className="text-3xl font-extrabold">{mode === 'login' ? 'Welcome back' : 'Create your account'}</h2><p className="mt-2 text-slate-500">{mode === 'login' ? 'Continue to your private health record workspace.' : 'Your medical records stay separated by account.'}</p><form onSubmit={submit} className="mt-8 space-y-5">{mode === 'register' && <label><span className="label">Full name</span><input className="input" required minLength={2} value={form.fullName} onChange={e=>setForm({...form,fullName:e.target.value})}/></label>}<label><span className="label">Email address</span><input className="input" type="email" required value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/></label><label><span className="label">Password</span><input className="input" type="password" required minLength={8} value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/></label>{error && <p className="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}<button disabled={busy} className="btn-primary w-full py-3">{busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}<ArrowRight className="h-4 w-4"/></button></form><button className="mt-6 w-full text-sm font-semibold text-teal-700" onClick={()=>{setMode(mode==='login'?'register':'login');setError('')}}>{mode === 'login' ? 'New to MediGuide? Create an account' : 'Already have an account? Sign in'}</button></div></section></div>
}

