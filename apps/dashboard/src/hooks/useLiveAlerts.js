/**
 * useLiveAlerts.js — Realtime Staff Alerts Hook
 * ================================================
 * Milestone 5: Lắng nghe alerts trong Firestore theo thời gian thực.
 *
 * Collection: tenants/{tenantId}/alerts
 * Order: created_at DESC (mới nhất trước)
 *
 * @returns {{ alerts, loading, error, pendingCount }}
 *   alerts       — mảng alert objects kèm alert_id
 *   loading      — true trong lần fetch đầu
 *   error        — Error object nếu có lỗi
 *   pendingCount — số alerts chưa xử lý (CREATED hoặc ACKNOWLEDGED)
 */

import { useState, useEffect } from 'react'
import { collection, query, orderBy, limit, onSnapshot } from 'firebase/firestore'
import { db } from '../firebase.js'

const USE_MOCK = import.meta.env.VITE_USE_MOCK_FIRESTORE === 'true'
const TENANT_ID = import.meta.env.VITE_DEMO_TENANT_ID || 'pho-ba-lan_1722500000000'

// Mock data khi VITE_USE_MOCK_FIRESTORE=true
const MOCK_ALERTS = [
  {
    alert_id:       'mock-alert-001',
    feedback_id:    'mock-fb-001',
    location:       'Bàn 5',
    status:         'CREATED',
    intent:         'SUPPORT_REQUEST',
    transcript:     'Cho tôi thêm ly nước đá ạ',
    created_at:     { seconds: Date.now() / 1000 - 120, toDate: () => new Date(Date.now() - 120000) },
    acknowledged_at: null,
    resolved_at:    null,
  },
  {
    alert_id:       'mock-alert-002',
    feedback_id:    'mock-fb-002',
    location:       'Bàn 2',
    status:         'ACKNOWLEDGED',
    intent:         'SUPPORT_REQUEST',
    transcript:     'Tính tiền đi, tôi vội',
    created_at:     { seconds: Date.now() / 1000 - 600, toDate: () => new Date(Date.now() - 600000) },
    acknowledged_at: { seconds: Date.now() / 1000 - 300, toDate: () => new Date(Date.now() - 300000) },
    resolved_at:    null,
  },
  {
    alert_id:       'mock-alert-003',
    feedback_id:    'mock-fb-003',
    location:       'Khu A',
    status:         'RESOLVED',
    intent:         'SUPPORT_REQUEST',
    transcript:     'Bật điều hòa lên giúp tôi',
    created_at:     { seconds: Date.now() / 1000 - 3600, toDate: () => new Date(Date.now() - 3600000) },
    acknowledged_at: { seconds: Date.now() / 1000 - 3500, toDate: () => new Date(Date.now() - 3500000) },
    resolved_at:    { seconds: Date.now() / 1000 - 3400, toDate: () => new Date(Date.now() - 3400000) },
  },
]

export function useLiveAlerts({ maxItems = 50 } = {}) {
  const [alerts, setAlerts]     = useState([])
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState(null)

  useEffect(() => {
    if (USE_MOCK) {
      // Mock mode: trả static data, simulate realtime với setTimeout
      setAlerts(MOCK_ALERTS)
      setLoading(false)
      return
    }

    const alertsRef = collection(db, 'tenants', TENANT_ID, 'alerts')
    const q = query(
      alertsRef,
      orderBy('created_at', 'desc'),
      limit(maxItems),
    )

    const unsub = onSnapshot(
      q,
      (snapshot) => {
        const docs = snapshot.docs.map(doc => ({
          alert_id: doc.id,
          ...doc.data(),
        }))
        setAlerts(docs)
        setLoading(false)
        setError(null)
      },
      (err) => {
        console.error('[useLiveAlerts] Firestore error:', err)
        setError(err)
        setLoading(false)
      },
    )

    return () => unsub()
  }, [maxItems])

  // Đếm số alerts chưa xử lý (CREATED + ACKNOWLEDGED)
  const pendingCount = alerts.filter(
    a => a.status === 'CREATED' || a.status === 'ACKNOWLEDGED'
  ).length

  return { alerts, loading, error, pendingCount }
}
