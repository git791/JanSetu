import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  TrendingUp,
  Users,
  Layers,
  Star,
  SlidersHorizontal,
  RefreshCw,
  MapPin,
} from 'lucide-react'
import { MOCK_CLUSTERS } from '../data/mockClusters'
import NeedClusterCard from '../components/NeedClusterCard'
import EvidenceDrawer from '../components/EvidenceDrawer'
import ConstituencyMap from '../components/ConstituencyMap'

const DEFAULT_WEIGHTS = { w1: 0.35, w2: 0.25, w3: 0.20, w4: 0.15, w5: 0.05 }

const WEIGHT_META = [
  { key: 'w1', label: 'Demand (w1)', desc: 'Citizen request volume' },
  { key: 'w2', label: 'Need Gap (w2)', desc: 'Service deficit vs benchmark' },
  { key: 'w3', label: 'Vulnerability (w3)', desc: 'SC/ST, BPL, gender index' },
  { key: 'w4', label: 'Feasibility (w4)', desc: 'Implementation readiness' },
  { key: 'w5', label: 'Overlap (w5)', desc: 'Scheme duplication penalty' },
]

function useAnimatedCounter(target, duration = 1200) {
  const [value, setValue] = useState(0)
  useEffect(() => {
    const start = Date.now()
    const tick = () => {
      const elapsed = Date.now() - start
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setValue(Math.round(eased * target))
      if (progress < 1) requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  }, [target, duration])
  return value
}

function StatCard({ label, value, icon: Icon, color, prefix = '', suffix = '' }) {
  const animated = useAnimatedCounter(typeof value === 'number' ? value : 0)
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl p-5 flex flex-col gap-3"
      style={{
        background: 'rgba(17,24,39,0.7)',
        border: '1px solid rgba(99,102,241,0.15)',
        backdropFilter: 'blur(12px)',
      }}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-gray-400">{label}</span>
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: `${color}18` }}
        >
          <Icon size={16} style={{ color }} />
        </div>
      </div>
      <div className="text-2xl font-black text-white">
        {prefix}{typeof value === 'number' ? animated.toLocaleString('en-IN') : value}{suffix}
      </div>
    </motion.div>
  )
}

function SkeletonCard() {
  return (
    <div
      className="rounded-2xl p-4 animate-pulse"
      style={{ background: 'rgba(17,24,39,0.5)', border: '1px solid rgba(255,255,255,0.05)' }}
    >
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-lg bg-gray-700" />
        <div className="w-9 h-9 rounded-xl bg-gray-700" />
        <div className="flex-1 space-y-2">
          <div className="h-3 bg-gray-700 rounded w-1/4" />
          <div className="h-4 bg-gray-700 rounded w-3/4" />
          <div className="h-2 bg-gray-700 rounded w-full" />
          <div className="h-3 bg-gray-700 rounded w-1/2" />
        </div>
      </div>
    </div>
  )
}

function recomputeScores(clusters, weights) {
  return clusters.map((c) => {
    const { D, G, V, F, O } = c.score_breakdown
    const raw =
      weights.w1 * D +
      weights.w2 * G +
      weights.w3 * V +
      weights.w4 * F -
      weights.w5 * O
    return { ...c, priority_score: Math.max(0, Math.min(100, Math.round(raw))) }
  }).sort((a, b) => b.priority_score - a.priority_score)
}

