import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Calculator,
  AlertTriangle,
  CheckCircle2,
  Users,
  IndianRupee,
  Star,
  X,
  BarChart3,
  Zap,
} from 'lucide-react'
import { MOCK_CLUSTERS, CATEGORY_LABELS } from '../data/mockClusters'

const BUDGET_MIN = 10   // lakhs
const BUDGET_MAX = 500  // lakhs (5 Cr)

function formatLakhs(val) {
  if (val >= 100) return `₹${(val / 100).toFixed(2)} Cr`
  return `₹${val}L`
}

function ClusterRow({ cluster, checked, onToggle }) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-3 rounded-xl px-4 py-3 transition-all duration-150 cursor-pointer"
      style={{
        background: checked ? 'rgba(99,102,241,0.1)' : 'rgba(17,24,39,0.5)',
        border: checked ? '1px solid rgba(99,102,241,0.35)' : '1px solid rgba(255,255,255,0.05)',
      }}
      onClick={() => onToggle(cluster.id)}
    >
      {/* Checkbox */}
      <div
        className="w-5 h-5 rounded-md flex items-center justify-center flex-shrink-0 transition-all duration-150"
        style={{
          background: checked ? 'linear-gradient(135deg,#6366F1,#8B5CF6)' : 'rgba(255,255,255,0.06)',
          border: checked ? 'none' : '1px solid rgba(255,255,255,0.15)',
        }}
      >
        {checked && <CheckCircle2 size={13} className="text-white" />}
      </div>

      {/* Cluster info */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-white truncate">{cluster.name}</p>
        <div className="flex items-center gap-3 mt-0.5">
          <span className="text-xs text-gray-500">{CATEGORY_LABELS[cluster.category] ?? cluster.category}</span>
          <span className="text-xs text-gray-600">·</span>
          <span className="text-xs text-gray-500">{cluster.location}</span>
        </div>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-4 flex-shrink-0 text-right">
        <div className="hidden sm:block">
          <p className="text-xs text-gray-500">Cost</p>
          <p className="text-sm font-bold text-amber-400">₹{cluster.cost_estimate}L</p>
        </div>
        <div className="hidden sm:block">
          <p className="text-xs text-gray-500">Beneficiaries</p>
          <p className="text-sm font-semibold text-green-400">{cluster.beneficiaries.toLocaleString('en-IN')}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Score</p>
          <p
            className="text-sm font-bold"
            style={{
              color: cluster.priority_score >= 70 ? '#EF4444' : cluster.priority_score >= 40 ? '#F59E0B' : '#10B981',
            }}
          >
            {cluster.priority_score}
          </p>
        </div>
      </div>
    </motion.div>
  )
}

function ReportModal({ onClose, summary }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)' }}
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        className="rounded-3xl p-6 w-full max-w-lg"
        style={{
          background: '#0D1529',
          border: '1px solid rgba(99,102,241,0.3)',
          boxShadow: '0 20px 60px rgba(0,0,0,0.6)',
        }}
      >
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <BarChart3 size={20} className="text-indigo-400" />
            Budget Simulation Report
          </h3>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/10 transition-colors">
            <X size={18} className="text-gray-400" />
          </button>
        </div>

        <div className="space-y-3 mb-5">
          {[
            { label: 'Total Budget', value: formatLakhs(summary.budget), color: '#818CF8' },
            { label: 'Allocated', value: formatLakhs(summary.allocated), color: '#F59E0B' },
            { label: 'Remaining', value: formatLakhs(summary.remaining), color: summary.remaining < 0 ? '#EF4444' : '#10B981' },
            { label: 'Projects Selected', value: summary.count, color: '#F9FAFB' },
            { label: 'Total Beneficiaries', value: summary.beneficiaries.toLocaleString('en-IN'), color: '#10B981' },
            { label: 'Weighted Impact Score', value: summary.impact.toFixed(1), color: '#6366F1' },
          ].map((row) => (
            <div
              key={row.label}
              className="flex justify-between items-center py-2 px-3 rounded-xl"
              style={{ background: 'rgba(255,255,255,0.04)' }}
            >
              <span className="text-sm text-gray-400">{row.label}</span>
              <span className="text-sm font-bold" style={{ color: row.color }}>{row.value}</span>
            </div>
          ))}
        </div>

        <div className="text-xs text-gray-500 mb-5 p-3 rounded-xl" style={{ background: 'rgba(99,102,241,0.08)' }}>
          📊 Simulation generated on {new Date().toLocaleString('en-IN')} for Bangalore South constituency. Scores computed using current weight configuration.
        </div>

        <button
          onClick={onClose}
          className="w-full py-3 rounded-xl font-semibold text-sm"
          style={{ background: 'linear-gradient(135deg,#6366F1,#8B5CF6)', color: 'white' }}
        >
          Close Report
        </button>
      </motion.div>
    </motion.div>
  )
}

