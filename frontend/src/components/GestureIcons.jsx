import React from 'react'

export default function GestureIcons() {
  return (
    <div className="w-full flex flex-col gap-2 text-sm text-gray-200">
      <div className="flex items-center gap-2">
        <span className="text-lg">👋</span>
        <span>
          <span className="font-semibold text-white">Hand Up</span> – answer this card.
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-lg">⬆️</span>
        <span>
          <span className="font-semibold text-white">Swipe Up</span> – mark as{' '}
          <span className="text-yellow-300 font-semibold">study more</span>.
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-lg">⬅️</span>
        <span>
          <span className="font-semibold text-white">Swipe Left</span> –{' '}
          <span className="text-red-400 font-semibold">revisit later</span>.
        </span>
      </div>
      <p className="text-xs text-gray-400 pt-1">
        Tip: Make big, clear gestures in front of your webcam for best detection.
      </p>
    </div>
  )
}
