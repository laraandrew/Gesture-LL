import React, { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"

const GESTURE_MAP = {
  HAND_UP: {
    label: "Hand Up — Recording",
    icon: "🎤",
    color: "bg-green-500/20 border-green-400 text-green-300"
  },
  SWIPE_UP: {
    label: "Swipe Up — Study More",
    icon: "⬆️",
    color: "bg-yellow-500/20 border-yellow-400 text-yellow-300"
  },
  SWIPE_LEFT: {
    label: "Swipe Left — Revisit Later",
    icon: "⬅️",
    color: "bg-red-500/20 border-red-400 text-red-300"
  }
}

export default function GestureIndicator({ lastEvent }) {
  const [gesture, setGesture] = useState(null)

  useEffect(() => {
    if (!lastEvent || lastEvent.kind !== "gesture") return

    setGesture(lastEvent.name)

    const timer = setTimeout(() => {
      setGesture(null)
    }, 1000)

    return () => clearTimeout(timer)
  }, [lastEvent])

  const config = gesture ? GESTURE_MAP[gesture] : null

  return (
    <AnimatePresence>
      {config && (
        <motion.div
          initial={{ opacity: 0, y: 16, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 12, scale: 0.95 }}
          transition={{ duration: 0.25, ease: "easeOut" }}
          className={`fixed bottom-6 right-6 z-50 px-5 py-3 rounded-xl backdrop-blur-md border shadow-xl flex items-center gap-3 ${config.color}`}
        >
          <span className="text-2xl">{config.icon}</span>
          <span className="font-semibold tracking-wide">
            {config.label}
          </span>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
