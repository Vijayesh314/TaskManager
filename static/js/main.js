// API Base URL
const API_BASE = '';

// State
let userData = null;
let tasks = [];

// Shop items - must match backend
const SHOP_ITEMS = {
    'mountain_boots': { name: 'Mountain Boots', cost: 100, icon: 'fa-hiking', description: 'Sturdy boots for mountain climbing' },
    'backpack': { name: 'Adventure Backpack', cost: 150, icon: 'fa-backpack', description: 'A spacious backpack for your journey' },
    'compass': { name: 'Golden Compass', cost: 200, icon: 'fa-compass', description: 'Never lose your way' },
    'rope': { name: 'Magic Rope', cost: 125, icon: 'fa-rope', description: 'Strong and lightweight climbing rope' },
    'map': { name: 'Ancient Map', cost: 175, icon: 'fa-map', description: 'Reveals hidden mountain paths' },
    'water_bottle': { name: 'Enchanted Water Bottle', cost: 100, icon: 'fa-bottle-water', description: 'Never runs empty' },
    'first_aid': { name: 'Healer\'s Kit', cost: 150, icon: 'fa-briefcase-medical', description: 'For magical healing' },
    'tent': { name: 'Cloud Tent', cost: 250, icon: 'fa-campground', description: 'A cozy shelter in the mountains' }
};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadUserData();
    loadTasks();
    
    // Setup form handler
    document.getElementById('taskForm').addEventListener('submit', handleTaskSubmit);
    // Settings button and form handlers (if present)
    const settingsBtn = document.getElementById('settingsBtn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', () => {
            openSettingsModal();
        });
    }

    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', saveSettings);
    }

    const uploadBtn = document.getElementById('uploadAvatarBtn');
    if (uploadBtn) {
        uploadBtn.addEventListener('click', uploadAvatar);
    }

    // Load existing settings to populate the modal
    loadSettings();
    
    // Check for notifications every minute
    setInterval(checkNotifications, 60000);
    // Load and apply theme preference
    loadTheme();
    // Inject theme switcher UI
    injectThemeSwitcher();
});

// Theme functions
async function loadTheme(){
    try{
        const resp = await fetch(`${API_BASE}/api/theme`);
        const data = await resp.json();
        if(data && data.theme){
            applyTheme(data.theme);
        }
    } catch(e){
        console.warn('Could not load theme:', e);
    }
}

function applyTheme(theme){
    if(!theme) theme = 'light';
    document.documentElement.setAttribute('data-theme', theme);
    // update select if present
    const sel = document.getElementById('theme-select');
    if(sel) sel.value = theme;
}

async function saveTheme(theme){
    try{
        const resp = await fetch(`${API_BASE}/api/theme`, {
            method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({theme})
        });
        if(resp.ok){
            applyTheme(theme);
            showNotification('Theme updated', 'success');
        } else {
            const data = await resp.json();
            showNotification(data.error || 'Failed to save theme', 'error');
        }
    } catch(e){
        showNotification('Network error saving theme', 'error');
    }
}

function injectThemeSwitcher(){
    const wrapper = document.createElement('div');
    wrapper.style.position = 'fixed';
    wrapper.style.right = '16px';
    wrapper.style.bottom = '16px';
    wrapper.style.zIndex = '9999';
    wrapper.style.display = 'flex';
    wrapper.style.gap = '8px';
    wrapper.style.alignItems = 'center';

    const select = document.createElement('select');
    select.id = 'theme-select';
    select.style.padding = '8px';
    select.style.borderRadius = '8px';
    select.style.border = '1px solid rgba(0,0,0,0.1)';
    select.innerHTML = `
        <option value="light">Light</option>
        <option value="dark">Dark</option>
        <option value="solar">Solar</option>
        <option value="midnight">Midnight</option>
        <option value="pastel">Pastel</option>
    `;

    const btn = document.createElement('button');
    btn.textContent = 'Apply';
    btn.className = 'btn btn-small';
    btn.style.padding = '8px 10px';
    btn.onclick = () => saveTheme(select.value);

    wrapper.appendChild(select);
    wrapper.appendChild(btn);
    document.body.appendChild(wrapper);
}

// Load user data
async function loadUserData() {
    try {
        const response = await fetch(`${API_BASE}/api/user`);
        const data = await response.json();
        userData = data.user;
        updateUserStats(data);
        updateBadges();
        updateShop();
    } catch (error) {
        console.error('Error loading user data:', error);
        showNotification('Error loading user data', 'error');
    }
}

