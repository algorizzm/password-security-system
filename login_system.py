import json
import bcrypt
import os
from pathlib import Path

class LoginSystem:
    """Handles user registration and login with secure password hashing."""

    def __init__(self, users_file='users.json'):
        self.users_file = users_file
        self.users = self.load_users()

    def load_users(self):
        """Load users from JSON file. Create empty dict if file doesn't exist."""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save_users(self):
        """Save users to JSON file."""
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)

    def hash_password(self, password):
        """
        Hash password using bcrypt with salt.
        Bcrypt is slow by design - it includes salt and uses many rounds.
        This makes brute-force attacks significantly more difficult.
        """
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(self, password, hashed_password):
        """Verify a plaintext password against a bcrypt hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    def register_user(self, username, password):
        """
        Register a new user.
        Returns: (success: bool, message: str)
        """
        if not username or not password:
            return False, "Username and password required"

        if username in self.users:
            return False, "Username already exists"

        if len(password) < 4:
            return False, "Password must be at least 4 characters"

        # Hash password before storing
        hashed_password = self.hash_password(password)
        self.users[username] = {
            'password_hash': hashed_password
        }

        self.save_users()
        return True, f"User '{username}' registered successfully"

    def login_user(self, username, password):
        """
        Verify user credentials.
        Returns: (success: bool, message: str)
        """
        if username not in self.users:
            return False, "Username not found"

        user = self.users[username]

        if self.verify_password(password, user['password_hash']):
            return True, "Login successful"
        else:
            return False, "Incorrect password"

    def get_user_hash(self, username):
        """Get the password hash for a specific user (for attack simulations)."""
        if username in self.users:
            return self.users[username]['password_hash']
        return None

    def get_all_users(self):
        """Get list of all registered usernames."""
        return list(self.users.keys())
