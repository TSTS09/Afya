<template>
  <div>
    <!-- Hero Section -->
    <v-card class="mb-6 hero-card" elevation="2">
      <v-card-text class="text-center pa-8">
        <div class="text-h3 font-weight-bold text-primary mb-4">
          <v-icon size="large" class="me-3">mdi-heart-pulse</v-icon>
          Welcome to Afya Medical EHR
        </div>
        <div class="text-h6 text-medium-emphasis mb-6">
          Transforming Healthcare Records in Ghana - One Phone at a Time
        </div>
        
        <v-card class="mx-auto" max-width="400" color="grey-darken-4">
          <v-card-text class="text-center py-6">
            <div class="text-h6 text-white mb-3">USSD Access Code</div>
            <div class="ussd-code text-h4 text-amber" @click="copyUssdCode">
              *714#
            </div>
            <div class="text-caption text-grey-lighten-2 mt-3">
              Dial from any mobile phone - No internet required
            </div>
          </v-card-text>
        </v-card>
      </v-card-text>
    </v-card>

    <!-- Statistics Cards -->
    <v-row class="mb-6">
      <v-col v-for="stat in statistics" :key="stat.title" cols="12" sm="6" md="3">
        <v-card class="stat-card h-100" :color="stat.color" dark>
          <v-card-text class="text-center pa-6">
            <v-icon size="60" class="mb-4">{{ stat.icon }}</v-icon>
            <div class="text-h3 font-weight-bold mb-2">{{ stat.value }}</div>
            <div class="text-h6">{{ stat.title }}</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Key Features -->
    <v-card class="mb-6" elevation="2">
      <v-card-title>
        <v-icon class="me-2 text-amber">mdi-star</v-icon>
        Key Features
      </v-card-title>
      <v-card-text>
        <v-row>
          <v-col v-for="feature in features" :key="feature.title" cols="12" md="4">
            <v-card class="feature-card h-100" elevation="1">
              <v-card-text class="text-center pa-6">
                <div class="feature-icon mx-auto mb-4">
                  <v-icon size="40" color="white">{{ feature.icon }}</v-icon>
                </div>
                <div class="text-h6 mb-3">{{ feature.title }}</div>
                <div class="text-body-2 text-medium-emphasis">{{ feature.description }}</div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Main Content Row -->
    <v-row>
      <!-- Recent Medical Records -->
      <v-col cols="12" lg="8">
        <v-card elevation="2">
          <v-card-title>
            <v-icon class="me-2 text-primary">mdi-clock-outline</v-icon>
            Recent Medical Records
          </v-card-title>
          <v-card-text>
            <v-data-table
              v-if="recentRecords.length > 0"
              :headers="recordHeaders"
              :items="recentRecords"
              :items-per-page="5"
              class="elevation-1"
            >
              <template v-slot:item.visit_date="{ item }">
                <v-chip size="small" color="grey">{{ item.visit_date }}</v-chip>
              </template>
              
              <template v-slot:item.patient="{ item }">
                <div>
                  <div class="font-weight-bold">{{ item.patient?.name || 'Unknown' }}</div>
                  <div class="text-caption text-medium-emphasis">{{ item.patient?.phone || 'N/A' }}</div>
                </div>
              </template>
              
              <template v-slot:item.diagnosis="{ item }">
                <div class="text-truncate" style="max-width: 200px;">
                  {{ item.diagnosis || 'Not specified' }}
                </div>
              </template>
            </v-data-table>

            <div v-else class="text-center py-12">
              <v-icon size="80" color="grey-lighten-2" class="mb-4">mdi-file-document-outline</v-icon>
              <div class="text-h6 text-medium-emphasis mb-2">No medical records yet</div>
              <div class="text-body-2 text-medium-emphasis mb-4">
                Records will appear here as healthcare providers create them
              </div>
              <v-btn color="primary" variant="outlined" class="me-2" @click="$router.push('/ussd-test')">
                <v-icon start>mdi-cellphone</v-icon>
                Test USSD
              </v-btn>
              <v-btn color="secondary" variant="outlined" @click="$router.push('/logs')">
                <v-icon start>mdi-text-box-search</v-icon>
                View System Logs
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Quick Actions & System Status -->
      <v-col cols="12" lg="4">
        <!-- Quick Actions -->
        <v-card class="mb-4" elevation="2">
          <v-card-title>
            <v-icon class="me-2 text-warning">mdi-lightning-bolt</v-icon>
            Quick Actions
          </v-card-title>
          <v-card-text>
            <div class="d-flex flex-column ga-2">
              <v-btn 
                v-for="action in quickActions" 
                :key="action.title"
                :color="action.color"
                variant="outlined"
                block
                @click="$router.push(action.to)"
              >
                <v-icon start>{{ action.icon }}</v-icon>
                {{ action.title }}
              </v-btn>
            </div>
          </v-card-text>
        </v-card>

        <!-- System Status -->
        <v-card elevation="2">
          <v-card-title>
            <v-icon class="me-2 text-success">mdi-heart-pulse</v-icon>
            System Status
          </v-card-title>
          <v-card-text>
            <div v-for="status in systemStatuses" :key="status.name" class="d-flex justify-space-between align-center mb-3">
              <span>{{ status.name }}</span>
              <v-chip :color="status.color" size="small">
                <v-icon start size="small">mdi-check-circle</v-icon>
                {{ status.status }}
              </v-chip>
            </div>
            <v-divider class="my-4"></v-divider>
            <div class="text-center">
              <v-btn color="primary" variant="outlined" size="small" @click="checkSystemHealth">
                <v-icon start>mdi-chart-line</v-icon>
                Detailed Status
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Usage Instructions -->
    <v-card class="mt-6" elevation="2">
      <v-card-title>
        <v-icon class="me-2 text-info">mdi-help-circle</v-icon>
        How to Use Afya Medical EHR
      </v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="6">
            <div class="text-h6 mb-3">
              <v-icon class="me-2 text-primary">mdi-doctor</v-icon>
              For Healthcare Providers:
            </div>
            <v-timeline density="compact">
              <v-timeline-item dot-color="primary" size="small">
                <strong>Register your facility and get provider credentials</strong>
              </v-timeline-item>
              <v-timeline-item dot-color="primary" size="small">
                <strong>Dial *714#</strong> from any mobile phone
              </v-timeline-item>
              <v-timeline-item dot-color="primary" size="small">
                <strong>Select "Healthcare Provider"</strong> and enter your PIN
              </v-timeline-item>
              <v-timeline-item dot-color="primary" size="small">
                <strong>Register patients, create records, view histories</strong>
              </v-timeline-item>
            </v-timeline>
          </v-col>
          
          <v-col cols="12" md="6">
            <div class="text-h6 mb-3">
              <v-icon class="me-2 text-success">mdi-account</v-icon>
              For Patients:
            </div>
            <v-timeline density="compact">
              <v-timeline-item dot-color="success" size="small">
                <strong>Get registered at any participating healthcare facility</strong>
              </v-timeline-item>
              <v-timeline-item dot-color="success" size="small">
                <strong>Dial *714#</strong> from your registered phone
              </v-timeline-item>
              <v-timeline-item dot-color="success" size="small">
                <strong>Select "Patient Services"</strong> to view your records
              </v-timeline-item>
              <v-timeline-item dot-color="success" size="small">
                <strong>Access your health information</strong> from anywhere in Ghana
              </v-timeline-item>
            </v-timeline>
          </v-col>
        </v-row>

        <!-- Demo Information -->
        <v-alert type="info" variant="tonal" class="mt-6">
          <template v-slot:title>
            <v-icon>mdi-information</v-icon>
            Demo Information
          </template>
          
          <v-row class="mt-2">
            <v-col cols="12" md="6">
              <strong>Demo Provider PINs:</strong>
              <ul class="mt-2">
                <li><code>1234</code> - Dr. Kwame Asante (General Medicine)</li>
                <li><code>5678</code> - Dr. Ama Mensah (Pediatrics)</li>
                <li><code>9012</code> - Dr. Kofi Boateng (Internal Medicine)</li>
              </ul>
            </v-col>
            <v-col cols="12" md="6">
              <strong>Test Phone Numbers:</strong>
              <ul class="mt-2">
                <li><code>0200123456</code> - John Doe</li>
                <li><code>0240234567</code> - Jane Smith</li>
                <li><code>0260345678</code> - Kwame Osei</li>
                <li><code>0270456789</code> - Akosua Addo</li>
              </ul>
            </v-col>
          </v-row>
        </v-alert>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import apiService from '@/services/apiService'

