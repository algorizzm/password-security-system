import time

class DictionaryAttack:
    """
    Educational simulation of a dictionary attack.

    A dictionary attack tries common passwords from a wordlist.
    This is much faster than brute-force but only works with common passwords.
    """

    def __init__(self, wordlist_file='wordlist.txt'):
        self.wordlist_file = wordlist_file
        self.wordlist = self.load_wordlist()

    def load_wordlist(self):
        """Load wordlist from file."""
        try:
            with open(self.wordlist_file, 'r') as f:
                return [word.strip() for word in f.readlines()]
        except FileNotFoundError:
            return []

    def attack(self, username, login_system, callback=None, stop_event=None):
        """
        Attempt dictionary attack on a user account.

        Args:
            username: Target username
            login_system: LoginSystem instance
            callback: Optional function called with progress updates
                     callback(attempts, elapsed_time, success, cracked_password)
            stop_event: Optional threading.Event to signal early stop

        Returns: (success: bool, attempts: int, elapsed_time: float, cracked_password: str or None)
        """
        if not self.wordlist:
            return False, 0, 0, None

        start_time = time.time()
        attempts = 0

        for password in self.wordlist:
            if stop_event and stop_event.is_set():
                elapsed = time.time() - start_time
                return False, attempts, elapsed, None

            attempts += 1
            success, _ = login_system.login_user(username, password)

            elapsed = time.time() - start_time

            if callback:
                callback(attempts, elapsed, success, password if success else None)

            if success:
                return True, attempts, elapsed, password

        elapsed = time.time() - start_time
        return False, attempts, elapsed, None

