from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
from datetime import datetime
import uuid
import csv
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Data storage file
DATA_FILE = 'user_data.json'

# Define shop items (centralized)
SHOP_ITEMS = {
    'mountain_boots': {'name': 'Mountain Boots', 'cost': 100, 'description': 'Sturdy boots for mountain climbing'},
    'backpack': {'name': 'Adventure Backpack', 'cost': 150, 'description': 'A spacious backpack for your journey'},
    'compass': {'name': 'Golden Compass', 'cost': 200, 'description': 'Never lose your way'},
    'rope': {'name': 'Magic Rope', 'cost': 125, 'description': 'Strong and lightweight climbing rope'},
    'map': {'name': 'Ancient Map', 'cost': 175, 'description': 'Reveals hidden mountain paths'},
    'water_bottle': {'name': 'Enchanted Water Bottle', 'cost': 100, 'description': 'Never runs empty'},
    'first_aid': {'name': 'Healer\'s Kit', 'cost': 150, 'description': 'For magical healing'},
    'tent': {'name': 'Cloud Tent', 'cost': 250, 'description': 'A cozy shelter in the mountains'}
}

# Quest templates
QUEST_TEMPLATES = {
    'early_bird': {
        'name': 'Early Bird',
        'description': 'Complete 5 tasks before 9 AM',
        'tasks_required': 5,
        'time_limit': 'morning',
        'xp_reward': 100,
        'coin_reward': 50
    },
    'streak_master': {
        'name': 'Streak Master',
        'description': 'Maintain a 7-day completion streak',
        'streak_required': 7,
        'xp_reward': 150,
        'coin_reward': 75
    },
    'coin_collector': {
        'name': 'Coin Collector',
        'description': 'Earn 500 coins total',
        'coins_required': 500,
        'xp_reward': 120,
        'coin_reward': 100
    },
    'level_up': {
        'name': 'Level Up Master',
        'description': 'Reach level 10',
        'level_required': 10,
        'xp_reward': 200,
        'coin_reward': 150
    },
    'shopping_spree': {
        'name': 'Shopping Spree',
        'description': 'Unlock 5 shop items',
        'items_required': 5,
        'xp_reward': 130,
        'coin_reward': 80
    }
}

# Challenge templates (time-limited)
CHALLENGE_TEMPLATES = {
    'daily_grind': {
        'name': 'Daily Grind',
        'description': 'Complete 3 tasks in 24 hours',
        'difficulty': 'easy',
        'tasks_required': 3,
        'duration_hours': 24,
        'xp_reward': 50,
        'coin_reward': 25,
        'icon': '📅'
    },
    'power_hour': {
        'name': 'Power Hour',
        'description': 'Complete 5 tasks in 1 hour',
        'difficulty': 'hard',
        'tasks_required': 5,
        'duration_hours': 1,
        'xp_reward': 200,
        'coin_reward': 100,
        'icon': '⚡'
    },
    'weekend_warrior': {
        'name': 'Weekend Warrior',
        'description': 'Complete 10 tasks in 48 hours',
        'difficulty': 'medium',
        'tasks_required': 10,
        'duration_hours': 48,
        'xp_reward': 150,
        'coin_reward': 75,
        'icon': '🗓️'
    },
    'night_owl': {
        'name': 'Night Owl',
        'description': 'Complete 4 tasks after 8 PM',
        'difficulty': 'medium',
        'tasks_required': 4,
        'time_constraint': 'after_8pm',
        'duration_hours': 24,
        'xp_reward': 120,
        'coin_reward': 60,
        'icon': '🌙'
    }
}

