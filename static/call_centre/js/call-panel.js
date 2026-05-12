/**
 * Call Panel JavaScript
 * Operator ekrani uchun barcha funksiyalar
 */

// Global variables
let currentCall = null;
let callTimer = null;
let callStartTime = null;
let isMuted = false;
let isOnHold = false;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadAgentStats();
    setupStatusChangeListener();
    
    // Load stats every 30 seconds
    setInterval(loadAgentStats, 30000);
});

// Dial Pad Functions
function dialNumber(digit) {
    const input = document.getElementById('phone-input');
    let currentValue = input.value;
    
    // Initialize with +998 if empty
    if (!currentValue) {
        currentValue = '+998';
    }
    
    input.value = currentValue + digit;
}

function clearNumber() {
    document.getElementById('phone-input').value = '+998';
}

function makeCall() {
    const phoneNumber = document.getElementById('phone-input').value;
    
    if (!phoneNumber || phoneNumber === '+998') {
        alert('Iltimos, telefon raqamini kiriting');
        return;
    }
    
    // Send AJAX request to initiate call
    fetch('/enrollment/call/initiate/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: `to_number=${encodeURIComponent(phoneNumber)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            startCall(data.call_id, phoneNumber);
            clearNumber();
        } else {
            alert('Xatolik: ' + (data.error || 'Qo\'ng\'iroq amalga oshmadi'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Qo\'ng\'iroq amalga oshmadi');
    });
}

// Incoming Call Functions
function handleIncomingCall(data) {
    const notification = document.getElementById('incoming-call-notification');
    document.getElementById('incoming-caller-number').textContent = data.caller_number;
    document.getElementById('incoming-caller-name').textContent = data.lead_name || 'Noma\'lum';
    
    notification.classList.remove('hidden');
    
    // Play ringtone (optional)
    playRingtone();
    
    // Store call data
    currentCall = {
        id: data.call_id,
        caller_number: data.caller_number,
        lead_name: data.lead_name
    };
}

function acceptCall() {
    if (!currentCall) return;
    
    // Hide notification
    document.getElementById('incoming-call-notification').classList.add('hidden');
    stopRingtone();
    
    // Start call
    startCall(currentCall.id, currentCall.caller_number, currentCall.lead_name);
    
    // Send accept request
    fetch(`/enrollment/call/${currentCall.id}/accept/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    });
}

function rejectCall() {
    if (!currentCall) return;
    
    // Hide notification
    document.getElementById('incoming-call-notification').classList.add('hidden');
    stopRingtone();
    
    // Send reject request
    fetch(`/enrollment/call/${currentCall.id}/reject/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    });
    
    currentCall = null;
}

// Active Call Functions
function startCall(callId, phoneNumber, leadName = null) {
    currentCall = {
        id: callId,
        caller_number: phoneNumber,
        lead_name: leadName
    };
    
    // Show active call card
    document.getElementById('active-call-card').classList.remove('hidden');
    document.getElementById('active-caller-number').textContent = phoneNumber;
    
    // Load customer info
    if (leadName) {
        loadCustomerInfo(phoneNumber);
    }
    
    // Start timer
    callStartTime = Date.now();
    startCallTimer();
}

function endCall() {
    if (!currentCall) return;
    
    // Send end call request
    fetch('/enrollment/call/end/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: `call_sid=local_${currentCall.id}`
    })
    .then(() => {
        stopCall();
    });
}

function stopCall() {
    // Hide active call card
    document.getElementById('active-call-card').classList.add('hidden');
    document.getElementById('customer-info-card').classList.add('hidden');
    
    // Stop timer
    stopCallTimer();
    
    // Reset state
    currentCall = null;
    isMuted = false;
    isOnHold = false;
    
    // Reload stats
    loadAgentStats();
}

