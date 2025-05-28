<template>
  <div>
    <!-- Page Header -->
    <v-card class="mb-6 hero-card" elevation="2">
      <v-card-text class="text-center pa-8">
        <div class="text-h3 font-weight-bold text-primary mb-4">
          <v-icon size="large" class="me-3">mdi-cellphone</v-icon>
          USSD Test Interface
        </div>
        <div class="text-h6 text-medium-emphasis">
          Test the Afya Medical EHR USSD system locally - No phone required!
        </div>
      </v-card-text>
    </v-card>

    <v-row>
      <!-- USSD Simulator -->
      <v-col cols="12" lg="8">
        <v-card class="simulator-card" elevation="3">
          <v-card-title class="text-white bg-primary">
            <v-icon class="me-2">mdi-cellphone</v-icon>
            USSD Simulator
          </v-card-title>
          
          <v-card-text class="pa-6">
            <!-- Session Info -->
            <v-row class="mb-4">
              <v-col cols="6">
                <v-text-field
                  label="Session ID"
                  v-model="sessionId"
                  readonly
                  density="compact"
                  variant="outlined"
                ></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-text-field
                  label="Service Code"
                  value="*714#"
                  readonly
                  density="compact"
                  variant="outlined"
                ></v-text-field>
              </v-col>
            </v-row>

            <!-- USSD Form -->
            <v-form @submit.prevent="sendUssdRequest">
              <v-row class="mb-4">
                <v-col cols="6">
                  <v-text-field
                    label="Phone Number"
                    v-model="phoneNumber"
                    placeholder="e.g., +233200123456"
                    density="compact"
                    variant="outlined"
                    :rules="phoneRules"
                  ></v-text-field>
                </v-col>
                <v-col cols="6">
                  <v-text-field
                    label="USSD Input"
                    v-model="ussdText"
                    placeholder="e.g., 1*1234"
                    density="compact"
                    variant="outlined"
                    hint="Leave empty for main menu"
                    persistent-hint
                    ref="ussdInput"
                  ></v-text-field>
                </v-col>
              </v-row>

              <v-row class="mb-4">
                <v-col cols="12">
                  <v-btn
                    type="submit"
                    color="success"
                    size="large"
                    :loading="sending"
                    :disabled="sending"
                  >
                    <v-icon start>mdi-send</v-icon>
                    Send USSD Request
                  </v-btn>
                  
                  <v-btn
                    color="warning"
                    variant="outlined"
                    class="ms-2"
                    @click="newSession"
                  >
                    <v-icon start>mdi-refresh</v-icon>
                    New Session
                  </v-btn>
                  
                  <v-btn
                    color="info"
                    variant="outlined"
                    class="ms-2"
                    @click="clearResponse"
                  >
                    <v-icon start>mdi-eraser</v-icon>
                    Clear Response
                  </v-btn>
                </v-col>
              </v-row>
            </v-form>

            <!-- Response Display -->
            <v-card variant="outlined" class="response-card">
              <v-card-title class="text-h6">USSD Response:</v-card-title>
              <v-card-text>
                <div class="response-content">
                  <pre v-if="ussdResponse" class="response-text">{{ ussdResponse }}</pre>
                  <div v-else class="text-medium-emphasis">
                    No response yet. Send a USSD request to see the response here.
                  </div>
                </div>
                
                <v-btn
                  v-if="ussdResponse"
                  color="primary"
                  variant="outlined"
                  size="small"
                  class="mt-3"
                  @click="copyResponse"
                >
                  <v-icon start>mdi-content-copy</v-icon>
                  Copy Response
                </v-btn>
              </v-card-text>
            </v-card>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Quick Test Panel -->
      <v-col cols="12" lg="4">
        <!-- Demo Credentials -->
        <v-card class="demo-card mb-4" elevation="2">
          <v-card-title class="text-white bg-info">
            <v-icon class="me-2">mdi-key</v-icon>
            Demo Credentials
          </v-card-title>
          <v-card-text>
            <div class="mb-4">
              <div class="text-subtitle-1 font-weight-bold mb-2">Provider PINs:</div>
              <v-list density="compact">
                <v-list-item v-for="provider in demoProviders" :key="provider.pin">
                  <template v-slot:prepend>
                    <v-chip size="small" color="primary">{{ provider.pin }}</v-chip>
                  </template>
                  <v-list-item-title class="text-body-2">{{ provider.name }}</v-list-item-title>
                  <v-list-item-subtitle>{{ provider.specialty }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </div>

            <div>
              <div class="text-subtitle-1 font-weight-bold mb-2">Test Phone Numbers:</div>
              <v-list density="compact">
                <v-list-item v-for="patient in demoPatients" :key="patient.phone">
                  <template v-slot:prepend>
                    <v-chip size="small" color="success">{{ patient.phone }}</v-chip>
                  </template>
                  <v-list-item-title class="text-body-2">{{ patient.name }}</v-list-item-title>
                </v-list-item>
              </v-list>
            </div>
          </v-card-text>
        </v-card>

        <!-- Quick Test Buttons -->
        <v-card class="quick-tests-card mb-4" elevation="2">
          <v-card-title class="text-white bg-success">
            <v-icon class="me-2">mdi-lightning-bolt</v-icon>
            Quick Tests
          </v-card-title>
          <v-card-text>
            <div class="mb-4">
              <div class="text-subtitle-2 mb-2">Basic Navigation:</div>
              <v-btn-group class="flex-wrap">
                <v-btn size="small" @click="quickTest('')">Main Menu</v-btn>
                <v-btn size="small" @click="quickTest('1')">Provider Login</v-btn>
                <v-btn size="small" @click="quickTest('2')">Patient Services</v-btn>
                <v-btn size="small" @click="quickTest('3')">Emergency</v-btn>
                <v-btn size="small" @click="quickTest('4')">System Info</v-btn>
              </v-btn-group>
            </div>

            <div class="mb-4">
              <div class="text-subtitle-2 mb-2">Provider Workflows:</div>
              <v-btn-group class="flex-wrap">
                <v-btn size="small" color="success" @click="quickTest('1*1234')">Login (1234)</v-btn>
                <v-btn size="small" color="success" @click="quickTest('1*1234*1')">Patient Lookup</v-btn>
                <v-btn size="small" color="success" @click="quickTest('1*1234*2')">New Patient</v-btn>
                <v-btn size="small" color="success" @click="quickTest('1*1234*3')">New Record</v-btn>
              </v-btn-group>
            </div>

            <div class="mb-4">
              <div class="text-subtitle-2 mb-2">Patient Workflows:</div>
              <v-btn-group class="flex-wrap">
                <v-btn size="small" color="info" @click="quickTest('2*1')">View Records</v-btn>
                <v-btn size="small" color="info" @click="quickTest('2*2')">Emergency Contact</v-btn>
                <v-btn size="small" color="info" @click="quickTest('2*3')">Appointments</v-btn>
              </v-btn-group>
            </div>

            <div>
              <div class="text-subtitle-2 mb-2">Emergency:</div>
              <v-btn-group class="flex-wrap">
                <v-btn size="small" color="error" @click="quickTest('3*1')">Call Ambulance</v-btn>
                <v-btn size="small" color="error" @click="quickTest('3*3')">Emergency Info</v-btn>
                <v-btn size="small" color="error" @click="quickTest('3*4')">Nearest Hospital</v-btn>
              </v-btn-group>
            </div>
          </v-card-text>
        </v-card>

        <!-- Test Scenarios -->
        <v-card elevation="2">
          <v-card-title class="text-white bg-warning">
            <v-icon class="me-2">mdi-clipboard-list</v-icon>
            Test Scenarios
          </v-card-title>
          <v-card-text>
            <v-expansion-panels>
              <v-expansion-panel v-for="scenario in testScenarios" :key="scenario.title">
                <v-expansion-panel-title>{{ scenario.title }}</v-expansion-panel-title>
                <v-expansion-panel-text>
                  <ol class="text-body-2">
                    <li v-for="step in scenario.steps" :key="step">{{ step }}</li>
                  </ol>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Instructions -->
    <v-card class="mt-6" elevation="2">
      <v-card-title>
        <v-icon class="me-2 text-info">mdi-information</v-icon>
        How to Use This USSD Test Interface
      </v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="6">
            <div class="text-h6 mb-3">USSD Input Format:</div>
            <v-list density="compact">
              <v-list-item>
                <template v-slot:prepend><v-chip size="small">Empty</v-chip></template>
                <v-list-item-title>Main menu</v-list-item-title>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend><v-chip size="small">"1"</v-chip></template>
                <v-list-item-title>Healthcare Provider</v-list-item-title>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend><v-chip size="small">"1*1234"</v-chip></template>
                <v-list-item-title>Provider login with PIN</v-list-item-title>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend><v-chip size="small">"1*1234*2"</v-chip></template>
                <v-list-item-title>Provider → New Patient</v-list-item-title>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend><v-chip size="small">"2*1"</v-chip></template>
                <v-list-item-title>Patient → View Records</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-col>
          <v-col cols="12" md="6">
            <div class="text-h6 mb-3">Response Types:</div>
            <v-list density="compact">
              <v-list-item>
                <template v-slot:prepend><v-chip size="small" color="info">CON</v-chip></template>
                <v-list-item-title>Continue (more input needed)</v-list-item-title>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend><v-chip size="small" color="success">END</v-chip></template>
                <v-list-item-title>End session (final response)</v-list-item-title>
              </v-list-item>
            </v-list>
            
            <div class="text-h6 mb-3 mt-4">Tips:</div>
            <v-list density="compact">
              <v-list-item>
                <v-list-item-title>Use the quick test buttons for common scenarios</v-list-item-title>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>Change phone numbers to test different users</v-list-item-title>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>Monitor system logs for detailed activity</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Basic Phone Optimization Notice -->
    <v-alert type="info" variant="tonal" class="mt-6">
      <template v-slot:title>
        <v-icon>mdi-cellphone</v-icon>
        Basic Phone Optimization
      </template>
      
      This USSD system is optimized for basic feature phones commonly used in Ghana. 
      Messages are kept under 160 characters, menus are simplified, and navigation is straightforward 
      to ensure compatibility with all mobile devices.
    </v-alert>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue'
import apiService from '@/services/apiService'

export default {
  name: 'UssdTest',
  emits: ['loading', 'alert'],
  setup(props, { emit }) {
    const sessionId = ref(`test_session_${Date.now()}`)
    const phoneNumber = ref('+233200000000')
    const ussdText = ref('')
    const ussdResponse = ref('')
    const sending = ref(false)
    const ussdInput = ref(null)

    const phoneRules = [
      v => !!v || 'Phone number is required',
      v => apiService.validateGhanaPhone(v).valid || 'Invalid Ghana phone number format'
    ]

    const demoProviders = [
      { pin: '1234', name: 'Dr. Kwame Asante', specialty: 'General Medicine' },
      { pin: '5678', name: 'Dr. Ama Mensah', specialty: 'Pediatrics' },
      { pin: '9012', name: 'Dr. Kofi Boateng', specialty: 'Internal Medicine' }
    ]

    const demoPatients = [
      { phone: '0200123456', name: 'John Doe' },
      { phone: '0240234567', name: 'Jane Smith' },
      { phone: '0260345678', name: 'Kwame Osei' },
      { phone: '0270456789', name: 'Akosua Addo' }
    ]

    const testScenarios = [
      {
        title: 'Scenario 1: Provider Journey',
        steps: [
          'Start with empty text (main menu)',
          'Select "1" (provider login)',
          'Enter "1*1234" (login with PIN)',
          'Try "1*1234*2" (new patient)'
        ]
      },
      {
        title: 'Scenario 2: Patient Journey',
        steps: [
          'Use patient phone: 0200123456',
          'Select "2" (patient services)',
          'Try "2*1" (view records)',
          'Try "2*2" (emergency contact)'
        ]
      },
      {
        title: 'Scenario 3: Emergency',
        steps: [
          'Select "3" (emergency services)',
          'Try "3*1" (call ambulance)',
          'Try "3*3" (emergency info)'
        ]
      }
    ]

    const quickTest = (text) => {
      ussdText.value = text
      nextTick(() => {
        sendUssdRequest()
      })
    }

    const newSession = () => {
      sessionId.value = `test_session_${Date.now()}`
      ussdText.value = ''
      clearResponse()
    }

    const clearResponse = () => {
      ussdResponse.value = ''
    }

    const sendUssdRequest = async () => {
      try {
        sending.value = true
        
        const ussdData = {
          sessionId: sessionId.value,
          serviceCode: '*714#',
          phoneNumber: phoneNumber.value,
          text: ussdText.value || ''
        }

        console.log('Sending USSD request:', ussdData)
        
        const response = await apiService.sendUssdRequest(ussdData)
        
        const timestamp = new Date().toLocaleTimeString()
        ussdResponse.value = `[${timestamp}] USSD Response:\n\n${response}`
        
        emit('alert', {
          type: 'success',
          title: 'USSD Request Sent',
          message: 'Response received successfully'
        })

      } catch (error) {
        console.error('USSD request failed:', error)
        ussdResponse.value = `Error: ${error.message}`
        
        emit('alert', {
          type: 'error',
          title: 'USSD Request Failed',
          message: error.message
        })
      } finally {
        sending.value = false
      }
    }

    const copyResponse = async () => {
      try {
        await navigator.clipboard.writeText(ussdResponse.value)
        emit('alert', {
          type: 'success',
          title: 'Copied',
          message: 'Response copied to clipboard'
        })
      } catch (error) {
        emit('alert', {
          type: 'error',
          title: 'Copy Failed',
          message: 'Failed to copy response'
        })
      }
    }

    onMounted(() => {
      // Focus on USSD input
      nextTick(() => {
        if (ussdInput.value) {
          ussdInput.value.focus()
        }
      })
    })

    return {
      sessionId,
      phoneNumber,
      ussdText,
      ussdResponse,
      sending,
      ussdInput,
      phoneRules,
      demoProviders,
      demoPatients,
      testScenarios,
      quickTest,
      newSession,
      clearResponse,
      sendUssdRequest,
      copyResponse
    }
  }
}
</script>

<style scoped>
.hero-card {
  background: linear-gradient(135deg, rgba(25, 118, 210, 0.1), rgba(156, 39, 176, 0.1));
}

.simulator-card {
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

.demo-card {
  background: linear-gradient(135deg, rgba(227, 242, 253, 0.8), rgba(243, 229, 245, 0.8));
}

.quick-tests-card {
  background: linear-gradient(135deg, rgba(232, 245, 233, 0.8), rgba(241, 248, 233, 0.8));
}

.response-card {
  background: #f8f9fa;
  min-height: 200px;
}

.response-content {
  min-height: 150px;
}

.response-text {
  font-family: 'Roboto Mono', monospace;
  white-space: pre-wrap;
  margin: 0;
  padding: 1rem;
  background: white;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.v-btn-group {
  gap: 0.5rem;
}

.v-btn-group .v-btn {
  margin-bottom: 0.5rem;
}
</style>