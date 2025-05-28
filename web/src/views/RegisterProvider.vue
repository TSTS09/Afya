<template>
  <div>
    <!-- Page Header -->
    <v-card class="mb-6 hero-card" elevation="2">
      <v-card-text class="text-center pa-8">
        <div class="text-h3 font-weight-bold text-success mb-4">
          <v-icon size="large" class="me-3">mdi-account-plus</v-icon>
          Register Healthcare Provider
        </div>
        <div class="text-h6 text-medium-emphasis">
          Add a new healthcare provider to the Afya Medical EHR system
        </div>
      </v-card-text>
    </v-card>

    <v-row justify="center">
      <v-col cols="12" md="8">
        <!-- Registration Form -->
        <v-card elevation="2">
          <v-card-title>
            <v-icon class="me-2 text-primary">mdi-doctor</v-icon>
            Provider Information
          </v-card-title>
          
          <v-card-text>
            <v-form v-model="formValid" @submit.prevent="registerProvider">
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="form.name"
                    label="Full Name"
                    placeholder="e.g., Dr. Kwame Asante"
                    variant="outlined"
                    :rules="nameRules"
                    required
                  >
                    <template v-slot:prepend-inner>
                      <v-icon>mdi-account</v-icon>
                    </template>
                  </v-text-field>
                </v-col>

                <v-col cols="12" md="6">
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
                      <v-tooltip text="This will be your login identifier for USSD access">
                        <template v-slot:activator="{ props }">
                          <v-icon v-bind="props" color="info">mdi-information</v-icon>
                        </template>
                      </v-tooltip>
                    </template>
                  </v-text-field>
                </v-col>
              </v-row>

              <v-row>
                <v-col cols="12" md="6">
                  <v-select
                    v-model="form.specialization"
                    label="Specialization"
                    :items="specializations"
                    variant="outlined"
                    :rules="[v => !!v || 'Specialization is required']"
                    required
                  >
                    <template v-slot:prepend-inner>
                      <v-icon>mdi-stethoscope</v-icon>
                    </template>
                  </v-select>
                </v-col>

                <v-col cols="12" md="6">
                  <v-select
                    v-model="form.facility_id"
                    label="Healthcare Facility"
                    :items="facilityItems"
                    item-title="text"
                    item-value="value"
                    variant="outlined"
                    :rules="[v => !!v || 'Facility is required']"
                    :loading="loadingFacilities"
                    required
                  >
                    <template v-slot:prepend-inner>
                      <v-icon>mdi-hospital-building</v-icon>
                    </template>
                    <template v-slot:append-inner>
                      <v-tooltip text="Select the facility where you work">
                        <template v-slot:activator="{ props }">
                          <v-icon v-bind="props" color="info">mdi-information</v-icon>
                        </template>
                      </v-tooltip>
                    </template>
                  </v-select>
                </v-col>
              </v-row>

              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="form.pin"
                    label="4-Digit PIN"
                    placeholder="Enter 4-digit PIN"
                    variant="outlined"
                    type="password"
                    :rules="pinRules"
                    maxlength="4"
                    required
                  >
                    <template v-slot:prepend-inner>
                      <v-icon>mdi-key</v-icon>
                    </template>
                    <template v-slot:append-inner>
                      <v-tooltip text="This PIN will be used to access the USSD system. Keep it secure!">
                        <template v-slot:activator="{ props }">
                          <v-icon v-bind="props" color="warning">mdi-lock</v-icon>
                        </template>
                      </v-tooltip>
                    </template>
                  </v-text-field>
                </v-col>

                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="confirmPin"
                    label="Confirm PIN"
                    placeholder="Re-enter PIN"
                    variant="outlined"
                    type="password"
                    :rules="confirmPinRules"
                    maxlength="4"
                    required
                  >
                    <template v-slot:prepend-inner>
                      <v-icon>mdi-key-variant</v-icon>
                    </template>
                  </v-text-field>
                </v-col>
              </v-row>

              <!-- Form Actions -->
              <v-row class="mt-4">
                <v-col cols="12">
                  <v-btn
                    type="submit"
                    color="success"
                    size="large"
                    :loading="registering"
                    :disabled="!formValid || registering"
                    block
                  >
                    <v-icon start>mdi-account-plus</v-icon>
                    Register Provider
                  </v-btn>
                </v-col>
              </v-row>

              <v-row>
                <v-col cols="12">
                  <v-btn
                    variant="outlined"
                    color="secondary"
                    block
                    @click="$router.push('/providers')"
                  >
                    <v-icon start>mdi-arrow-left</v-icon>
                    Back to Providers
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
            How to Use USSD System
          </v-card-title>
          <v-card-text>
            <div class="text-body-1 mb-4">After registration, you can access the system:</div>
            
            <v-timeline density="compact">
              <v-timeline-item dot-color="primary" size="small">
                <strong>Dial *384*15897#</strong> from your registered phone number
              </v-timeline-item>
              <v-timeline-item dot-color="primary" size="small">
                <strong>Select "1"</strong> for Healthcare Provider
              </v-timeline-item>
              <v-timeline-item dot-color="primary" size="small">
                <strong>Enter your 4-digit PIN</strong>
              </v-timeline-item>
              <v-timeline-item dot-color="primary" size="small">
                <strong>Access patient records</strong>, create new records, and manage appointments
              </v-timeline-item>
            </v-timeline>

            <v-alert type="info" variant="tonal" class="mt-4">
              <template v-slot:title>
                <v-icon>mdi-test-tube</v-icon>
                Demo PIN
              </template>
              For testing purposes, you can use PIN <strong>1234</strong> to access a demo provider account.
            </v-alert>
          </v-card-text>
        </v-card>

        <!-- No Facilities Warning -->
        <v-alert
          v-if="facilities.length === 0 && !loadingFacilities"
          type="warning"
          variant="tonal"
          class="mt-6"
        >
          <template v-slot:title>
            <v-icon>mdi-alert</v-icon>
            No Facilities Available
          </template>
          
          <div class="mt-2">
            You need to register at least one healthcare facility before registering providers.
          </div>
          
          <template v-slot:actions>
            <v-btn
              color="warning"
              variant="outlined"
              @click="$router.push('/facilities/register')"
            >
              <v-icon start>mdi-hospital-building</v-icon>
              Register Facility
            </v-btn>
          </template>
        </v-alert>
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
            <strong>Provider PIN:</strong> {{ form.pin }}
            <br>
            <strong>Phone:</strong> {{ $formatPhone(form.phone) }}
            <br>
            <strong>Facility:</strong> {{ selectedFacilityName }}
          </v-alert>
          
          <div class="text-body-2 mt-4">
            The provider can now access the USSD system by dialing <strong>*384*15897#</strong>
          </div>
        </v-card-text>
        
        <v-card-actions class="justify-center pb-6">
          <v-btn color="primary" @click="registerAnother">
            <v-icon start>mdi-plus</v-icon>
            Register Another
          </v-btn>
          <v-btn variant="outlined" @click="goToProviders">
            <v-icon start>mdi-view-list</v-icon>
            View Providers
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import apiService from '@/services/apiService'

