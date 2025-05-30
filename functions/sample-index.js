const functions = require('firebase-functions');
const express = require('express');
const bodyParser = require('body-parser');
const app = express();
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));
app.post('/ussd', (req, res) => {
    const { sessionId, serviceCode, phoneNumber, text } = req.body;
    let response = '';
    
    if (text === '') {
        // First request
        response = `CON What would you like to check ? 
        1. My Account 
        2. My Phone Number 
        `;
    } else if (text === '1') {
        // Register a new patient
        response = `Con choose account information you want to view 
        1. Account Number 
        2. Account balance `;
    } else if (text === ('2')) {
        // Get the mobile number from Firestore Database 
        response = `END Your phone number is ${phoneNumber}`;
    } else if (text === '1*1') {
        // View patient records
        const accountNumber = '1234567890'; // This should be fetched from the database
        response = `END Your account number is ${accountNumber}`;
    } else if (text === '1*2') {
        // View account balance
        const accountBalance = 'KES 1000'; // This should be fetched from the database
        response = `END Your account balance is ${accountBalance}`;
    }
    
    res.set('Content-Type', 'text/plain');
    res.send(response)
})

exports.ussd = functions.https.onRequest(app);