/**
 * useConsent.js — Hook quản lý trạng thái đồng ý xử lý dữ liệu cá nhân
 * =========================================================================
 * Module 2 — Tuân thủ Nghị định 356/2025/NĐ-CP
 *
 * CĂN CỨ PHÁP LÝ:
 *   Điều 6.3 NĐ 356/2025/NĐ-CP — cấm thiết lập mặc định đồng ý hoặc chỉ
 *   dẫn không rõ ràng → consent phải là hành động CHỦ ĐỘNG của người dùng.
 *
 *   Điều 6.2 NĐ 356/2025/NĐ-CP — bên kiểm soát dữ liệu phải lưu giữ bằng
 *   chứng đồng ý. Hook này lưu local (localStorage) làm bản sao phía client;
 *   bản gốc pháp lý được gửi và lưu trên Firestore qua POST /consent/record.
 *
 * CHIẾN LƯỢC STORAGE:
 *   - Key localStorage: `sentrix_consent_v1` (theo schema bên dưới)
 *   - Expire sau CONSENT_TTL_DAYS ngày (mặc định 30) kể từ consent_given_at.
 *   - Khi consent_version thay đổi → tự động invalidate → hiện lại màn hình.
 *   - Không lưu theo SĐT hash để đơn giản hoá (SĐT có thể thay đổi).
 *
 * SCHEMA localStorage:
 *   {
 *     "consent_version":  "v1.0-356-2025",
 *     "consent_given_at": "2026-08-26T09:00:00.000Z",  // ISO 8601 UTC
 *     "tenant_id":        "pho-ba-lan_1722500000000",
 *     "anonymous":        false
 *   }
 */

import { useState, useEffect, useCallback } from 'react'
import { recordConsent } from '../api/consent.js'

// ---------------------------------------------------------------------------
// Hằng số cấu hình
// ---------------------------------------------------------------------------

/** Phiên bản điều khoản hiện tại — phải khớp với CURRENT_CONSENT_VERSION ở backend */
export const CONSENT_VERSION = 'v1.0-356-2025'

/** Số ngày consent còn hiệu lực kể từ khi đồng ý */
const CONSENT_TTL_DAYS = 30

/** Key trong localStorage */
const STORAGE_KEY = 'sentrix_consent_v1'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Đọc consent record từ localStorage.
 * @returns {Object|null} parsed record hoặc null nếu không có / đã expire
 */
function readConsentFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null

    const parsed = JSON.parse(raw)

    // Kiểm tra version — nếu điều khoản đổi → invalidate ngay
    if (parsed.consent_version !== CONSENT_VERSION) {
      localStorage.removeItem(STORAGE_KEY)
      return null
    }

    // Kiểm tra TTL
    const givenAt = new Date(parsed.consent_given_at)
    const expireAt = new Date(givenAt.getTime() + CONSENT_TTL_DAYS * 86400 * 1000)
    if (Date.now() > expireAt.getTime()) {
      localStorage.removeItem(STORAGE_KEY)
      return null
    }

    return parsed
  } catch {
    return null
  }
}

/**
 * Lưu consent vào localStorage.
 */
function writeConsentToStorage({ tenantId, anonymous }) {
  const record = {
    consent_version:  CONSENT_VERSION,
    consent_given_at: new Date().toISOString(),
    tenant_id:        tenantId,
    anonymous:        anonymous,
  }
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(record))
  } catch {
    // localStorage không khả dụng (private browsing trên một số trình duyệt)
    // → không block UX, chỉ mất local cache
    console.warn('[Sentrix] Không ghi được localStorage — consent chỉ lưu server.')
  }
  return record
}

/**
 * Tính SHA-256 của SĐT bằng Web Crypto API (built-in trình duyệt, không cần thư viện).
 * Dùng để gửi phone_hash lên consent/record mà không lộ SĐT thô.
 *
 * @param {string} phone  — SĐT thô (sẽ normalize trước khi hash)
 * @returns {Promise<string>} hex string SHA-256
 */
