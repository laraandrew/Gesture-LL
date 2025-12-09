import React, { useEffect, useState } from 'react'
import ChristmasFrame from './components/ChristmasFrame.jsx'
import Flashcard from './components/Flashcard.jsx'
import GestureIcons from './components/GestureIcons.jsx'

const API_BASE = 'http://localhost:8000'

export default function App() {
  const [state, setState] = useState(null)
  const [lastEvent, setLastEvent] = useState(null)

  useEffect(() => {
    async function fetchInitialState() {
      try {
        const res = await fetch(`${API_BASE}/api/state`)
        const data = await res.json()
        setState(data)
      } catch (err) {
        console.error('Failed to fetch initial state', err)
      }
    }

    fetchInitialState()

    const ws = new WebSocket('ws://localhost:8000/ws')

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        if (message.type === 'state') {
          setState(message.payload)
        } else if (message.type === 'event') {
          setLastEvent(message.payload)
        }
      } catch (err) {
        console.error('Error parsing WebSocket message', err)
      }
    }

    ws.onerror = (err) => {
      console.error('WebSocket error', err)
    }

    return () => {
      ws.close()
    }
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-10">
      <ChristmasFrame>
        <div className="flex flex-col gap-6 items-center">
          <h1 className="text-3xl md:text-4xl font-bold text-center">
            🎄 Gesture Language Learning 🎄
          </h1>
          <p className="text-sm text-gray-200 text-center max-w-md">
            Raise your hand to answer, swipe up to study more, swipe left to revisit later.
            Watch the camera window for gesture recognition.
          </p>
          <Flashcard state={state} lastEvent={lastEvent} />
          <GestureIcons />
        </div>
      </ChristmasFrame>
    </div>
  )
}
