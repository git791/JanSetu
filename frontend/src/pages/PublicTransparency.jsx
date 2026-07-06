import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  Search,
  Globe,
  GraduationCap,
  Construction,
  Droplets,
  HeartPulse,
  Zap,
  Shield,
  HelpCircle,
  Users,
  MapPin,
  Star,
} from 'lucide-react'
import { MOCK_CLUSTERS, CATEGORY_LABELS } from '../data/mockClusters'
import StatusTimeline from '../components/StatusTimeline'
import PriorityScoreBar from '../components/PriorityScoreBar'

const STATUS_FILTERS = ['All', 'Received', 'Under Review', 'Approved', 'In Progress', 'Completed']

const CATEGORY_ICONS = {
  education: GraduationCap,
  road: Construction,
  water: Droplets,
  health: HeartPulse,
  electricity: Zap,
  public_safety: Shield,
}

const CATEGORY_COLORS = {
  education: '#6366F1',
  road: '#F59E0B',
  water: '#06B6D4',
  health: '#EF4444',
  electricity: '#EAB308',
  public_safety: '#10B981',
}

const STATUS_STYLES = {
  Received: { bg: 'rgba(107,114,128,0.2)', color: '#9CA3AF' },
  'Under Review': { bg: 'rgba(245,158,11,0.15)', color: '#F59E0B' },
  Approved: { bg: 'rgba(99,102,241,0.2)', color: '#818CF8' },
  'In Progress': { bg: 'rgba(59,130,246,0.2)', color: '#60A5FA' },
  Completed: { bg: 'rgba(16,185,129,0.2)', color: '#34D399' },
}

function ClusterStatusCard({ cluster }) {
  const [expanded, setExpanded] = useState(false)
  const Icon = CATEGORY_ICONS[cluster.category] ?? HelpCircle
  const catColor = CATEGORY_COLORS[cluster.category] ?? '#6366F1'
  const statusStyle = STATUS_STYLES[cluster.status] ?? STATUS_STYLES.Received

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl overflow-hidden"
      style={{
        background: 'rgba(17,24,39,0.7)',
        border: '1px solid rgba(99,102,241,0.12)',
        backdropFilter: 'blur(12px)',
      }}
    >
      <div className="p-5">
        {/* Header */}
        <div className="flex items-start gap-3 mb-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background: `${catColor}18` }}
          >
            <Icon size={18} style={{ color: catColor }} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2 mb-1">
              <span
                className="text-xs font-medium px-2 py-0.5 rounded-full"
                style={{ background: `${catColor}18`, color: catColor }}
              >
                {CATEGORY_LABELS[cluster.category] ?? cluster.category}
              </span>
              <span
                className="text-xs font-medium px-2 py-0.5 rounded-full flex-shrink-0"
                style={{ background: statusStyle.bg, color: statusStyle.color }}
              >
                {cluster.status}
              </span>
            </div>
            <h3 className="text-sm font-bold text-white leading-snug">{cluster.name}</h3>
          </div>
        </div>

        {/* Score bar */}
        <div className="mb-3">
          <PriorityScoreBar score={cluster.priority_score} height={5} />
        </div>

        {/* Stats */}
        <div className="flex items-center justify-between text-xs text-gray-400 mb-4">
          <span className="flex items-center gap-1">
            <Users size={11} />
            {cluster.demand_count.toLocaleString('en-IN')} citizens
          </span>
          <span className="flex items-center gap-1">
            <MapPin size={11} />
            {cluster.location}
          </span>
          <span className="flex items-center gap-1">
            <Star size={11} />
            Score {cluster.priority_score}
          </span>
        </div>

        {/* Toggle timeline */}
        <button
          onClick={() => setExpanded((x) => !x)}
          className="w-full text-xs font-medium py-2 rounded-lg transition-all duration-200 hover:bg-white/10"
          style={{
            color: '#818CF8',
            background: 'rgba(99,102,241,0.08)',
            border: '1px solid rgba(99,102,241,0.15)',
          }}
        >
          {expanded ? 'Hide Timeline ↑' : 'View Timeline ↓'}
        </button>
      </div>

      {/* Expanded timeline */}
      {expanded && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className="px-5 pb-5"
          style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}
        >
          <div className="pt-4">
            <StatusTimeline currentStatus={cluster.status} />
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}

