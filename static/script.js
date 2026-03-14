// Notification handling for Todo App

console.log('📱 Notification script loaded');

// Request notification permission immediately when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('📱 DOM loaded, checking notification support...');
    
    if ('Notification' in window) {
        console.log('📱 Notifications supported, current permission:', Notification.permission);
        
        if (Notification.permission === 'default') {
            console.log('📱 Requesting notification permission...');
            Notification.requestPermission().then(permission => {
                console.log('📱 Permission result:', permission);
                if (permission === 'granted') {
                    // Test notification
                    new Notification('✅ Notifications enabled!', {
                        body: 'You will now receive task reminders',
                        tag: 'test'
                    });
                }
            });
        } else if (Notification.permission === 'granted') {
            console.log('📱 Permission already granted');
            // Test notification
            new Notification('✅ Notifications ready!', {
                body: 'Waiting for tasks...',
                tag: 'test'
            });
        }
    } else {
        console.log('❌ Notifications not supported in this browser');
    }
    
    // Start checking for notifications after 5 seconds
    setTimeout(() => {
        console.log('📱 Starting notification checks...');
        checkForNotifications();
        
        // Check every 30 seconds for testing
        setInterval(() => {
            console.log('📱 Running scheduled notification check...');
            checkForNotifications();
        }, 30000); // Check every 30 seconds for faster testing
    }, 5000);
});

