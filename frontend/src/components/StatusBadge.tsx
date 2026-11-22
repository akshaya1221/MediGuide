import type { DocumentStatus } from '../types'

const styles: Record<DocumentStatus, string> = {
  ready: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  needs_review: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  failed: 'bg-rose-50 text-rose-700 ring-rose-600/20',
  processing: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  uploaded: 'bg-slate-50 text-slate-700 ring-slate-500/20',
}
export function StatusBadge({ status }: { status: DocumentStatus }) {
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${styles[status]}`}>{status.replace('_', ' ')}</span>
}

