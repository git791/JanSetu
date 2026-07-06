import { motion, AnimatePresence } from 'framer-motion'
import {
  X,
  BookOpen,
  MapPin,
  FileText,
  BarChart2,
  ExternalLink,
  CheckCircle,
  Clock,
  AlertCircle,
  Database,
  Layers,
} from 'lucide-react'
import PriorityScoreBar from './PriorityScoreBar'
import StatusTimeline from './StatusTimeline'

const FACTOR_META = {
  D: { label: 'Demand (w1)', description: 'Unique citizen requests weighted by frequency' },
  G: { label: 'Need Gap (w2)', description: 'Gap between current service level and benchmark' },
  V: { label: 'Vulnerability (w3)', description: 'SC/ST, BPL, gender disparity index' },
  F: { label: 'Feasibility (w4)', description: 'Implementation readiness & resource availability' },
  O: { label: 'Overlap Penalty (w5)', description: 'Deduction for schemes already covering area' },
}

const EVIDENCE_META = {
  udise_ref: { icon: BookOpen, label: 'UDISE+ Reference', color: '#6366F1' },
  census_ref: { icon: Database, label: 'Census / NFHS Data', color: '#8B5CF6' },
  maps_ref: { icon: MapPin, label: 'Geospatial / Maps', color: '#F59E0B' },
  plan_ref: { icon: FileText, label: 'Scheme / Plan Ref', color: '#10B981' },
}

const STATUS_COLORS = {
  Received: 'bg-gray-700 text-gray-300',
  'Under Review': 'bg-amber-900/40 text-amber-300',
  Approved: 'bg-indigo-900/40 text-indigo-300',
  'In Progress': 'bg-blue-900/40 text-blue-300',
  Completed: 'bg-green-900/40 text-green-300',
}