export default function WhatIfSimulator() {
  const [budget, setBudget] = useState(150)
  const [selected, setSelected] = useState(new Set())
  const [showReport, setShowReport] = useState(false)
  const [simulating, setSimulating] = useState(false)

  const toggleCluster = (id) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const selectedClusters = useMemo(
    () => MOCK_CLUSTERS.filter((c) => selected.has(c.id)),
    [selected]
  )

  const totalCost = useMemo(
    () => selectedClusters.reduce((s, c) => s + c.cost_estimate, 0),
    [selectedClusters]
  )

  const totalBeneficiaries = useMemo(
    () => selectedClusters.reduce((s, c) => s + c.beneficiaries, 0),
    [selectedClusters]
  )

  const weightedImpact = useMemo(() => {
    if (!selectedClusters.length) return 0
    return selectedClusters.reduce((s, c) => s + c.priority_score * c.beneficiaries, 0) /
      (totalBeneficiaries || 1)
  }, [selectedClusters, totalBeneficiaries])

  const overBudget = totalCost > budget
  const remaining = budget - totalCost

  const handleSimulate = async () => {
    setSimulating(true)
    try {
      await fetch('/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cluster_ids: [...selected], budget }),
      })
    } catch { /* backend may be offline */ }
    await new Promise((r) => setTimeout(r, 600))
    setSimulating(false)
    setShowReport(true)
  }

  const reportSummary = {
    budget,
    allocated: totalCost,
    remaining,
    count: selectedClusters.length,
    beneficiaries: totalBeneficiaries,
    impact: weightedImpact,
  }

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      <AnimatePresence>
        {showReport && (
          <ReportModal onClose={() => setShowReport(false)} summary={reportSummary} />
        )}
      </AnimatePresence>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'rgba(99,102,241,0.2)' }}
            >
              <Calculator size={20} className="text-indigo-400" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">What-If Budget Simulator</h1>
              <p className="text-sm text-gray-400">Model different investment scenarios for Bangalore South</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: cluster selector */}
          <div className="lg:col-span-2 space-y-4">
            {/* Budget slider */}
            <div
              className="rounded-2xl p-5"
              style={{
                background: 'rgba(17,24,39,0.7)',
                border: '1px solid rgba(99,102,241,0.15)',
              }}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                  <IndianRupee size={14} className="text-amber-400" />
                  Quarterly Budget
                </span>
                <span className="text-xl font-black text-white">{formatLakhs(budget)}</span>
              </div>
              <input
                type="range"
                min={BUDGET_MIN}
                max={BUDGET_MAX}
                step={5}
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
                className="w-full h-2 rounded-full appearance-none cursor-pointer"
                style={{ accentColor: '#F59E0B' }}
              />
              <div className="flex justify-between text-xs text-gray-600 mt-1">
                <span>₹10L</span>
                <span>₹5 Cr</span>
              </div>
            </div>

            {/* Cluster selection */}
            <div
              className="rounded-2xl p-5"
              style={{
                background: 'rgba(17,24,39,0.7)',
                border: '1px solid rgba(99,102,241,0.15)',
              }}
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-bold text-white">Select Projects</h2>
                <div className="flex gap-2">
                  <button
                    onClick={() => setSelected(new Set(MOCK_CLUSTERS.map((c) => c.id)))}
                    className="text-xs px-3 py-1.5 rounded-lg transition-colors hover:bg-white/10"
                    style={{ color: '#818CF8', border: '1px solid rgba(99,102,241,0.25)' }}
                  >
                    Select All
                  </button>
                  <button
                    onClick={() => setSelected(new Set())}
                    className="text-xs px-3 py-1.5 rounded-lg transition-colors hover:bg-white/10"
                    style={{ color: '#9CA3AF', border: '1px solid rgba(255,255,255,0.1)' }}
                  >
                    Clear
                  </button>
                </div>
              </div>
              <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                {[...MOCK_CLUSTERS].sort((a, b) => b.priority_score - a.priority_score).map((cluster) => (
                  <ClusterRow
                    key={cluster.id}
                    cluster={cluster}
                    checked={selected.has(cluster.id)}
                    onToggle={toggleCluster}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Right: live impact panel */}
          <div className="space-y-4">
            <div
              className="rounded-2xl p-5 sticky top-24"
              style={{
                background: 'rgba(17,24,39,0.85)',
                border: '1px solid rgba(99,102,241,0.2)',
                backdropFilter: 'blur(16px)',
              }}
            >
              <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                <Zap size={16} className="text-amber-400" />
                Live Impact Preview
              </h2>

              {/* Budget bar */}
              <div className="mb-5">
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-gray-400">Budget Used</span>
                  <span
                    className="font-bold"
                    style={{ color: overBudget ? '#EF4444' : '#10B981' }}
                  >
                    {formatLakhs(totalCost)} / {formatLakhs(budget)}
                  </span>
                </div>
                <div
                  className="w-full rounded-full overflow-hidden"
                  style={{ height: 8, background: 'rgba(255,255,255,0.06)' }}
                >
                  <motion.div
                    animate={{ width: `${Math.min((totalCost / budget) * 100, 100)}%` }}
                    transition={{ duration: 0.4 }}
                    style={{
                      height: '100%',
                      borderRadius: 9999,
                      background: overBudget
                        ? 'linear-gradient(90deg,#F59E0B,#EF4444)'
                        : 'linear-gradient(90deg,#6366F1,#10B981)',
                    }}
                  />
                </div>
              </div>

              {/* Warning */}
              {overBudget && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="rounded-xl p-3 mb-4 flex items-start gap-2"
                  style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)' }}
                >
                  <AlertTriangle size={14} className="text-red-400 flex-shrink-0 mt-0.5" />
                  <p className="text-xs text-red-300">
                    Over budget by <b>{formatLakhs(Math.abs(remaining))}</b>. Remove projects to stay within budget.
                  </p>
                </motion.div>
              )}

              {/* Metrics */}
              {[
                {
                  label: 'Projects Selected',
                  value: selectedClusters.length,
                  color: '#818CF8',
                },
                {
                  label: 'Total Cost',
                  value: formatLakhs(totalCost),
                  color: overBudget ? '#EF4444' : '#F59E0B',
                },
                {
                  label: 'Remaining Budget',
                  value: formatLakhs(remaining),
                  color: remaining < 0 ? '#EF4444' : '#10B981',
                },
                {
                  label: 'Total Beneficiaries',
                  value: totalBeneficiaries.toLocaleString('en-IN'),
                  color: '#10B981',
                },
                {
                  label: 'Weighted Impact Score',
                  value: weightedImpact.toFixed(1),
                  color: '#6366F1',
                },
              ].map((m) => (
                <div
                  key={m.label}
                  className="flex justify-between items-center py-2.5 border-b"
                  style={{ borderColor: 'rgba(255,255,255,0.05)' }}
                >
                  <span className="text-xs text-gray-400">{m.label}</span>
                  <span className="text-sm font-bold" style={{ color: m.color }}>
                    {m.value}
                  </span>
                </div>
              ))}

              <motion.button
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.97 }}
                onClick={handleSimulate}
                disabled={!selectedClusters.length || simulating}
                className="w-full mt-5 py-3 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all duration-200 disabled:opacity-40"
                style={{
                  background: 'linear-gradient(135deg,#6366F1,#8B5CF6)',
                  color: 'white',
                  boxShadow: selectedClusters.length ? '0 4px 20px rgba(99,102,241,0.35)' : 'none',
                }}
              >
                <BarChart3 size={16} />
                {simulating ? 'Generating…' : 'Generate Report'}
              </motion.button>

              <p className="text-xs text-gray-600 mt-3 text-center">
                {selectedClusters.length} of {MOCK_CLUSTERS.length} projects selected
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
