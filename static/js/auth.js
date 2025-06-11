import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js';
import { 
    getAuth, 
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    signOut,
    onAuthStateChanged 
} from 'https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js';

const firebaseConfig = {
    apiKey: "AIzaSyBjvprd8WUgODpOkDeJ_GKoEczvdjtWgL8",
    authDomain: "newp-b1e94.firebaseapp.com",
    projectId: "newp-b1e94",
    storageBucket: "newp-b1e94.firebasestorage.app",
    messagingSenderId: "237376629362",
    appId: "1:237376629362:web:088b1b131da1b4e74970eb",
    measurementId: "G-E2FFK6NF8M"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth();

// Handle signup form submission
export function handleSignup(email, password) {
    // Check if the email is already registered
    return fetch('/check-email', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: email })
    })
    .then(response => response.json())
    .then(data => {
        if (data.exists) {
            throw new Error('Email already registered');
        } else {
            // Proceed with signup if email is not registered
            return createUserWithEmailAndPassword(auth, email, password);
        }
    })
    .then((userCredential) => {
        return userCredential.user.getIdToken();
    })
    .then((idToken) => {
        return fetch('/session-login', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${idToken}`
            }
        });
    })
    .then((response) => {
        if (response.ok) {
            window.location.href = '/dashboard';
        } else {
            throw new Error('Session login failed');
        }
    })
    .catch((error) => {
        console.error('Error during signup:', error);
        alert('Signup failed: ' + error.message);
    });
}

// Handle login form submission with enhanced error handling
export async function handleLogin(email, password) {
    const errorElement = document.getElementById('login-error');
    
    try {
        // First try regular form login
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await response.json();
        
        if (data.success) {
            window.location.href = data.redirect || '/dashboard';
            return;
        }
        
        throw new Error(data.error || 'Login failed');
    } catch (error) {
        console.error('Login error:', error);
        if (errorElement) {
            errorElement.textContent = error.message;
            errorElement.style.display = 'block';
        }
        throw error;
    }
}

// Handle logout
document.getElementById('logoutBtn')?.addEventListener('click', () => {
    signOut(auth).then(() => {
        fetch('/logout').then(() => {
            window.location.href = '/';
        });
    }).catch((error) => {
        console.error('Error during logout:', error);
        alert('Logout failed: ' + error.message);
    });
});