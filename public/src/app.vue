<template>
  <v-app>
    <!-- Navigation Drawer for Mobile -->
    <v-navigation-drawer
      v-model="drawer"
      temporary
      app
      width="280"
    >
      <v-list>
        <v-list-item>
          <v-list-item-title class="text-h6 text-primary">
            <v-icon class="me-2">mdi-heart-pulse</v-icon>
            Afya Medical EHR
          </v-list-item-title>
        </v-list-item>
      </v-list>

      <v-divider></v-divider>

      <v-list nav>
        <v-list-item
          v-for="item in navigationItems"
          :key="item.title"
          :to="item.to"
          exact
        >
          <template v-slot:prepend>
            <v-icon>{{ item.icon }}</v-icon>
          </template>
          <v-list-item-title>{{ item.title }}</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <!-- App Bar -->
    <v-app-bar
      app
      color="white"
      elevation="1"
      height="70"
    >
      <v-app-bar-nav-icon
        @click="drawer = !drawer"
        class="d-lg-none"
      ></v-app-bar-nav-icon>

      <v-app-bar-title class="text-h6 font-weight-bold text-primary">
        <v-icon class="me-2">mdi-heart-pulse</v-icon>
        Afya Medical EHR
      </v-app-bar-title>

      <v-spacer></v-spacer>

      <!-- USSD Code Display -->
      <v-chip
        color="primary"
        variant="outlined"
        class="me-4 d-none d-sm-flex"
        @click="copyUssdCode"
      >
        <v-icon start>mdi-phone</v-icon>
        *384*15897#
      </v-chip>

      <!-- System Status -->
      <v-chip
        :color="systemStatus.color"
        size="small"
        class="me-2"
      >
        <v-icon start size="small">mdi-circle</v-icon>
        {{ systemStatus.text }}
      </v-chip>

      <!-- Desktop Navigation -->
      <v-btn-group class="d-none d-lg-flex">
        <v-btn
          v-for="item in navigationItems"
          :key="item.title"
          :to="item.to"
          variant="text"
          exact
        >
          <v-icon start>{{ item.icon }}</v-icon>
          {{ item.title }}
        </v-btn>
      </v-btn-group>
    </v-app-bar>

    <!-- Main Content -->
    <v-main>
      <v-container fluid>
        <!-- Loading Overlay -->
        <v-overlay
          v-model="loading"
          class="align-center justify-center"
          persistent
        >
          <v-progress-circular
            color="primary"
            indeterminate
            size="64"
          ></v-progress-circular>
        </v-overlay>

        <!-- Alert Messages -->
        <v-alert
          v-if="alert.show"
          :type="alert.type"
          :title="alert.title"
          :text="alert.message"
          closable
          class="mb-4"
          @click:close="closeAlert"
        ></v-alert>

        <!-- Router View -->
        <router-view @loading="setLoading" @alert="showAlert" />
      </v-container>
    </v-main>

    <!-- Footer -->
    <v-footer app class="text-center">
      <v-row no-gutters>
        <v-col cols="12">
          <div class="text-body-2">
            <strong>Afya Medical EHR</strong> - Transforming Healthcare in Ghana
          </div>
          <div class="text-caption text-medium-emphasis">
            © 2025 Afya Medical Systems. Built with ❤️ for better healthcare access.
          </div>
        </v-col>
      </v-row>
    </v-footer>

    <!-- USSD Code Snackbar -->
    <v-snackbar
      v-model="ussdCopied"
      timeout="2000"
      color="success"
    >
      USSD Code copied to clipboard!
      <template v-slot:actions>
        <v-btn
          color="white"
          variant="text"
          @click="ussdCopied = false"
        >
          Close
        </v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiService from '@/services/apiService'

export default {
  name: 'App',
  setup() {
    const router = useRouter()
    const drawer = ref(false)
    const loading = ref(false)
    const ussdCopied = ref(false)
    
    const alert = reactive({
      show: false,
      type: 'info',
      title: '',
      message: ''
    })

    const systemStatus = reactive({
      color: 'success',
      text: 'Online'
    })

    const navigationItems = [
      {
        title: 'Dashboard',
        icon: 'mdi-view-dashboard',
        to: '/'
      },
      {
        title: 'Patients',
        icon: 'mdi-account-group',
        to: '/patients'
      },
      {
        title: 'Providers',
        icon: 'mdi-doctor',
        to: '/providers'
      },
      {
        title: 'Facilities',
        icon: 'mdi-hospital-building',
        to: '/facilities'
      },
      {
        title: 'USSD Test',
        icon: 'mdi-cellphone',
        to: '/ussd-test'
      },
      {
        title: 'System Logs',
        icon: 'mdi-text-box-search',
        to: '/logs'
      }
    ]

    const copyUssdCode = async () => {
      try {
        await navigator.clipboard.writeText('*384*15897#')
        ussdCopied.value = true
      } catch (error) {
        console.error('Failed to copy USSD code:', error)
      }
    }

    const setLoading = (isLoading) => {
      loading.value = isLoading
    }

    const showAlert = (alertData) => {
      alert.show = true
      alert.type = alertData.type || 'info'
      alert.title = alertData.title || ''
      alert.message = alertData.message || ''
    }

    const closeAlert = () => {
      alert.show = false
    }

    const checkSystemHealth = async () => {
      try {
        const health = await apiService.getHealth()
        if (health.status === 'healthy') {
          systemStatus.color = 'success'
          systemStatus.text = 'Online'
        } else {
          systemStatus.color = 'warning'
          systemStatus.text = 'Issues'
        }
      } catch (error) {
        systemStatus.color = 'error'
        systemStatus.text = 'Offline'
      }
    }

    onMounted(() => {
      checkSystemHealth()
      // Check system health every 30 seconds
      setInterval(checkSystemHealth, 30000)
    })

    return {
      drawer,
      loading,
      ussdCopied,
      alert,
      systemStatus,
      navigationItems,
      copyUssdCode,
      setLoading,
      showAlert,
      closeAlert
    }
  }
}
</script>

<style scoped>
.v-app-bar-title {
  cursor: pointer;
}

.v-chip {
  cursor: pointer;
}

.v-btn-group .v-btn {
  text-transform: none;
}
</style>