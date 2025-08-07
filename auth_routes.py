from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from datetime import datetime
import os

# Add these imports to the top of your flask_mls_dashboard.py file
# Make sure you have the existing Flask app setup

# Set a secret key for sessions
app.secret_key = os.environ.get('SECRET_KEY', 'mls_system_secret_key_2025')

# Define the credentials
ADMIN_CREDENTIALS = {
    'admin': 'Admin@2025'
}


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to the main page
    if 'username' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password:
            # Store user info in session
            session['username'] = username
            session['login_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Log successful login
            logger.info(f"User '{username}' logged in successfully")
            flash('Login successful! Welcome to MLS Point Locator.', 'success')

            # Redirect to the main page
            return redirect(url_for('index'))
        else:
            # Log failed login attempt
            logger.warning(f"Failed login attempt for username: '{username}'")
            flash('Invalid username or password. Please try again.', 'danger')

    # For GET request or failed login, show the login form
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template('login.html', current_time=current_time)


# Logout route
@app.route('/logout')
def logout():
    username = session.pop('username', None)
    if username:
        logger.info(f"User '{username}' logged out")
        flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function