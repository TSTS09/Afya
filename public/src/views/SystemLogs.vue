<template>
  <div>
    <!-- Page Header -->
    <v-card class="mb-6 hero-card" elevation="2">
      <v-card-text class="text-center pa-8">
        <div class="text-h3 font-weight-bold text-info mb-4">
          <v-icon size="large" class="me-3">mdi-text-box-search</v-icon>
          System Activity Logs
        </div>
        <div class="text-h6 text-medium-emphasis">
          Monitor system activities and user interactions
        </div>
      </v-card-text>
    </v-card>

    <!-- Log Statistics -->
    <v-row class="mb-6">
      <v-col v-for="stat in logStatistics" :key="stat.title" cols="12" sm="6" md="3">
        <v-card class="stat-card h-100" :color="stat.color" dark>
          <v-card-text class="text-center pa-6">
            <v-icon size="40" class="mb-3">{{ stat.icon }}</v-icon>
            <div class="text-h4 font-weight-bold mb-2">{{ stat.value }}</div>
            <div class="text-subtitle-1">{{ stat.title }}</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Filters and Actions -->
    <v-card class="mb-6" elevation="2">
      <v-card-title>
        <v-icon class="me-2 text-primary">mdi-filter</v-icon>
        Log Filters
      </v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="searchQuery"
              label="Search logs"
              placeholder="Search by action, phone, or details..."
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              clearable
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="actionFilter"
              label="Filter by action"
              :items="actionTypes"
              variant="outlined"
              density="compact"
              clearable
            ></v-select>
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="timeFilter"
              label="Time period"
              :items="timePeriods"
              variant="outlined"
              density="compact"
            ></v-select>
          </v-col>
          <v-col cols="12" md="2" class="d-flex align-center">
            <v-btn color="primary" @click="refreshLogs" :loading="loading">
              <v-icon start>mdi-refresh</v-icon>
              Refresh
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Logs Table -->
    <v-card elevation="2">
      <v-card-title class="d-flex align-center">
        <v-icon class="me-2 text-primary">mdi-clock-outline</v-icon>
        Recent Activity
        <v-spacer></v-spacer>
        <v-chip color="primary" variant="outlined">
          {{ filteredLogs.length }} Total Logs
        </v-chip>
      </v-card-title>

      <v-card-text>
        <v-data-table
          v-if="logs.length > 0"
          :headers="headers"
          :items="filteredLogs"
          :loading="loading"
          :items-per-page="25"
          class="elevation-1"
          loading-text="Loading system logs..."
        >
          <!-- Timestamp -->
          <template v-slot:item.timestamp="{ item }">
            <div class="text-caption">{{ $formatDate(item.timestamp || item.created_at) }}</div>
          </template>

          <!-- Phone Number -->
          <template v-slot:item.user_phone="{ item }">
            <v-chip
              v-if="item.user_phone"
              variant="outlined"
              density="compact"
              size="small"
            >
              {{ item.user_phone }}
            </v-chip>
            <v-chip
              v-else
              color="grey"
              size="small"
              variant="tonal"
            >
              System
            </v-chip>
          </template>

          <!-- Action -->
          <template v-slot:item.action="{ item }">
            <v-chip
              :color="getActionColor(item.action)"
              size="small"
              variant="tonal"
            >
              {{ item.action }}
            </v-chip>
          </template>

          <!-- Details -->
          <template v-slot:item.details="{ item }">
            <div class="text-truncate" style="max-width: 300px;">
              {{ item.details || '-' }}
            </div>
          </template>

          <!-- Actions -->
          <template v-slot:item.actions="{ item }">
            <v-btn
              size="small"
              variant="outlined"
              @click="viewLogDetails(item)"
              title="View Details"
            >
              <v-icon>mdi-eye</v-icon>
            </v-btn>
          </template>
        </v-data-table>

        <!-- Empty State -->
        <div v-else class="text-center py-12">
          <v-icon size="80" color="grey-lighten-2" class="mb-4">mdi-clipboard-list</v-icon>
          <div class="text-h5 text-medium-emphasis mb-2">No activity logs yet</div>
          <div class="text-body-1 text-medium-emphasis mb-6">
            Activity logs will appear here as users interact with the system.
          </div>
          
          <v-card class="mx-auto mb-6" max-width="500" variant="outlined">
            <v-card-title>To generate logs:</v-card-title>
            <v-card-text>
              <v-list density="compact">
                <v-list-item>
                  <v-list-item-title>Use the USSD test interface</v-list-item-title>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>Register providers and facilities</v-list-item-title>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>Test patient registration via USSD</v-list-item-title>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>Create medical records</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>

          <v-btn color="primary" class="me-4" @click="$router.push('/ussd-test')">
            <v-icon start>mdi-cellphone</v-icon>
            Test USSD
          </v-btn>
          <v-btn color="secondary" variant="outlined" @click="$router.push('/')">
            <v-icon start>mdi-view-dashboard</v-icon>
            Dashboard
          </v-btn>
        </div>
      </v-card-text>
    </v-card>

    <!-- Log Details Dialog -->
    <v-dialog v-model="detailsDialog" max-width="600">
      <v-card v-if="selectedLog">
        <v-card-title class="d-flex align-center">
          <v-icon class="me-2" :color="getActionColor(selectedLog.action)">mdi-information</v-icon>
          Log Details
        </v-card-title>
        
        <v-card-text>
          <v-list density="compact">
            <v-list-item>
              <template v-slot:prepend>
                <v-icon>mdi-clock</v-icon>
              </template>
              <v-list-item-title>Timestamp</v-list-item-title>
              <v-list-item-subtitle>{{ $formatDate(selectedLog.timestamp || selectedLog.created_at) }}</v-list-item-subtitle>
            </v-list-item>
            
            <v-list-item>
              <template v-slot:prepend>
                <v-icon>mdi-phone</v-icon>
              </template>
              <v-list-item-title>User Phone</v-list-item-title>
              <v-list-item-subtitle>{{ selectedLog.user_phone || 'System' }}</v-list-item-subtitle>
            </v-list-item>
            
            <v-list-item>
              <template v-slot:prepend>
                <v-icon>mdi-cog</v-icon>
              </template>
              <v-list-item-title>Action</v-list-item-title>
              <v-list-item-subtitle>
                <v-chip :color="getActionColor(selectedLog.action)" size="small" variant="tonal">
                  {{ selectedLog.action }}
                </v-chip>
              </v-list-item-subtitle>
            </v-list-item>
            
            <v-list-item v-if="selectedLog.details">
              <template v-slot:prepend>
                <v-icon>mdi-information-outline</v-icon>
              </template>
              <v-list-item-title>Details</v-list-item-title>
              <v-list-item-subtitle class="text-wrap">{{ selectedLog.details }}</v-list-item-subtitle>
            </v-list-item>
            
            <v-list-item v-if="selectedLog.id">
              <template v-slot:prepend>
                <v-icon>mdi-identifier</v-icon>
              </template>
              <v-list-item-title>Log ID</v-list-item-title>
              <v-list-item-subtitle>{{ selectedLog.id }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card-text>
        
        <v-card-actions>
          <v-btn color="primary" @click="copyLogDetails">
            <v-icon start>mdi-content-copy</v-icon>
            Copy Details
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn variant="outlined" @click="detailsDialog = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Log Information -->
    <v-card class="mt-6" elevation="2">
      <v-card-title>
        <v-icon class="me-2 text-info">mdi-information</v-icon>
        About System Logs
      </v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="6">
            <div class="text-h6 mb-3">
              <v-icon class="me-2 text-primary">mdi-list</v-icon>
              What's Logged:
            </div>
            <v-list density="compact">
              <v-list-item v-for="item in whatIsLogged" :key="item">
                <template v-slot:prepend>
                  <v-icon size="small" color="primary">mdi-check</v-icon>
                </template>
                <v-list-item-title class="text-body-2">{{ item }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-col>
          <v-col cols="12" md="6">
            <div class="text-h6 mb-3">
              <v-icon class="me-2 text-success">mdi-shield-check</v-icon>
              Privacy & Security:
            </div>
            <v-list density="compact">
              <v-list-item v-for="item in privacyFeatures" :key="item">
                <template v-slot:prepend>
                  <v-icon size="small" color="success">mdi-check</v-icon>
                </template>
                <v-list-item-title class="text-body-2">{{ item }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import apiService from '@/services/apiService'

export default {
  name: 'SystemLogs',
  emits: ['loading', 'alert'],
  setup(props, { emit }) {
    const logs = ref([])
    const loading = ref(false)
    const searchQuery = ref('')
    const actionFilter = ref('')
    const timeFilter = ref('all')
    const selectedLog = ref(null)
    const detailsDialog = ref(false)

    const actionTypes = [
      'USSD_Access',
      'Provider_Registration',
      'Facility_Registration',
      'Patient_Registration',
      'Status_Toggle',
      'PIN_Reset',
      'System_Error'
    ]

    const timePeriods = [
      { title: 'All Time', value: 'all' },
      { title: 'Last 24 Hours', value: '24h' },
      { title: 'Last 7 Days', value: '7d' },
      { title: 'Last 30 Days', value: '30d' }
    ]

    const whatIsLogged = [
      'USSD interactions and menu selections',
      'Provider and facility registrations',
      'Patient registration activities',
      'Medical record creation',
      'System errors and warnings',
      'Status changes and updates'
    ]

    const privacyFeatures = [
      'Personal medical data is not logged',
      'Only system actions are recorded',
      'Logs help with system monitoring',
      'Used for troubleshooting issues',
      'Automatic cleanup after 30 days',
      'Secure access controls'
    ]

    const headers = [
      { title: 'Timestamp', key: 'timestamp', width: '150px' },
      { title: 'Phone', key: 'user_phone', width: '120px' },
      { title: 'Action', key: 'action', width: '150px' },
      { title: 'Details', key: 'details', width: '300px' },
      { title: 'Actions', key: 'actions', width: '100px', sortable: false }
    ]

    const logStatistics = computed(() => {
      const totalLogs = logs.value.length
      const ussdLogs = logs.value.filter(log => log.action?.includes('USSD')).length
      const userActions = logs.value.filter(log => log.user_phone).length
      const systemEvents = logs.value.filter(log => !log.user_phone).length

      return [
        { title: 'Total Logs', value: totalLogs, icon: 'mdi-text-box', color: 'primary' },
        { title: 'USSD Activities', value: ussdLogs, icon: 'mdi-cellphone', color: 'info' },
        { title: 'User Actions', value: userActions, icon: 'mdi-account', color: 'success' },
        { title: 'System Events', value: systemEvents, icon: 'mdi-server', color: 'warning' }
      ]
    })

    const filteredLogs = computed(() => {
      let filtered = logs.value

      // Filter by search query
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        filtered = filtered.filter(log => 
          log.action?.toLowerCase().includes(query) ||
          log.user_phone?.includes(query) ||
          log.details?.toLowerCase().includes(query)
        )
      }

      // Filter by action type
      if (actionFilter.value) {
        filtered = filtered.filter(log => 
          log.action?.includes(actionFilter.value)
        )
      }

      // Filter by time period
      if (timeFilter.value !== 'all') {
        const now = new Date()
        const timeThresholds = {
          '24h': new Date(now.getTime() - 24 * 60 * 60 * 1000),
          '7d': new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000),
          '30d': new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
        }
        
        const threshold = timeThresholds[timeFilter.value]
        if (threshold) {
          filtered = filtered.filter(log => {
            const logDate = new Date(log.timestamp || log.created_at)
            return logDate >= threshold
          })
        }
      }

      return filtered
    })

    const getActionColor = (action) => {
      if (!action) return 'grey'
      
      if (action.includes('Error')) return 'error'
      if (action.includes('Success') || action.includes('Registration')) return 'success'
      if (action.includes('USSD')) return 'info'
      if (action.includes('Toggle') || action.includes('Reset')) return 'warning'
      return 'primary'
    }

    const loadLogs = async () => {
      try {
        emit('loading', true)
        loading.value = true
        
        const data = await apiService.getLogs(200) // Get more logs for better filtering
        logs.value = data || []
        
        if (logs.value.length === 0) {
          emit('alert', {
            type: 'info',
            title: 'No Logs',
            message: 'No system logs found. Activity will appear here as users interact with the system.'
          })
        }
      } catch (error) {
        console.error('Failed to load logs:', error)
        emit('alert', {
          type: 'error',
          title: 'Error',
          message: 'Failed to load system logs: ' + error.message
        })
      } finally {
        emit('loading', false)
        loading.value = false
      }
    }

    const refreshLogs = async () => {
      await loadLogs()
      emit('alert', {
        type: 'success',
        title: 'Refreshed',
        message: 'System logs have been refreshed'
      })
    }

    const viewLogDetails = (log) => {
      selectedLog.value = log
      detailsDialog.value = true
    }

    const copyLogDetails = async () => {
      if (!selectedLog.value) return

      const logText = `
Timestamp: ${selectedLog.value.timestamp || selectedLog.value.created_at}
User Phone: ${selectedLog.value.user_phone || 'System'}
Action: ${selectedLog.value.action}
Details: ${selectedLog.value.details || 'N/A'}
Log ID: ${selectedLog.value.id || 'N/A'}
      `.trim()

      try {
        await navigator.clipboard.writeText(logText)
        emit('alert', {
          type: 'success',
          title: 'Copied',
          message: 'Log details copied to clipboard'
        })
      } catch (error) {
        emit('alert', {
          type: 'error',
          title: 'Copy Failed',
          message: 'Failed to copy log details'
        })
      }
    }

    onMounted(() => {
      loadLogs()
    })

    return {
      logs,
      loading,
      searchQuery,
      actionFilter,
      timeFilter,
      selectedLog,
      detailsDialog,
      actionTypes,
      timePeriods,
      whatIsLogged,
      privacyFeatures,
      headers,
      logStatistics,
      filteredLogs,
      getActionColor,
      refreshLogs,
      viewLogDetails,
      copyLogDetails
    }
  }
}
</script>

<style scoped>
.hero-card {
  background: linear-gradient(135deg, rgba(33, 150, 243, 0.1), rgba(156, 39, 176, 0.1));
}

.stat-card {
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
}
</style>