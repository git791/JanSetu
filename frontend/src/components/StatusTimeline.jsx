import { CheckCircle2, Circle, Clock } from 'lucide-react'
import { motion } from 'framer-motion'

const STEPS = [
  'Received',
  'Under Review',
  'Approved',
  'In Progress',
  'Completed',
]

export default function StatusTimeline({ currentStatus, dates = {} }) {
  const currentIndex = STEPS.indexOf(currentStatus)

  return (
    <div className="flex flex-col gap-0">
      {STEPS.map((step, idx) => {
        const isDone = idx < currentIndex
        const isCurrent = idx === currentIndex
        const isFuture = idx > currentIndex

        return (
          <div key={step} className="flex items-start gap-3">
            {/* Icon column */}
            <div className="flex flex-col items-center">
              {/* Circle */}
              <div className="relative flex items-center justify-center" style={{ width: 24, height: 24 }}>
                {isDone && (
                  <CheckCircle2 size={22} className="text-indigo-400" />
                )}
                {isCurrent && (
                  <>
                    <motion.div
                      className="absolute rounded-full"
                      style={{
                        width: 22,
                        height: 22,
                        border: '2px solid #6366F1',
                        background: 'rgba(99,102,241,0.15)',
                      }}
                      animate={{ scale: [1, 1.25, 1], opacity: [1, 0.5, 1] }}
                      transition={{ repeat: Infinity, duration: 1.6, ease: 'easeInOut' }}
                    />
                    <div
                      className="rounded-full bg-indigo-500"
                      style={{ width: 10, height: 10 }}
                    />
                  </>
                )}
                {isFuture && (
                  <Circle size={22} className="text-gray-600" />
                )}
              </div>
              {/* Vertical connector */}
              {idx < STEPS.length - 1 && (
                <div
                  style={{
                    width: 2,
                    height: 28,
                    background: isDone ? '#6366F1' : 'rgba(255,255,255,0.08)',
                    margin: '2px 0',
                    borderRadius: 1,
                  }}
                />
              )}
            </div>

            {/* Label column */}
            <div className="pb-6">
              <p
                className={`text-sm font-medium leading-tight ${
                  isDone
                    ? 'text-indigo-400'
                    : isCurrent
                    ? 'text-white'
                    : 'text-gray-500'
                }`}
              >
                {step}
              </p>
              {dates[step] && (
                <p className="text-xs text-gray-500 mt-0.5 flex items-center gap-1">
                  <Clock size={10} />
                  {new Date(dates[step]).toLocaleDateString('en-IN', {
                    day: 'numeric',
                    month: 'short',
                    year: 'numeric',
                  })}
                </p>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