export default function PublicTransparency() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('All')

  const filtered = useMemo(() => {
    let list = [...MOCK_CLUSTERS]
    if (statusFilter !== 'All') list = list.filter((c) => c.status === statusFilter)
    if (search.trim()) {
      const q = search.toLowerCase()
      list = list.filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          c.location.toLowerCase().includes(q) ||
          (CATEGORY_LABELS[c.category] ?? c.category).toLowerCase().includes(q)
      )
    }
    return list.sort((a, b) => b.priority_score - a.priority_score)
  }, [search, statusFilter])

  const stats = useMemo(() => ({
    total: MOCK_CLUSTERS.length,
    completed: MOCK_CLUSTERS.filter((c) => c.status === 'Completed').length,
    inProgress: MOCK_CLUSTERS.filter((c) => c.status === 'In Progress').length,
    citizens: MOCK_CLUSTERS.reduce((s, c) => s + c.demand_count, 0),
  }), [])

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Header */}
        <div className="text-center mb-10">
          <div
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium mb-4"
            style={{
              background: 'rgba(99,102,241,0.15)',
              border: '1px solid rgba(99,102,241,0.25)',
              color: '#818CF8',
            }}
          >
            <Globe size={12} />
            Public Transparency Dashboard
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white mb-3">
            Bangalore South - <span className="gradient-text">Development Tracker</span>
          </h1>
          <p className="text-gray-400 max-w-xl mx-auto text-sm">
            Track every citizen-raised need cluster. All data is anonymised — no personally identifiable information is displayed.
          </p>
        </div>

        {/* Summary stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Total Clusters', value: stats.total, color: '#818CF8' },
            { label: 'Completed', value: stats.completed, color: '#34D399' },
            { label: 'In Progress', value: stats.inProgress, color: '#60A5FA' },
            { label: 'Citizens Heard', value: stats.citizens.toLocaleString('en-IN'), color: '#F59E0B' },
          ].map((s) => (
            <div
              key={s.label}
              className="rounded-2xl p-4 text-center"
              style={{
                background: 'rgba(17,24,39,0.7)',
                border: '1px solid rgba(99,102,241,0.1)',
              }}
            >
              <p className="text-xl font-black" style={{ color: s.color }}>{s.value}</p>
              <p className="text-xs text-gray-500 mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Search & Filter */}
        <div className="flex flex-col sm:flex-row gap-3 mb-6">
          {/* Search */}
          <div className="relative flex-1">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none"
            />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by category, location or name…"
              className="w-full rounded-xl pl-9 pr-4 py-2.5 text-sm text-white placeholder-gray-500 outline-none"
              style={{
                background: 'rgba(17,24,39,0.8)',
                border: '1px solid rgba(99,102,241,0.2)',
              }}
            />
          </div>

          {/* Status filter pills */}
          <div className="flex gap-1.5 flex-wrap">
            {STATUS_FILTERS.map((s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className="px-3 py-2 rounded-xl text-xs font-medium transition-all duration-150"
                style={{
                  background: statusFilter === s ? 'rgba(99,102,241,0.25)' : 'rgba(17,24,39,0.8)',
                  border: statusFilter === s
                    ? '1px solid rgba(99,102,241,0.5)'
                    : '1px solid rgba(255,255,255,0.07)',
                  color: statusFilter === s ? '#818CF8' : '#6B7280',
                }}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Results count */}
        <p className="text-xs text-gray-500 mb-4">
          Showing <span className="text-gray-300 font-medium">{filtered.length}</span> of {MOCK_CLUSTERS.length} clusters
        </p>

        {/* Grid */}
        {filtered.length === 0 ? (
          <div className="text-center py-20">
            <Search size={36} className="text-gray-700 mx-auto mb-3" />
            <p className="text-gray-500">No clusters match your filters</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
            {filtered.map((cluster) => (
              <ClusterStatusCard key={cluster.id} cluster={cluster} />
            ))}
          </div>
        )}

        {/* Footer note */}
        <p className="text-xs text-gray-700 text-center mt-12">
          Data refreshed daily · No PII displayed · JanSetu AI Constituency Intelligence Platform
        </p>
      </div>
    </div>
  )
}
