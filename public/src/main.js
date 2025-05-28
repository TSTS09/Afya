import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { mdi } from 'vuetify/iconsets/mdi'
import '@mdi/font/css/materialdesignicons.css'

// Custom theme for Afya Medical EHR
const afyaTheme = {
  dark: false,
  colors: {
    primary: '#2E8B57',      // Sea Green - Healthcare/nature theme
    secondary: '#20B2AA',    // Light Sea Green
    accent: '#FFD700',       // Gold
    error: '#F44336',        // Red
    warning: '#FF9800',      // Orange
    info: '#2196F3',         // Blue
    success: '#4CAF50',      // Green
    surface: '#FFFFFF',      // White
    'on-surface': '#000000', // Black
    background: '#F8F9FA'    // Light grey
  }
}

const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
    sets: {
      mdi
    }
  },
  theme: {
    defaultTheme: 'afyaTheme',
    themes: {
      afyaTheme
    }
  },
  defaults: {
    VBtn: {
      variant: 'flat',
      style: 'text-transform: none;'
    },
    VCard: {
      elevation: 2
    },
    VSheet: {
      elevation: 1
    }
  }
})

const app = createApp(App)

// Global error handler
app.config.errorHandler = (error, instance, info) => {
  console.error('Global error:', error)
  console.error('Component instance:', instance)
  console.error('Error info:', info)
  
  // You can send errors to a logging service here
  // For example: LoggingService.logError(error, instance, info)
}

// Global properties
app.config.globalProperties.$formatPhone = (phone) => {
  if (!phone) return ''
  
  // Ghana phone format: 0XX XXX XXXX
  if (phone.length === 10 && phone.startsWith('0')) {
    return `${phone.substring(0, 3)} ${phone.substring(3, 6)} ${phone.substring(6)}`
  }
  
  return phone
}

app.config.globalProperties.$formatDate = (dateString) => {
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (error) {
    return dateString
  }
}

app.config.globalProperties.$copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (error) {
    console.error('Failed to copy to clipboard:', error)
    return false
  }
}

// Use plugins
app.use(router)
app.use(vuetify)

// Mount the app
app.mount('#app')

// Service Worker registration for PWA capabilities (optional)
if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('SW registered: ', registration)
      })
      .catch((registrationError) => {
        console.log('SW registration failed: ', registrationError)
      })
  })
}

// Global keyboard shortcuts
document.addEventListener('keydown', (event) => {
  // Ctrl/Cmd + K for search (future feature)
  if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
    event.preventDefault()
    console.log('Search shortcut triggered')
    // Implement global search functionality
  }
  
  // Ctrl/Cmd + H for home/dashboard
  if ((event.ctrlKey || event.metaKey) && event.key === 'h') {
    event.preventDefault()
    router.push('/')
  }
  
  // Ctrl/Cmd + T for USSD test
  if ((event.ctrlKey || event.metaKey) && event.key === 't') {
    event.preventDefault()
    router.push('/ussd-test')
  }
})

// Performance monitoring
if (process.env.NODE_ENV === 'development') {
  // Log performance metrics in development
  window.addEventListener('load', () => {
    setTimeout(() => {
      const perfData = performance.getEntriesByType('navigation')[0]
      console.log('Page load performance:', {
        domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
        loadComplete: perfData.loadEventEnd - perfData.loadEventStart,
        totalTime: perfData.loadEventEnd - perfData.fetchStart
      })
    }, 0)
  })
}

export default app