export default function MPDashboard() {
  const [clusters, setClusters] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [weights, setWeights] = useState(DEFAULT_WEIGHTS)
  const [liveScores, setLiveScores] = useState([])

  const today = new Date().toLocaleDateString('en-IN', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  })

  const fetchClusters = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/clusters')
      if (!res.ok) throw new Error()
      const data = await res.json()
      if (data.clusters && Array.isArray(data.clusters)) {
        setClusters(data.clusters)
        setLiveScores(recomputeScores(data.clusters, weights))
      } else {
        throw new Error('Invalid data format')
      }
    } catch (error) {
      console.error('Failed to fetch real clusters', error)
      setClusters([])
      setLiveScores([])
    }
    setLoading(false)
  }, []) // eslint-disable-line

  useEffect(() => { fetchClusters() }, [fetchClusters])

  useEffect(() => {
    if (clusters.length) setLiveScores(recomputeScores(clusters, weights))
  }, [weights, clusters])

  const totalSubmissions = clusters.reduce((s, c) => s + c.demand_count, 0)
  const activeClusters = clusters.length
  const citizensReached = clusters.reduce((s, c) => s + c.beneficiaries, 0)
  const avgScore = clusters.length
    ? Math.round(clusters.reduce((s, c) => s + c.priority_score, 0) / clusters.length)
    : 0

  return (
    <div
      className="min-h-screen"
      style={{ background: 'var(--bg-primary)' }}
    >
      <EvidenceDrawer cluster={selected} onClose={() => setSelected(null)} />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Top bar */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-8">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
              Good morning, MP's Office 🌄
            </h1>
            <p className="text-gray-400 text-sm mt-1 flex items-center gap-1">
              <MapPin size={13} />
              <span className="font-medium text-indigo-300">Bangalore South</span>
              &nbsp;·&nbsp;{today}
            </p>
          </div>
          <button
            onClick={fetchClusters}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 hover:opacity-80 self-start sm:self-auto"
            style={{
              background: 'rgba(99,102,241,0.15)',
              border: '1px solid rgba(99,102,241,0.25)',
              color: '#818CF8',
            }}
          >
            <RefreshCw size={14} /> Refresh
          </button>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard label="Total Submissions" value={totalSubmissions} icon={TrendingUp} color="#6366F1" />
          <StatCard label="Need Clusters" value={activeClusters} icon={Layers} color="#8B5CF6" />
          <StatCard label="Citizens Reached" value={citizensReached} icon={Users} color="#10B981" />
          <StatCard label="Avg Priority Score" value={avgScore} icon={Star} color="#F59E0B" suffix="/100" />
        </div>

        {/* Main content — 2 columns */}
        <div className="grid grid-cols-1 xl:grid-cols-5 gap-6 mb-8">
          {/* Cluster list — 60% */}
          <div className="xl:col-span-3">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Layers size={18} className="text-indigo-400" />
              Ranked Need Clusters
            </h2>
            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
              {loading
                ? Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)
                : liveScores.map((cluster, idx) => (
                    <NeedClusterCard
                      key={cluster.id}
                      cluster={cluster}
                      rank={idx + 1}
                      index={idx}
                      onSelect={setSelected}
                    />
                  ))}
            </div>
          </div>

          {/* Map — 40% */}
          <div className="xl:col-span-2">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <MapPin size={18} className="text-indigo-400" />
              Constituency Map
            </h2>
            <div style={{ height: 600 }}>
              <ConstituencyMap clusters={liveScores} onClusterSelect={setSelected} />
            </div>
          </div>
        </div>

        {/* Weight adjustment panel */}
        <div
          className="rounded-2xl p-6"
          style={{
            background: 'rgba(17,24,39,0.7)',
            border: '1px solid rgba(99,102,241,0.15)',
            backdropFilter: 'blur(12px)',
          }}
        >
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <SlidersHorizontal size={18} className="text-indigo-400" />
              Priority Weight Configuration
            </h2>
            <button
              onClick={() => setWeights(DEFAULT_WEIGHTS)}
              className="text-xs text-gray-400 hover:text-indigo-300 transition-colors"
            >
              Reset to defaults
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5">
            {WEIGHT_META.map(({ key, label, desc }) => (
              <div key={key}>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs font-semibold text-gray-300">{label}</span>
                  <span className="text-xs font-bold text-indigo-300">
                    {(weights[key] * 100).toFixed(0)}%
                  </span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.01}
                  value={weights[key]}
                  onChange={(e) =>
                    setWeights((w) => ({ ...w, [key]: parseFloat(e.target.value) }))
                  }
                  className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
                  style={{ accentColor: '#6366F1' }}
                />
                <p className="text-xs text-gray-600 mt-1">{desc}</p>
              </div>
            ))}
          </div>

          <p className="text-xs text-gray-600 mt-4">
            Weights affect live re-ranking above. Total weight: {' '}
            <span className="text-gray-400 font-medium">
              {(Object.values(weights).reduce((a, b) => a + b, 0) * 100).toFixed(0)}%
            </span>
          </p>
        </div>
      </div>
    </div>
  )
}
