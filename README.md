# Password Attack & Defense Simulation System

An educational Python desktop application demonstrating password security concepts, secure password storage, and attack simulations in a **safe, local, and controlled environment**.

## 🎯 Project Purpose

This project is designed to **educate** about:
- Why password strength matters
- How secure password storage works
- Why bcrypt is better than simple hashing
- How dictionary attacks work
- Why brute-force attacks are impractical for strong passwords
- Real-world password security concepts

**This is NOT a hacking tool and should NEVER be used against real systems.**

## ✨ Features

### 1. Secure User Registration & Login
- User registration with password hashing
- bcrypt password hashing (salted, 12 rounds)
- Secure login verification
- Local JSON storage (no database required)

### 2. Real-Time Password Strength Meter
Evaluates passwords based on:
- Length (minimum 8 characters recommended)
- Uppercase letters
- Lowercase letters
- Numbers
- Special characters

Displays:
- Strength level: Weak / Medium / Strong
- Strength score (0-100)
- Actionable feedback for improvement

### 3. Dictionary Attack Simulation
**Educational demonstration only**
- Loads a wordlist of common passwords
- Simulates password cracking attempt
- Measures:
  - Number of attempts needed
  - Time elapsed
  - Success/failure status

Shows why dictionary attacks only work against weak, common passwords.

### 4. Brute-Force Attack Simulation
**Intentionally limited for educational purposes**
- Maximum 4 characters (lowercase letters only)
- Demonstrates why brute-force is slow
- Helps understand:
  - Why longer passwords are exponentially harder to crack
  - Why bcrypt's slow hashing is important

### 5. User-Friendly GUI
Built with Tkinter:
- **Left Panel**: Target system for registration/login
- **Right Panel**: Attack simulator for demonstrations
- Real-time visual feedback
- Attack progress monitoring

## 📋 Requirements

- Python 3.7+
- bcrypt library

## 🚀 Installation

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or manually install bcrypt:
```bash
pip install bcrypt==4.1.2
```

### Step 2: Prepare Wordlist

The `wordlist.txt` file is included with common passwords for the dictionary attack simulation.

### Step 3: Run the Application

```bash
python main.py
```

## 💻 Usage Guide

### Registering a User

1. Click the **"Register"** tab
2. Enter a username (e.g., "alice")
3. Enter a password and watch the strength meter update in real-time
4. Read the feedback for improvement suggestions
5. Click **"Register User"**

**Test Different Passwords:**
- **Weak**: `abc` - Gets cracked quickly by dictionary attack
- **Medium**: `MyPass123` - More resistant but still not ideal
- **Strong**: `MyP@ssw0rd2024!` - Very resistant to attacks

### Logging In

1. Click the **"Login"** tab
2. Enter registered credentials
3. See success/failure status

### Viewing Registered Users

1. Click the **"Users"** tab
2. See all registered users
3. Click "Refresh List" to update

### Running an Attack Simulation

1. **Select Target User**: Choose a registered user from dropdown
2. **Select Attack Type**:
   - **Dictionary Attack**: Uses common passwords (faster)
   - **Brute Force**: Tries all combinations up to 4 chars (slower)
3. Click **"Start Attack"**
4. Watch progress in real-time
5. See results and statistics

### Observing the Differences

**Compare two users:**

1. Register "weak_user" with password: `abc`
   - Dictionary attack: Cracks in milliseconds
   - Shows why common passwords are dangerous

2. Register "strong_user" with password: `SecureP@ss2024`
   - Dictionary attack: Fails (not in common wordlist)
   - Brute force: Fails (too long for 4-char limit)
   - Demonstrates why strong passwords protect you

## 📊 Educational Insights

### What You'll Learn

1. **Password Strength Matters**
   - Weak passwords: Cracked in milliseconds
   - Strong passwords: Resistant to attacks

2. **Bcrypt is Slow (On Purpose)**
   - Uses salt (unique random prefix)
   - Uses multiple rounds (12 by default)
   - Makes dictionary attacks 1000x slower
   - Makes brute-force impractical

3. **Dictionary Attacks Work Against Common Passwords**
   - Only ~1% of weak passwords resist dictionary attacks
   - Completely useless against strong, unique passwords

4. **Brute-Force is Impractical**
   - 4 characters: ~475,000 attempts
   - 8 characters: ~2.8 trillion attempts
   - Longer = exponentially harder

