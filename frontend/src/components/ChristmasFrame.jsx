import React from 'react'
import { motion } from 'framer-motion'

export default function ChristmasFrame({ children }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="relative max-w-xl w-full rounded-3xl border border-christmasGreen/60 bg-gradient-to-br from-black via-slate-900 to-black shadow-2xl p-6 md:p-8"
    >
      <div className="absolute -top-4 left-1/2 -translate-x-1/2 flex gap-2 text-lg">
        <span>🎄</span>
        <span>🎁</span>
        <span>❄️</span>
        <span>🔔</span>
      </div>
      <div className="absolute inset-0 rounded-3xl pointer-events-none border border-christmasRed/50" />
      <div className="relative">{children}</div>
    </motion.div>
  )
}
