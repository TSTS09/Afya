<template>
  <div>
    <!-- Page Header -->
    <v-card class="mb-6 hero-card" elevation="2">
      <v-card-text class="text-center pa-8">
        <div class="text-h3 font-weight-bold text-primary mb-4">
          <v-icon size="large" class="me-3">mdi-hospital-building</v-icon>
          Register Healthcare Facility
        </div>
        <div class="text-h6 text-medium-emphasis">
          Add a new healthcare facility to the Afya Medical EHR network
        </div>
      </v-card-text>
    </v-card>

    <v-row justify="center">
      <v-col cols="12" md="8">
        <!-- Registration Form -->
        <v-card elevation="2">
          <v-card-title>
            <v-icon class="me-2 text-primary">mdi-hospital-building</v-icon>
            Facility Information
          </v-card-title>
          
          <v-card-text>
            <v-form v-model="formValid" @submit.prevent="registerFacility">
              <v-row>
                <v-col cols="12" md="8">
                  <v-text-field
                    v-model="form.name"
                    label="Facility Name"
                    placeholder="e.g., Korle Bu Teaching Hospital"
                    variant="outlined"
                    :rules="nameRules"
                    required
                  >
                    <template v-slot:prepend-inner>
                      <v-icon>mdi-hospital-building</v-icon>
                    </template>
                  </v-text-field>
                </v-col>

                <v-col cols="12" md="4">
                  <v-select
                    v-model="form.facility_type"
                    label="Facility Type"
                    :items="facilityTypes"
                    variant="outlined"
                    :rules="[v => !!v || 'Facility type is required']"
                    required
                  >
                    <template v-slot:prepend-inner>
                      <v-icon>mdi-tag</v-icon>
                    </template>
                  </v-select>
                </v-col>
              </v-row>

              <v-row>
                <v-col cols="12" md="8">
                  <v-text-field
                    v-model="form.location"
                    label="Location"
                    placeholder="e.g., Accra Central, Greater Accra"
                    variant="outlined"
                    :rules="locationRules"
                    required
                  >
                    <template v-slot:prepend-inner>
                      <v-icon>mdi-map-marker</v-icon>
                    </template>
                  </v-text-field>
                </v-col>

                <v-col cols="12" md="4">
                  <v-text-field
                    v-model="form.phone"
                    label="Phone Number"
                    placeholder="e.g., 0501234567"
                    variant="outlined"
                    :rules="phoneRules"
                    required
                  >
                    <template v-slot:prepend-inner>
                      <v-icon>mdi-phone</v-icon>
                    </template>
                    <template v-slot:append-inner>
                      <v-tooltip text="This will be used for facility identification">
                        <template v-slot:activator="{ props }">
                          <v-icon v-bind="props" color="info">mdi-information</v-icon>
                        </template>
                      </v-tooltip>
                    </template>
                  </v-text-field>
                </v-col>
              </v-row>

              <!-- Additional Information -->
              <v-row>
                <v-col cols="12">
                  <v-textarea
                    v-model="form.description"
                    label="Description (Optional)"
                    placeholder="Brief description of the facility and services offered..."
                    variant="outlined"
                    rows="3"
                    counter="500"
                    :rules="[v => !v || v.length <= 500 || 'Description must be less than 500 characters']"
                  >
                    <template v-slot:prepend-inner>
                      <v-icon>mdi-text</v-icon>
                    </template>
                  </v-textarea>
                </v-col>
              </v-row>

              <!-- Preview Card -->
              <v-card v-if="isFormFilled" variant="outlined" class="mt-4 mb-4">
                <v-card-title class="text-h6">
                  <v-icon class="me-2" :color="getFacilityTypeColor(form.facility_type)">
                    {{ getFacilityIcon(form.facility_type) }}
                  </v-icon>
                  Preview
                </v-card-title>
                <v-card-text>
                  <v-row>
                    <v-col cols="12" md="8">
                      <div class="text-h6">{{ form.name }}</div>
                      <div class="text-body-2 text-medium-emphasis mb-2">
                        <v-icon size="small" class="me-1">mdi-map-marker</v-icon>
                        {{ form.location }}
                      </div>
                      <v-chip 
                        :color="getFacilityTypeColor(form.facility_type)"
                        size="small"
                        variant="tonal"
                      >
                        {{ form.facility_type }}
                      </v-chip>
                    </v-col>
                    <v-col cols="12" md="4">
                      <v-list density="compact">
                        <v-list-item>
                          <template v-slot:prepend>
                            <v-icon size="small">mdi-phone</v-icon>
                          </template>
                          <v-list-item-title class="text-body-2">{{ form.phone }}</v-list-item-title>
                        </v-list-item>
                        <v-list-item v-if="form.description">
                          <template v-slot:prepend>
                            <v-icon size="small">mdi-text</v-icon>
                          </template>
                          <v-list-item-title class="text-body-2">{{ form.description.substring(0, 50) }}...</v-list-item-title>
                        </v-list-item>
                      </v-list>
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>

              <!-- Form Actions -->
              <v-row class="mt-4">
                <v-col cols="12">
                  <v-btn
                    type="submit"
                    color="primary"
                    size="large"
                    :loading="registering"
                    :disabled="!formValid || registering"
                    block
                  >
                    <v-icon start>mdi-hospital-building</v-icon>
                    Register Facility
                  </v-btn>
                </v-col>
              </v-row>

              <v-row>
                <v-col cols="12">
                  <v-btn
                    variant="outlined"
                    color="secondary"
                    block
                    @click="$router.push('/facilities')"
                  >
                    <v-icon start>mdi-arrow-left</v-icon>
                    Back to Facilities
                  </v-btn>
                </v-col>
              </v-row>
            </v-form>
          </v-card-text>
        </v-card>

        <!-- Information Card -->
        <v-card class="mt-6" elevation="2">
          <v-card-title>
            <v-icon class="me-2 text-info">mdi-information</v-icon>
            After Registration
          </v-card-title>
          <v-card-text>
            <div class="text-body-1 mb-4">Once your facility is registered, you can:</div>
            
            <v-row>
              <v-col cols="12" md="6">
                <v-list density="compact">
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon color="success">mdi-check</v-icon>
                    </template>
                    <v-list-item-title>Register healthcare providers for your facility</v-list-item-title>
                  </v-list-item>
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon color="success">mdi-check</v-icon>
                    </template>
                    <v-list-item-title>Start using the USSD system by dialing <strong>*384*15897#</strong></v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-col>
              <v-col cols="12" md="6">
                <v-list density="compact">
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon color="success">mdi-check</v-icon>
                    </template>
                    <v-list-item-title>Access the web dashboard for advanced features</v-list-item-title>
                  </v-list-item>
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon color="success">mdi-check</v-icon>
                    </template>
                    <v-list-item-title>View patient records and manage appointments</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>

        <!-- Facility Types Information -->
        <v-card class="mt-6" elevation="2">
          <v-card-title>
            <v-icon class="me-2 text-primary">mdi-information-outline</v-icon>
            Facility Types Guide
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col 
                v-for="type in facilityTypeGuide" 
                :key="type.name"
                cols="12" 
                md="6"
              >
                <v-card variant="outlined" class="h-100">
                  <v-card-text>
                    <div class="d-flex align-center mb-2">
                      <v-icon :color="type.color" class="me-2">{{ type.icon }}</v-icon>
                      <span class="text-h6">{{ type.name }}</span>
                    </div>
                    <div class="text-body-2 text-medium-emphasis">{{ type.description }}</div>
                    <div class="text-caption mt-2">
                      <strong>Examples:</strong> {{ type.examples.join(', ') }}
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Success Dialog -->
    <v-dialog v-model="successDialog" max-width="500" persistent>
      <v-card>
        <v-card-title class="text-center">
          <v-icon size="large" color="success" class="mb-2">mdi-check-circle</v-icon>
          <div>Registration Successful!</div>
        </v-card-title>
        
        <v-card-text class="text-center">
          <div class="text-h6 mb-4">{{ form.name }} has been registered successfully.</div>
          
          <v-alert type="success" variant="tonal">
            <strong>Facility:</strong> {{ form.name }}
            <br>
            <strong>Type:</strong> {{ form.facility_type }}
            <br>
            <strong>Location:</strong> {{ form.location }}
            <br>
            <strong>Phone:</strong> {{ $formatPhone(form.phone) }}
          </v-alert>
          
          <div class="text-body-2 mt-4">
            You can now register healthcare providers for this facility.
          </div>
        </v-card-text>
        
        <v-card-actions class="justify-center pb-6">
          <v-btn color="success" @click="registerProvider">
            <v-icon start>mdi-account-plus</v-icon>
            Register Provider
          </v-btn>
          <v-btn variant="outlined" @click="registerAnother">
            <v-icon start>mdi-plus</v-icon>
            Register Another
          </v-btn>
          <v-btn variant="outlined" @click="goToFacilities">
            <v-icon start>mdi-view-list</v-icon>
            View Facilities
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import apiService from '@/services/apiService'

