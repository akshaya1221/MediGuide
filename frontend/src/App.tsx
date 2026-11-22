import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { useAuth } from './context/AuthContext'
import { AuthPage } from './pages/AuthPage'
import { FollowUpsPage, MedicationsPage, QuestionsPage, TimelinePage } from './pages/CarePages'
import { DashboardPage } from './pages/DashboardPage'
import { DocumentDetailPage } from './pages/DocumentDetailPage'
import { DocumentsPage } from './pages/DocumentsPage'
import { UploadPage } from './pages/UploadPage'

function Protected() {
  const { user, loading } = useAuth()
  if (loading) return <div className="grid min-h-screen place-items-center text-slate-500">Opening your private workspace…</div>
  return user ? <Layout/> : <Navigate to="/auth" replace/>
}

export default function App() {
  return <Routes><Route path="/auth" element={<AuthPage/>}/><Route element={<Protected/>}><Route index element={<DashboardPage/>}/><Route path="upload" element={<UploadPage/>}/><Route path="documents" element={<DocumentsPage/>}/><Route path="documents/:id" element={<DocumentDetailPage/>}/><Route path="timeline" element={<TimelinePage/>}/><Route path="follow-ups" element={<FollowUpsPage/>}/><Route path="medications" element={<MedicationsPage/>}/><Route path="questions" element={<QuestionsPage/>}/></Route><Route path="*" element={<Navigate to="/" replace/>}/></Routes>
}