export default {
  name: 'RegisterProvider',
  emits: ['loading', 'alert'],
  setup(props, { emit }) {
    const formValid = ref(false)
    const registering = ref(false)
    const loadingFacilities = ref(false)
    const facilities = ref([])
    const successDialog = ref(false)
    const confirmPin = ref('')

    const form = ref({
      name: '',
      phone: '',
      specialization: 'General Medicine',
      facility_id: '',
      pin: ''
    })

    const specializations = [
      'General Medicine',
      'Pediatrics',
      'Obstetrics/Gynecology',
      'Internal Medicine',
      'Surgery',
      'Cardiology',
      'Dermatology',
      'Emergency Medicine',
      'Family Medicine',
      'Psychiatry',
      'Radiology',
      'Anesthesiology',
      'Pathology',
      'Nursing',
      'Pharmacy',
      'Laboratory',
      'Other'
    ]

    const nameRules = [
      v => !!v || 'Name is required',
      v => (v && v.length >= 3) || 'Name must be at least 3 characters',
      v => (v && v.length <= 100) || 'Name must be less than 100 characters'
    ]

    const phoneRules = [
      v => !!v || 'Phone number is required',
      v => {
        const validation = apiService.validateGhanaPhone(v)
        return validation.valid || validation.message
      }
    ]

    const pinRules = [
      v => !!v || 'PIN is required',
      v => (v && v.length === 4) || 'PIN must be exactly 4 digits',
      v => /^\d{4}$/.test(v) || 'PIN must contain only numbers'
    ]

    const confirmPinRules = [
      v => !!v || 'Please confirm your PIN',
      v => v === form.value.pin || 'PINs do not match'
    ]

    const facilityItems = computed(() => {
      return facilities.value.map(facility => ({
        text: `${facility.name} - ${facility.location || 'No location'}`,
        value: facility.id
      }))
    })

    const selectedFacilityName = computed(() => {
      const facility = facilities.value.find(f => f.id === form.value.facility_id)
      return facility ? facility.name : ''
    })

    const loadFacilities = async () => {
      try {
        loadingFacilities.value = true
        const data = await apiService.getFacilities()
        facilities.value = data.filter(f => f.is_active) || []
        
        // Auto-select if only one facility
        if (facilities.value.length === 1) {
          form.value.facility_id = facilities.value[0].id
        }
      } catch (error) {
        console.error('Failed to load facilities:', error)
        emit('alert', {
          type: 'error',
          title: 'Error',
          message: 'Failed to load facilities: ' + error.message
        })
      } finally {
        loadingFacilities.value = false
      }
    }

    const registerProvider = async () => {
      if (!formValid.value) return

      try {
        registering.value = true
        emit('loading', true)

        // Validate phone number
        const phoneValidation = apiService.validateGhanaPhone(form.value.phone)
        if (!phoneValidation.valid) {
          throw new Error(phoneValidation.message)
        }

        // Prepare provider data
        const providerData = {
          name: form.value.name.trim(),
          phone: phoneValidation.phone,
          specialization: form.value.specialization,
          facility_id: form.value.facility_id,
          pin: form.value.pin
        }

        // Register provider
        const result = await apiService.createProvider(providerData)
        
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

    const registerAnother = () => {
      successDialog.value = false
      
      // Reset form
      form.value = {
        name: '',
        phone: '',
        specialization: 'General Medicine',
        facility_id: form.value.facility_id, // Keep same facility
        pin: ''
      }
      confirmPin.value = ''
      formValid.value = false
    }

    const goToProviders = () => {
      successDialog.value = false
      emit('loading', false)
      // Use setTimeout to ensure dialog closes before navigation
      setTimeout(() => {
        window.location.href = '/providers'
      }, 100)
    }

    const generateRandomPin = () => {
      form.value.pin = Math.floor(1000 + Math.random() * 9000).toString()
      confirmPin.value = form.value.pin
    }

    onMounted(() => {
      loadFacilities()
    })

    return {
      formValid,
      registering,
      loadingFacilities,
      facilities,
      successDialog,
      confirmPin,
      form,
      specializations,
      nameRules,
      phoneRules,
      pinRules,
      confirmPinRules,
      facilityItems,
      selectedFacilityName,
      registerProvider,
      registerAnother,
      goToProviders,
      generateRandomPin
    }
  }
}
</script>

<style scoped>
.hero-card {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.1), rgba(104, 159, 56, 0.1));
}

.v-form {
  width: 100%;
}

.v-text-field, .v-select {
  margin-bottom: 8px;
}
</style>