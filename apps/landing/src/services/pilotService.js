/**
 * pilotService.js — Pilot form submission abstraction
 *
 * Currently stores submissions to localStorage (demo mode).
 * To connect a real backend, replace submitPilotLead() body:
 *
 *   Option A: Firebase Firestore
 *     import { db } from '../firebase'
 *     await addDoc(collection(db, 'pilot_leads'), data)
 *
 *   Option B: API endpoint
 *     await fetch('/api/pilot-leads', { method: 'POST', body: JSON.stringify(data) })
 *
 *   Option C: Google Sheets via Apps Script
 *     await fetch(GOOGLE_SCRIPT_URL, { method: 'POST', body: JSON.stringify(data) })
 */

const STORAGE_KEY = 'sentrix_pilot_leads'

/**
 * Submit a pilot lead.
 * @param {Object} formData - form fields
 * @returns {Promise<{ success: boolean, id: string }>}
 */
export async function submitPilotLead(formData) {
  // Simulate network latency for demo realism
  await new Promise(resolve => setTimeout(resolve, 900))

  const lead = {
    id: `lead_${Date.now()}`,
    submittedAt: new Date().toISOString(),
    ...formData
  }

  // Store to localStorage (demo only)
  try {
    const existing = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    existing.push(lead)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(existing))
  } catch (e) {
    // Storage unavailable — still succeed for UX
  }

  // TODO: Replace above with real backend call before production launch
  // console.log('[Sentrix Pilot Lead]', lead)

  return { success: true, id: lead.id }
}

/**
 * Retrieve all stored leads (dev/debug only).
 */
export function getStoredLeads() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch {
    return []
  }
}
