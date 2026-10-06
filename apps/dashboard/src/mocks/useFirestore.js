/**
 * useFirestore.js — Hook đọc dữ liệu Firestore (thật hoặc mock)
 *
 * Điều khiển bởi VITE_USE_MOCK_FIRESTORE:
 *   false → onSnapshot thật từ Firestore
 *   true  → trả về mock data từ firestoreMock.js
 *
 * Collections theo backend/db/schema.md:
 *   tenants/{tenantId}/feedbacks    — phản hồi khách hàng
 *   tenants/{tenantId}/customers    — hồ sơ khách hàng + RFMS
 *   tenants/{tenantId}              — thông tin tenant
 */

import { useState, useEffect } from 'react'
import {
  collection, query, orderBy, limit, onSnapshot,
  where, doc, getDoc,
} from 'firebase/firestore'
import { db } from '../firebase.js'
import {
  MOCK_FEEDBACKS,
  MOCK_CUSTOMERS,
  MOCK_TENANT,
} from './firestoreMock.js'

const USE_MOCK = import.meta.env.VITE_USE_MOCK_FIRESTORE === 'true'
const TENANT_ID = import.meta.env.VITE_DEMO_TENANT_ID || 'pho-ba-lan_1722500000000'

// ─────────────────────────────────────────────────────────────
// Helper: chuyển Firestore Timestamp → JS Date an toàn
// ─────────────────────────────────────────────────────────────
export function tsToDate(ts) {
  if (!ts) return new Date(0)
  if (ts.toDate) return ts.toDate()
  if (ts.seconds) return new Date(ts.seconds * 1000)
  return new Date(ts)
}

// ─────────────────────────────────────────────────────────────
// Hook: useFeedbacks
// Query: tenants/{tenantId}/feedbacks ORDER BY timestamp DESC LIMIT 100
// ─────────────────────────────────────────────────────────────
export function useFeedbacks(tenantId = TENANT_ID) {
  const [feedbacks, setFeedbacks] = useState([])
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState(null)

  useEffect(() => {
    if (USE_MOCK) {
      setFeedbacks(MOCK_FEEDBACKS)
      setLoading(false)
      return
    }

    // Thật: onSnapshot realtime
    const ref = collection(db, `tenants/${tenantId}/feedbacks`)
    const q   = query(ref, orderBy('timestamp', 'desc'), limit(300))

    console.log('[DASHBOARD RT] listener attached')
    const unsub = onSnapshot(
      q,
      snapshot => {
        console.log(`[DASHBOARD RT] snapshot size=${snapshot.size}`)
        console.log(`[DASHBOARD RT] snapshotChanges=${snapshot.docChanges().length}`)
        snapshot.docChanges().forEach(change => {
           console.log(`[DASHBOARD RT] incoming feedback_id=${change.doc.id} type=${change.type}`)
        })
        const docs = snapshot.docs.map(d => ({
          feedback_id: d.id,
          ...d.data(),
        }))
        console.log(`[DASHBOARD RT] state update count=${docs.length}`)
        setFeedbacks(docs)
        setLoading(false)
      },
      err => {
        console.error('[useFeedbacks] Firestore error:', err)
        setError(err.message)
        setLoading(false)
      }
    )

    return () => unsub()
  }, [tenantId])

  return { feedbacks, loading, error }
}

// ─────────────────────────────────────────────────────────────
// Hook: useCustomers
// Query: tenants/{tenantId}/customers ORDER BY p_churn DESC LIMIT 50
// ─────────────────────────────────────────────────────────────
export function useCustomers(tenantId = TENANT_ID) {
  const [customers, setCustomers] = useState([])
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState(null)

  useEffect(() => {
    if (USE_MOCK) {
      setCustomers(MOCK_CUSTOMERS)
      setLoading(false)
      return
    }

    const ref = collection(db, `tenants/${tenantId}/customers`)
    const q   = query(ref, orderBy('p_churn', 'desc'), limit(100))

    const unsub = onSnapshot(
      q,
      snapshot => {
        const docs = snapshot.docs.map(d => ({
          customer_id: d.id,
          ...d.data(),
        }))
        setCustomers(docs)
        setLoading(false)
      },
      err => {
        console.error('[useCustomers] Firestore error:', err)
        setError(err.message)
        setLoading(false)
      }
    )

    return () => unsub()
  }, [tenantId])

  return { customers, loading, error }
}

// ─────────────────────────────────────────────────────────────
// Hook: useTenant — đọc document tenant để lấy business_name, plan...
// ─────────────────────────────────────────────────────────────
export function useTenant(tenantId = TENANT_ID) {
  const [tenant, setTenant] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (USE_MOCK) {
      setTenant(MOCK_TENANT)
      setLoading(false)
      return
    }

    const ref = doc(db, 'tenants', tenantId)
    const unsub = onSnapshot(
      ref,
      snap => {
        if (snap.exists()) {
          setTenant({ tenant_id: snap.id, ...snap.data() })
        }
        setLoading(false)
      },
      err => {
        console.error('[useTenant] Firestore error:', err)
        setLoading(false)
      }
    )

    return () => unsub()
  }, [tenantId])

  return { tenant, loading }
}

// ─────────────────────────────────────────────────────────────
// Export helper timeAgo để dùng trong Pages
// ─────────────────────────────────────────────────────────────
export function timeAgo(ts) {
  const date = tsToDate(ts)
  const now  = new Date()
  const diff = Math.floor((now - date) / 1000)

  if (diff < 60)  return `${diff}s trước`
  if (diff < 3600) return `${Math.floor(diff / 60)}p trước`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h trước`
  return `${Math.floor(diff / 86400)}d trước`
}

// Export để pages biết đang dùng mock hay thật
export const IS_MOCK = USE_MOCK

// ─────────────────────────────────────────────────────────────
// Helper: isBusinessFeedback — predicate dùng chung cho mọi tab
//
// Một feedback "business hợp lệ" phải thỏa mãn:
//   - processing_status === 'done'          (đã xử lý xong)
//   - !is_suspicious                        (không phải bất thường)
//   - intent !== 'SUPPORT_REQUEST'          (không phải yêu cầu hỗ trợ)
//   - validity_status === 'valid' (hoặc không có field — legacy)
//
// Dùng cùng predicate này ở mọi tab để đảm bảo count nhất quán.
// ─────────────────────────────────────────────────────────────
export function isBusinessFeedback(f) {
  if (f.processing_status !== 'done') return false
  if (f.is_suspicious) return false
  if (f.intent === 'SUPPORT_REQUEST') return false
  // Nếu có validity_status (Module 1 anti-fraud), chỉ lấy 'valid'
  // Nếu không có field (legacy records), vẫn accept
  if (f.validity_status && f.validity_status !== 'valid') return false
  return true
}

// ─────────────────────────────────────────────────────────────
// Hook: useBusinessFeedbacks — wrapper tiện dụng trả về
//   feedbacks đã lọc + raw feedbacks + loading + error
// ─────────────────────────────────────────────────────────────
export function useBusinessFeedbacks(tenantId = TENANT_ID) {
  const { feedbacks, loading, error } = useFeedbacks(tenantId)
  const businessFeedbacks = feedbacks.filter(isBusinessFeedback)
  return { feedbacks, businessFeedbacks, loading, error }
}
