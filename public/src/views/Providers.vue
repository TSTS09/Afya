<template>
  <div>
    <!-- Page Header -->
    <v-card class="mb-6 hero-card" elevation="2">
      <v-card-text class="text-center pa-8">
        <div class="text-h3 font-weight-bold text-primary mb-4">
          <v-icon size="large" class="me-3">mdi-doctor</v-icon>
          Healthcare Providers
        </div>
        <div class="text-h6 text-medium-emphasis">
          Manage healthcare providers in the Afya Medical EHR system
        </div>
      </v-card-text>
    </v-card>

    <!-- Statistics Cards -->
    <v-row class="mb-6">
      <v-col v-for="stat in statistics" :key="stat.title" cols="12" sm="6" md="3">
        <v-card class="stat-card h-100" :color="stat.color" dark>
          <v-card-text class="text-center pa-6">
            <v-icon size="40" class="mb-3">{{ stat.icon }}</v-icon>
            <div class="text-h4 font-weight-bold mb-2">{{ stat.value }}</div>
            <div class="text-subtitle-1">{{ stat.title }}</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Search and Actions -->
    <v-card class="mb-6" elevation="2">
      <v-card-title>
        <v-icon class="me-2 text-primary">mdi-account-search</v-icon>
        Provider Management
      </v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="8">
            <v-text-field
              v-model="searchQuery"
              label="Search providers"
              placeholder="Search by name, phone, or specialization..."
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              clearable
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="4" class="d-flex align-center">
            <v-btn color="primary" class="me-2" @click="refreshProviders">
              <v-icon start>mdi-refresh</v-icon>
              Refresh
            </v-btn>
            <v-btn color="success" @click="$router.push('/providers/register')">
              <v-icon start>mdi-account-plus</v-icon>
              Register Provider
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Providers Display -->
    <div v-if="providers.length > 0">
      <v-row>
        <v-col 
          v-for="provider in filteredProviders" 
          :key="provider.id" 
          cols="12" 
          lg="4" 
          md="6"
        >
          <v-card class="provider-card h-100" elevation="2">
            <!-- Provider Header -->
            <v-card-title class="provider-header">
              <v-row align="center" no-gutters>
                <v-col cols="3">
                  <v-avatar size="60" :color="provider.is_active ? 'primary' : 'grey'">
                    <v-icon size="30" color="white">mdi-doctor</v-icon>
                  </v-avatar>
                </v-col>
                <v-col cols="9">
                  <div class="text-h6 mb-1">{{ provider.name }}</div>
                  <v-chip 
                    size="small" 
                    :color="getSpecializationColor(provider.specialization)"
                    variant="tonal"
                  >
                    <v-icon start size="small">mdi-stethoscope</v-icon>
                    {{ provider.specialization || 'General' }}
                  </v-chip>
                </v-col>
              </v-row>
              
              <!-- Status Badge -->
              <v-chip 
                :color="provider.is_active ? 'success' : 'error'"
                size="small"
                class="status-chip"
              >
                <v-icon start size="small">mdi-circle</v-icon>
                {{ provider.is_active ? 'Active' : 'Inactive' }}
              </v-chip>
            </v-card-title>

            <!-- Provider Details -->
            <v-card-text>
              <v-list density="compact">
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon color="primary">mdi-phone</v-icon>
                  </template>
                  <v-list-item-title>{{ $formatPhone(provider.phone) }}</v-list-item-title>
                </v-list-item>
                
                <v-list-item v-if="provider.facility">
                  <template v-slot:prepend>
                    <v-icon color="secondary">mdi-hospital-building</v-icon>
                  </template>
                  <v-list-item-title>{{ provider.facility.name }}</v-list-item-title>
                  <v-list-item-subtitle>{{ provider.facility.location }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item v-else>
                  <template v-slot:prepend>
                    <v-icon color="grey">mdi-hospital-building</v-icon>
                  </template>
                  <v-list-item-title class="text-medium-emphasis">No Facility Assigned</v-list-item-title>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon color="info">mdi-calendar</v-icon>
                  </template>
                  <v-list-item-title>Registered</v-list-item-title>
                  <v-list-item-subtitle>{{ $formatDate(provider.registration_date) }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>

            <!-- Action Buttons -->
            <v-card-actions class="pa-4">
              <v-btn
                variant="outlined"
                block
                @click="viewProvider(provider)"
                class="mb-2"
              >
                <v-icon start>mdi-eye</v-icon>
                View Details
              </v-btn>
              
              <v-row no-gutters>
                <v-col cols="4">
                  <v-btn
                    variant="outlined"
                    size="small"
                    @click="editProvider(provider)"
                    title="Edit Provider"
                  >
                    <v-icon>mdi-pencil</v-icon>
                  </v-btn>
                </v-col>
                <v-col cols="4">
                  <v-btn
                    variant="outlined"
                    size="small"
                    color="warning"
                    @click="resetPin(provider)"
                    title="Reset PIN"
                  >
                    <v-icon>mdi-key</v-icon>
                  </v-btn>
                </v-col>
                <v-col cols="4">
                  <v-btn
                    variant="outlined"
                    size="small"
                    :color="provider.is_active ? 'error' : 'success'"
                    @click="toggleStatus(provider)"
                    :title="provider.is_active ? 'Deactivate' : 'Activate'"
                  >
                    <v-icon>{{ provider.is_active ? 'mdi-pause' : 'mdi-play' }}</v-icon>
                  </v-btn>
                </v-col>
              </v-row>
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>
    </div>

    <!-- Empty State -->
    <v-card v-else elevation="2">
      <v-card-text class="text-center py-12">
        <v-icon size="80" color="grey-lighten-2" class="mb-4">mdi-doctor</v-icon>
        <div class="text-h5 text-medium-emphasis mb-2">No healthcare providers registered yet</div>
        <div class="text-body-1 text-medium-emphasis mb-6">
          Start by registering healthcare providers to use the USSD system.
        </div>
        
        <v-card class="mx-auto mb-6" max-width="500" variant="outlined">
          <v-card-title>How to register providers:</v-card-title>
          <v-card-text>
            <v-timeline density="compact">
              <v-timeline-item dot-color="primary" size="small">
                First, <router-link to="/facilities/register">register a healthcare facility</router-link>
              </v-timeline-item>
              <v-timeline-item dot-color="primary" size="small">
                Then, <router-link to="/providers/register">register healthcare providers</router-link>
              </v-timeline-item>
              <v-timeline-item dot-color="primary" size="small">
                Providers can access the system via USSD: <strong>*384*15897#</strong>
              </v-timeline-item>
            </v-timeline>
          </v-card-text>
        </v-card>

        <v-btn color="success" size="large" class="me-4" @click="$router.push('/providers/register')">
          <v-icon start>mdi-account-plus</v-icon>
          Register First Provider
        </v-btn>
        <v-btn color="primary" variant="outlined" size="large" @click="$router.push('/ussd-test')">
          <v-icon start>mdi-cellphone</v-icon>
          Test USSD System
        </v-btn>
      </v-card-text>
    </v-card>

    <!-- Provider Details Dialog -->
    <v-dialog v-model="detailsDialog" max-width="700">
      <v-card v-if="selectedProvider">
        <v-card-title class="d-flex align-center">
          <v-avatar :color="selectedProvider.is_active ? 'primary' : 'grey'" class="me-3">
            <v-icon color="white">mdi-doctor</v-icon>
          </v-avatar>
          {{ selectedProvider.name }}
        </v-card-title>
        
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <v-list density="compact">
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon>mdi-phone</v-icon>
                  </template>
                  <v-list-item-title>Phone</v-list-item-title>
                  <v-list-item-subtitle>{{ $formatPhone(selectedProvider.phone) }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon>mdi-stethoscope</v-icon>
                  </template>
                  <v-list-item-title>Specialization</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedProvider.specialization || 'General' }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon>mdi-circle</v-icon>
                  </template>
                  <v-list-item-title>Status</v-list-item-title>
                  <v-list-item-subtitle>
                    <v-chip 
                      :color="selectedProvider.is_active ? 'success' : 'error'"
                      size="small"
                    >
                      {{ selectedProvider.is_active ? 'Active' : 'Inactive' }}
                    </v-chip>
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-col>
            
            <v-col cols="12" md="6">
              <v-list density="compact">
                <v-list-item v-if="selectedProvider.facility">
                  <template v-slot:prepend>
                    <v-icon>mdi-hospital-building</v-icon>
                  </template>
                  <v-list-item-title>Facility</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedProvider.facility.name }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item v-if="selectedProvider.facility?.location">
                  <template v-slot:prepend>
                    <v-icon>mdi-map-marker</v-icon>
                  </template>
                  <v-list-item-title>Location</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedProvider.facility.location }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon>mdi-calendar</v-icon>
                  </template>
                  <v-list-item-title>Registration Date</v-list-item-title>
                  <v-list-item-subtitle>{{ $formatDate(selectedProvider.registration_date) }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-col>
          </v-row>
        </v-card-text>
        
        <v-card-actions>
          <v-btn color="warning" @click="resetPin(selectedProvider)">
            <v-icon start>mdi-key</v-icon>
            Reset PIN
          </v-btn>
          <v-btn 
            :color="selectedProvider.is_active ? 'error' : 'success'"
            @click="toggleStatus(selectedProvider)"
          >
            <v-icon start>{{ selectedProvider.is_active ? 'mdi-pause' : 'mdi-play' }}</v-icon>
            {{ selectedProvider.is_active ? 'Deactivate' : 'Activate' }}
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn variant="outlined" @click="detailsDialog = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- USSD Information -->
    <v-card class="mt-6" elevation="2">
      <v-card-title>
        <v-icon class="me-2 text-primary">mdi-cellphone</v-icon>
        USSD Access for Providers
      </v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="6">
            <div class="text-h6 mb-3">
              <v-icon class="me-2 text-success">mdi-phone</v-icon>
              How to Access:
            </div>
            <v-timeline density="compact">
              <v-timeline-item dot-color="primary" size="small">
                Dial <strong>*384*15897#</strong> from registered phone
              </v-timeline-item>
              <v-timeline-item dot-color="primary" size="small">
                Select <strong>"1"</strong> for Healthcare Provider
              </v-timeline-item>
              <v-timeline-item dot-color="primary" size="small">
                Enter your 4-digit PIN
              </v-timeline-item>
              <v-timeline-item dot-color="primary" size="small">
                Access patient records, register new patients
              </v-timeline-item>
            </v-timeline>
          </v-col>
          <v-col cols="12" md="6">
            <div class="text-h6 mb-3">
              <v-icon class="me-2 text-warning">mdi-key</v-icon>
              Demo PINs for Testing:
            </div>
            <v-list density="compact">
              <v-list-item v-for="demo in demoPins" :key="demo.pin">
                <template v-slot:prepend>
                  <v-chip size="small" color="primary">{{ demo.pin }}</v-chip>
                </template>
                <v-list-item-title>{{ demo.name }}</v-list-item-title>
                <v-list-item-subtitle>{{ demo.specialty }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
            
            <div class="text-center mt-4">
              <v-btn color="primary" @click="$router.push('/ussd-test')">
                <v-icon start>mdi-test-tube</v-icon>
                Test USSD Interface
              </v-btn>
            </div>
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
  name: 'Providers',
  emits: ['loading', 'alert'],
  setup(props, { emit }) {
    const providers = ref([])
    const loading = ref(false)
    const searchQuery = ref('')
    const selectedProvider = ref(null)
    const detailsDialog = ref(false)

    const demoPins = [
      { pin: '1234', name: 'Dr. Kwame Asante', specialty: 'General Medicine' },
      { pin: '5678', name: 'Dr. Ama Mensah', specialty: 'Pediatrics' },
      { pin: '9012', name: 'Dr. Kofi Boateng', specialty: 'Internal Medicine' }
    ]

    const statistics = computed(() => {
      const activeProviders = providers.value.filter(p => p.is_active).length
      const specializations = new Set(providers.value.map(p => p.specialization).filter(Boolean)).size
      const facilitiesWithProviders = new Set(providers.value.map(p => p.facility_id).filter(Boolean)).size

      return [
        { 
          title: 'Total Providers', 
          value: providers.value.length, 
          icon: 'mdi-doctor', 
          color: 'primary' 
        },
        { 
          title: 'Active Providers', 
          value: activeProviders, 
          icon: 'mdi-check-circle', 
          color: 'success' 
        },
        { 
          title: 'Specializations', 
          value: specializations, 
          icon: 'mdi-stethoscope', 
          color: 'info' 
        },
        { 
          title: 'Facilities Served', 
          value: facilitiesWithProviders, 
          icon: 'mdi-hospital-building', 
          color: 'secondary' 
        }
      ]
    })

    const filteredProviders = computed(() => {
      if (!searchQuery.value) return providers.value
      
      const query = searchQuery.value.toLowerCase()
      return providers.value.filter(provider => 
        provider.name?.toLowerCase().includes(query) ||
        provider.phone?.includes(query) ||
        provider.specialization?.toLowerCase().includes(query) ||
        provider.facility?.name?.toLowerCase().includes(query)
      )
    })

    const getSpecializationColor = (specialization) => {
      const colors = {
        'General Medicine': 'primary',
        'Pediatrics': 'pink',
        'Internal Medicine': 'indigo',
        'Surgery': 'red',
        'Cardiology': 'deep-purple',
        'Dermatology': 'orange',
        'Nursing': 'teal',
        'Pharmacy': 'green'
      }
      return colors[specialization] || 'grey'
    }

    const loadProviders = async () => {
      try {
        emit('loading', true)
        const data = await apiService.getProviders()
        providers.value = data || []
        
        if (providers.value.length === 0) {
          emit('alert', {
            type: 'info',
            title: 'No Providers',
            message: 'No healthcare providers found. Register some providers to get started.'
          })
        }
      } catch (error) {
        console.error('Failed to load providers:', error)
        emit('alert', {
          type: 'error',
          title: 'Error',
          message: 'Failed to load providers: ' + error.message
        })
      } finally {
        emit('loading', false)
      }
    }

    const refreshProviders = async () => {
      await loadProviders()
      emit('alert', {
        type: 'success',
        title: 'Refreshed',
        message: 'Provider list has been refreshed'
      })
    }

    const viewProvider = (provider) => {
      selectedProvider.value = provider
      detailsDialog.value = true
    }

    const editProvider = (provider) => {
      emit('alert', {
        type: 'info',
        title: 'Edit Provider',
        message: `Edit functionality for ${provider.name} would be implemented here`
      })
    }

    const resetPin = async (provider) => {
      try {
        const confirmed = confirm(`Are you sure you want to reset the PIN for ${provider.name}?`)
        if (!confirmed) return

        emit('loading', true)
        const result = await apiService.resetProviderPin(provider.id)
        
        emit('alert', {
          type: 'success',
          title: 'PIN Reset',
          message: `PIN reset successfully. New PIN: ${result.new_pin}`
        })
        
        // Close dialog if open
        if (detailsDialog.value) {
          detailsDialog.value = false
        }
        
      } catch (error) {
        console.error('Failed to reset PIN:', error)
        emit('alert', {
          type: 'error',
          title: 'Error',
          message: 'Failed to reset PIN: ' + error.message
        })
      } finally {
        emit('loading', false)
      }
    }

    const toggleStatus = async (provider) => {
      try {
        const action = provider.is_active ? 'deactivate' : 'activate'
        const confirmed = confirm(`Are you sure you want to ${action} ${provider.name}?`)
        if (!confirmed) return

        emit('loading', true)
        await apiService.toggleProviderStatus(provider.id)
        
        // Update local state
        provider.is_active = !provider.is_active
        
        emit('alert', {
          type: 'success',
          title: 'Status Updated',
          message: `${provider.name} has been ${action}d successfully`
        })
        
      } catch (error) {
        console.error('Failed to toggle status:', error)
        emit('alert', {
          type: 'error',
          title: 'Error',
          message: 'Failed to update status: ' + error.message
        })
      } finally {
        emit('loading', false)
      }
    }

    onMounted(() => {
      loadProviders()
    })

    return {
      providers,
      loading,
      searchQuery,
      selectedProvider,
      detailsDialog,
      demoPins,
      statistics,
      filteredProviders,
      getSpecializationColor,
      refreshProviders,
      viewProvider,
      editProvider,
      resetPin,
      toggleStatus
    }
  }
}
</script>

<style scoped>
.hero-card {
  background: linear-gradient(135deg, rgba(25, 118, 210, 0.1), rgba(63, 81, 181, 0.1));
}

.stat-card {
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.provider-card {
  transition: all 0.3s ease;
  border-radius: 16px;
  overflow: hidden;
}

.provider-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0,0,0,0.12);
}

.provider-header {
  background: linear-gradient(135deg, rgba(25, 118, 210, 0.05), rgba(63, 81, 181, 0.05));
  position: relative;
  padding-bottom: 1rem !important;
}

.status-chip {
  position: absolute;
  top: 1rem;
  right: 1rem;
}
</style>