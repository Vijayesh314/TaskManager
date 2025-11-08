from flask import Flask, render_template, request, jsonify, session
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Data storage file
DATA_FILE = 'user_data.json'

def load_data():
    """Load user data from JSON file"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {
        'users': {},
        'tasks': {},
        'achievements': {}
    }

def save_data(data):
    """Save user data to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_user_id():
    """Get or create user session ID"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']

def initialize_user(data, user_id):
    """Initialize user data if not exists"""
    if user_id not in data['users']:
        data['users'][user_id] = {
            'level': 1,
            'xp': 0,
            'coins': 0,
            'streak': 0,
            'last_completed_date': None,
            'total_tasks_completed': 0,
            'badges': [],
            'avatar_customizations': ['default']
        }
    return data['users'][user_id]

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks for current user"""
    data = load_data()
    user_id = get_user_id()
    initialize_user(data, user_id)
    
    user_tasks = [task for task in data['tasks'].values() if task.get('user_id') == user_id]
    return jsonify({'tasks': user_tasks})

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    data = load_data()
    user_id = get_user_id()
    user = initialize_user(data, user_id)
    
    task_data = request.json
    task_id = str(uuid.uuid4())
    
    new_task = {
        'id': task_id,
        'user_id': user_id,
        'title': task_data.get('title'),
        'description': task_data.get('description', ''),
        'recurring': task_data.get('recurring', False),
        'frequency': task_data.get('frequency', 'daily'),  # daily, weekly, custom
        'scheduled_time': task_data.get('scheduled_time', ''),
        'xp_reward': task_data.get('xp_reward', 10),
        'coin_reward': task_data.get('coin_reward', 5),
        'completed': False,
        'completed_dates': [],
        'created_at': datetime.now().isoformat(),
        'streak': 0
    }
    
    data['tasks'][task_id] = new_task
    save_data(data)
    
    return jsonify({'task': new_task, 'message': 'Task created successfully!'})

@app.route('/api/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task"""
    data = load_data()
    user_id = get_user_id()
    
    if task_id not in data['tasks'] or data['tasks'][task_id].get('user_id') != user_id:
        return jsonify({'error': 'Task not found'}), 404
    
    task_data = request.json
    task = data['tasks'][task_id]
    
    # Update task fields
    for key in ['title', 'description', 'recurring', 'frequency', 'scheduled_time']:
        if key in task_data:
            task[key] = task_data[key]
    
    save_data(data)
    return jsonify({'task': task, 'message': 'Task updated successfully!'})

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task"""
    data = load_data()
    user_id = get_user_id()
    
    if task_id not in data['tasks'] or data['tasks'][task_id].get('user_id') != user_id:
        return jsonify({'error': 'Task not found'}), 404
    
    del data['tasks'][task_id]
    save_data(data)
    return jsonify({'message': 'Task deleted successfully!'})

@app.route('/api/tasks/<task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """Mark task as completed and award rewards"""
    data = load_data()
    user_id = get_user_id()
    user = initialize_user(data, user_id)
    
    if task_id not in data['tasks'] or data['tasks'][task_id].get('user_id') != user_id:
        return jsonify({'error': 'Task not found'}), 404
    
    task = data['tasks'][task_id]
    today = datetime.now().date().isoformat()
    
    # Check if already completed today
    if today in task.get('completed_dates', []):
        return jsonify({'error': 'Task already completed today'}), 400
    
    # Award rewards
    xp_reward = task.get('xp_reward', 10)
    coin_reward = task.get('coin_reward', 5)
    
    user['xp'] += xp_reward
    user['coins'] += coin_reward
    user['total_tasks_completed'] += 1
    
    # Update streak
    last_date = user.get('last_completed_date')
    if last_date:
        last_date_obj = datetime.fromisoformat(last_date).date()
        today_obj = datetime.now().date()
        
        if (today_obj - last_date_obj).days == 1:
            user['streak'] += 1
            task['streak'] = task.get('streak', 0) + 1
        elif (today_obj - last_date_obj).days > 1:
            user['streak'] = 1
            task['streak'] = 1
        else:
            # Same day, maintain streak
            pass
    else:
        user['streak'] = 1
        task['streak'] = 1
    
    user['last_completed_date'] = datetime.now().isoformat()
    
    # Update task
    if 'completed_dates' not in task:
        task['completed_dates'] = []
    task['completed_dates'].append(today)
    task['completed'] = True
    
    # Level up check
    xp_for_next_level = user['level'] * 100
    level_up = False
    while user['xp'] >= xp_for_next_level:
        user['level'] += 1
        user['xp'] -= xp_for_next_level
        xp_for_next_level = user['level'] * 100
        level_up = True
        user['coins'] += 50  # Bonus coins on level up
    
    # Check for achievements
    achievements_unlocked = []
    
    # Streak achievements
    if user['streak'] == 7 and 'streak_7' not in user['badges']:
        user['badges'].append('streak_7')
        achievements_unlocked.append('7 Day Streak!')
    if user['streak'] == 30 and 'streak_30' not in user['badges']:
        user['badges'].append('streak_30')
        achievements_unlocked.append('30 Day Streak!')
    
    # Task completion achievements
    if user['total_tasks_completed'] == 10 and 'tasks_10' not in user['badges']:
        user['badges'].append('tasks_10')
        achievements_unlocked.append('10 Tasks Completed!')
    if user['total_tasks_completed'] == 50 and 'tasks_50' not in user['badges']:
        user['badges'].append('tasks_50')
        achievements_unlocked.append('50 Tasks Completed!')
    
    save_data(data)
    
    return jsonify({
        'message': 'Task completed!',
        'xp_reward': xp_reward,
        'coin_reward': coin_reward,
        'user': user,
        'level_up': level_up,
        'achievements': achievements_unlocked
    })

@app.route('/api/user', methods=['GET'])
def get_user():
    """Get current user data"""
    data = load_data()
    user_id = get_user_id()
    user = initialize_user(data, user_id)
    
    # Calculate XP needed for next level
    xp_needed = user['level'] * 100
    xp_progress = user['xp'] % xp_needed if user['level'] > 1 else user['xp']
    xp_percentage = (xp_progress / xp_needed) * 100
    
    return jsonify({
        'user': user,
        'xp_needed': xp_needed,
        'xp_progress': xp_progress,
        'xp_percentage': xp_percentage
    })

@app.route('/api/user/unlock', methods=['POST'])
def unlock_customization():
    """Unlock avatar/item customization"""
    data = load_data()
    user_id = get_user_id()
    user = initialize_user(data, user_id)
    
    item_data = request.json
    item_name = item_data.get('item')
    item_cost = item_data.get('cost', 100)
    
    if item_name in user['avatar_customizations']:
        return jsonify({'error': 'Item already unlocked'}), 400
    
    if user['coins'] < item_cost:
        return jsonify({'error': 'Not enough coins'}), 400
    
    user['coins'] -= item_cost
    user['avatar_customizations'].append(item_name)
    
    save_data(data)
    return jsonify({'message': 'Item unlocked!', 'user': user})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
