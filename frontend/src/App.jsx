import React, { useEffect, useState } from 'react'
import ChristmasFrame from './components/ChristmasFrame.jsx'
import Flashcard from './components/Flashcard.jsx'
import GestureIcons from './components/GestureIcons.jsx'
import GestureIndicator from './components/GestureIndicator.jsx'

const API_BASE = 'http://localhost:8000'

export default function App() {
  const [state, setState] = useState(null)
  const [lastEvent, setLastEvent] = useState(null)

  const [isRecording, setIsRecording] = useState(false)
  const [recognizedText, setRecognizedText] = useState("")
  const [evaluation, setEvaluation] = useState(null)

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

        switch (message.type) {
          case "state":
            setState(message.payload)
            break

          case "event":
            setLastEvent(message.payload)

            if (message.payload.kind === "evaluation") {
              setEvaluation({
                correct: message.payload.correct,
                spoken: message.payload.spoken
              })
            }
            break

          case "START_RECORDING":
            setIsRecording(true)
            setRecognizedText("")
            
            setTimeout(() => {
              setIsRecording(false)
            }, 1000)

            break


          case "STOP_RECORDING":
            // We only use this for text, NOT UI visibility
            setRecognizedText(message.text)
            break

          default:
            console.log("Unknown WS message:", message)
        }
      } catch (err) {
        console.error('Error parsing WebSocket message', err)
      }
    }

    ws.onerror = (err) => console.error('WebSocket error', err)

    return () => ws.close()
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
            Recording begins automatically when your hand is raised.
          </p>

          {recognizedText && (
            <div className="text-green-300 text-lg">
              <strong>You said:</strong> {recognizedText}
            </div>
          )}

          {evaluation && (
            <div className={`text-lg font-semibold ${
              evaluation.correct ? "text-green-400" : "text-red-400"
            }`}>
              {evaluation.correct ? "✔ Correct!" : "✖ Incorrect"}
              <div className="text-sm opacity-80">({evaluation.spoken})</div>
            </div>
          )}

          <Flashcard state={state} lastEvent={lastEvent} />

          <GestureIcons />
        </div>
      </ChristmasFrame>

      {/* Gesture feedback overlay */}
      <GestureIndicator lastEvent={lastEvent} />
    </div>
  )
}
