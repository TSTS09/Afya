<template>
  <div>
    <!-- Page Header -->
    <v-card class="mb-6 hero-card" elevation="2">
      <v-card-text class="text-center pa-8">
        <div class="text-h3 font-weight-bold text-primary mb-4">
          <v-icon size="large" class="me-3">mdi-hospital-building</v-icon>
          Healthcare Facilities
        </div>
        <div class="text-h6 text-medium-emphasis">
          Manage healthcare facilities in the Afya Medical EHR network
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
        <v-icon class="me-2 text-primary">mdi-magnify</v-icon>
        Facility Management
      </v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="8">
            <v-text-field
              v-model="searchQuery"
              label="Search facilities"
              placeholder="Search by name, location, or type..."
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              clearable
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="4" class="d-flex align-center">
            <v-btn color="primary" class="me-2" @click="refreshFacilities">
              <v-icon start>mdi-refresh</v-icon>
              Refresh
            </v-btn>
            <v-btn color="success" @click="$router.push('/facilities/register')">
              <v-icon start>mdi-hospital-building</v-icon>
              Register Facility
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Facilities Display -->
    <div v-if="facilities.length > 0">
      <v-row>
        <v-col 
          v-for="facility in filteredFacilities" 
          :key="facility.id" 
          cols="12" 
          lg="4" 
          xl="3" 
          md="6"
        >
          <v-card class="facility-card h-100" elevation="2">
            <!-- Facility Header -->
            <div class="facility-header">
              <!-- Facility Type Badge -->
              <v-chip 
                class="facility-type-badge"
                :color="getFacilityTypeColor(facility.facility_type)"
                size="small"
                variant="tonal"
              >
                {{ facility.facility_type || 'Clinic' }}
              </v-chip>
              
              <v-row align="center" no-gutters class="pa-4">
                <v-col cols="3">
                  <v-icon 
                    size="40" 
                    :color="facility.is_active ? 'primary' : 'grey'"
                    class="facility-icon"
                  >
                    {{ getFacilityIcon(facility.facility_type) }}
                  </v-icon>
                </v-col>
                <v-col cols="9">
                  <div class="text-h6 mb-1">{{ facility.name }}</div>
                  <div class="text-body-2 text-medium-emphasis">
                    <v-icon size="small" class="me-1">mdi-map-marker</v-icon>
                    {{ facility.location || 'Location not specified' }}
                  </div>
                </v-col>
              </v-row>
            </div>

            <!-- Facility Details -->
            <v-card-text>
              <v-list density="compact">
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon color="primary">mdi-phone</v-icon>
                  </template>
                  <v-list-item-title>{{ facility.phone || 'No phone' }}</v-list-item-title>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon :color="facility.is_active ? 'success' : 'error'">mdi-circle</v-icon>
                  </template>
                  <v-list-item-title>Status</v-list-item-title>
                  <v-list-item-subtitle>
                    <v-chip 
                      :color="facility.is_active ? 'success' : 'error'"
                      size="small"
                    >
                      {{ facility.is_active ? 'Active' : 'Inactive' }}
                    </v-chip>
                  </v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon color="info">mdi-calendar</v-icon>
                  </template>
                  <v-list-item-title>Registered</v-list-item-title>
                  <v-list-item-subtitle>{{ $formatDate(facility.registration_date) }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>

              <!-- Facility Stats -->
              <v-card variant="tonal" class="facility-stats mt-3">
                <v-card-text class="pa-3">
                  <v-row>
                    <v-col cols="6" class="text-center">
                      <div class="text-h6 mb-1">{{ facility.providers_count || 0 }}</div>
                      <div class="text-caption text-medium-emphasis">Providers</div>
                    </v-col>
                    <v-col cols="6" class="text-center">
                      <div class="text-h6 mb-1">{{ facility.records_count || 0 }}</div>
                      <div class="text-caption text-medium-emphasis">Records</div>
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>
            </v-card-text>

            <!-- Action Buttons -->
            <v-card-actions class="pa-4">
              <v-btn
                variant="outlined"
                block
                @click="viewFacility(facility)"
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
                    @click="editFacility(facility)"
                    title="Edit Facility"
                  >
                    <v-icon>mdi-pencil</v-icon>
                  </v-btn>
                </v-col>
                <v-col cols="4">
                  <v-btn
                    variant="outlined"
                    size="small"
                    color="info"
                    @click="viewProviders(facility)"
                    title="View Providers"
                  >
                    <v-icon>mdi-doctor</v-icon>
                  </v-btn>
                </v-col>
                <v-col cols="4">
                  <v-btn
                    variant="outlined"
                    size="small"
                    :color="facility.is_active ? 'error' : 'success'"
                    @click="toggleStatus(facility)"
                    :title="facility.is_active ? 'Deactivate' : 'Activate'"
                  >
                    <v-icon>{{ facility.is_active ? 'mdi-pause' : 'mdi-play' }}</v-icon>
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
        <v-icon size="80" color="grey-lighten-2" class="mb-4">mdi-hospital-building</v-icon>
        <div class="text-h5 text-medium-emphasis mb-2">No healthcare facilities registered yet</div>
        <div class="text-body-1 text-medium-emphasis mb-6">
          Start by registering healthcare facilities to build your EHR network.
        </div>
        
        <v-card class="mx-auto mb-6" max-width="500" variant="outlined">
          <v-card-title>Getting Started:</v-card-title>
          <v-card-text>
            <v-timeline density="compact">
              <v-timeline-item dot-color="primary" size="small">
                <router-link to="/facilities/register">Register healthcare facilities</router-link>
              </v-timeline-item>
              <v-timeline-item dot-color="primary" size="small">
                <router-link to="/providers/register">Register healthcare providers</router-link>
              </v-timeline-item>
              <v-timeline-item dot-color="primary" size="small">
                Start using USSD system: <strong>*384*15897#</strong>
              </v-timeline-item>
              <v-timeline-item dot-color="primary" size="small">
                Begin registering patients and creating records
              </v-timeline-item>
            </v-timeline>
          </v-card-text>
        </v-card>

        <v-btn color="success" size="large" class="me-4" @click="$router.push('/facilities/register')">
          <v-icon start>mdi-hospital-building</v-icon>
          Register First Facility
        </v-btn>
        <v-btn color="primary" variant="outlined" size="large" @click="$router.push('/ussd-test')">
          <v-icon start>mdi-cellphone</v-icon>
          Test USSD System
        </v-btn>
      </v-card-text>
    </v-card>

    <!-- Facility Details Dialog -->
    <v-dialog v-model="detailsDialog" max-width="700">
      <v-card v-if="selectedFacility">
        <v-card-title class="d-flex align-center">
          <v-icon 
            :color="selectedFacility.is_active ? 'primary' : 'grey'" 
            size="large" 
            class="me-3"
          >
            {{ getFacilityIcon(selectedFacility.facility_type) }}
          </v-icon>
          {{ selectedFacility.name }}
        </v-card-title>
        
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <v-list density="compact">
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon>mdi-tag</v-icon>
                  </template>
                  <v-list-item-title>Facility Type</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedFacility.facility_type || 'Clinic' }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon>mdi-map-marker</v-icon>
                  </template>
                  <v-list-item-title>Location</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedFacility.location || 'Not specified' }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon>mdi-phone</v-icon>
                  </template>
                  <v-list-item-title>Phone</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedFacility.phone || 'Not provided' }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-col>
            
            <v-col cols="12" md="6">
              <v-list density="compact">
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon>mdi-circle</v-icon>
                  </template>
                  <v-list-item-title>Status</v-list-item-title>
                  <v-list-item-subtitle>
                    <v-chip 
                      :color="selectedFacility.is_active ? 'success' : 'error'"
                      size="small"
                    >
                      {{ selectedFacility.is_active ? 'Active' : 'Inactive' }}
                    </v-chip>
                  </v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon>mdi-doctor</v-icon>
                  </template>
                  <v-list-item-title>Providers</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedFacility.providers_count || 0 }} registered</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon>mdi-file-document</v-icon>
                  </template>
                  <v-list-item-title>Medical Records</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedFacility.records_count || 0 }} total</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-col>
          </v-row>
          
          <v-divider class="my-4"></v-divider>
          
          <div class="text-caption text-medium-emphasis">
            Registered: {{ $formatDate(selectedFacility.registration_date) }}
          </div>
        </v-card-text>
        
        <v-card-actions>
          <v-btn color="info" @click="viewProviders(selectedFacility)">
            <v-icon start>mdi-doctor</v-icon>
            View Providers
          </v-btn>
          <v-btn 
            :color="selectedFacility.is_active ? 'error' : 'success'"
            @click="toggleStatus(selectedFacility)"
          >
            <v-icon start>{{ selectedFacility.is_active ? 'mdi-pause' : 'mdi-play' }}</v-icon>
            {{ selectedFacility.is_active ? 'Deactivate' : 'Activate' }}
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn variant="outlined" @click="detailsDialog = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Facility Types Overview -->
    <v-card class="mt-6" elevation="2">
      <v-card-title>
        <v-icon class="me-2 text-primary">mdi-information</v-icon>
        Supported Facility Types
      </v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="6">
            <div class="text-h6 mb-3">
              <v-icon class="me-2 text-primary">mdi-hospital-building</v-icon>
              Primary Care Facilities:
            </div>
            <v-list density="compact">
              <v-list-item v-for="type in primaryCareTypes" :key="type.name">
                <template v-slot:prepend>
                  <v-icon :color="type.color">{{ type.icon }}</v-icon>
                </template>
                <v-list-item-title>{{ type.name }}</v-list-item-title>
                <v-list-item-subtitle>{{ type.description }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-col>
          <v-col cols="12" md="6">
            <div class="text-h6 mb-3">
              <v-icon class="me-2 text-success">mdi-cog</v-icon>
              Specialized Services:
            </div>
            <v-list density="compact">
              <v-list-item v-for="type in specializedTypes" :key="type.name">
                <template v-slot:prepend>
                  <v-icon :color="type.color">{{ type.icon }}</v-icon>
                </template>
                <v-list-item-title>{{ type.name }}</v-list-item-title>
                <v-list-item-subtitle>{{ type.description }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-col>
        </v-row>
        <div class="text-center mt-4">
          <v-btn color="primary" @click="$router.push('/facilities/register')">
            <v-icon start>mdi-plus</v-icon>
            Register New Facility
          </v-btn>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import apiService from '@/services/apiService'

export default {
  name: 'Facilities',
  emits: ['loading', 'alert'],
  setup(props, { emit }) {
    const facilities = ref([])
    const loading = ref(false)
    const searchQuery = ref('')
    const selectedFacility = ref(null)
    const detailsDialog = ref(false)

    const primaryCareTypes = [
      { name: 'Hospitals', icon: 'mdi-hospital-building', color: 'primary', description: 'Full-service medical facilities' },
      { name: 'Health Centers', icon: 'mdi-hospital', color: 'secondary', description: 'Community healthcare facilities' },
      { name: 'Clinics', icon: 'mdi-medical-bag', color: 'info', description: 'Outpatient medical facilities' }
    ]

    const specializedTypes = [
      { name: 'Pharmacies', icon: 'mdi-pill', color: 'green', description: 'Medication dispensing facilities' },
      { name: 'Laboratories', icon: 'mdi-test-tube', color: 'orange', description: 'Diagnostic and testing facilities' },
      { name: 'Emergency Centers', icon: 'mdi-ambulance', color: 'red', description: 'Urgent care facilities' }
    ]

    const statistics = computed(() => {
      const activeFacilities = facilities.value.filter(f => f.is_active).length
      const locations = new Set(facilities.value.map(f => f.location).filter(Boolean)).size
      const facilityTypes = new Set(facilities.value.map(f => f.facility_type).filter(Boolean)).size

      return [
        { 
          title: 'Total Facilities', 
          value: facilities.value.length, 
          icon: 'mdi-hospital-building', 
          color: 'primary' 
        },
        { 
          title: 'Active Facilities', 
          value: activeFacilities, 
          icon: 'mdi-check-circle', 
          color: 'success' 
        },
        { 
          title: 'Locations', 
          value: locations, 
          icon: 'mdi-map-marker', 
          color: 'info' 
        },
        { 
          title: 'Facility Types', 
          value: facilityTypes, 
          icon: 'mdi-tag', 
          color: 'secondary' 
        }
      ]
    })

    const filteredFacilities = computed(() => {
      if (!searchQuery.value) return facilities.value
      
      const query = searchQuery.value.toLowerCase()
      return facilities.value.filter(facility => 
        facility.name?.toLowerCase().includes(query) ||
        facility.location?.toLowerCase().includes(query) ||
        facility.facility_type?.toLowerCase().includes(query) ||
        facility.phone?.includes(query)
      )
    })

    const getFacilityTypeColor = (type) => {
      const colors = {
        'Hospital': 'primary',
        'Health Center': 'secondary',
        'Clinic': 'info',
        'Pharmacy': 'green',
        'Laboratory': 'orange',
        'Emergency Center': 'red'
      }
      return colors[type] || 'grey'
    }

    const getFacilityIcon = (type) => {
      const icons = {
        'Hospital': 'mdi-hospital-building',
        'Health Center': 'mdi-hospital',
        'Clinic': 'mdi-medical-bag',
        'Pharmacy': 'mdi-pill',
        'Laboratory': 'mdi-test-tube',
        'Emergency Center': 'mdi-ambulance'
      }
      return icons[type] || 'mdi-hospital-building'
    }

    const loadFacilities = async () => {
      try {
        emit('loading', true)
        const data = await apiService.getFacilities()
        facilities.value = data || []
        
        if (facilities.value.length === 0) {
          emit('alert', {
            type: 'info',
            title: 'No Facilities',
            message: 'No healthcare facilities found. Register some facilities to get started.'
          })
        }
      } catch (error) {
        console.error('Failed to load facilities:', error)
        emit('alert', {
          type: 'error',
          title: 'Error',
          message: 'Failed to load facilities: ' + error.message
        })
      } finally {
        emit('loading', false)
      }
    }

    const refreshFacilities = async () => {
      await loadFacilities()
      emit('alert', {
        type: 'success',
        title: 'Refreshed',
        message: 'Facility list has been refreshed'
      })
    }

    const viewFacility = (facility) => {
      selectedFacility.value = facility
      detailsDialog.value = true
    }

    const editFacility = (facility) => {
      emit('alert', {
        type: 'info',
        title: 'Edit Facility',
        message: `Edit functionality for ${facility.name} would be implemented here`
      })
    }

    const viewProviders = (facility) => {
      // Navigate to providers page filtered by facility
      emit('alert', {
        type: 'info',
        title: 'View Providers',
        message: `Viewing providers for ${facility.name} would be implemented here`
      })
    }

    const toggleStatus = async (facility) => {
      try {
        const action = facility.is_active ? 'deactivate' : 'activate'
        const confirmed = confirm(`Are you sure you want to ${action} ${facility.name}?`)
        if (!confirmed) return

        emit('loading', true)
        await apiService.toggleFacilityStatus(facility.id)
        
        // Update local state
        facility.is_active = !facility.is_active
        
        emit('alert', {
          type: 'success',
          title: 'Status Updated',
          message: `${facility.name} has been ${action}d successfully`
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
      loadFacilities()
    })

    return {
      facilities,
      loading,
      searchQuery,
      selectedFacility,
      detailsDialog,
      primaryCareTypes,
      specializedTypes,
      statistics,
      filteredFacilities,
      getFacilityTypeColor,
      getFacilityIcon,
      refreshFacilities,
      viewFacility,
      editFacility,
      viewProviders,
      toggleStatus
    }
  }
}
</script>

<style scoped>
.hero-card {
  background: linear-gradient(135deg, rgba(25, 118, 210, 0.1), rgba(103, 58, 183, 0.1));
}

.stat-card {
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.facility-card {
  transition: all 0.3s ease;
  border-radius: 20px;
  overflow: hidden;
}

.facility-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0,0,0,0.12);
}

.facility-header {
  background: linear-gradient(135deg, rgba(25, 118, 210, 0.05), rgba(103, 58, 183, 0.05));
  position: relative;
}

.facility-type-badge {
  position: absolute;
  top: 1rem;
  right: 1rem;
  backdrop-filter: blur(10px);
  z-index: 1;
}

.facility-icon {
  opacity: 0.8;
}

.facility-stats {
  background: rgba(var(--v-theme-surface), 0.7);
  border-radius: 12px;
}
</style>