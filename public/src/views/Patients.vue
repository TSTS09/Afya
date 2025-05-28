<template>
  <div>
    <!-- Page Header -->
    <v-card class="mb-6 hero-card" elevation="2">
      <v-card-text class="text-center pa-8">
        <div class="text-h3 font-weight-bold text-success mb-4">
          <v-icon size="large" class="me-3">mdi-account-group</v-icon>
          Registered Patients
        </div>
        <div class="text-h6 text-medium-emphasis">
          View and manage patient records in the Afya Medical EHR system
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
        Patient Management
      </v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="8">
            <v-text-field
              v-model="searchQuery"
              label="Search patients"
              placeholder="Search by name, phone number..."
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              clearable
              @input="searchPatients"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="4" class="d-flex align-center">
            <v-btn color="primary" class="me-2" @click="refreshPatients">
              <v-icon start>mdi-refresh</v-icon>
              Refresh
            </v-btn>
            <v-btn color="success" @click="showRegistrationInfo">
              <v-icon start>mdi-account-plus</v-icon>
              Register Patient
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Patients Data Table -->
    <v-card elevation="2">
      <v-card-title class="d-flex align-center">
        <v-icon class="me-2 text-primary">mdi-account-group</v-icon>
        Patient Records
        <v-spacer></v-spacer>
        <v-chip color="primary" variant="outlined">
          {{ filteredPatients.length }} Total Patients
        </v-chip>
      </v-card-title>

      <v-card-text>
        <v-data-table
          v-if="patients.length > 0"
          :headers="headers"
          :items="filteredPatients"
          :loading="loading"
          :items-per-page="10"
          class="elevation-1"
          loading-text="Loading patients..."
        >
          <!-- Patient ID -->
          <template v-slot:item.id="{ item }">
            <v-chip size="small" color="secondary">
              #{{ item.id.substring(0, 8) }}
            </v-chip>
          </template>

          <!-- Patient Name and DOB -->
          <template v-slot:item.name="{ item }">
            <div>
              <div class="font-weight-bold">{{ item.name }}</div>
              <div v-if="item.date_of_birth" class="text-caption text-medium-emphasis">
                DOB: {{ item.date_of_birth }}
              </div>
            </div>
          </template>

          <!-- Phone Number -->
          <template v-slot:item.phone="{ item }">
            <v-chip variant="outlined" density="compact">
              {{ $formatPhone(item.phone) }}
            </v-chip>
          </template>

          <!-- Gender -->
          <template v-slot:item.gender="{ item }">
            <v-chip
              v-if="item.gender"
              :color="item.gender === 'Male' ? 'blue' : 'pink'"
              size="small"
              variant="tonal"
            >
              <v-icon start size="small">
                {{ item.gender === 'Male' ? 'mdi-human-male' : 'mdi-human-female' }}
              </v-icon>
              {{ item.gender }}
            </v-chip>
            <span v-else class="text-medium-emphasis">Not specified</span>
          </template>

          <!-- Blood Type -->
          <template v-slot:item.blood_type="{ item }">
            <v-chip
              v-if="item.blood_type"
              color="red"
              size="small"
              variant="tonal"
            >
              {{ item.blood_type }}
            </v-chip>
            <span v-else class="text-medium-emphasis">Unknown</span>
          </template>

          <!-- Registration Date -->
          <template v-slot:item.registration_date="{ item }">
            <div class="text-caption">
              {{ $formatDate(item.registration_date) }}
            </div>
          </template>

          <!-- Actions -->
          <template v-slot:item.actions="{ item }">
            <v-btn-group variant="outlined" density="compact">
              <v-btn size="small" @click="viewPatient(item)" title="View Details">
                <v-icon>mdi-eye</v-icon>
              </v-btn>
              <v-btn size="small" @click="editPatient(item)" title="Edit Patient">
                <v-icon>mdi-pencil</v-icon>
              </v-btn>
              <v-btn size="small" @click="viewRecords(item)" title="Medical Records">
                <v-icon>mdi-file-document</v-icon>
              </v-btn>
            </v-btn-group>
          </template>
        </v-data-table>

        <!-- Empty State -->
        <div v-else class="text-center py-12">
          <v-icon size="80" color="grey-lighten-2" class="mb-4">mdi-account-plus</v-icon>
          <div class="text-h5 text-medium-emphasis mb-2">No patients registered yet</div>
          <div class="text-body-1 text-medium-emphasis mb-6">
            Patients will be registered through the USSD system by healthcare providers.
          </div>
          
          <v-card class="mx-auto mb-6" max-width="500" variant="outlined">
            <v-card-title>How to register patients:</v-card-title>
            <v-card-text>
              <v-timeline density="compact">
                <v-timeline-item dot-color="primary" size="small">
                  <strong>Dial *384*15897#</strong> from your phone
                </v-timeline-item>
                <v-timeline-item dot-color="primary" size="small">
                  Select <strong>"1"</strong> for Healthcare Provider
                </v-timeline-item>
                <v-timeline-item dot-color="primary" size="small">
                  Enter your PIN (demo PIN: <code>1234</code>)
                </v-timeline-item>
                <v-timeline-item dot-color="primary" size="small">
                  Select <strong>"2"</strong> for New Patient
                </v-timeline-item>
              </v-timeline>
            </v-card-text>
          </v-card>

          <v-btn color="primary" size="large" class="me-4" @click="$router.push('/ussd-test')">
            <v-icon start>mdi-cellphone</v-icon>
            Test USSD Registration
          </v-btn>
          <v-btn color="secondary" variant="outlined" size="large" @click="showRegistrationInfo">
            <v-icon start>mdi-information</v-icon>
            Registration Info
          </v-btn>
        </div>
      </v-card-text>
    </v-card>

    <!-- Patient Details Dialog -->
    <v-dialog v-model="detailsDialog" max-width="600">
      <v-card v-if="selectedPatient">
        <v-card-title class="d-flex align-center">
          <v-avatar color="primary" class="me-3">
            <v-icon color="white">mdi-account</v-icon>
          </v-avatar>
          {{ selectedPatient.name }}
        </v-card-title>
        
        <v-card-text>
          <v-row>
            <v-col cols="6">
              <v-list density="compact">
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon>mdi-phone</v-icon>
                  </template>
                  <v-list-item-title>Phone</v-list-item-title>
                  <v-list-item-subtitle>{{ $formatPhone(selectedPatient.phone) }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item v-if="selectedPatient.date_of_birth">
                  <template v-slot:prepend>
                    <v-icon>mdi-calendar</v-icon>
                  </template>
                  <v-list-item-title>Date of Birth</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedPatient.date_of_birth }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item v-if="selectedPatient.gender">
                  <template v-slot:prepend>
                    <v-icon>{{ selectedPatient.gender === 'Male' ? 'mdi-human-male' : 'mdi-human-female' }}</v-icon>
                  </template>
                  <v-list-item-title>Gender</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedPatient.gender }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-col>
            
            <v-col cols="6">
              <v-list density="compact">
                <v-list-item v-if="selectedPatient.blood_type">
                  <template v-slot:prepend>
                    <v-icon color="red">mdi-water</v-icon>
                  </template>
                  <v-list-item-title>Blood Type</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedPatient.blood_type }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item v-if="selectedPatient.allergies">
                  <template v-slot:prepend>
                    <v-icon color="orange">mdi-alert</v-icon>
                  </template>
                  <v-list-item-title>Allergies</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedPatient.allergies }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item v-if="selectedPatient.emergency_contact">
                  <template v-slot:prepend>
                    <v-icon color="red">mdi-phone-alert</v-icon>
                  </template>
                  <v-list-item-title>Emergency Contact</v-list-item-title>
                  <v-list-item-subtitle>{{ $formatPhone(selectedPatient.emergency_contact) }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-col>
          </v-row>
          
          <v-divider class="my-4"></v-divider>
          
          <div class="text-caption text-medium-emphasis">
            Registered: {{ $formatDate(selectedPatient.registration_date) }}
          </div>
        </v-card-text>
        
        <v-card-actions>
          <v-btn color="primary" @click="viewRecords(selectedPatient)">
            <v-icon start>mdi-file-document</v-icon>
            View Medical Records
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn variant="outlined" @click="detailsDialog = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Registration Info Dialog -->
    <v-dialog v-model="registrationDialog" max-width="700">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="me-2 text-primary">mdi-cellphone</v-icon>
          Patient Registration Methods
        </v-card-title>
        
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <v-card variant="outlined" class="h-100">
                <v-card-title class="text-center">
                  <v-icon color="primary" size="large">mdi-cellphone</v-icon>
                  <div>USSD Registration</div>
                </v-card-title>
                <v-card-text class="text-center">
                  <div class="ussd-code mb-4">*384*15897#</div>
                  <div class="text-body-2">
                    Works on any mobile phone - No internet required
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
            
            <v-col cols="12" md="6">
              <v-card variant="outlined" class="h-100">
                <v-card-title class="text-center">
                  <v-icon color="success" size="large">mdi-web</v-icon>
                  <div>Web Testing</div>
                </v-card-title>
                <v-card-text class="text-center">
                  <div class="text-body-2 mb-4">
                    Test USSD functionality online
                  </div>
                  <v-btn color="success" @click="$router.push('/ussd-test')">
                    <v-icon start>mdi-test-tube</v-icon>
                    Test USSD
                  </v-btn>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="outlined" @click="registrationDialog = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import apiService from '@/services/apiService'

export default {
  name: 'Patients',
  emits: ['loading', 'alert'],
  setup(props, { emit }) {
    const patients = ref([])
    const loading = ref(false)
    const searchQuery = ref('')
    const selectedPatient = ref(null)
    const detailsDialog = ref(false)
    const registrationDialog = ref(false)

    const statistics = computed(() => [
      { 
        title: 'Total Patients', 
        value: patients.value.length, 
        icon: 'mdi-account-group', 
        color: 'primary' 
      },
      { 
        title: 'Male Patients', 
        value: patients.value.filter(p => p.gender === 'Male').length, 
        icon: 'mdi-human-male', 
        color: 'blue' 
      },
      { 
        title: 'Female Patients', 
        value: patients.value.filter(p => p.gender === 'Female').length, 
        icon: 'mdi-human-female', 
        color: 'pink' 
      },
      { 
        title: 'With Blood Type', 
        value: patients.value.filter(p => p.blood_type).length, 
        icon: 'mdi-water', 
        color: 'red' 
      }
    ])

    const filteredPatients = computed(() => {
      if (!searchQuery.value) return patients.value
      
      const query = searchQuery.value.toLowerCase()
      return patients.value.filter(patient => 
        patient.name?.toLowerCase().includes(query) ||
        patient.phone?.includes(query) ||
        patient.id?.toLowerCase().includes(query)
      )
    })

    const headers = [
      { title: 'ID', key: 'id', width: '100px' },
      { title: 'Patient Name', key: 'name', width: '200px' },
      { title: 'Phone Number', key: 'phone', width: '150px' },
      { title: 'Gender', key: 'gender', width: '120px' },
      { title: 'Blood Type', key: 'blood_type', width: '120px' },
      { title: 'Registration Date', key: 'registration_date', width: '150px' },
      { title: 'Actions', key: 'actions', width: '150px', sortable: false }
    ]

    const loadPatients = async () => {
      try {
        emit('loading', true)
        const data = await apiService.getPatients()
        patients.value = data || []
        
        if (patients.value.length === 0) {
          emit('alert', {
            type: 'info',
            title: 'No Patients',
            message: 'No patients found. They will appear here as healthcare providers register them.'
          })
        }
      } catch (error) {
        console.error('Failed to load patients:', error)
        emit('alert', {
          type: 'error',
          title: 'Error',
          message: 'Failed to load patients: ' + error.message
        })
      } finally {
        emit('loading', false)
      }
    }

    const refreshPatients = async () => {
      await loadPatients()
      emit('alert', {
        type: 'success',
        title: 'Refreshed',
        message: 'Patient list has been refreshed'
      })
    }

    const searchPatients = () => {
      // The computed property handles the filtering
      // This method could be extended to include API-based search
    }

    const viewPatient = (patient) => {
      selectedPatient.value = patient
      detailsDialog.value = true
    }

    const editPatient = (patient) => {
      // Navigate to edit patient page or open edit dialog
      emit('alert', {
        type: 'info',
        title: 'Edit Patient',
        message: `Edit functionality for ${patient.name} would be implemented here`
      })
    }

    const viewRecords = (patient) => {
      // Navigate to patient records page
      emit('alert', {
        type: 'info',
        title: 'Medical Records',
        message: `Viewing medical records for ${patient.name} would be implemented here`
      })
    }

    const showRegistrationInfo = () => {
      registrationDialog.value = true
    }

    onMounted(() => {
      loadPatients()
    })

    return {
      patients,
      loading,
      searchQuery,
      selectedPatient,
      detailsDialog,
      registrationDialog,
      statistics,
      filteredPatients,
      headers,
      loadPatients,
      refreshPatients,
      searchPatients,
      viewPatient,
      editPatient,
      viewRecords,
      showRegistrationInfo
    }
  }
}
</script>

<style scoped>
.hero-card {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.1), rgba(139, 195, 74, 0.1));
}

.stat-card {
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.ussd-code {
  font-family: 'Roboto Mono', monospace;
  font-size: 2rem;
  font-weight: bold;
  color: #1976d2;
  background: #f5f5f5;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  border: 2px solid #1976d2;
}
</style>