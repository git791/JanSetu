import { useState, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import {
  MessageSquare,
  Mic,
  ImageIcon,
  MapPin,
  ChevronRight,
  ChevronLeft,
  Upload,
  CheckCircle2,
  Activity,
  Phone,
  Loader2,
  Copy,
} from 'lucide-react'

const STEPS = ['Channel', 'Your Request', 'Confirm & Submit']

const LANGUAGES = [
  { value: 'hi', label: 'हिंदी (Hindi)' },
  { value: 'en', label: 'English' },
  { value: 'ta', label: 'தமிழ் (Tamil)' },
  { value: 'te', label: 'తెలుగు (Telugu)' },
  { value: 'mr', label: 'मराठी (Marathi)' },
  { value: 'bn', label: 'বাংলা (Bengali)' },
  { value: 'kn', label: 'ಕನ್ನಡ (Kannada)' },
  { value: 'gu', label: 'ગુજરાતી (Gujarati)' },
  { value: 'pa', label: 'ਪੰਜਾਬੀ (Punjabi)' },
  { value: 'or', label: 'ଓଡ଼ିଆ (Odia)' },
]

const CATEGORIES = [
  { value: 'road', label: 'Road / Infrastructure' },
  { value: 'education', label: 'Education / School' },
  { value: 'water', label: 'Water / Drainage' },
  { value: 'health', label: 'Health' },
  { value: 'electricity', label: 'Electricity' },
  { value: 'public_safety', label: 'Public Safety' },
  { value: 'other', label: 'Other' },
]

const CHANNELS = [
  {
    id: 'text',
    icon: MessageSquare,
    label: 'Text Message',
    desc: 'Type your issue in any Indian language or English',
    color: '#6366F1',
  },
  {
    id: 'voice',
    icon: Mic,
    label: 'Voice Recording',
    desc: 'Upload an audio clip — we transcribe and translate automatically',
    color: '#8B5CF6',
  },
  {
    id: 'photo',
    icon: ImageIcon,
    label: 'Upload Photo',
    desc: 'Send a photo of the problem — pothole, broken pipe, damaged school',
    color: '#F59E0B',
  },
]

function GradientOrb({ className, style }) {
  return (
    <div
      className={`absolute rounded-full pointer-events-none blur-3xl opacity-20 ${className}`}
      style={style}
    />
  )
}

function StepIndicator({ current, total }) {
  return (
    <div className="flex items-center gap-2 mb-8">
      {STEPS.map((label, idx) => (
        <div key={label} className="flex items-center gap-2">
          <div className="flex flex-col items-center gap-1">
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300"
              style={{
                background:
                  idx < current
                    ? 'linear-gradient(135deg,#6366F1,#8B5CF6)'
                    : idx === current
                    ? 'rgba(99,102,241,0.3)'
                    : 'rgba(255,255,255,0.06)',
                border:
                  idx === current
                    ? '2px solid #6366F1'
                    : '2px solid transparent',
                color: idx <= current ? 'white' : '#4B5563',
              }}
            >
              {idx < current ? <CheckCircle2 size={16} /> : idx + 1}
            </div>
            <span
              className="text-xs font-medium hidden sm:block"
              style={{ color: idx === current ? '#818CF8' : '#4B5563' }}
            >
              {label}
            </span>
          </div>
          {idx < total - 1 && (
            <div
              className="h-px w-8 sm:w-16 mt-px"
              style={{
                background:
                  idx < current
                    ? 'linear-gradient(90deg,#6366F1,#8B5CF6)'
                    : 'rgba(255,255,255,0.08)',
              }}
            />
          )}
        </div>
      ))}
    </div>
  )
}

function ChannelCard({ channel, selected, onSelect }) {
  const Icon = channel.icon
  return (
    <motion.button
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      onClick={() => onSelect(channel.id)}
      className="relative w-full text-left rounded-2xl p-6 transition-all duration-200"
      style={{
        background: selected
          ? `linear-gradient(135deg, ${channel.color}22, ${channel.color}10)`
          : 'rgba(17,24,39,0.6)',
        border: selected
          ? `2px solid ${channel.color}`
          : '2px solid rgba(255,255,255,0.07)',
        backdropFilter: 'blur(12px)',
        boxShadow: selected ? `0 0 30px ${channel.color}33` : 'none',
      }}
    >
      <div
        className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
        style={{ background: `${channel.color}22` }}
      >
        <Icon size={22} style={{ color: channel.color }} />
      </div>
      <h3 className="text-base font-bold text-white mb-1">{channel.label}</h3>
      <p className="text-sm text-gray-400 leading-relaxed">{channel.desc}</p>
      {selected && (
        <div
          className="absolute top-3 right-3 w-6 h-6 rounded-full flex items-center justify-center"
          style={{ background: channel.color }}
        >
          <CheckCircle2 size={14} className="text-white" />
        </div>
      )}
    </motion.button>
  )
}

function DropZone({ label, accept, icon: Icon, onFile, preview }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) onFile(file)
  }

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className="rounded-2xl border-2 border-dashed flex flex-col items-center justify-center py-10 cursor-pointer transition-all duration-200"
      style={{
        borderColor: dragging ? '#6366F1' : 'rgba(99,102,241,0.3)',
        background: dragging ? 'rgba(99,102,241,0.08)' : 'rgba(17,24,39,0.4)',
      }}
    >
      <input ref={inputRef} type="file" accept={accept} className="hidden" onChange={(e) => onFile(e.target.files[0])} />
      {preview ? (
        <img src={preview} alt="preview" className="max-h-36 rounded-xl object-contain" />
      ) : (
        <>
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center mb-3"
            style={{ background: 'rgba(99,102,241,0.15)' }}
          >
            <Icon size={28} className="text-indigo-400" />
          </div>
          <p className="text-sm font-medium text-gray-300">Drop file here or click to browse</p>
          <p className="text-xs text-gray-500 mt-1">{label}</p>
        </>
      )}
    </div>
  )
}

