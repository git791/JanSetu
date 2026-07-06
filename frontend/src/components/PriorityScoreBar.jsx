import { motion } from 'framer-motion'

/**
 * PriorityScoreBar — animated horizontal bar showing a score 0-100.
 * Color: green (0-40) → amber (40-70) → red (70-100)
 * High score = high priority = red.
 */
export default function PriorityScoreBar({ score, showLabel = true, height = 8 }) {
  const clampedScore = Math.max(0, Math.min(100, score ?? 0))

  const getColor = (s) => {
    if (s >= 70) return '#EF4444' // red — high priority
    if (s >= 40) return '#F59E0B' // amber — medium
    return '#10B981'              // green — low
  }

  const color = getColor(clampedScore)

  return (
    <div className="w-full">
      {showLabel && (
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs text-gray-400">Priority Score</span>
          <span
            className="text-sm font-bold"
            style={{ color }}
          >
            {clampedScore}
          </span>
        </div>
      )}
      <div
        className="w-full rounded-full overflow-hidden"
        style={{
          height: `${height}px`,
          background: 'rgba(255,255,255,0.08)',
        }}
      >
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${clampedScore}%` }}
          transition={{ duration: 0.8, ease: 'easeOut', delay: 0.1 }}
          style={{
            height: '100%',
            background: `linear-gradient(90deg, ${color}99, ${color})`,
            borderRadius: 'inherit',
            boxShadow: `0 0 8px ${color}66`,
          }}
        />
      </div>
    </div>
  )
}
