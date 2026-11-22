import { ShieldCheck } from 'lucide-react'
export function SafetyNotice({ compact = false }: { compact?: boolean }) {
  return <div className={`flex gap-3 rounded-2xl border border-amber-200 bg-amber-50 text-amber-950 ${compact ? 'p-3 text-xs' : 'p-4 text-sm'}`}><ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-amber-600"/><p><strong>For understanding, not diagnosis.</strong> MediGuide explains uploaded records and keeps the original wording traceable. Confirm medicines, results and medical decisions with a qualified healthcare professional.</p></div>
}