export default {
  name: 'Dashboard',
  emits: ['loading', 'alert'],
  setup(props, { emit }) {
    const statistics = ref([
      { title: 'Healthcare Providers', value: 0, icon: 'mdi-doctor', color: 'primary' },
      { title: 'Healthcare Facilities', value: 0, icon: 'mdi-hospital-building', color: 'secondary' },
      { title: 'Total Patients', value: 0, icon: 'mdi-account-group', color: 'success' },
      { title: 'Recent Records', value: 0, icon: 'mdi-file-document', color: 'info' }
    ])

    const recentRecords = ref([])

    const features = [
      {
        title: 'USSD Access',
        icon: 'mdi-cellphone',
        description: 'Works on any mobile phone - from basic feature phones to smartphones. No internet connection required.'
      },
      {
        title: 'Secure & Private',
        icon: 'mdi-shield-check',
        description: 'End-to-end encryption, role-based access controls, and HIPAA-compliant data protection.'
      },
      {
        title: 'Nationwide Access',
        icon: 'mdi-earth',
        description: 'Patient records accessible from any healthcare facility across Ghana - rural or urban.'
      }
    ]

    const quickActions = [
      { title: 'Register Facility', icon: 'mdi-hospital-building', color: 'primary', to: '/facilities/register' },
      { title: 'Register Provider', icon: 'mdi-doctor', color: 'success', to: '/providers/register' },
      { title: 'View Patients', icon: 'mdi-magnify', color: 'info', to: '/patients' },
      { title: 'Test USSD', icon: 'mdi-cellphone', color: 'warning', to: '/ussd-test' },
      { title: 'All Providers', icon: 'mdi-doctor', color: 'secondary', to: '/providers' },
      { title: 'All Facilities', icon: 'mdi-hospital-building', color: 'grey', to: '/facilities' }
    ]

    const systemStatuses = ref([
      { name: 'USSD Gateway', status: 'Online', color: 'success' },
      { name: 'Database', status: 'Connected', color: 'success' },
      { name: 'SMS Service', status: 'Active', color: 'success' },
      { name: 'Web Interface', status: 'Operational', color: 'success' }
    ])

    const recordHeaders = [
      { title: 'Date', key: 'visit_date' },
      { title: 'Patient', key: 'patient' },
      { title: 'Provider', key: 'provider.name' },
      { title: 'Facility', key: 'facility.name' },
      { title: 'Diagnosis', key: 'diagnosis' }
    ]

    const copyUssdCode = async () => {
      try {
        await navigator.clipboard.writeText('*714#')
        emit('alert', {
          type: 'success',
          title: 'Success',
          message: 'USSD Code copied to clipboard!'
        })
      } catch (error) {
        emit('alert', {
          type: 'error',
          title: 'Error',
          message: 'Failed to copy USSD code'
        })
      }
    }

    const loadDashboardData = async () => {
      try {
        emit('loading', true)
        const data = await apiService.getDashboardStats()
        
        // Update statistics
        statistics.value[0].value = data.total_providers
        statistics.value[1].value = data.total_facilities
        statistics.value[2].value = data.total_patients
        statistics.value[3].value = data.recent_records?.length || 0

        // Update recent records
        recentRecords.value = data.recent_records || []

      } catch (error) {
        console.error('Failed to load dashboard data:', error)
        emit('alert', {
          type: 'error',
          title: 'Error',
          message: 'Failed to load dashboard data'
        })
      } finally {
        emit('loading', false)
      }
    }

    const checkSystemHealth = async () => {
      try {
        const health = await apiService.getHealth()
        
        if (health.status === 'healthy') {
          systemStatuses.value.forEach(status => {
            status.status = 'Online'
            status.color = 'success'
          })
        } else {
          systemStatuses.value.forEach(status => {
            status.status = 'Issues'
            status.color = 'warning'
          })
        }
        
        emit('alert', {
          type: 'success',
          title: 'System Health',
          message: `System is ${health.status}`
        })
      } catch (error) {
        systemStatuses.value.forEach(status => {
          status.status = 'Offline'
          status.color = 'error'
        })
        
        emit('alert', {
          type: 'error',
          title: 'System Health',
          message: 'Failed to check system health'
        })
      }
    }

    onMounted(() => {
      loadDashboardData()
    })

    return {
      statistics,
      recentRecords,
      features,
      quickActions,
      systemStatuses,
      recordHeaders,
      copyUssdCode,
      checkSystemHealth,
      loadDashboardData
    }
  }
}
</script>

<style scoped>
.hero-card {
  background: linear-gradient(135deg, rgba(25, 118, 210, 0.1), rgba(156, 39, 176, 0.1));
}

.ussd-code {
  font-family: 'Roboto Mono', monospace;
  cursor: pointer;
  transition: all 0.3s ease;
}

.ussd-code:hover {
  transform: scale(1.05);
}

.stat-card {
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.feature-card {
  transition: transform 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-2px);
}

.feature-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #1976d2, #9c27b0);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>