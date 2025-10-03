// BLACK BOX UI - Client-Side JavaScript
// Handles voice interaction, quick actions, and system status

// Configuration
const ORCHESTRATOR_URL = 'http://localhost:8000';
const AUDIO_RECORDING_TIMEOUT = 30000; // 30 seconds max
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

// DOM Elements
const voiceButton = document.getElementById('voice-button');
const feedbackText = document.getElementById('feedback-text');
const transcriptionSection = document.getElementById('transcription-section');
const transcriptionText = document.getElementById('transcription-text');
const responseSection = document.getElementById('response-section');
const responseText = document.getElementById('response-text');
const loadingOverlay = document.getElementById('loading-overlay');
const statusText = document.querySelector('.status-text');
const thermalStatus = document.getElementById('thermal-status');
const uptimeDisplay = document.getElementById('uptime');

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('BLACK BOX UI initialized');
    
    // Set up voice button
    voiceButton.addEventListener('click', handleVoiceButtonClick);
    
    // Start periodic status updates
    updateSystemStatus();
    setInterval(updateSystemStatus, 10000); // Every 10 seconds
    
    // Check browser compatibility
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showError('Your browser does not support audio recording. Please use a modern browser.');
    }
});

// ============================================================================
// Voice Interaction
// ============================================================================

async function handleVoiceButtonClick() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

async function startRecording() {
    try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // Create media recorder
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.addEventListener('dataavailable', event => {
            audioChunks.push(event.data);
        });
        
        mediaRecorder.addEventListener('stop', async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            await processVoiceInput(audioBlob);
            
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
        });
        
        // Start recording
        mediaRecorder.start();
        isRecording = true;
        
        // Update UI
        voiceButton.classList.add('recording');
        voiceButton.querySelector('.button-text').textContent = 'LISTENING...';
        feedbackText.textContent = 'Listening... Click again when done speaking';
        statusText.textContent = 'Recording';
        
        // Auto-stop after timeout
        setTimeout(() => {
            if (isRecording) {
                stopRecording();
            }
        }, AUDIO_RECORDING_TIMEOUT);
        
    } catch (error) {
        console.error('Failed to start recording:', error);
        showError('Could not access microphone. Please check permissions.');
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        
        // Update UI
        voiceButton.classList.remove('recording');
        voiceButton.querySelector('.button-text').textContent = 'PROCESSING...';
        feedbackText.textContent = 'Processing your request...';
    }
}

async function processVoiceInput(audioBlob) {
    try {
        // Show loading
        showLoading();
        
        // Convert blob to base64
        const audioBase64 = await blobToBase64(audioBlob);
        
        // Send to orchestrator
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        formData.append('user_id', 'default_user');
        
        const response = await fetch(`${ORCHESTRATOR_URL}/voice/interact`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Request failed: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Display results
        displayTranscription(result.transcription);
        displayResponse(result.response_text);
        
        // Play audio response if available
        if (result.audio_url) {
            // TODO: Play audio response
        }
        
        // Show timing info
        console.log('Pipeline timing:', result.timing);
        
        // Reset UI
        resetVoiceButton();
        hideLoading();
        
    } catch (error) {
        console.error('Voice processing failed:', error);
        showError('Failed to process your request. Please try again.');
        resetVoiceButton();
        hideLoading();
    }
}

// ============================================================================
// Quick Actions
// ============================================================================

function handleQuickAction(action) {
    console.log('Quick action:', action);
    
    switch (action) {
        case 'reminders':
            showReminders();
            break;
        case 'media':
            sendTextQuery('Play my music');
            break;
        case 'vault':
            showVault();
            break;
        case 'time':
            sendTextQuery('What time is it?');
            break;
    }
}

async function sendTextQuery(text) {
    try {
        showLoading();
        
        const response = await fetch(`${ORCHESTRATOR_URL}/text/interact`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                user_id: 'default_user'
            })
        });
        
        if (!response.ok) {
            throw new Error(`Request failed: ${response.status}`);
        }
        
        const result = await response.json();
        
        displayTranscription(text);
        displayResponse(result.response_text);
        
        hideLoading();
        
    } catch (error) {
        console.error('Text query failed:', error);
        showError('Failed to process your request.');
        hideLoading();
    }
}

