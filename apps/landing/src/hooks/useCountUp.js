import { useState, useEffect, useRef } from 'react'
import { useReducedMotion } from './useReducedMotion'

/**
 * useCountUp — animates a number from 0 to `end` when the ref enters viewport.
 *
 * @param {number} end - target number
 * @param {number} duration - animation duration in ms (default 1800)
 * @param {string} suffix - text appended to number (e.g. '+', '%')
 * @returns {{ ref, value }} - attach ref to container element
 */
export function useCountUp(end, duration = 1800, suffix = '') {
  const [value, setValue] = useState(0)
  const ref = useRef(null)
  const reducedMotion = useReducedMotion()
  const hasStarted = useRef(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    if (reducedMotion) {
      setValue(end)
      return
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasStarted.current) {
          hasStarted.current = true
          animateCount()
          observer.disconnect()
        }
      },
      { threshold: 0.5 }
    )

    observer.observe(el)
    return () => observer.disconnect()
  }, [end, duration, reducedMotion])

  function animateCount() {
    const startTime = performance.now()

    function step(currentTime) {
      const elapsed = currentTime - startTime
      const progress = Math.min(elapsed / duration, 1)
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      const current = Math.round(eased * end)
      setValue(current)

      if (progress < 1) {
        requestAnimationFrame(step)
      } else {
        setValue(end)
      }
    }

    requestAnimationFrame(step)
  }

  return { ref, value: `${value}${suffix}` }
}
