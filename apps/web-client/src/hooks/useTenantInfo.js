/**
 * useTenantInfo.js - Hook doc thong tin tenant tu Firestore
 * Milestone 4: Tenant Context - xoa businessName hard-code
 *
 * Doc document tenants/{tenantId} de lay:
 *   - business_name: ten hien thi (thay the hard-code Pho Ba Lan)
 *   - active: tenant co dang hoat dong khong
 *
 * Cases:
 *   1. tenant ton tai + active -> { businessName, isActive: true }
 *   2. tenant ton tai + active=false -> { businessName, isActive: false } -> show error
 *   3. tenant khong ton tai -> { businessName: fallback, isActive: false } -> show error
 *   4. Firestore khong config (db=null) -> graceful degradation, dung fallback
 *   5. Network error -> graceful degradation, khong block UX
 */

import { useState, useEffect } from 'react'
import { doc, getDoc } from 'firebase/firestore'
import { db } from '../firebase.js'

/**
 * Suy ra display name tu tenant_id khi Firestore khong kha dung.
 * Vi du: 'pho-ba-lan_1722500000000' -> 'Pho Ba Lan'
 */
function inferBusinessNameFromId(tenantId) {
  if (!tenantId) return 'Quan'
  const withoutTimestamp = tenantId.replace(/_\d+$/, '')
  return withoutTimestamp
    .split('-')
    .map(w => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

/**
 * useTenantInfo - doc thong tin tenant tu Firestore
 *
 * @param {string} tenantId - tu QR code param ?tenant_id=
 * @returns {{
 *   businessName: string,
 *   isActive: boolean,
 *   tenantExists: boolean,
 *   loading: boolean,
 *   error: string|null,
 * }}
 */
export function useTenantInfo(tenantId) {
  const fallbackName = inferBusinessNameFromId(tenantId)

  const [businessName, setBusinessName] = useState(fallbackName)
  const [isActive, setIsActive]         = useState(true)
  const [tenantExists, setTenantExists] = useState(true)
  const [loading, setLoading]           = useState(true)
  const [error, setError]               = useState(null)

  useEffect(() => {
    if (!tenantId) {
      setLoading(false)
      setError('Thieu ma quan (tenant_id). Vui long quet lai QR.')
      setIsActive(false)
      return
    }

    if (!db) {
      console.warn('[useTenantInfo] Firestore khong kha dung - dung fallback name tu tenant_id.')
      setBusinessName(fallbackName)
      setIsActive(true)
      setTenantExists(true)
      setLoading(false)
      return
    }

    let cancelled = false
    setLoading(true)
    setError(null)

    async function fetchTenant() {
      try {
        const tenantRef = doc(db, 'tenants', tenantId)
        const snapshot  = await getDoc(tenantRef)

        if (cancelled) return

        if (!snapshot.exists()) {
          setBusinessName(fallbackName)
          setIsActive(false)
          setTenantExists(false)
          setError('Quan nay chua duoc dang ky tren he thong Sentrix.')
          return
        }

        const data = snapshot.data()
        const name = data?.business_name || data?.businessName || fallbackName
        setBusinessName(name)

        const active = data?.active !== undefined ? Boolean(data.active) : true
        setIsActive(active)
        setTenantExists(true)

        if (!active) {
          setError('Quan nay hien chua kich hoat dich vu Sentrix. Vui long lien he chu quan.')
        }
      } catch (err) {
        if (cancelled) return
        console.error('[useTenantInfo] Loi doc tenant:', err.message)
        setBusinessName(fallbackName)
        setIsActive(true)
        setTenantExists(true)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchTenant()
    return () => { cancelled = true }
  }, [tenantId, fallbackName])

  return { businessName, isActive, tenantExists, loading, error }
}