// Update user stats display
function updateUserStats(data) {
    document.getElementById('userLevel').textContent = data.user.level;
    document.getElementById('userXP').textContent = data.user.xp;
    document.getElementById('userCoins').textContent = data.user.coins;
    document.getElementById('userStreak').textContent = data.user.streak;
    
    // Update XP bar
    const xpBarFill = document.getElementById('xpBarFill');
    const xpProgressText = document.getElementById('xpProgressText');
    xpBarFill.style.width = `${data.xp_percentage}%`;
    xpProgressText.textContent = `${data.xp_progress} / ${data.xp_needed} XP`;
}

// Load tasks
async function loadTasks() {
    try {
        const response = await fetch(`${API_BASE}/api/tasks`);
        const data = await response.json();
        tasks = data.tasks;
        renderTasks();
    } catch (error) {
        console.error('Error loading tasks:', error);
        showNotification('Error loading tasks', 'error');
    }
}

// Render tasks
function renderTasks() {
    const tasksList = document.getElementById('tasksList');
    
    if (tasks.length === 0) {
        tasksList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📝</div>
                <div class="empty-state-text">No tasks yet. Create your first task to get started!</div>
            </div>
        `;
        return;
    }
    
    tasksList.innerHTML = tasks.map(task => createTaskHTML(task)).join('');
    
    // Add event listeners
    tasks.forEach(task => {
        const completeBtn = document.getElementById(`complete-${task.id}`);
        const deleteBtn = document.getElementById(`delete-${task.id}`);
        
        if (completeBtn) {
            completeBtn.addEventListener('click', () => completeTask(task.id));
        }
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => deleteTask(task.id));
        }
    });
}

// Create task HTML
function createTaskHTML(task) {
    const today = new Date().toISOString().split('T')[0];
    const isCompletedToday = task.completed_dates && task.completed_dates.includes(today);
    const completedClass = isCompletedToday ? 'completed' : '';
    
    return `
        <div class="task-item ${completedClass}" id="task-${task.id}">
            <div class="task-header">
                <div class="task-title">${escapeHtml(task.title)}</div>
                ${task.streak > 0 ? `<div class="task-streak">🔥 ${task.streak} day streak</div>` : ''}
            </div>
            ${task.description ? `<div class="task-description">${escapeHtml(task.description)}</div>` : ''}
            <div class="task-meta">
                ${task.recurring ? `<span>🔄 ${task.frequency}</span>` : '<span>📌 One-time</span>'}
                ${task.scheduled_time ? `<span>⏰ ${task.scheduled_time}</span>` : ''}
            </div>
            <div class="task-rewards">
                <span class="reward-badge">⭐ ${task.xp_reward} XP</span>
                <span class="reward-badge coin">💰 ${task.coin_reward} Coins</span>
            </div>
            <div class="task-actions">
                ${!isCompletedToday ? 
                    `<button class="btn btn-success btn-small" id="complete-${task.id}">✅ Complete</button>` :
                    `<span style="color: var(--success-color); font-weight: 600;">✓ Completed Today</span>`
                }
                <button class="btn btn-danger btn-small" id="delete-${task.id}">🗑️ Delete</button>
            </div>
        </div>
    `;
}

// Handle task form submission
async function handleTaskSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const taskData = {
        title: formData.get('title'),
        description: formData.get('description'),
        recurring: formData.get('recurring') === 'on',
        frequency: formData.get('frequency'),
        scheduled_time: formData.get('scheduled_time'),
        xp_reward: parseInt(formData.get('xp_reward')),
        coin_reward: parseInt(formData.get('coin_reward'))
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/tasks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(taskData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Task created successfully!', 'success');
            e.target.reset();
            loadTasks();
            playSound('success');
        } else {
            showNotification(data.error || 'Error creating task', 'error');
        }
    } catch (error) {
        console.error('Error creating task:', error);
        showNotification('Error creating task', 'error');
    }
}

// Complete task
async function completeTask(taskId) {
    try {
        const response = await fetch(`${API_BASE}/api/tasks/${taskId}/complete`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification(`Task completed! +${data.xp_reward} XP, +${data.coin_reward} Coins`, 'success');
            playSound('complete');
            
            // Update user data
            await loadUserData();
            await loadTasks();
            
            // Check for level up
            if (data.level_up) {
                showLevelUpModal(data.user.level);
            }
            
            // Show achievements
            if (data.achievements && data.achievements.length > 0) {
                data.achievements.forEach(achievement => {
                    setTimeout(() => {
                        showNotification(`🏆 Achievement Unlocked: ${achievement}`, 'success');
                    }, 500);
                });
            }
            
            // Confetti animation
            createConfetti();
        } else {
            showNotification(data.error || 'Error completing task', 'error');
        }
    } catch (error) {
        console.error('Error completing task:', error);
        showNotification('Error completing task', 'error');
    }
}

// Delete task
async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/tasks/${taskId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Task deleted successfully', 'success');
            loadTasks();
        } else {
            showNotification(data.error || 'Error deleting task', 'error');
        }
    } catch (error) {
        console.error('Error deleting task:', error);
        showNotification('Error deleting task', 'error');
    }
}

// Update badges display
function updateBadges() {
    if (!userData) return;
    
    const badgesList = document.getElementById('badgesList');
    const allBadges = [
        { id: 'streak_7', name: '7 Day Streak', icon: '🔥', description: 'Complete tasks for 7 days in a row' },
        { id: 'streak_30', name: '30 Day Streak', icon: '🏆', description: 'Complete tasks for 30 days in a row' },
        { id: 'tasks_10', name: '10 Tasks', icon: '⭐', description: 'Complete 10 tasks' },
        { id: 'tasks_50', name: '50 Tasks', icon: '🌟', description: 'Complete 50 tasks' }
    ];
    
    badgesList.innerHTML = allBadges.map(badge => {
        const unlocked = userData.badges.includes(badge.id);
        return `
            <div class="badge-item ${unlocked ? '' : 'locked'}">
                <div class="badge-icon">${badge.icon}</div>
                <div class="badge-name">${badge.name}</div>
            </div>
        `;
    }).join('');
}

// Update shop display
function updateShop() {
    if (!userData) return;
    
    const shopList = document.getElementById('shopList');
    
    shopList.innerHTML = Object.keys(SHOP_ITEMS).map(itemId => {
        const item = SHOP_ITEMS[itemId];
        const unlocked = userData.inventory && userData.inventory.includes(itemId);
        return `
            <div class="shop-item ${unlocked ? 'unlocked' : ''}" onclick="${unlocked ? '' : `unlockItem('${itemId}', ${item.cost})`}">
                <div class="shop-item-icon"><i class="fas ${item.icon}"></i></div>
                <div class="shop-item-name">${item.name}</div>
                <div class="shop-item-cost">${unlocked ? 'Unlocked ✓' : `💰 ${item.cost} Coins`}</div>
            </div>
        `;
    }).join('');
}

// Unlock item
async function unlockItem(itemId, cost) {
    if (!userData || userData.coins < cost) {
        showNotification('Not enough coins!', 'error');
        return;
    }
    
    if (!confirm(`Unlock this item for ${cost} coins?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/user/unlock`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ item: itemId, cost: cost })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Item unlocked!', 'success');
            playSound('success');
            await loadUserData();
        } else {
            showNotification(data.error || 'Error unlocking item', 'error');
        }
    } catch (error) {
        console.error('Error unlocking item:', error);
        showNotification('Error unlocking item', 'error');
    }
}

// Show notification
function showNotification(message, type = 'success') {
    const container = document.getElementById('notificationContainer');
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => {
            container.removeChild(notification);
        }, 300);
    }, 3000);
}

// Show level up modal
function showLevelUpModal(level) {
    document.getElementById('newLevel').textContent = level;
    document.getElementById('levelUpModal').classList.add('active');
    playSound('levelup');
}

// Close level up modal
function closeLevelUpModal() {
    document.getElementById('levelUpModal').classList.remove('active');
}

// Play sound (using Web Audio API for simple beeps)
function playSound(type) {
    // Simple audio feedback using Web Audio API
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    if (type === 'complete') {
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
    } else if (type === 'levelup') {
        oscillator.frequency.value = 1000;
        oscillator.type = 'sine';
    } else if (type === 'success') {
        oscillator.frequency.value = 600;
        oscillator.type = 'sine';
    }
    
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
}

// Create confetti animation
function createConfetti() {
    const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#f0932b', '#eb4d4b'];
    const confettiCount = 50;
    
    for (let i = 0; i < confettiCount; i++) {
        setTimeout(() => {
            const confetti = document.createElement('div');
            confetti.style.position = 'fixed';
            confetti.style.left = Math.random() * 100 + '%';
            confetti.style.top = '-10px';
            confetti.style.width = '10px';
            confetti.style.height = '10px';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.borderRadius = '50%';
            confetti.style.pointerEvents = 'none';
            confetti.style.zIndex = '9999';
            confetti.style.transition = 'all 3s ease-out';
            
            document.body.appendChild(confetti);
            
            setTimeout(() => {
                confetti.style.top = '100%';
                confetti.style.transform = `rotate(${Math.random() * 360}deg)`;
                confetti.style.opacity = '0';
            }, 10);
            
            setTimeout(() => {
                document.body.removeChild(confetti);
            }, 3000);
        }, i * 10);
    }
}

// Check for notifications (task reminders)
function checkNotifications() {
    const now = new Date();
    const currentTime = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    
    tasks.forEach(task => {
        if (task.scheduled_time && task.scheduled_time === currentTime) {
            const today = new Date().toISOString().split('T')[0];
            if (!task.completed_dates || !task.completed_dates.includes(today)) {
                showNotification(`⏰ Reminder: ${task.title}`, 'warning');
            }
        }
    });
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ----------------- Settings & Avatar -----------------
async function loadSettings() {
    try {
        const resp = await fetch(`${API_BASE}/api/settings`);
        if (!resp.ok) return;
        const data = await resp.json();
        const settings = data.settings || {};

        const xp = document.getElementById('defaultXp');
        const coins = document.getElementById('defaultCoins');
        const notif = document.getElementById('notificationsEnabled');
        const avatarPreview = document.getElementById('avatarPreview');

        if (xp) xp.value = settings.default_xp_reward || 10;
        if (coins) coins.value = settings.default_coin_reward || 5;
        if (notif) notif.checked = settings.notifications_enabled === undefined ? true : settings.notifications_enabled;

        if (avatarPreview && settings.avatar_url) {
            avatarPreview.innerHTML = `<img src="${settings.avatar_url}" alt="avatar" style="width:64px;height:64px;border-radius:8px;object-fit:cover;">`;
        }
    } catch (e) {
        console.warn('Could not load settings', e);
    }
}

function openSettingsModal() {
    const modal = document.getElementById('settingsModal');
    if (modal) modal.classList.add('active');
}

function closeSettingsModal() {
    const modal = document.getElementById('settingsModal');
    if (modal) modal.classList.remove('active');
}

async function saveSettings(e) {
    if (e) e.preventDefault();
    const xp = document.getElementById('defaultXp').value;
    const coins = document.getElementById('defaultCoins').value;
    const notif = document.getElementById('notificationsEnabled').checked;

    try {
        const resp = await fetch(`${API_BASE}/api/settings`, {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ default_xp_reward: xp, default_coin_reward: coins, notifications_enabled: notif })
        });
        const data = await resp.json();
        if (resp.ok) {
            showNotification('Settings saved', 'success');
            closeSettingsModal();
            await loadUserData();
        } else {
            showNotification(data.error || 'Failed to save settings', 'error');
        }
    } catch (e) {
        console.error('Error saving settings', e);
        showNotification('Network error saving settings', 'error');
    }
}

async function uploadAvatar() {
    const fileInput = document.getElementById('avatarFile');
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        showNotification('Choose a file first', 'warning');
        return;
    }

    const file = fileInput.files[0];
    const form = new FormData();
    form.append('file', file);

    try {
        const resp = await fetch(`${API_BASE}/api/user/avatar`, { method: 'POST', body: form });
        const data = await resp.json();
        if (resp.ok) {
            showNotification('Avatar uploaded', 'success');
            const preview = document.getElementById('avatarPreview');
            if (preview && data.avatar_url) {
                preview.innerHTML = `<img src="${data.avatar_url}" alt="avatar" style="width:64px;height:64px;border-radius:8px;object-fit:cover;">`;
            }
            await loadUserData();
        } else {
            showNotification(data.error || 'Failed to upload avatar', 'error');
        }
    } catch (e) {
        console.error('Avatar upload failed', e);
        showNotification('Network error uploading avatar', 'error');
    }
}
