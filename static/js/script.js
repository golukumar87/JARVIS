// JARVIS 3D GUI - Frontend JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // ========== GLOBAL VARIABLES ==========
    let socket = null;
    let isListening = false;
    let messageCount = 0;
    let startTime = Date.now();
    
    // ========== SOCKET.IO CONNECTION ==========
    function connectSocket() {
        socket = io();
        
        socket.on('connect', function() {
            showToast('Connected to JARVIS', 'success');
            updateConnectionStatus(true);
        });
        
        socket.on('disconnect', function() {
            showToast('Disconnected from JARVIS', 'error');
            updateConnectionStatus(false);
        });
        
        socket.on('status_update', function(data) {
            updateStatusCards(data);
        });
        
        socket.on('assistant_speak', function(data) {
            addMessage('jarvis', data.text);
            animateVoiceBars();
        });
        
        socket.on('user_speech', function(data) {
            addMessage('user', data.text);
        });
        
        socket.on('new_message', function(data) {
            addMessage(data.sender, data.text, data.time);
        });
        
        socket.on('listening_status', function(data) {
            updateListeningStatus(data.status);
        });
        
        socket.on('error', function(data) {
            showToast(data.message || 'An error occurred', 'error');
        });
    }
    
    // ========== UI UPDATES ==========
    function updateStatusCards(data) {
        if (data.mic) {
            document.getElementById('mic-status-text').textContent = data.mic;
        }
        if (data.ai) {
            document.getElementById('ai-status-text').textContent = data.ai;
        }
        if (data.connection) {
            document.getElementById('connection-status-text').textContent = data.connection;
        }
    }
    
    function updateConnectionStatus(connected) {
        const statusText = connected ? 'Online' : 'Offline';
        const statusDot = document.getElementById('connection-status-card').querySelector('.status-dot');
        
        document.getElementById('connection-status-text').textContent = statusText;
        statusDot.classList.toggle('active', connected);
    }
    
    function updateListeningStatus(listening) {
        isListening = listening;
        const micCard = document.getElementById('mic-status-card');
        const micText = document.getElementById('mic-status-text');
        const pulseDot = micCard.querySelector('.pulse-dot');
        
        if (listening) {
            micText.textContent = 'Listening...';
            pulseDot.style.animationPlayState = 'running';
            playSound('voiceStartSound');
        } else {
            micText.textContent = 'Active';
            pulseDot.style.animationPlayState = 'paused';
            if (isListening) {
                playSound('voiceEndSound');
            }
        }
    }
    
    function updateUptime() {
        const now = Date.now();
        const diff = now - startTime;
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);
        
        const uptimeElement = document.getElementById('uptime');
        if (uptimeElement) {
            uptimeElement.textContent = 
                `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
    }
    
    // ========== MESSAGES ==========
    function addMessage(sender, text, time = null) {
        const messagesContainer = document.getElementById('messagesContainer');
        const messageCountElement = document.getElementById('messageCount');
        const messageCountSide = document.getElementById('messageCountSide');
        
        if (!time) {
            const now = new Date();
            time = now.getHours().toString().padStart(2, '0') + ':' + 
                   now.getMinutes().toString().padStart(2, '0');
        }
        
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}-message`;
        
        const avatarIcon = sender === 'jarvis' ? 'fas fa-robot' : 'fas fa-user';
        const senderName = sender === 'jarvis' ? 'जार्विस' : 'आप';
        
        messageElement.innerHTML = `
            <div class="message-avatar">
                <i class="${avatarIcon}"></i>
            </div>
            <div class="message-content">
                <div class="message-sender">${senderName}</div>
                <div class="message-text">${text}</div>
                <div class="message-time">${time}</div>
            </div>
        `;
        
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        messageCount++;
        if (messageCountElement) {
            messageCountElement.textContent = `${messageCount} संदेश`;
        }
        if (messageCountSide) {
            messageCountSide.textContent = messageCount;
        }
    }
    
    // ========== VOICE VISUALIZER ==========
    function animateVoiceBars() {
        const bars = document.querySelectorAll('.visualizer-bars .bar');
        bars.forEach((bar, index) => {
            bar.style.animation = 'none';
            setTimeout(() => {
                bar.style.animation = `soundWave 1.5s ease-in-out ${index * 0.1}s infinite`;
            }, 10);
        });
        
        // Animate assistant avatar mouth
        const mouth = document.querySelector('.mouth');
        if (mouth) {
            mouth.style.animation = 'talk 0.5s ease-in-out 3';
            setTimeout(() => {
                mouth.style.animation = 'talk 2s infinite alternate';
            }, 1500);
        }
    }
    
    // ========== TOAST NOTIFICATIONS ==========
    function showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        toast.innerHTML = `
            <div class="toast-header">
                <i class="toast-icon ${icons[type]}"></i>
                <div class="toast-title">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
            </div>
            <div class="toast-message">${message}</div>
        `;
        
        toastContainer.appendChild(toast);
        playSound('notificationSound');
        
        // Remove toast after 3 seconds
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
    
    // ========== SOUND FUNCTIONS ==========
    function playSound(soundId) {
        const sound = document.getElementById(soundId);
        if (sound) {
            sound.currentTime = 0;
            sound.play().catch(e => console.log('Audio play failed:', e));
        }
    }
    
    // ========== EVENT HANDLERS ==========
    function setupEventListeners() {
        // Start/Stop Listening buttons
        document.getElementById('startListeningBtn').addEventListener('click', function() {
            if (socket) {
                socket.emit('start_listening');
                showToast('Listening started. Speak now...', 'info');
            }
        });
        
        document.getElementById('stopListeningBtn').addEventListener('click', function() {
            if (socket) {
                socket.emit('stop_listening');
                showToast('Listening stopped', 'info');
            }
        });
        
        // Clear chat button
        document.getElementById('clearChatBtn').addEventListener('click', function() {
            const messagesContainer = document.getElementById('messagesContainer');
            const welcomeMessage = messagesContainer.querySelector('.welcome-message');
            
            messagesContainer.innerHTML = '';
            if (welcomeMessage) {
                messagesContainer.appendChild(welcomeMessage);
            }
            
            messageCount = 0;
            document.getElementById('messageCount').textContent = '0 संदेश';
            document.getElementById('messageCountSide').textContent = '0';
            
            if (socket) {
                socket.emit('clear_conversation');
            }
            
            showToast('Chat cleared', 'success');
        });
        
        // Help button
        document.getElementById('helpBtn').addEventListener('click', function() {
            const helpMessage = `
                <strong>उपलब्ध कमांड्स:</strong><br>
                • समय बताओ - वर्तमान समय<br>
                • तारीख बताओ - आज की तारीख<br>
                • मौसम बताओ - मौसम जानकारी<br>
                • खबर बताओ - ताजा खबरें<br>
                • मजाक सुनाओ - मजाक सुनें<br>
                • यूट्यूब खोलो - YouTube खोलें<br>
                • गूगल खोलो - Google खोलें<br>
                • स्क्रीनशॉट लो - स्क्रीनशॉट लें<br>
                • ईमेल भेजो - ईमेल भेजें<br><br>
                <strong>एक्टिवेशन वर्ड:</strong> "Hello Raj" या "जार्विस"
            `;
            addMessage('jarvis', helpMessage);
            showToast('Help information displayed', 'info');
        });
        
        // Quick action buttons
        document.querySelectorAll('.action-btn').forEach(button => {
            button.addEventListener('click', function() {
                const command = this.getAttribute('data-command');
                if (socket && command) {
                    socket.emit('quick_command', { command: command });
                    showToast(`Command sent: ${command}`, 'info');
                }
            });
        });
        
        // Message input
        const messageInput = document.getElementById('messageInput');
        const sendMessageBtn = document.getElementById('sendMessageBtn');
        const voiceInputBtn = document.getElementById('voiceInputBtn');
        
        sendMessageBtn.addEventListener('click', sendMessage);
        
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        voiceInputBtn.addEventListener('click', function() {
            if (socket) {
                if (!isListening) {
                    socket.emit('start_listening');
                    showToast('Listening started. Speak now...', 'info');
                } else {
                    socket.emit('stop_listening');
                    showToast('Listening stopped', 'info');
                }
            }
        });
        
        // Spacebar for voice input
        document.addEventListener('keydown', function(e) {
            if (e.code === 'Space' && document.activeElement !== messageInput) {
                e.preventDefault();
                if (socket && !isListening) {
                    socket.emit('start_listening');
                    showToast('Listening started. Speak now...', 'info');
                }
            }
        });
        
        // Footer buttons
        document.getElementById('githubBtn').addEventListener('click', function() {
            window.open('https://github.com', '_blank');
        });
        
        document.getElementById('docsBtn').addEventListener('click', function() {
            showToast('Documentation coming soon!', 'info');
        });
        
        document.getElementById('settingsBtn').addEventListener('click', function() {
            showToast('Settings panel coming soon!', 'info');
        });
    }
    
    function sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (message && socket) {
            socket.emit('voice_command', { command: message });
            messageInput.value = '';
            showToast('Message sent', 'success');
        } else if (!message) {
            showToast('Please enter a message', 'warning');
        }
    }
    
    // ========== INITIALIZATION ==========
    function init() {
        connectSocket();
        setupEventListeners();
        
        // Start uptime counter
        setInterval(updateUptime, 1000);
        
        // Add initial message
        setTimeout(() => {
            addMessage('jarvis', 'राधे राधे! मैं जार्विस आपकी सेवा में हूं। बोलें "Hello Raj" या "जार्विस" सुनने के लिए।');
        }, 1000);
        
        // Check email status
        setTimeout(() => {
            const emailStatusDot = document.getElementById('emailStatusDot');
            const emailStatusText = document.getElementById('emailStatusText');
            if (emailStatusDot && emailStatusText) {
                emailStatusDot.classList.add('active');
                emailStatusText.textContent = 'Configured';
            }
        }, 2000);
        
        console.log('JARVIS 3D GUI Initialized');
    }
    
    // ========== START APPLICATION ==========
    init();
});