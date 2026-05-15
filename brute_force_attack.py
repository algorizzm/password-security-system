import itertools
import time
from login_system import LoginSystem

class BruteForceAttack:
    """
    Educational simulation of a brute-force attack.

    A brute-force attack tries all possible character combinations.
    INTENTIONALLY LIMITED to 4 characters for educational purposes.
    Real brute-force is impractical for longer passwords.
    """

    def __init__(self, max_length=4, charset='abcdefghijklmnopqrstuvwxyz'):
        """
        Args:
            max_length: Maximum password length to attempt (limited to 4 for demo)
            charset: Characters to use in attempts
        """
        if max_length > 4:
            raise ValueError("Brute-force limited to 4 characters for educational purposes")
        self.max_length = max_length
        self.charset = charset

    def attack(self, username, login_system, callback=None, stop_event=None):
        """
        Attempt brute-force attack on a user account.

        Args:
            username: Target username
            login_system: LoginSystem instance
            callback: Optional function for progress updates
                     callback(attempts, elapsed_time, current_attempt, success, cracked_password)
            stop_event: Optional threading.Event to signal early stop

        Returns: (success: bool, attempts: int, elapsed_time: float, cracked_password: str or None)
        """
        start_time = time.time()
        attempts = 0

        for length in range(1, self.max_length + 1):
            for attempt in itertools.product(self.charset, repeat=length):
                if stop_event and stop_event.is_set():
                    elapsed = time.time() - start_time
                    return False, attempts, elapsed, None

                password = ''.join(attempt)
                attempts += 1

                success, _ = login_system.login_user(username, password)
                elapsed = time.time() - start_time

                if callback:
                    callback(attempts, elapsed, password, success, password if success else None)

                if success:
                    return True, attempts, elapsed, password

        elapsed = time.time() - start_time
        return False, attempts, elapsed, None

    def estimate_attempts(self):
        """Estimate total attempts needed for full brute-force."""
        charset_size = len(self.charset)
        total = 0
        for length in range(1, self.max_length + 1):
            total += charset_size ** length
        return total
