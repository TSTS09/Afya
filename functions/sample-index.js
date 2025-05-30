const functions = require('firebase-functions');
const express = require('express');
const bodyParser = require('body-parser');
const app = express();
const firebase = require('firebase/app');
const { create } = require('lodash');
require('firebase/firestore');


app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));
const firebaseConfig = {
    apiKey: "AIzaSyB-7Gd_jCUUExp-h2DYlsEGwwnfAKzbeck",
    authDomain: "afya-a1006.firebaseapp.com",
    projectId: "afya-a1006",
    storageBucket: "afya-a1006.firebasestorage.app",
    messagingSenderId: "448798271887",
    appId: "1:448798271887:web:c7f04b6c63e3ae799a03fa",
    measurementId: "G-GWSPKP6TVT"
};
firebaseConfig.initializeApp(firebaseConfig);
const db = firebase.firestore();


appInit();
function appInit() {

    app.post('/ussd', (req, res) => {
        const { sessionId, serviceCode, phoneNumber, text } = req.body;
        let response = '';
        let account = '';

        if (text === '') {
            // First request
            response = `CON What would you like to check ? 
        1. Create Record 
        2. Update Record
        3. Read Record
        4. Delete Record 
        `;
        } else if (text === '1') {
            account = createRec();
        } else if (text === ('2')) {
            account = updateRec();
        } else if (text === ('3')) {
            account = readRec();
        } else if (text === ('4')) {
            account = deleteRec();
        } else if (text === '1*1') {
            // View patient records
            const accountNumber = '1234567890'; // This should be fetched from the database
            response = `END Your account number is ${accountNumber}`;
        } else if (text === '1*2') {
            // View account balance
            const accountBalance = 'GHC 1000'; // This should be fetched from the database
            response = `END Your account balance is ${accountBalance}`;
        }

        res.set('Content-Type', 'text/plain');
        res.send(response)
    })
    exports.ussd = functions.https.onRequest(app);
}

function createRec() {
    db.collection('afya')
        .add({
            name: 'John Doe',
            age: 30,
            condition: 'Healthy',
            createdAt: firebase.firestore.FieldValue.serverTimestamp()
        })
        .then(docRef => {
            console.log('Document written with ID: ', docRef.id);
            return docRef.id; // Return the document ID
        })
        .catch(error => {
            console.error('Error adding document: ', error);
            throw new Error('Error creating record');
        });
    response = `END Record created successfully.`;
    return response;
}
function updateRec() {

}
function deleteRec() {

}
function readRec() {

}
