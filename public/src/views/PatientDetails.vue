<template>
  <div>
    <v-card class="mb-6">
      <v-card-text class="text-center pa-8">
        <div class="text-h3 font-weight-bold text-success mb-4">
          <v-icon size="large" class="me-3">mdi-account</v-icon>
          Patient Details
        </div>
      </v-card-text>
    </v-card>
    <v-row justify="center">
      <v-col cols="12" md="8">
        <v-card elevation="2">
          <v-card-text>
            <div class="text-center py-12">
              <div class="text-h6 mb-4">Patient ID: {{ $route.params.id }}</div>
              <v-btn color="primary" @click="$router.push('/patients')">
                <v-icon start>mdi-arrow-left</v-icon>
                Back to Patients
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script>
export default {
  name: 'PatientDetails'
}
</script>
