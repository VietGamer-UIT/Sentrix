/**
 * firebase.js — Firebase SDK cho Web Client
 *
 * Web Client cần Firestore để update feedback document với
 * thông tin spin (phone_masked + voucher_code) sau khi user quay xong.
 *
 * Dùng cùng project Firebase với Dashboard (sentrix-demo-164).
 * Cùng biến VITE_FIREBASE_* từ .env.
 *
 * Export:
 *   db — Firestore instance (dùng cho updateFeedbackWithSpin)
 */

import { initializeApp, getApps } from 'firebase/app'
import { getFirestore } from 'firebase/firestore'

// Guard: chỉ khởi tạo nếu có env vars — không crash nếu thiếu
const hasConfig = import.meta.env.VITE_FIREBASE_API_KEY &&
                  import.meta.env.VITE_FIREBASE_PROJECT_ID

let db = null

if (hasConfig) {
  const firebaseConfig = {
    apiKey:            import.meta.env.VITE_FIREBASE_API_KEY            || '',
    authDomain:        import.meta.env.VITE_FIREBASE_AUTH_DOMAIN        || '',
    projectId:         import.meta.env.VITE_FIREBASE_PROJECT_ID         || '',
    storageBucket:     import.meta.env.VITE_FIREBASE_STORAGE_BUCKET     || '',
    messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '',
    appId:             import.meta.env.VITE_FIREBASE_APP_ID             || '',
  }

  // Tránh khởi tạo 2 lần khi Vite HMR reload
  const app = getApps().length === 0
    ? initializeApp(firebaseConfig, 'web-client')
    : getApps().find(a => a.name === 'web-client') || getApps()[0]

  db = getFirestore(app)
} else {
  console.warn('[Sentrix web-client] Thiếu VITE_FIREBASE_* — Firestore update sẽ bị bỏ qua.')
}

export { db }