// Check for upcoming tasks and previous tasks
function checkForNotifications() {
    console.log('📱 Checking for notifications...');
    
    // Check for upcoming tasks (5 minutes before)
    fetch('/api/check-notifications')
        .then(response => {
            console.log('📱 API response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('📱 Upcoming tasks data:', data);
            if (data.tasks && data.tasks.length > 0) {
                console.log('📱 Found upcoming tasks:', data.tasks.length);
                data.tasks.forEach(task => {
                    showUpcomingNotification(task);
                });
            } else {
                console.log('📱 No upcoming tasks found');
            }
        })
        .catch(error => console.error('❌ Error checking notifications:', error));
    
    // Check for tasks that need completion check
    fetch('/api/get-previous-tasks')
        .then(response => {
            console.log('📱 Previous tasks API response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('📱 Previous tasks data:', data);
            if (data.tasks && data.tasks.length > 0) {
                console.log('📱 Found previous tasks:', data.tasks.length);
                data.tasks.forEach(task => {
                    showCompletionPrompt(task);
                });
            } else {
                console.log('📱 No previous tasks found');
            }
        })
        .catch(error => console.error('❌ Error checking previous tasks:', error));
}

// Show upcoming task notification
function showUpcomingNotification(task) {
    console.log('📱 Showing upcoming notification for task:', task);
    
    const title = `⏰ Task Reminder`;
    const body = `Time to start: "${task.title}" at ${task.task_time}`;
    
    // Mark as notified
    fetch(`/api/mark-notified/${task.id}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(() => console.log('📱 Task marked as notified'));
    
    // Show browser notification
    if (Notification.permission === 'granted') {
        try {
            const notification = new Notification(title, {
                body: body,
                icon: '/static/icon.png',
                tag: 'task-reminder',
                requireInteraction: true, // Keep notification until user interacts
                silent: false
            });
            
            notification.onclick = function() {
                console.log('📱 Notification clicked');
                window.focus();
                this.close();
            };
            
            console.log('📱 Notification shown successfully');
        } catch (e) {
            console.error('❌ Error showing notification:', e);
        }
    } else {
        console.log('❌ Cannot show notification - permission:', Notification.permission);
    }
    
    // Also show in-app notification
    showInAppNotification(body);
}

// Show completion prompt with Yes/No buttons
function showCompletionPrompt(task) {
    console.log('📱 Showing completion prompt for task:', task);
    
    const title = `❓ Did you complete?`;
    const body = `Have you finished: "${task.title}" (was at ${task.task_time})?`;
    
    // Show in-app prompt
    showInAppPrompt(task.id, task.title, body);
    
    // Browser notification with actions
    if (Notification.permission === 'granted') {
        try {
            const notification = new Notification(title, {
                body: body,
                icon: '/static/icon.png',
                tag: 'task-completion',
                requireInteraction: true,
                actions: [
                    { action: 'yes', title: '✅ Yes, completed' },
                    { action: 'no', title: '❌ No, not yet' }
                ]
            });
            
            notification.onclick = function(event) {
                event.preventDefault();
                console.log('📱 Notification clicked');
                window.focus();
            };
            
            notification.onaction = function(event) {
                console.log('📱 Notification action:', event.action);
                if (event.action === 'yes') {
                    sendTaskResponse(task.id, 'yes');
                    notification.close();
                } else if (event.action === 'no') {
                    sendTaskResponse(task.id, 'no');
                    notification.close();
                }
            };
        } catch (e) {
            console.error('❌ Error showing action notification:', e);
        }
    }
}

// Show in-app prompt
function showInAppPrompt(taskId, taskTitle, message) {
    console.log('📱 Showing in-app prompt');
    
    // Remove any existing prompts
    const existingPrompt = document.getElementById(`prompt-${taskId}`);
    if (existingPrompt) existingPrompt.remove();
    
    const promptDiv = document.createElement('div');
    promptDiv.id = `prompt-${taskId}`;
    promptDiv.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 20px;
        right: 20px;
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        max-width: 400px;
        margin: 0 auto;
        animation: slideUp 0.3s ease;
        border: 2px solid #007AFF;
    `;
    
    promptDiv.innerHTML = `
        <p style="margin-bottom: 16px; font-size: 16px; color: #333;">
            <strong>${taskTitle}</strong><br>
            <span style="color: #666; font-size: 14px;">${message}</span>
        </p>
        <div style="display: flex; gap: 12px;">
            <button onclick="handlePromptResponse(${taskId}, 'yes')" 
                    style="flex: 1; padding: 12px; background: #34C759; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer;">
                ✅ Yes, completed
            </button>
            <button onclick="handlePromptResponse(${taskId}, 'no')" 
                    style="flex: 1; padding: 12px; background: #FF3B30; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer;">
                ❌ No, not yet
            </button>
        </div>
    `;
    
    document.body.appendChild(promptDiv);
    console.log('📱 In-app prompt added to DOM');
}

// Handle in-app prompt response
window.handlePromptResponse = function(taskId, response) {
    console.log('📱 Prompt response:', taskId, response);
    sendTaskResponse(taskId, response);
    const element = document.getElementById(`prompt-${taskId}`);
    if (element) element.remove();
};

// Send task response to server
function sendTaskResponse(taskId, response) {
    console.log('📱 Sending response to server:', taskId, response);
    
    fetch(`/api/task-response/${taskId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ response: response })
    })
    .then(response => response.json())
    .then(data => {
        console.log('📱 Server response:', data);
        if (data.success) {
            if (response === 'yes') {
                setTimeout(() => location.reload(), 1000);
            }
        }
    })
    .catch(error => console.error('❌ Error sending response:', error));
}

// Show in-app notification
function showInAppNotification(message) {
    console.log('📱 Showing in-app notification:', message);
    
    const notificationDiv = document.createElement('div');
    notificationDiv.style.cssText = `
        position: fixed;
        top: 20px;
        left: 20px;
        right: 20px;
        background: #007AFF;
        color: white;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        max-width: 400px;
        margin: 0 auto;
        text-align: center;
        animation: slideDown 0.3s ease;
    `;
    
    notificationDiv.textContent = message;
    document.body.appendChild(notificationDiv);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notificationDiv.remove();
    }, 5000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideUp {
        from { transform: translateY(100px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    @keyframes slideDown {
        from { transform: translateY(-100px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
`;
document.head.appendChild(style);

console.log('📱 Script initialization complete');