async function showReminders() {
    try {
        const response = await fetch(`${ORCHESTRATOR_URL}/reminders/default_user`);
        if (!response.ok) {
            throw new Error('Failed to fetch reminders');
        }
        
        const reminders = await response.json();
        
        // Display reminders
        let message = 'Your reminders:\n\n';
        if (reminders.length === 0) {
            message = 'You have no reminders set.';
        } else {
            reminders.forEach((reminder, index) => {
                message += `${index + 1}. ${reminder.title}\n   Due: ${reminder.due_date}\n\n`;
            });
        }
        
        showModal('My Reminders', message);
        
    } catch (error) {
        console.error('Failed to load reminders:', error);
        showError('Could not load reminders.');
    }
}

function showVault() {
    showModal('Secure Vault', 'Vault access requires voice authentication. Please say "Open my vault" using the voice button.');
}

// ============================================================================
// UI Updates
// ============================================================================

function displayTranscription(text) {
    transcriptionText.textContent = text;
    transcriptionSection.style.display = 'block';
}

function displayResponse(text) {
    responseText.textContent = text;
    responseSection.style.display = 'block';
}

function resetVoiceButton() {
    voiceButton.querySelector('.button-text').textContent = 'PRESS TO SPEAK';
    feedbackText.textContent = 'Press the button and speak your request';
    statusText.textContent = 'Ready';
}

function showLoading() {
    loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
}

function showModal(title, message) {
    const modal = document.getElementById('confirmation-modal');
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-message').textContent = message;
    modal.style.display = 'flex';
}

function closeModal() {
    document.getElementById('confirmation-modal').style.display = 'none';
}

function showError(message) {
    showModal('Error', message);
}

// ============================================================================
// System Status
// ============================================================================

async function updateSystemStatus() {
    try {
        const response = await fetch(`${ORCHESTRATOR_URL}/health`);
        if (!response.ok) {
            throw new Error('Health check failed');
        }
        
        const health = await response.json();
        
        // Update thermal status
        const thermal = health.thermal;
        if (thermal && thermal.max_temperature) {
            const temp = Math.round(thermal.max_temperature);
            const state = thermal.state;
            
            let icon = '🌡️';
            let status = 'Normal';
            
            if (state === 'warning') {
                icon = '⚠️';
                status = 'Warm';
            } else if (state === 'critical') {
                icon = '🔥';
                status = 'Hot';
            }
            
            thermalStatus.textContent = `${icon} ${status} (${temp}°C)`;
        }
        
        // Update uptime
        if (health.uptime_seconds) {
            const hours = Math.floor(health.uptime_seconds / 3600);
            const minutes = Math.floor((health.uptime_seconds % 3600) / 60);
            uptimeDisplay.textContent = `⏱️ Uptime: ${hours}h ${minutes}m`;
        }
        
        // Update overall status
        if (health.status === 'healthy') {
            document.querySelector('.status-dot').style.background = 'var(--primary-color)';
            statusText.textContent = 'Ready';
            statusText.style.color = 'var(--primary-color)';
        } else {
            document.querySelector('.status-dot').style.background = 'var(--danger-color)';
            statusText.textContent = 'Degraded';
            statusText.style.color = 'var(--danger-color)';
        }
        
    } catch (error) {
        console.error('Failed to update system status:', error);
        // Don't show error to user for status updates
    }
}

// ============================================================================
// Utilities
// ============================================================================

function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result.split(',')[1]);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}

// ============================================================================
// Keyboard Shortcuts
// ============================================================================

document.addEventListener('keydown', (event) => {
    // Space bar to activate voice
    if (event.code === 'Space' && !isRecording) {
        event.preventDefault();
        startRecording();
    }
    
    // Escape to stop recording
    if (event.code === 'Escape' && isRecording) {
        event.preventDefault();
        stopRecording();
    }
});

