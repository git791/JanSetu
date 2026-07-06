import { motion } from 'framer-motion'
import {
  GraduationCap,
  Construction,
  Droplets,
  HeartPulse,
  Zap,
  Shield,
  HelpCircle,
  MapPin,
  Users,
  ChevronRight,
} from 'lucide-react'
import PriorityScoreBar from './PriorityScoreBar'

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

const CATEGORY_LABELS = {
  education: 'Education',
  road: 'Road & Infra',
  water: 'Water',
  health: 'Health',
  electricity: 'Electricity',
  public_safety: 'Public Safety',
}

const STATUS_STYLES = {
  Received: { bg: 'rgba(107,114,128,0.2)', color: '#9CA3AF' },
  'Under Review': { bg: 'rgba(245,158,11,0.15)', color: '#F59E0B' },
  Approved: { bg: 'rgba(99,102,241,0.2)', color: '#818CF8' },
  'In Progress': { bg: 'rgba(59,130,246,0.2)', color: '#60A5FA' },
  Completed: { bg: 'rgba(16,185,129,0.2)', color: '#34D399' },
}

export default function NeedClusterCard({ cluster, rank, index, onSelect }) {
  const Icon = CATEGORY_ICONS[cluster.category] ?? HelpCircle
  const catColor = CATEGORY_COLORS[cluster.category] ?? '#6366F1'
  const statusStyle = STATUS_STYLES[cluster.status] ?? STATUS_STYLES.Received

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.07, ease: 'easeOut' }}
      whileHover={{
        y: -2,
        boxShadow: `0 8px 32px rgba(99,102,241,0.25)`,
      }}
      onClick={() => onSelect(cluster)}
      className="cursor-pointer rounded-2xl p-4 transition-all duration-200"
      style={{
        background: 'rgba(17,24,39,0.7)',
        border: '1px solid rgba(99,102,241,0.15)',
        backdropFilter: 'blur(12px)',
      }}
    >
      <div className="flex items-start gap-3">
        {/* Rank badge */}
        <div
          className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-sm font-black"
          style={{
            background:
              rank === 1
                ? 'linear-gradient(135deg, #F59E0B, #EF4444)'
                : rank === 2
                ? 'linear-gradient(135deg, #9CA3AF, #6B7280)'
                : rank === 3
                ? 'linear-gradient(135deg, #B45309, #92400E)'
                : 'rgba(99,102,241,0.2)',
            color: rank <= 3 ? 'white' : '#818CF8',
          }}
        >
          {rank}
        </div>

        {/* Category icon */}
        <div
          className="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center"
          style={{ background: `${catColor}18` }}
        >
          <Icon size={18} style={{ color: catColor }} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-1">
            <div className="min-w-0">
              <span
                className="text-xs font-medium px-1.5 py-0.5 rounded-md mr-2"
                style={{ background: `${catColor}18`, color: catColor }}
              >
                {CATEGORY_LABELS[cluster.category] ?? cluster.category}
              </span>
            </div>
            {/* Status badge */}
            <span
              className="text-xs font-medium px-2 py-0.5 rounded-full flex-shrink-0"
              style={{ background: statusStyle.bg, color: statusStyle.color }}
            >
              {cluster.status}
            </span>
          </div>

          <h3 className="text-sm font-semibold text-white leading-tight line-clamp-2 mb-2">
            {cluster.name}
          </h3>

          {/* Score bar */}
          <div className="mb-2">
            <PriorityScoreBar score={cluster.priority_score} height={6} />
          </div>

          {/* Footer row */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-xs text-gray-400 flex items-center gap-1">
                <Users size={11} />
                {cluster.demand_count?.toLocaleString('en-IN')} citizens
              </span>
              <span className="text-xs text-gray-500 flex items-center gap-1">
                <MapPin size={11} />
                {cluster.location}
              </span>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation()
                onSelect(cluster)
              }}
              className="text-xs flex items-center gap-0.5 font-medium transition-colors hover:text-indigo-300"
              style={{ color: '#6366F1' }}
            >
              Evidence
              <ChevronRight size={12} />
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
