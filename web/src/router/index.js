import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: {
      title: 'Dashboard - Afya Medical EHR'
    }
  },
  {
    path: '/patients',
    name: 'Patients',
    component: () => import('@/views/Patients.vue'),
    meta: {
      title: 'Patients - Afya Medical EHR'
    }
  },
  {
    path: '/providers',
    name: 'Providers',
    component: () => import('@/views/Providers.vue'),
    meta: {
      title: 'Healthcare Providers - Afya Medical EHR'
    }
  },
  {
    path: '/providers/register',
    name: 'RegisterProvider',
    component: () => import('@/views/RegisterProvider.vue'),
    meta: {
      title: 'Register Provider - Afya Medical EHR'
    }
  },
  {
    path: '/facilities',
    name: 'Facilities',
    component: () => import('@/views/Facilities.vue'),
    meta: {
      title: 'Healthcare Facilities - Afya Medical EHR'
    }
  },
  {
    path: '/facilities/register',
    name: 'RegisterFacility',
    component: () => import('@/views/RegisterFacility.vue'),
    meta: {
      title: 'Register Facility - Afya Medical EHR'
    }
  },
  {
    path: '/ussd-test',
    name: 'UssdTest',
    component: () => import('@/views/UssdTest.vue'),
    meta: {
      title: 'USSD Test - Afya Medical EHR'
    }
  },
  {
    path: '/logs',
    name: 'SystemLogs',
    component: () => import('@/views/SystemLogs.vue'),
    meta: {
      title: 'System Logs - Afya Medical EHR'
    }
  },
  {
    path: '/health',
    name: 'SystemHealth',
    component: () => import('@/views/SystemHealth.vue'),
    meta: {
      title: 'System Health - Afya Medical EHR'
    }
  },
  {
    path: '/patients/:id',
    name: 'PatientDetails',
    component: () => import('@/views/PatientDetails.vue'),
    meta: {
      title: 'Patient Details - Afya Medical EHR'
    }
  },
  {
    path: '/providers/:id',
    name: 'ProviderDetails',
    component: () => import('@/views/ProviderDetails.vue'),
    meta: {
      title: 'Provider Details - Afya Medical EHR'
    }
  },
  {
    path: '/facilities/:id',
    name: 'FacilityDetails',
    component: () => import('@/views/FacilityDetails.vue'),
    meta: {
      title: 'Facility Details - Afya Medical EHR'
    }
  },
  {
    path: '/records/:id',
    name: 'RecordDetails',
    component: () => import('@/views/RecordDetails.vue'),
    meta: {
      title: 'Medical Record - Afya Medical EHR'
    }
  },
  // Catch-all route for 404 errors
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: {
      title: '404 - Page Not Found'
    }
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // Always scroll to top when navigating to a new route
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// Navigation guards
router.beforeEach((to, from, next) => {
  // Update document title
  if (to.meta.title) {
    document.title = to.meta.title
  } else {
    document.title = 'Afya Medical EHR'
  }

  // Add any authentication logic here if needed in the future
  // For now, all routes are public
  next()
})

router.afterEach((to, from) => {
  // Log route changes for analytics/debugging
  console.log(`Navigated from ${from.path} to ${to.path}`)
})

export default router