import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

// ONLY REPLACE THE VALUES INSIDE THE QUOTES
const firebaseConfig = {
    apiKey: "AIzaSyDidOEZcXrgLIDTURGbHIWs0HjZG4ZajWc",
    authDomain: "sportsguard-ai.firebaseapp.com",
    projectId: "sportsguard-ai",
    storageBucket: "sportsguard-ai.firebasestorage.app",
    messagingSenderId: "52294715882",
    appId: "1:52294715882:web:b28c1ad54ccdce1e6a0a93"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firestore and export it so App.jsx can use it
export const db = getFirestore(app);