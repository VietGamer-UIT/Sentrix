/**
 * firebase.js — Khởi tạo Firebase app dùng chung cho Dashboard
 *
 * Đọc credentials từ biến VITE_FIREBASE_* trong .env
 * Giai đoạn 6: Kết nối Firestore thật (VITE_USE_MOCK_FIRESTORE=false)
 *
 * Export:
 *   app       — Firebase App instance
 *   db        — Firestore instance (dùng cho mọi query)
 *   auth      — Firebase Auth instance (Google Sign-In cho demo)
 */

import { initializeApp } from 'firebase/app'
import { getFirestore } from 'firebase/firestore'
import { getAuth, GoogleAuthProvider } from 'firebase/auth'

// ─── Env guard: crash sớm với thông báo rõ ràng thay vì lỗi ngầm ───────────
const REQUIRED_VARS = [
  'VITE_FIREBASE_API_KEY',
  'VITE_FIREBASE_AUTH_DOMAIN',
  'VITE_FIREBASE_PROJECT_ID',
  'VITE_FIREBASE_STORAGE_BUCKET',
  'VITE_FIREBASE_MESSAGING_SENDER_ID',
  'VITE_FIREBASE_APP_ID',
]

const missing = REQUIRED_VARS.filter(k => !import.meta.env[k])
if (missing.length > 0) {
  throw new Error(
    `[Sentrix] Thiếu biến môi trường Firebase:\n  ${missing.join('\n  ')}\n` +
    'Kiểm tra file .env tại apps/dashboard/.env (xem .env.example)'
  )
}
// ────────────────────────────────────────────────────────────────────────────

const firebaseConfig = {
  apiKey:            import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain:        import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId:         import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket:     import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId:             import.meta.env.VITE_FIREBASE_APP_ID,
}

// Khởi tạo một lần duy nhất
export const app  = initializeApp(firebaseConfig)
export const db   = getFirestore(app)
export const auth = getAuth(app)
export const googleProvider = new GoogleAuthProvider()