def load_data():
    """Load user data from JSON file"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {
        'users': {},
        'tasks': {},
        'achievements': {},
        'quests': {},
        'challenges': {},
        'quest_templates': {}
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
            'inventory': [],
            'username': 'Player',
            'joined_date': datetime.now().isoformat(),
            'total_coins_earned': 0,
            'active_quests': [],
            'completed_quests': [],
            'active_challenges': [],
            'completed_challenges': []
        }
    # Migrate old data structure if needed
    user = data['users'][user_id]
    if 'avatar_customizations' in user and 'inventory' not in user:
        user['inventory'] = [item for item in user['avatar_customizations'] if item != 'default']
        del user['avatar_customizations']
        save_data(data)
    if 'inventory' not in user:
        user['inventory'] = []
        save_data(data)
    # Add new fields if they don't exist
    if 'username' not in user:
        user['username'] = 'Player'
    if 'joined_date' not in user:
        user['joined_date'] = datetime.now().isoformat()
    if 'total_coins_earned' not in user:
        user['total_coins_earned'] = user.get('coins', 0)
    if 'active_quests' not in user:
        user['active_quests'] = []
    if 'completed_quests' not in user:
        user['completed_quests'] = []
    if 'active_challenges' not in user:
        user['active_challenges'] = []
    if 'completed_challenges' not in user:
        user['completed_challenges'] = []
    return user

@app.route('/')
def index():
    """Main page"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        if not username or not password:
            return render_template('login.html', error='Please fill in all fields')
        
        # Read CSV file
        try:
            with open('login_info.csv', 'r') as f:
                reader = csv.DictReader(f)
                for user in reader:
                    if user['username'] == username and check_password_hash(user['password'], password):
                        session['username'] = username
                        session['user_id'] = str(uuid.uuid4())
                        session['avatar'] = user['avatar']
                        session['coins'] = int(user['coins'])
                        return redirect(url_for('index'))
            
            return render_template('login.html', error='Invalid username or password')
        except FileNotFoundError:
            return render_template('login.html', error='System error. Please try again later.')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register page"""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username or not password:
            return render_template('register.html', error='Please fill in all fields')
            
        if len(username) < 3:
            return render_template('register.html', error='Username must be at least 3 characters long')
            
        if len(password) < 6:
            return render_template('register.html', error='Password must be at least 6 characters long')
            
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')
        
        try:
            # Check if username already exists
            with open('login_info.csv', 'r') as f:
                reader = csv.DictReader(f)
                if any(user['username'] == username for user in reader):
                    return render_template('register.html', error='Username already exists')
            
            # Hash password and add new user
            hashed_password = generate_password_hash(password)
            with open('login_info.csv', 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([username, hashed_password, 'default', 100, ''])  # Starting with 100 coins
            
            # Start session
            session['username'] = username
            session['user_id'] = str(uuid.uuid4())
            session['avatar'] = 'default'
            session['coins'] = 100
            
            return redirect(url_for('index'))
        except Exception as e:
            return render_template('register.html', error='Registration failed. Please try again.')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('login'))

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
    item_id = item_data.get('item')
    item_cost = item_data.get('cost', 100)
    
    # Validate item exists
    if item_id not in SHOP_ITEMS:
        return jsonify({'error': 'Invalid item'}), 400
        
    item = SHOP_ITEMS[item_id]
    
    # Initialize inventory if doesn't exist
    if 'inventory' not in user:
        user['inventory'] = []
    
    # Check if already owned
    if item_id in user.get('inventory', []):
        return jsonify({'error': 'Item already unlocked'}), 400
    
    # Check if enough coins
    if user['coins'] < item['cost']:
        return jsonify({'error': 'Not enough coins'}), 400
    
    # Purchase the item
    user['coins'] -= item['cost']
    user['inventory'].append(item_id)
    
    save_data(data)
    return jsonify({
        'message': f'Successfully purchased {item["name"]}!',
        'user': user,
        'item': {
            'id': item_id,
            'name': item['name'],
            'cost': item['cost']
        }
    })

# ============ QUESTS ENDPOINTS ============

@app.route('/api/quest-templates', methods=['GET'])
def get_quest_templates():
    """Get available quest templates"""
    return jsonify({'templates': QUEST_TEMPLATES})

@app.route('/api/quests', methods=['GET'])
def get_quests():
    """Get all quests for current user"""
    data = load_data()
    user_id = get_user_id()
    user = initialize_user(data, user_id)
    
    # Get active and completed quests
    active_quests = []
    completed_quests = []
    
    if 'active_quests' in data and user_id in data['active_quests']:
        for quest_id in data['active_quests'][user_id]:
            if quest_id in data['quests']:
                quest = data['quests'][quest_id]
                quest['id'] = quest_id
                active_quests.append(quest)
    
    if 'completed_quests' in data and user_id in data['completed_quests']:
        for quest_id in data['completed_quests'][user_id]:
            if quest_id in data['quests']:
                quest = data['quests'][quest_id]
                quest['id'] = quest_id
                completed_quests.append(quest)
    
    return jsonify({
        'active': active_quests,
        'completed': completed_quests,
        'templates': QUEST_TEMPLATES
    })

@app.route('/api/quests', methods=['POST'])
def create_quest():
    """Start a new quest from template"""
    data = load_data()
    user_id = get_user_id()
    user = initialize_user(data, user_id)
    
    quest_data = request.json
    template_id = quest_data.get('template_id')
    
    if template_id not in QUEST_TEMPLATES:
        return jsonify({'error': 'Invalid quest template'}), 400
    
    template = QUEST_TEMPLATES[template_id]
    quest_id = str(uuid.uuid4())
    
    new_quest = {
        'id': quest_id,
        'user_id': user_id,
        'template_id': template_id,
        'name': template['name'],
        'description': template['description'],
        'started_at': datetime.now().isoformat(),
        'progress': 0,
        'completed': False,
        'xp_reward': template['xp_reward'],
        'coin_reward': template['coin_reward'],
        'metadata': {k: v for k, v in template.items() if k not in ['name', 'description', 'xp_reward', 'coin_reward']}
    }
    
    data['quests'][quest_id] = new_quest
    
    # Track user quests
    if 'active_quests' not in data:
        data['active_quests'] = {}
    if user_id not in data['active_quests']:
        data['active_quests'][user_id] = []
    
    data['active_quests'][user_id].append(quest_id)
    
    save_data(data)
    
    return jsonify({
        'quest': new_quest,
        'message': f'Started quest: {template["name"]}'
    })

@app.route('/api/quests/<quest_id>/check', methods=['POST'])
def check_quest_progress(quest_id):
    """Check if quest objective is met and complete if so"""
    data = load_data()
    user_id = get_user_id()
    user = initialize_user(data, user_id)
    
    if quest_id not in data['quests'] or data['quests'][quest_id].get('user_id') != user_id:
        return jsonify({'error': 'Quest not found'}), 404
    
    quest = data['quests'][quest_id]
    
    if quest['completed']:
        return jsonify({'error': 'Quest already completed'}), 400
    
    # Check progress based on template
    template_id = quest['template_id']
    template = QUEST_TEMPLATES[template_id]
    progress = 0
    completed = False
    
    if template_id == 'early_bird':
        # Count tasks completed today before 9 AM
        today = datetime.now().date().isoformat()
        morning_tasks = sum(1 for task in data['tasks'].values() 
                           if task.get('user_id') == user_id 
                           and today in task.get('completed_dates', [])
                           and task.get('scheduled_time', '') < '09:00')
        progress = min(morning_tasks, template['tasks_required'])
        completed = morning_tasks >= template['tasks_required']
    
    elif template_id == 'streak_master':
        progress = user['streak']
        completed = user['streak'] >= template['streak_required']
    
    elif template_id == 'coin_collector':
        # Total coins earned (current + spent on items)
        total_earned = user['coins'] + sum(SHOP_ITEMS[item]['cost'] 
                                          for item in user.get('inventory', []) 
                                          if item in SHOP_ITEMS)
        progress = total_earned
        completed = total_earned >= template['coins_required']
    
    elif template_id == 'level_up':
        progress = user['level']
        completed = user['level'] >= template['level_required']
    
    elif template_id == 'shopping_spree':
        progress = len(user.get('inventory', []))
        completed = len(user.get('inventory', [])) >= template['items_required']
    
    quest['progress'] = progress
    
    if completed and not quest['completed']:
        quest['completed'] = True
        quest['completed_at'] = datetime.now().isoformat()
        
        # Award rewards
        user['xp'] += quest['xp_reward']
        user['coins'] += quest['coin_reward']
        user['total_coins_earned'] += quest['coin_reward']
        
        # Move quest to completed
        if user_id in data['active_quests']:
            data['active_quests'][user_id].remove(quest_id)
        
        if 'completed_quests' not in data:
            data['completed_quests'] = {}
        if user_id not in data['completed_quests']:
            data['completed_quests'][user_id] = []
        
        data['completed_quests'][user_id].append(quest_id)
        
        # Check for level up
        xp_for_next_level = user['level'] * 100
        level_up = False
        while user['xp'] >= xp_for_next_level:
            user['level'] += 1
            user['xp'] -= xp_for_next_level
            xp_for_next_level = user['level'] * 100
            level_up = True
            user['coins'] += 50
        
        save_data(data)
        
        return jsonify({
            'completed': True,
            'xp_reward': quest['xp_reward'],
            'coin_reward': quest['coin_reward'],
            'user': user,
            'level_up': level_up,
            'message': f'Quest completed: {quest["name"]}!'
        })
    
    save_data(data)
    
    return jsonify({
        'completed': False,
        'progress': progress,
        'required': template.get('tasks_required') or template.get('streak_required') or template.get('coins_required') or template.get('level_required') or template.get('items_required'),
        'message': f'Progress: {progress}/{template.get("tasks_required") or template.get("streak_required") or template.get("coins_required") or template.get("level_required") or template.get("items_required")}'
    })

@app.route('/api/quests/<quest_id>', methods=['DELETE'])
def abandon_quest(quest_id):
    """Abandon an active quest"""
    data = load_data()
    user_id = get_user_id()
    
    if quest_id not in data['quests'] or data['quests'][quest_id].get('user_id') != user_id:
        return jsonify({'error': 'Quest not found'}), 404
    
    if user_id in data.get('active_quests', {}):
        if quest_id in data['active_quests'][user_id]:
            data['active_quests'][user_id].remove(quest_id)
    
    save_data(data)
    return jsonify({'message': 'Quest abandoned'})

# ============ CHALLENGES ENDPOINTS ============

@app.route('/api/challenge-templates', methods=['GET'])
def get_challenge_templates():
    """Get available challenge templates"""
    return jsonify({'templates': CHALLENGE_TEMPLATES})

@app.route('/api/challenges', methods=['GET'])
def get_challenges():
    """Get all challenges for current user"""
    data = load_data()
    user_id = get_user_id()
    user = initialize_user(data, user_id)
    
    active_challenges = []
    completed_challenges = []
    
    # Get all challenges and filter for this user
    for challenge_id, challenge in data.get('challenges', {}).items():
        if challenge.get('user_id') == user_id:
            challenge_data = challenge.copy()
            challenge_data['id'] = challenge_id
            
            # Calculate time remaining
            if not challenge.get('completed'):
                started_at = datetime.fromisoformat(challenge['started_at'])
                duration = challenge.get('duration_hours', 24)
                expires_at = started_at + datetime.timedelta(hours=duration)
                time_remaining = (expires_at - datetime.now()).total_seconds()
                
                if time_remaining > 0:
                    challenge_data['time_remaining_seconds'] = int(time_remaining)
                    active_challenges.append(challenge_data)
                else:
                    # Challenge expired
                    challenge['completed'] = True
                    challenge['expired'] = True
                    completed_challenges.append(challenge_data)
            else:
                completed_challenges.append(challenge_data)
    
    save_data(data)
    
    return jsonify({
        'active': active_challenges,
        'completed': completed_challenges,
        'templates': CHALLENGE_TEMPLATES
    })

@app.route('/api/challenges', methods=['POST'])
def create_challenge():
    """Start a new challenge from template"""
    data = load_data()
    user_id = get_user_id()
    user = initialize_user(data, user_id)
    
    challenge_data = request.json
    template_id = challenge_data.get('template_id')
    
    if template_id not in CHALLENGE_TEMPLATES:
        return jsonify({'error': 'Invalid challenge template'}), 400
    
    template = CHALLENGE_TEMPLATES[template_id]
    challenge_id = str(uuid.uuid4())
    
    new_challenge = {
        'id': challenge_id,
        'user_id': user_id,
        'template_id': template_id,
        'name': template['name'],
        'description': template['description'],
        'difficulty': template['difficulty'],
        'icon': template.get('icon', '🎯'),
        'started_at': datetime.now().isoformat(),
        'progress': 0,
        'completed': False,
        'duration_hours': template['duration_hours'],
        'xp_reward': template['xp_reward'],
        'coin_reward': template['coin_reward'],
        'metadata': {k: v for k, v in template.items() 
                    if k not in ['name', 'description', 'difficulty', 'icon', 'xp_reward', 'coin_reward', 'duration_hours']}
    }
    
    if 'challenges' not in data:
        data['challenges'] = {}
    
    data['challenges'][challenge_id] = new_challenge
    save_data(data)
    
    return jsonify({
        'challenge': new_challenge,
        'message': f'Challenge started: {template["name"]}'
    })

@app.route('/api/challenges/<challenge_id>/check', methods=['POST'])
def check_challenge_progress(challenge_id):
    """Check challenge progress"""
    data = load_data()
    user_id = get_user_id()
    user = initialize_user(data, user_id)
    
    if challenge_id not in data.get('challenges', {}) or data['challenges'][challenge_id].get('user_id') != user_id:
        return jsonify({'error': 'Challenge not found'}), 404
    
    challenge = data['challenges'][challenge_id]
    
    if challenge['completed']:
        return jsonify({'error': 'Challenge already completed'}), 400
    
    template_id = challenge['template_id']
    template = CHALLENGE_TEMPLATES[template_id]
    
    # Count tasks completed since challenge started
    challenge_start = datetime.fromisoformat(challenge['started_at'])
    tasks_completed_since = 0
    
    for task in data['tasks'].values():
        if task.get('user_id') == user_id:
            for completed_date in task.get('completed_dates', []):
                completed_datetime = datetime.fromisoformat(completed_date + 'T00:00:00')
                if completed_datetime >= challenge_start:
                    tasks_completed_since += 1
    
    progress = tasks_completed_since
    completed = progress >= template['tasks_required']
    
    challenge['progress'] = progress
    
    if completed and not challenge['completed']:
        challenge['completed'] = True
        challenge['completed_at'] = datetime.now().isoformat()
        
        # Award rewards
        user['xp'] += challenge['xp_reward']
        user['coins'] += challenge['coin_reward']
        user['total_coins_earned'] += challenge['coin_reward']
        
        # Check for level up
        xp_for_next_level = user['level'] * 100
        level_up = False
        while user['xp'] >= xp_for_next_level:
            user['level'] += 1
            user['xp'] -= xp_for_next_level
            xp_for_next_level = user['level'] * 100
            level_up = True
            user['coins'] += 50
        
        save_data(data)
        
        return jsonify({
            'completed': True,
            'xp_reward': challenge['xp_reward'],
            'coin_reward': challenge['coin_reward'],
            'user': user,
            'level_up': level_up,
            'message': f'Challenge completed: {challenge["name"]}!'
        })
    
    save_data(data)
    
    return jsonify({
        'completed': False,
        'progress': progress,
        'required': template['tasks_required'],
        'message': f'Progress: {progress}/{template["tasks_required"]}'
    })

# ============ LEADERBOARDS ENDPOINTS ============

@app.route('/api/leaderboards', methods=['GET'])
def get_leaderboards():
    """Get global leaderboards"""
    data = load_data()
    user_id = get_user_id()
    current_user = initialize_user(data, user_id)
    
    # Create user list with stats
    users_list = []
    for uid, user in data['users'].items():
        total_earned = user.get('coins', 0) + sum(SHOP_ITEMS[item]['cost'] 
                                                   for item in user.get('inventory', []) 
                                                   if item in SHOP_ITEMS)
        users_list.append({
            'id': uid,
            'username': user.get('username', 'Player'),
            'level': user.get('level', 1),
            'xp': user.get('xp', 0),
            'coins': user.get('coins', 0),
            'total_coins_earned': total_earned,
            'streak': user.get('streak', 0),
            'total_tasks_completed': user.get('total_tasks_completed', 0),
            'badges_count': len(user.get('badges', [])),
            'is_current_user': uid == user_id
        })
    
    # Sort by different criteria
    by_level = sorted(users_list, key=lambda x: (-x['level'], -x['xp']))
    by_xp = sorted(users_list, key=lambda x: -x['xp'])
    by_coins = sorted(users_list, key=lambda x: -x['coins'])
    by_streak = sorted(users_list, key=lambda x: -x['streak'])
    by_tasks = sorted(users_list, key=lambda x: -x['total_tasks_completed'])
    
    # Add rank to each leaderboard
    for i, user in enumerate(by_level):
        user['rank_level'] = i + 1
    for i, user in enumerate(by_xp):
        user['rank_xp'] = i + 1
    for i, user in enumerate(by_coins):
        user['rank_coins'] = i + 1
    for i, user in enumerate(by_streak):
        user['rank_streak'] = i + 1
    for i, user in enumerate(by_tasks):
        user['rank_tasks'] = i + 1
    
    return jsonify({
        'by_level': by_level[:50],  # Top 50
        'by_xp': by_xp[:50],
        'by_coins': by_coins[:50],
        'by_streak': by_streak[:50],
        'by_tasks': by_tasks[:50],
        'current_user': current_user
    })

@app.route('/profile')
def profile():
    """User profile page"""
    if 'username' not in session:
        return redirect(url_for('login'))
        
    data = load_data()
    user_id = get_user_id()
    user = initialize_user(data, user_id)
    
    # Store username in user data
    user['username'] = session['username']
    
    # Initialize inventory if doesn't exist
    if 'inventory' not in user:
        user['inventory'] = []
        save_data(data)
    
    # Get user's purchased items
    purchased_items = [
        {**SHOP_ITEMS[item], 'id': item}
        for item in user.get('inventory', [])
        if item in SHOP_ITEMS
    ]
    
    # Get total coins earned (current + spent)
    total_coins_earned = user['coins'] + sum(SHOP_ITEMS[item]['cost'] for item in user.get('inventory', []) if item in SHOP_ITEMS)
    
    return render_template('profile.html',
                         username=session['username'],
                         user=user,
                         purchased_items=purchased_items,
                         total_coins_earned=total_coins_earned)

@app.route('/gamemechanics')
def gamemechanics():
    """Quests, challenges, and leaderboards page"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('gamemechanics.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
