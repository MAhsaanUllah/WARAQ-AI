import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ClerkProvider } from '@clerk/clerk-react'
import './index.css'
import App from './App.jsx'

// Import your publishable key
const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

import { dark } from '@clerk/themes'

const isDummyKey = !PUBLISHABLE_KEY || PUBLISHABLE_KEY.includes('xxxxxxxxxxxxxxxx');

if (isDummyKey) {
  createRoot(document.getElementById('root')).render(
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', padding: '2rem', textAlign: 'center', color: 'white', background: '#111' }}>
      <h1>Action Required</h1>
      <p style={{ maxWidth: '500px', margin: '1rem 0' }}>
        The application is missing a valid <b>Clerk Publishable Key</b>.
      </p>
      <p style={{ maxWidth: '500px', margin: '0' }}>
        Please open <code>frontend/.env</code> and replace the placeholder with your actual <code>pk_test_...</code> key from the Clerk dashboard.
      </p>
    </div>
  )
} else {
  createRoot(document.getElementById('root')).render(
    <StrictMode>
      <ClerkProvider 
        publishableKey={PUBLISHABLE_KEY} 
        afterSignOutUrl="/"
        appearance={{
          baseTheme: dark,
          variables: { colorPrimary: '#9CD67D' }
        }}
      >
        <App />
      </ClerkProvider>
    </StrictMode>,
  )
}
