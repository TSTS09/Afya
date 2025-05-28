<template>
  <div class="not-found-container">
    <v-container class="fill-height">
      <v-row align="center" justify="center">
        <v-col cols="12" sm="8" md="6" class="text-center">
          <!-- 404 Icon -->
          <div class="error-icon mb-6">
            <v-icon size="120" color="primary">mdi-hospital-building</v-icon>
            <div class="error-code">404</div>
          </div>

          <!-- Error Message -->
          <h1 class="text-h3 font-weight-bold text-primary mb-4">
            Page Not Found
          </h1>
          
          <p class="text-h6 text-medium-emphasis mb-6">
            The page you're looking for doesn't exist in the Afya Medical EHR system.
          </p>

          <!-- Helpful Links -->
          <v-card variant="outlined" class="mx-auto mb-6" max-width="400">
            <v-card-title class="text-center">
              <v-icon class="me-2">mdi-compass</v-icon>
              Where would you like to go?
            </v-card-title>
            <v-card-text>
              <v-list density="compact">
                <v-list-item @click="$router.push('/')">
                  <template v-slot:prepend>
                    <v-icon>mdi-view-dashboard</v-icon>
                  </template>
                  <v-list-item-title>Dashboard</v-list-item-title>
                  <v-list-item-subtitle>System overview and statistics</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item @click="$router.push('/patients')">
                  <template v-slot:prepend>
                    <v-icon>mdi-account-group</v-icon>
                  </template>
                  <v-list-item-title>Patients</v-list-item-title>
                  <v-list-item-subtitle>View patient records</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item @click="$router.push('/providers')">
                  <template v-slot:prepend>
                    <v-icon>mdi-doctor</v-icon>
                  </template>
                  <v-list-item-title>Providers</v-list-item-title>
                  <v-list-item-subtitle>Healthcare providers</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item @click="$router.push('/ussd-test')">
                  <template v-slot:prepend>
                    <v-icon>mdi-cellphone</v-icon>
                  </template>
                  <v-list-item-title>USSD Test</v-list-item-title>
                  <v-list-item-subtitle>Test USSD functionality</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>

          <!-- Action Buttons -->
          <div class="action-buttons">
            <v-btn 
              color="primary" 
              size="large" 
              @click="$router.push('/')"
              class="me-4"
            >
              <v-icon start>mdi-home</v-icon>
              Go to Dashboard
            </v-btn>
            
            <v-btn 
              variant="outlined" 
              size="large" 
              @click="goBack"
            >
              <v-icon start>mdi-arrow-left</v-icon>
              Go Back
            </v-btn>
          </div>

          <!-- USSD Information -->
          <v-alert 
            type="info" 
            variant="tonal" 
            class="mt-6 mx-auto" 
            max-width="500"
          >
            <template v-slot:title>
              <v-icon>mdi-cellphone</v-icon>
              USSD Access Available
            </template>
            
            For basic phone access without internet, dial <strong>*714#</strong> from any mobile phone in Ghana.
          </v-alert>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script>
export default {
  name: 'NotFound',
  methods: {
    goBack() {
      // Go back to previous page or dashboard if no history
      if (window.history.length > 1) {
        this.$router.go(-1)
      } else {
        this.$router.push('/')
      }
    }
  },
  mounted() {
    // Update document title
    document.title = '404 - Page Not Found | Afya Medical EHR'
  }
}
</script>

<style scoped>
.not-found-container {
  min-height: 100vh;
  background: linear-gradient(135deg, rgba(46, 139, 87, 0.05), rgba(32, 178, 170, 0.05));
}

.error-icon {
  position: relative;
  display: inline-block;
}

.error-code {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 2.5rem;
  font-weight: bold;
  color: #2E8B57;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
}

.action-buttons {
  margin-top: 2rem;
}

.v-list-item {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.v-list-item:hover {
  background-color: rgba(46, 139, 87, 0.1);
}
</style>