export async function hashPhoneForConsent(phone) {
  // Normalize về dạng +84...
  let p = phone.trim().replace(/[\s-]/g, '')
  if (p.startsWith('0')) p = '+84' + p.slice(1)
  else if (!p.startsWith('+')) p = '+84' + p

  const encoder = new TextEncoder()
  const data = encoder.encode(p)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}

// ---------------------------------------------------------------------------
// Hook chính
// ---------------------------------------------------------------------------

/**
 * useConsent — Hook cho phép component kiểm tra và cập nhật trạng thái consent.
 *
 * @param {string} tenantId — ID tenant (từ QR code), dùng để lưu consent theo tenant
 *
 * @returns {{
 *   hasConsented: boolean,      — true nếu đã có consent hợp lệ trong TTL
 *   consentRecord: Object|null, — raw record từ localStorage (hoặc null)
 *   giveConsent: Function,      — gọi khi user bấm "Đồng ý" (async)
 *   revokeConsent: Function,    — xóa consent (nếu user muốn đổi ý)
 *   isLoading: boolean,         — đang gọi POST /consent/record
 *   error: string|null,         — lỗi nếu gọi server fail
 * }}
 */
export function useConsent(tenantId) {
  const [consentRecord, setConsentRecord] = useState(() => readConsentFromStorage())
  const [isLoading, setIsLoading]         = useState(false)
  const [error, setError]                 = useState(null)

  // Tự động re-check khi tenantId thay đổi (navigate sang tenant khác)
  useEffect(() => {
    setConsentRecord(readConsentFromStorage())
    setError(null)
  }, [tenantId])

  const hasConsented = consentRecord !== null

  /**
   * Ghi nhận đồng ý: lưu localStorage + gọi POST /consent/record lên backend.
   *
   * @param {Object} opts
   * @param {boolean} opts.anonymous — true nếu user chọn ẩn danh
   * @param {string|null} opts.phone — SĐT thô nếu có (sẽ hash trước khi gửi)
   */
  const giveConsent = useCallback(async ({ anonymous = false, phone = null } = {}) => {
    setIsLoading(true)
    setError(null)

    // 1. Lưu localStorage ngay (không chờ server)
    const localRecord = writeConsentToStorage({ tenantId, anonymous })
    setConsentRecord(localRecord)

    // 2. Hash SĐT nếu có (để gửi lên server làm bằng chứng — không gửi thô)
    let phoneHash = null
    if (phone && !anonymous) {
      try {
        phoneHash = await hashPhoneForConsent(phone)
      } catch {
        phoneHash = null  // Không block nếu Web Crypto lỗi
      }
    }

    // 3. Gửi lên server (async, không block UX nếu fail)
    try {
      await recordConsent({
        tenantId,
        consentVersion:  CONSENT_VERSION,
        consentGivenAt:  localRecord.consent_given_at,
        phoneHash,
        anonymous,
      })
    } catch (err) {
      // Server fail → chỉ log, KHÔNG xóa localStorage consent
      // Lý do: UX ưu tiên — consent đã có ở local, server có thể retry sau.
      console.error('[Sentrix][PDPA] Không lưu được consent record lên server:', err.message)
      setError('Lưu bằng chứng đồng ý tạm thời thất bại — phản hồi của bạn vẫn được ghi nhận.')
    } finally {
      setIsLoading(false)
    }
  }, [tenantId])

  /**
   * Xóa consent (dùng khi user muốn thu hồi hoặc test).
   * Trong thực tế, "rút đồng ý" cần gửi yêu cầu xóa dữ liệu lên backend.
   */
  const revokeConsent = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY)
    setConsentRecord(null)
  }, [])

  return {
    hasConsented,
    consentRecord,
    giveConsent,
    revokeConsent,
    isLoading,
    error,
  }
}
