import React from 'react'
import { motion } from 'framer-motion'

export default function Flashcard({ state, lastEvent }) {
  const card = state?.current_card
  const learnedCount = state?.learned_words?.length ?? 0
  const studyMoreCount = state?.study_more_words?.length ?? 0
  const revisitCount = state?.revisit_words?.length ?? 0

  const isCorrect = lastEvent?.kind === 'evaluation' && lastEvent.correct === true
  const isIncorrect = lastEvent?.kind === 'evaluation' && lastEvent.correct === false

  return (
    <motion.div
      key={card?.english ?? 'placeholder'}
      initial={{ y: 16, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.25 }}
      className="w-full rounded-2xl bg-white/10 border border-white/20 p-5 md:p-6 flex flex-col gap-4"
    >
      <div className="flex justify-between items-center">
        <span className="text-xs uppercase tracking-widest text-gray-300">
          English → Spanish
        </span>
        <span className="text-xs text-gray-300">
          Learned: <span className="text-christmasGreen font-semibold">{learnedCount}</span> ·
          Study: <span className="text-yellow-300 font-semibold">{studyMoreCount}</span> ·
          Revisit: <span className="text-red-400 font-semibold">{revisitCount}</span>
        </span>
      </div>

      <div className="flex flex-col items-center justify-center py-4 gap-2">
        <p className="text-sm text-gray-300">Current word</p>
        <p className="text-3xl md:text-4xl font-bold text-white tracking-wide">
          {card?.english ?? 'No words loaded'}
        </p>
      </div>

      <motion.div
        initial={false}
        animate={
          isCorrect
            ? { backgroundColor: 'rgba(22,163,74,0.2)', scale: 1.02 }
            : isIncorrect
            ? { backgroundColor: 'rgba(185,28,28,0.2)', scale: 1.02 }
            : { backgroundColor: 'rgba(15,23,42,0.7)', scale: 1 }
        }
        transition={{ duration: 0.25 }}
        className="rounded-xl px-4 py-3 flex items-center justify-between"
      >
        <div className="flex flex-col gap-1">
          <span className="text-xs text-gray-300 uppercase tracking-wide">
            Last Result
          </span>
          <span className="text-sm">
            {isCorrect && (
              <span className="text-christmasGreen font-semibold flex items-center gap-1">
                ✔ Correct!
              </span>
            )}
            {isIncorrect && (
              <span className="text-red-400 font-semibold flex items-center gap-1">
                ✘ Incorrect · Card will be revisited
              </span>
            )}
            {!isCorrect && !isIncorrect && (
              <span className="text-gray-300">Waiting for your next answer...</span>
            )}
          </span>
        </div>
        <div className="text-2xl">
          {isCorrect && <span>🎁</span>}
          {isIncorrect && <span>🎄</span>}
          {!isCorrect && !isIncorrect && <span>❄️</span>}
        </div>
      </motion.div>
    </motion.div>
  )
}