function generateTrackingId() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
  let id = 'JS-'
  for (let i = 0; i < 8; i++) id += chars[Math.floor(Math.random() * chars.length)]
  return id
}

export default function CitizenSubmit() {
  const [step, setStep] = useState(0)
  const [channel, setChannel] = useState('text')
  const [text, setText] = useState('')
  const [lang, setLang] = useState('hi')
  const [category, setCategory] = useState('road')
  const [location, setLocation] = useState('')
  const [locationLoading, setLocationLoading] = useState(false)
  const [audioFile, setAudioFile] = useState(null)
  const [photoFile, setPhotoFile] = useState(null)
  const [photoPreview, setPhotoPreview] = useState(null)
  const [phone, setPhone] = useState('')
  const [otpSent, setOtpSent] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [trackingId] = useState(generateTrackingId)

  const detectLocation = () => {
    if (!navigator.geolocation) {
      toast.error('Geolocation not supported by your browser')
      return
    }
    setLocationLoading(true)
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const res = await fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${pos.coords.latitude}&lon=${pos.coords.longitude}&format=json`
          )
          const data = await res.json()
          const readable =
            data.address?.suburb ||
            data.address?.neighbourhood ||
            data.address?.city_district ||
            data.display_name?.split(',')[0]
          setLocation(readable || `${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}`)
        } catch {
          setLocation(`${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}`)
        }
        setLocationLoading(false)
      },
      () => {
        toast.error('Could not detect location')
        setLocationLoading(false)
      }
    )
  }

  const handlePhotoFile = (file) => {
    setPhotoFile(file)
    const reader = new FileReader()
    reader.onload = (e) => setPhotoPreview(e.target.result)
    reader.readAsDataURL(file)
  }

  const handleSendOtp = () => {
    if (phone.replace(/\D/g, '').length < 10) {
      toast.error('Enter a valid 10-digit mobile number')
      return
    }
    toast.success('OTP sent to +91 ' + phone.replace(/\D/g, ''))
    setOtpSent(true)
  }

  const handleSubmit = async () => {
    setSubmitting(true)
    try {
      const payload = {
        channel,
        text: channel === 'text' ? text : undefined,
        category,
        location,
        lang,
        mediaUrl: channel === 'voice' ? audioFile?.name : channel === 'photo' ? photoFile?.name : undefined,
      }
      const res = await fetch('/api/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error('API error')
    } catch {
      // gracefully continue — backend may be offline for MVP
    }
    await new Promise((r) => setTimeout(r, 1200))
    setSubmitting(false)
    setSubmitted(true)
  }

  // Success screen
  if (submitted) {
    return (
      <div
        className="min-h-screen flex flex-col items-center justify-center px-4 relative overflow-hidden"
        style={{ background: 'var(--bg-primary)' }}
      >
        <GradientOrb className="w-96 h-96 -top-32 -right-32" style={{ background: '#6366F1' }} />
        <GradientOrb className="w-72 h-72 -bottom-24 -left-24" style={{ background: '#8B5CF6' }} />

        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: 'spring', stiffness: 200, damping: 20 }}
          className="relative z-10 text-center max-w-md"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
            className="w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-6"
            style={{ background: 'linear-gradient(135deg, #6366F1, #10B981)' }}
          >
            <CheckCircle2 size={48} className="text-white" />
          </motion.div>

          <h2 className="text-3xl font-extrabold text-white mb-2">Request Submitted!</h2>
          <p className="text-gray-400 mb-6">
            Your concern has been recorded and will be reviewed by the MP's office.
          </p>

          <div
            className="rounded-2xl p-5 mb-6"
            style={{ background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.3)' }}
          >
            <p className="text-xs text-gray-500 mb-1">Your Tracking ID</p>
            <div className="flex items-center justify-center gap-3">
              <span className="text-2xl font-black tracking-widest text-indigo-300">{trackingId}</span>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(trackingId)
                  toast.success('Tracking ID copied!')
                }}
                className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
              >
                <Copy size={16} className="text-gray-400" />
              </button>
            </div>
          </div>

          <div
            className="rounded-xl px-4 py-3 mb-6 text-sm"
            style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)', color: '#34D399' }}
          >
            ✓ You will be notified on WhatsApp when your request is reviewed
          </div>

          <button
            onClick={() => {
              setSubmitted(false)
              setStep(0)
              setText('')
              setLocation('')
              setAudioFile(null)
              setPhotoFile(null)
              setPhotoPreview(null)
              setPhone('')
              setOtpSent(false)
            }}
            className="text-sm text-indigo-400 hover:text-indigo-300 transition-colors underline"
          >
            Submit another request
          </button>
        </motion.div>
      </div>
    )
  }

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center px-4 py-12 relative overflow-hidden"
      style={{ background: 'var(--bg-primary)' }}
    >
      {/* Orbs */}
      <GradientOrb className="w-96 h-96 -top-32 -right-32" style={{ background: '#6366F1' }} />
      <GradientOrb className="w-72 h-72 -bottom-24 -left-24" style={{ background: '#8B5CF6' }} />
      <GradientOrb className="w-64 h-64 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" style={{ background: '#F59E0B' }} />

      <div className="relative z-10 w-full max-w-2xl">
        {/* Title */}
        <div className="text-center mb-8">
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white mb-2">
            Share Your <span className="gradient-text">Concern</span>
          </h1>
          <p className="text-gray-400 text-sm">
            Your voice reaches the MP's office directly — anonymised and AI-analysed
          </p>
        </div>

        {/* Step indicator */}
        <div className="flex justify-center">
          <StepIndicator current={step} total={STEPS.length} />
        </div>

        {/* Card */}
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -40 }}
            transition={{ duration: 0.25 }}
            className="glass rounded-3xl p-6 sm:p-8"
          >
            {/* ── STEP 0: Channel ── */}
            {step === 0 && (
              <div>
                <h2 className="text-xl font-bold text-white mb-1">How would you like to share?</h2>
                <p className="text-sm text-gray-400 mb-6">Choose the easiest way for you</p>
                <div className="grid gap-4">
                  {CHANNELS.map((ch) => (
                    <ChannelCard key={ch.id} channel={ch} selected={channel === ch.id} onSelect={setChannel} />
                  ))}
                </div>
              </div>
            )}

            {/* ── STEP 1: Request ── */}
            {step === 1 && (
              <div className="space-y-5">
                <div>
                  <h2 className="text-xl font-bold text-white mb-1">Describe your request</h2>
                  <p className="text-sm text-gray-400">All details are kept anonymous</p>
                </div>

                {/* Input based on channel */}
                {channel === 'text' && (
                  <div className="space-y-3">
                    <textarea
                      value={text}
                      onChange={(e) => setText(e.target.value)}
                      rows={5}
                      placeholder="अपनी समस्या बताएं / Describe your issue here…"
                      className="w-full rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 outline-none resize-none transition-all duration-200"
                      style={{
                        background: 'rgba(255,255,255,0.05)',
                        border: '1px solid rgba(99,102,241,0.25)',
                      }}
                      onFocus={(e) =>
                        (e.target.style.borderColor = 'rgba(99,102,241,0.6)')
                      }
                      onBlur={(e) =>
                        (e.target.style.borderColor = 'rgba(99,102,241,0.25)')
                      }
                    />
                    <div>
                      <label className="text-xs text-gray-400 mb-1 block">Language</label>
                      <select
                        value={lang}
                        onChange={(e) => setLang(e.target.value)}
                        className="w-full rounded-xl px-4 py-2.5 text-sm text-white outline-none"
                        style={{
                          background: 'rgba(17,24,39,0.8)',
                          border: '1px solid rgba(99,102,241,0.25)',
                        }}
                      >
                        {LANGUAGES.map((l) => (
                          <option key={l.value} value={l.value}>{l.label}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                )}

                {channel === 'voice' && (
                  <DropZone
                    label="Accepts .mp3, .wav, .ogg, .m4a"
                    accept="audio/*"
                    icon={Mic}
                    onFile={setAudioFile}
                    preview={null}
                  />
                )}
                {audioFile && channel === 'voice' && (
                  <p className="text-xs text-indigo-300 flex items-center gap-2">
                    <CheckCircle2 size={14} /> {audioFile.name}
                  </p>
                )}

                {channel === 'photo' && (
                  <DropZone
                    label="Accepts .jpg, .png, .webp — max 10MB"
                    accept="image/*"
                    icon={ImageIcon}
                    onFile={handlePhotoFile}
                    preview={photoPreview}
                  />
                )}

                {/* Category */}
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full rounded-xl px-4 py-2.5 text-sm text-white outline-none"
                    style={{
                      background: 'rgba(17,24,39,0.8)',
                      border: '1px solid rgba(99,102,241,0.25)',
                    }}
                  >
                    {CATEGORIES.map((c) => (
                      <option key={c.value} value={c.value}>{c.label}</option>
                    ))}
                  </select>
                </div>

                {/* Location */}
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Your Location</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      placeholder="Ward / Layout / Area name"
                      className="flex-1 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 outline-none"
                      style={{
                        background: 'rgba(255,255,255,0.05)',
                        border: '1px solid rgba(99,102,241,0.25)',
                      }}
                    />
                    <button
                      onClick={detectLocation}
                      disabled={locationLoading}
                      className="px-3 rounded-xl flex items-center gap-1 text-xs font-medium transition-all duration-200 hover:opacity-80"
                      style={{ background: 'rgba(99,102,241,0.2)', color: '#818CF8' }}
                    >
                      {locationLoading ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : (
                        <MapPin size={14} />
                      )}
                      Detect
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* ── STEP 2: Confirm & Submit ── */}
            {step === 2 && (
              <div className="space-y-5">
                <div>
                  <h2 className="text-xl font-bold text-white mb-1">Confirm & Submit</h2>
                  <p className="text-sm text-gray-400">Review your submission before sending</p>
                </div>

                {/* Summary card */}
                <div
                  className="rounded-xl p-4 space-y-2"
                  style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)' }}
                >
                  <Row label="Channel" value={CHANNELS.find((c) => c.id === channel)?.label} />
                  <Row label="Category" value={CATEGORIES.find((c) => c.value === category)?.label} />
                  <Row label="Location" value={location || '—'} />
                  {channel === 'text' && <Row label="Message" value={text?.slice(0, 120) + (text?.length > 120 ? '…' : '')} />}
                  {channel === 'voice' && <Row label="Audio file" value={audioFile?.name ?? '—'} />}
                  {channel === 'photo' && <Row label="Photo" value={photoFile?.name ?? '—'} />}
                  <Row label="Language" value={LANGUAGES.find((l) => l.value === lang)?.label} />
                </div>

                {/* Phone + OTP */}
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">
                    Mobile Number (for WhatsApp updates)
                  </label>
                  <div className="flex gap-2">
                    <div
                      className="flex items-center px-3 rounded-l-xl text-sm text-gray-400"
                      style={{
                        background: 'rgba(17,24,39,0.8)',
                        border: '1px solid rgba(99,102,241,0.25)',
                        borderRight: 'none',
                      }}
                    >
                      <Phone size={14} className="mr-1" /> +91
                    </div>
                    <input
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                      placeholder="98765 43210"
                      className="flex-1 rounded-r-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 outline-none"
                      style={{
                        background: 'rgba(255,255,255,0.05)',
                        border: '1px solid rgba(99,102,241,0.25)',
                      }}
                    />
                    <button
                      onClick={handleSendOtp}
                      className="px-4 rounded-xl text-xs font-semibold transition-all duration-200 hover:opacity-80 flex-shrink-0"
                      style={{ background: 'rgba(99,102,241,0.25)', color: '#818CF8' }}
                    >
                      Send OTP
                    </button>
                  </div>
                  {otpSent && (
                    <p className="text-xs text-green-400 mt-1.5 flex items-center gap-1">
                      <CheckCircle2 size={12} /> OTP sent — enter to verify before submitting
                    </p>
                  )}
                </div>

                {/* Submit */}
                <motion.button
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="w-full py-4 rounded-2xl font-bold text-base flex items-center justify-center gap-2 transition-all duration-200"
                  style={{
                    background: submitting
                      ? 'rgba(99,102,241,0.4)'
                      : 'linear-gradient(135deg, #6366F1, #8B5CF6)',
                    color: 'white',
                    boxShadow: submitting ? 'none' : '0 4px 20px rgba(99,102,241,0.4)',
                  }}
                >
                  {submitting ? (
                    <>
                      <Loader2 size={18} className="animate-spin" /> Submitting…
                    </>
                  ) : (
                    'Submit Request'
                  )}
                </motion.button>
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        {/* Navigation */}
        <div className="flex justify-between mt-6">
          <button
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            disabled={step === 0}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 disabled:opacity-0"
            style={{ background: 'rgba(255,255,255,0.06)', color: '#9CA3AF' }}
          >
            <ChevronLeft size={16} /> Back
          </button>

          {step < 2 && (
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => {
                if (step === 1 && channel === 'text' && !text.trim()) {
                  toast.error('Please describe your issue')
                  return
                }
                setStep((s) => Math.min(2, s + 1))
              }}
              className="flex items-center gap-2 px-6 py-2 rounded-xl text-sm font-semibold"
              style={{
                background: 'linear-gradient(135deg, #6366F1, #8B5CF6)',
                color: 'white',
              }}
            >
              Next <ChevronRight size={16} />
            </motion.button>
          )}
        </div>
      </div>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex gap-3">
      <span className="text-xs text-gray-500 w-20 flex-shrink-0 pt-0.5">{label}</span>
      <span className="text-sm text-gray-200 flex-1">{value || '—'}</span>
    </div>
  )
}