export default {
  name: 'RegisterFacility',
  emits: ['loading', 'alert'],
  setup(props, { emit }) {
    const formValid = ref(false)
    const registering = ref(false)
    const successDialog = ref(false)

    const form = ref({
      name: '',
      facility_type: 'Clinic',
      location: '',
      phone: '',
      description: ''
    })

    const facilityTypes = [
      'Hospital',
      'Health Center',
      'Clinic',
      'Pharmacy',
      'Laboratory',
      'Emergency Center',
      'Maternity Home',
      'Mental Health Center',
      'Rehabilitation Center',
      'Mobile Clinic'
    ]

    const facilityTypeGuide = [
      {
        name: 'Hospital',
        icon: 'mdi-hospital-building',
        color: 'primary',
        description: 'Large medical facilities offering comprehensive inpatient and outpatient services',
        examples: ['Teaching Hospital', 'Regional Hospital', 'District Hospital']
      },
      {
        name: 'Health Center',
        icon: 'mdi-hospital',
        color: 'secondary',
        description: 'Community-based facilities providing primary healthcare services',
        examples: ['Community Health Center', 'Rural Health Center', 'Urban Health Center']
      },
      {
        name: 'Clinic',
        icon: 'mdi-medical-bag',
        color: 'info',
        description: 'Smaller healthcare facilities focusing on outpatient care and specific services',
        examples: ['Private Clinic', 'Specialist Clinic', 'Dental Clinic']
      },
      {
        name: 'Pharmacy',
        icon: 'mdi-pill',
        color: 'green',
        description: 'Facilities specializing in medication dispensing and pharmaceutical care',
        examples: ['Community Pharmacy', 'Hospital Pharmacy', 'Clinical Pharmacy']
      },
      {
        name: 'Laboratory',
        icon: 'mdi-test-tube',
        color: 'orange',
        description: 'Diagnostic facilities providing medical testing and analysis services',
        examples: ['Clinical Laboratory', 'Pathology Lab', 'Blood Bank']
      },
      {
        name: 'Emergency Center',
        icon: 'mdi-ambulance',
        color: 'red',
        description: 'Facilities providing urgent and emergency medical care',
        examples: ['Emergency Room', 'Trauma Center', 'Urgent Care Center']
      }
    ]

    const nameRules = [
      v => !!v || 'Facility name is required',
      v => (v && v.length >= 3) || 'Name must be at least 3 characters',
      v => (v && v.length <= 200) || 'Name must be less than 200 characters'
    ]

    const locationRules = [
      v => !!v || 'Location is required',
      v => (v && v.length >= 3) || 'Location must be at least 3 characters',
      v => (v && v.length <= 200) || 'Location must be less than 200 characters'
    ]

    const phoneRules = [
      v => !!v || 'Phone number is required',
      v => {
        const validation = apiService.validateGhanaPhone(v)
        return validation.valid || validation.message
      }
    ]

    const isFormFilled = computed(() => {
      return form.value.name && form.value.facility_type && form.value.location && form.value.phone
    })

    const getFacilityTypeColor = (type) => {
      const colors = {
        'Hospital': 'primary',
        'Health Center': 'secondary',
        'Clinic': 'info',
        'Pharmacy': 'green',
        'Laboratory': 'orange',
        'Emergency Center': 'red',
        'Maternity Home': 'pink',
        'Mental Health Center': 'purple',
        'Rehabilitation Center': 'teal',
        'Mobile Clinic': 'amber'
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
        'Emergency Center': 'mdi-ambulance',
        'Maternity Home': 'mdi-baby',
        'Mental Health Center': 'mdi-brain',
        'Rehabilitation Center': 'mdi-wheelchair-accessibility',
        'Mobile Clinic': 'mdi-truck-plus'
      }
      return icons[type] || 'mdi-hospital-building'
    }

    const registerFacility = async () => {
      if (!formValid.value) return

      try {
        registering.value = true
        emit('loading', true)

        // Validate phone number
        const phoneValidation = apiService.validateGhanaPhone(form.value.phone)
        if (!phoneValidation.valid) {
          throw new Error(phoneValidation.message)
        }

        // Prepare facility data
        const facilityData = {
          name: form.value.name.trim(),
          facility_type: form.value.facility_type,
          location: form.value.location.trim(),
          phone: phoneValidation.phone,
          description: form.value.description?.trim() || ''
        }

        // Register facility
        const result = await apiService.createFacility(facilityData)
        
        if (result.success) {
          successDialog.value = true
          
          emit('alert', {
            type: 'success',
            title: 'Registration Successful',
            message: `${form.value.name} has been registered successfully!`
          })
        } else {
          throw new Error(result.message || 'Registration failed')
        }

      } catch (error) {
        console.error('Registration failed:', error)
        emit('alert', {
          type: 'error',
          title: 'Registration Failed',
          message: error.message
        })
      } finally {
        registering.value = false
        emit('loading', false)
      }
    }

    const registerProvider = () => {
      successDialog.value = false
      emit('loading', false)
      setTimeout(() => {
        window.location.href = '/providers/register'
      }, 100)
    }

    const registerAnother = () => {
      successDialog.value = false
      
      // Reset form
      form.value = {
        name: '',
        facility_type: 'Clinic',
        location: '',
        phone: '',
        description: ''
      }
      formValid.value = false
    }

    const goToFacilities = () => {
      successDialog.value = false
      emit('loading', false)
      setTimeout(() => {
        window.location.href = '/facilities'
      }, 100)
    }

    return {
      formValid,
      registering,
      successDialog,
      form,
      facilityTypes,
      facilityTypeGuide,
      nameRules,
      locationRules,
      phoneRules,
      isFormFilled,
      getFacilityTypeColor,
      getFacilityIcon,
      registerFacility,
      registerProvider,
      registerAnother,
      goToFacilities
    }
  }
}
</script>

<style scoped>
.hero-card {
  background: linear-gradient(135deg, rgba(25, 118, 210, 0.1), rgba(63, 81, 181, 0.1));
}

.v-form {
  width: 100%;
}

.v-text-field, .v-select, .v-textarea {
  margin-bottom: 8px;
}
</style>