export default function EvidenceDrawer({ cluster, onClose }) {
  if (!cluster) return null

  const handleApprove = async () => {
    try {
      // Optimistically update or just call API
      const res = await fetch(`/api/clusters/${cluster.id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'Approved' }),
      })
      if (res.ok) {
        alert(`Cluster ${cluster.id} approved! Check backend terminal for SMS stub.`)
        onClose()
      } else {
        alert(`Failed to approve: Backend returned ${res.status}`)
      }
    } catch (err) {
      console.error('Approval error:', err)
      alert('Network error connecting to backend. Is it running?')
    }
  }

  return (
    <AnimatePresence>
      {cluster && (
        <>
          {/* Backdrop */}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40"
            style={{ background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)' }}
            onClick={onClose}
          />

          {/* Drawer */}
          <motion.div
            key="drawer"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="fixed right-0 top-0 h-full z-50 overflow-y-auto"
            style={{
              width: 'min(520px, 100vw)',
              background: '#0D1529',
              borderLeft: '1px solid rgba(99,102,241,0.25)',
              boxShadow: '-20px 0 60px rgba(0,0,0,0.5)',
            }}
          >
            {/* Header */}
            <div
              className="sticky top-0 z-10 flex items-start justify-between p-6 pb-4"
              style={{ background: '#0D1529', borderBottom: '1px solid rgba(99,102,241,0.15)' }}
            >
              <div className="flex-1 pr-4">
                <div className="flex items-center gap-2 mb-2">
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      STATUS_COLORS[cluster.status] ?? 'bg-gray-700 text-gray-300'
                    }`}
                  >
                    {cluster.status}
                  </span>
                  <span className="text-xs text-gray-500">{cluster.ward_id}</span>
                </div>
                <h2 className="text-lg font-bold text-white leading-tight">{cluster.name}</h2>
                <p className="text-sm text-gray-400 mt-1 flex items-center gap-1">
                  <MapPin size={12} />
                  {cluster.location}
                </p>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-white/10 transition-colors flex-shrink-0"
              >
                <X size={20} className="text-gray-400" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Priority Score Summary */}
              <div
                className="rounded-xl p-4"
                style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)' }}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                    <BarChart2 size={16} className="text-indigo-400" />
                    Priority Score Breakdown
                  </span>
                  <span className="text-2xl font-black text-white">{cluster.priority_score}</span>
                </div>

                <div className="space-y-3">
                  {Object.entries(cluster.score_breakdown ?? {}).map(([key, val]) => {
                    const meta = FACTOR_META[key]
                    return (
                      <div key={key}>
                        <div className="flex justify-between items-center mb-1">
                          <div>
                            <span className="text-xs font-semibold text-white">{meta?.label ?? key}</span>
                            <p className="text-xs text-gray-500">{meta?.description}</p>
                          </div>
                          <span className="text-sm font-bold text-indigo-300 ml-4 flex-shrink-0">{val}</span>
                        </div>
                        <div
                          className="w-full rounded-full overflow-hidden"
                          style={{ height: 6, background: 'rgba(255,255,255,0.06)' }}
                        >
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${val}%` }}
                            transition={{ duration: 0.6, delay: 0.1 }}
                            style={{
                              height: '100%',
                              background: 'linear-gradient(90deg, #6366F1, #8B5CF6)',
                              borderRadius: 9999,
                            }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Key Stats */}
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: 'Citizens', value: cluster.demand_count?.toLocaleString('en-IN') },
                  { label: 'Beneficiaries', value: cluster.beneficiaries?.toLocaleString('en-IN') },
                  { label: 'Cost Est.', value: `₹${cluster.cost_estimate}L` },
                ].map((s) => (
                  <div
                    key={s.label}
                    className="rounded-lg p-3 text-center"
                    style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}
                  >
                    <p className="text-lg font-bold text-white">{s.value}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{s.label}</p>
                  </div>
                ))}
              </div>

              {/* Evidence Cards */}
              <div>
                <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                  <Layers size={14} className="text-indigo-400" />
                  Evidence Sources
                </h3>
                <div className="space-y-2">
                  {Object.entries(EVIDENCE_META).map(([key, meta]) => {
                    const value = cluster.evidence?.[key]
                    if (!value || value === 'N/A') return null
                    const Icon = meta.icon
                    return (
                      <div
                        key={key}
                        className="rounded-lg p-3 flex gap-3"
                        style={{
                          background: 'rgba(255,255,255,0.03)',
                          border: '1px solid rgba(255,255,255,0.06)',
                        }}
                      >
                        <div
                          className="rounded-lg p-1.5 flex-shrink-0 self-start mt-0.5"
                          style={{ background: `${meta.color}18` }}
                        >
                          <Icon size={14} style={{ color: meta.color }} />
                        </div>
                        <div className="min-w-0">
                          <p className="text-xs font-semibold" style={{ color: meta.color }}>
                            {meta.label}
                          </p>
                          <p className="text-xs text-gray-400 mt-0.5 leading-relaxed">{value}</p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Status Timeline */}
              <div>
                <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                  <Clock size={14} className="text-indigo-400" />
                  Status History
                </h3>
                <StatusTimeline
                  currentStatus={cluster.status}
                  dates={{
                    Received: '2026-06-01T00:00:00Z',
                    'Under Review': cluster.status !== 'Received' ? '2026-06-10T00:00:00Z' : undefined,
                    Approved: ['Approved', 'In Progress', 'Completed'].includes(cluster.status)
                      ? '2026-06-18T00:00:00Z'
                      : undefined,
                    'In Progress': ['In Progress', 'Completed'].includes(cluster.status)
                      ? '2026-06-25T00:00:00Z'
                      : undefined,
                    Completed: cluster.status === 'Completed' ? cluster.last_updated : undefined,
                  }}
                />
              </div>

              {/* Last updated */}
              <p className="text-xs text-gray-600">
                Last updated:{' '}
                {new Date(cluster.last_updated).toLocaleString('en-IN', {
                  day: 'numeric',
                  month: 'short',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>

              {/* Action Buttons */}
              <div className="space-y-2 pb-4">
                <button
                  onClick={handleApprove}
                  className="w-full py-3 rounded-xl font-semibold text-sm transition-all duration-200 hover:opacity-90"
                  style={{ background: 'linear-gradient(135deg, #6366F1, #8B5CF6)', color: 'white' }}
                >
                  <CheckCircle size={16} className="inline mr-2" />
                  Approve for Budget Allocation
                </button>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    className="py-2.5 rounded-xl font-medium text-sm transition-all duration-200 hover:bg-white/10"
                    style={{
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid rgba(255,255,255,0.1)',
                      color: '#9CA3AF',
                    }}
                  >
                    <Clock size={14} className="inline mr-1" />
                    Defer
                  </button>
                  <button
                    className="py-2.5 rounded-xl font-medium text-sm transition-all duration-200 hover:bg-white/10"
                    style={{
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid rgba(255,255,255,0.1)',
                      color: '#9CA3AF',
                    }}
                  >
                    <AlertCircle size={14} className="inline mr-1" />
                    Request Data
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
