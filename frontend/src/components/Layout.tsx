import { CalendarClock, ClipboardList, FileText, HelpCircle, LayoutDashboard, LogOut, Menu, Pill, Plus, Stethoscope, X } from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const nav = [
  ['Dashboard', '/', LayoutDashboard], ['Documents', '/documents', FileText], ['Timeline', '/timeline', ClipboardList],
  ['Follow-ups', '/follow-ups', CalendarClock], ['Medications', '/medications', Pill], ['Doctor questions', '/questions', HelpCircle],
] as const

export function Layout() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const sidebar = <><div className="flex h-20 items-center gap-3 px-6"><div className="grid h-10 w-10 place-items-center rounded-xl bg-teal-700 text-white"><Stethoscope/></div><div><p className="font-extrabold text-teal-900">MediGuide AI</p><p className="text-xs text-slate-500">Records made clear</p></div></div><nav className="space-y-1 px-3">{nav.map(([label, path, Icon]) => <NavLink key={path} to={path} end={path === '/'} onClick={() => setOpen(false)} className={({isActive}) => `flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold transition ${isActive ? 'bg-teal-50 text-teal-700' : 'text-slate-600 hover:bg-slate-50 hover:text-ink'}`}><Icon className="h-5 w-5"/>{label}</NavLink>)}</nav><div className="mt-auto p-4"><div className="mb-3 rounded-xl bg-sand p-3"><p className="truncate text-sm font-semibold">{user?.full_name}</p><p className="truncate text-xs text-slate-500">{user?.email}</p></div><button onClick={logout} className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold text-slate-500 hover:bg-rose-50 hover:text-rose-700"><LogOut className="h-4 w-4"/>Sign out</button></div></>
  return <div className="min-h-screen lg:grid lg:grid-cols-[250px_1fr]"><aside className="hidden border-r bg-white lg:flex lg:flex-col">{sidebar}</aside>{open && <div className="fixed inset-0 z-50 flex lg:hidden"><div className="absolute inset-0 bg-ink/30" onClick={() => setOpen(false)}/><aside className="relative flex w-72 flex-col bg-white shadow-2xl">{sidebar}<button className="absolute right-3 top-3 p-2" onClick={() => setOpen(false)}><X/></button></aside></div>}<main><header className="sticky top-0 z-30 flex h-20 items-center justify-between border-b bg-white/90 px-4 backdrop-blur lg:px-8"><button className="p-2 lg:hidden" onClick={() => setOpen(true)}><Menu/></button><div><p className="text-xs font-bold uppercase tracking-[.18em] text-teal-600">Patient workspace</p><h1 className="text-lg font-bold">Welcome back, {user?.full_name.split(' ')[0]}</h1></div><NavLink to="/upload" className="btn-primary"><Plus className="h-4 w-4"/><span className="hidden sm:inline">Add record</span></NavLink></header><div className="mx-auto max-w-7xl p-4 lg:p-8"><Outlet/></div></main></div>
}