function startCallTimer() {
    callTimer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - callStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        document.getElementById('call-duration').textContent = 
            `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }, 1000);
}

function stopCallTimer() {
    if (callTimer) {
        clearInterval(callTimer);
        callTimer = null;
    }
    document.getElementById('call-duration').textContent = '00:00';
}

function toggleMute() {
    isMuted = !isMuted;
    const btn = document.getElementById('mute-btn');
    
    if (isMuted) {
        btn.classList.add('bg-red-500', 'text-white');
        btn.classList.remove('bg-gray-200');
        btn.querySelector('i').classList.replace('fa-microphone', 'fa-microphone-slash');
    } else {
        btn.classList.remove('bg-red-500', 'text-white');
        btn.classList.add('bg-gray-200');
        btn.querySelector('i').classList.replace('fa-microphone-slash', 'fa-microphone');
    }
}

function toggleHold() {
    isOnHold = !isOnHold;
    const btn = document.getElementById('hold-btn');
    
    if (isOnHold) {
        btn.classList.add('bg-yellow-500', 'text-white');
        btn.classList.remove('bg-gray-200');
        btn.querySelector('i').classList.replace('fa-pause', 'fa-play');
    } else {
        btn.classList.remove('bg-yellow-500', 'text-white');
        btn.classList.add('bg-gray-200');
        btn.querySelector('i').classList.replace('fa-play', 'fa-pause');
    }
}

function openDialPad() {
    // Show dial pad in modal (optional feature)
    alert('DTMF dial pad - keyingi versiyada');
}

// Customer Info Functions
function loadCustomerInfo(phoneNumber) {
    fetch(`/enrollment/api/customer-info/?phone=${encodeURIComponent(phoneNumber)}`)
        .then(response => response.json())
        .then(data => {
            if (data.found) {
                document.getElementById('customer-info-card').classList.remove('hidden');
                document.getElementById('customer-name').textContent = data.name || '-';
                document.getElementById('customer-phone').textContent = data.phone || '-';
                document.getElementById('customer-region').textContent = data.region || '-';
                document.getElementById('customer-children').textContent = data.children_count || '-';
                document.getElementById('customer-grade').textContent = data.interested_grade || '-';
                document.getElementById('customer-last-call').textContent = data.last_call || '-';
            }
        })
        .catch(error => console.error('Error loading customer info:', error));
}

function saveCallNotes() {
    if (!currentCall) return;
    
    const notes = document.getElementById('call-notes').value;
    
    fetch(`/enrollment/call/${currentCall.id}/notes/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: `notes=${encodeURIComponent(notes)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            alert('Eslatma saqlandi');
            document.getElementById('call-notes').value = '';
        }
    });
}

// Agent Status Functions
function setupStatusChangeListener() {
    const statusSelect = document.getElementById('status-select');
    statusSelect.addEventListener('change', function() {
        updateAgentStatus(this.value);
    });
}

function updateAgentStatus(status) {
    // Send via WebSocket
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'agent_status_update',
            status: status
        }));
    }
    
    // Also send via HTTP
    fetch('/enrollment/agent/status/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: `status=${status}`
    });
}

function loadAgentStats() {
    fetch('/enrollment/api/agent-stats/')
        .then(response => response.json())
        .then(data => {
            document.getElementById('calls-today').textContent = data.calls_today || 0;
            document.getElementById('answered-today').textContent = data.answered_today || 0;
            document.getElementById('missed-today').textContent = data.missed_today || 0;
        })
        .catch(error => console.error('Error loading stats:', error));
}

// Audio Player Functions
function playRecording(url) {
    const modal = document.getElementById('audio-player-modal');
    const audioSource = document.getElementById('audio-source');
    const audioPlayer = document.getElementById('audio-player');
    
    audioSource.src = url;
    audioPlayer.load();
    modal.classList.remove('hidden');
}

function closeAudioPlayer() {
    const modal = document.getElementById('audio-player-modal');
    const audioPlayer = document.getElementById('audio-player');
    
    audioPlayer.pause();
    modal.classList.add('hidden');
}

// Ringtone Functions
let ringtoneAudio = null;

function playRingtone() {
    // Create audio element for ringtone
    if (!ringtoneAudio) {
        ringtoneAudio = new Audio('/static/call_centre/sounds/ringtone.mp3');
        ringtoneAudio.loop = true;
    }
    ringtoneAudio.play().catch(e => console.log('Ringtone play failed:', e));
}

function stopRingtone() {
    if (ringtoneAudio) {
        ringtoneAudio.pause();
        ringtoneAudio.currentTime = 0;
    }
}

// WebSocket Message Handlers
function handleCallStatusUpdate(data) {
    if (currentCall && currentCall.id === data.call_id) {
        if (data.status === 'completed' || data.status === 'failed') {
            stopCall();
        }
    }
}

// Utility Functions
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl + Enter to make call
    if (e.ctrlKey && e.key === 'Enter') {
        makeCall();
    }
    
    // Escape to end call
    if (e.key === 'Escape' && currentCall) {
        endCall();
    }
});