5. **Why Security Matters**
   - One weak password = compromised account
   - Bcrypt + strong password = practical security

## 🔒 Security Notes

### What This Project DOES:
✓ Demonstrate educational security concepts
✓ Show password hashing with bcrypt
✓ Simulate attacks in safe environment
✓ Work entirely locally (no networking)
✓ Build security awareness

### What This Project DOES NOT:
✗ Attack real systems
✗ Target real accounts
✗ Connect to external networks
✗ Include credential theft
✗ Have persistence mechanisms
✗ Include malware functionality

**This is strictly for educational purposes.**

## 📁 Project Structure

```
password-defense-simulator/
│
├── main.py                 # Main GUI application
├── login_system.py         # User registration and login logic
├── strength_checker.py      # Password strength evaluation
├── attacks.py              # Dictionary attack and brute-force simulation
├── wordlist.txt            # Common passwords for dictionary attack
├── users.json              # Stores registered users (auto-created)
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🔑 Key Classes

### LoginSystem
- `register_user()` - Create new user with bcrypt hashing
- `login_user()` - Verify credentials
- `verify_password()` - Check plaintext against hash

### PasswordStrengthChecker
- `get_strength_level()` - Evaluate password strength
- `calculate_score()` - Get numeric strength (0-100)
- `check_criteria()` - Check specific password requirements

### DictionaryAttack
- `attack()` - Attempt dictionary attack simulation
- `load_wordlist()` - Load common passwords

### BruteForceAttack
- `attack()` - Attempt brute-force simulation (limited to 4 chars)
- `estimate_attempts()` - Calculate total possible combinations

## 🎓 Classroom Usage

### Demo Scenarios

1. **Introduction to Password Hashing**
   - Register a user
   - Show password hash in users.json
   - Explain why bcrypt is better than plain hashes

2. **Dictionary Attacks**
   - Register user with weak password ("password", "123456")
   - Run dictionary attack
   - Show how quickly it cracks

3. **Strong Passwords**
   - Register user with complex password
   - Run dictionary attack (fails)
   - Explain why complexity matters

4. **Brute-Force Limitations**
   - Show that 4-char limit cracks, but real passwords don't
   - Demonstrate exponential growth of attempts
   - Explain why password length is critical

### Discussion Points

- Why is bcrypt slower than SHA-256? (That's a feature, not a bug!)
- What makes a password "strong"?
- Why use salts in password hashing?
- How do real hackers actually crack passwords?
- What should you do to protect your accounts?

## 📝 Example Walkthrough

### Scenario: Testing Password Strength

1. **Register "demo_user" with weak password:**
   ```
   Username: demo_user
   Password: admin
   Result: Weak (Score: 15/100)
   Feedback: "Use at least 8 characters", "Add numbers", etc.
   ```

2. **Run Dictionary Attack:**
   - Attacks: ~10
   - Time: ~0.05 seconds
   - Result: **SUCCESS** - Password "admin" cracked

3. **Register "demo_user2" with strong password:**
   ```
   Username: demo_user2
   Password: MySecureP@ssw0rd2024!
   Result: Strong (Score: 95/100)
   Feedback: (None - all criteria met!)
   ```

4. **Run Dictionary Attack:**
   - Attacks: All ~50 in wordlist tried
   - Time: ~0.5 seconds
   - Result: **FAILED** - Password not in wordlist

## 🐛 Troubleshooting

### No wordlist.txt
If dictionary attack fails immediately, ensure `wordlist.txt` is in the same directory as `main.py`.

### bcrypt not installed
```bash
pip install bcrypt
```

### GUI doesn't appear
Ensure Tkinter is installed:
- **Windows/Mac**: Usually included with Python
- **Linux**: `sudo apt-get install python3-tk`

### users.json issues
Delete `users.json` to start fresh. It will be recreated automatically.

## 📚 Educational References

- OWASP: Password Hashing Cheat Sheet
- "Cracking Codes with Python" - Introduction to Cryptography
- NIST Special Publication 800-132: Password-Based Key Derivation

## 🙋 Questions & Feedback

This project demonstrates important security concepts:
- Never store plaintext passwords
- Always use bcrypt or similar (Argon2, scrypt)
- Encourage strong, unique passwords
- Understand attack methods to defend against them

## 📄 License

This educational project is provided for learning purposes only.

---

**Remember: With great knowledge comes great responsibility. Use this for education and defense, never for harm.**
