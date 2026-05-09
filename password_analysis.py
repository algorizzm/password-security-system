import bcrypt

class PasswordAnalyzer:
    """Educational helper for analyzing and visualizing bcrypt password storage."""

    @staticmethod
    def parse_bcrypt_hash(hash_string):
        """
        Parse bcrypt hash structure for educational visualization.

        Returns dict with hash components explained.
        Example hash: $2b$12$saltpart...hashedpart
        """
        if not hash_string or not hash_string.startswith('$'):
            return None

        parts = hash_string.split('$')

        if len(parts) < 4:
            return None

        analysis = {
            'full_hash': hash_string,
            'length': len(hash_string),
            'version': parts[1],  # e.g., "2b"
            'cost_factor': parts[2],  # e.g., "12"
            'salt_and_hash': f"${parts[3]}${''.join(parts[4:])}",  # Salt + hash combined
        }

        # Educational breakdown
        analysis['breakdown'] = [
            f"$2b$ → bcrypt version identifier (2b = current standard)",
            f"${parts[2]}$ → Cost factor (work factor = 2^{parts[2]}={2**int(parts[2])} rounds)",
            f"Salt (22 chars) → Random unique salt added to prevent rainbow tables",
            f"Hash (31 chars) → Computationally expensive output"
        ]

        return analysis

    @staticmethod
    def generate_example_hashes(password="admin123", count=3):
        """
        Generate multiple hashes of the same password to show salt uniqueness.

        Educational demonstration of why bcrypt produces different outputs
        even for identical passwords.
        """
        hashes = []
        for i in range(count):
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
            hashes.append(hashed.decode('utf-8'))

        return {
            'password': password,
            'hashes': hashes,
            'explanation': [
                "bcrypt automatically generates a unique random salt for every hash.",
                "Notice how ALL three hashes are different, even though the password is identical.",
                "This happens because bcrypt adds a random salt before hashing.",
                "Random salts prevent attackers from using precomputed 'rainbow tables'.",
                "Each time you hash the same password, you get a completely different result.",
                "During login, bcrypt re-extracts the salt from the stored hash and uses it to verify the password."
            ]
        }

    @staticmethod
    def get_security_explanation(password_strength, hash_exists=True):
        """
        Provide educational explanation of password security concepts.
        """
        explanations = {
            'plaintext_danger': [
                "❌ PLAINTEXT STORAGE (INSECURE):",
                "  • If database is leaked, all passwords are exposed",
                "  • Attackers can immediately access user accounts",
                "  • No computational cost to crack - instant access",
                "  • Used by very few legitimate systems (only for demos)"
            ],
            'bcrypt_secure': [
                "✓ BCRYPT STORAGE (SECURE):",
                "  • If database is leaked, passwords are still protected",
                "  • Each hash has a unique random salt",
                "  • Computationally expensive to crack (by design)",
                "  • Even weak passwords take significant time to break",
                "  • Industry standard for password hashing"
            ],
            'salt_importance': [
                "🔑 WHY SALTS MATTER:",
                "  • Salt = random data added before hashing",
                "  • Each user's salt is unique",
                "  • Prevents 'rainbow table' attacks (precomputed hashes)",
                "  • Two identical passwords = completely different hashes",
                "  • Attackers must crack each password individually"
            ],
            'work_factor': [
                "⏱️  COST FACTOR (WORK FACTOR):",
                "  • bcrypt uses a configurable 'cost' parameter",
                "  • Cost = 2^{cost_factor} = number of iterations",
                "  • Higher cost = slower hashing = harder to crack",
                "  • Default (12) means 2^12 = 4,096 iterations",
                "  • Makes brute-force attacks 1000s of times slower",
                "  • Can be increased as computers get faster"
            ],
            'weak_password_note': [
                "⚠️  IMPORTANT - HASHING DOESN'T MAKE WEAK PASSWORDS STRONG:",
                "  • bcrypt slows down attack, but doesn't eliminate it",
                "  • Weak passwords (like 'admin', 'password') can still be cracked",
                "  • bcrypt protects against brute-force, but not dictionary attacks",
                "  • Use STRONG passwords + bcrypt for best security",
                "  • Strong password = hard to guess, Long = slow to brute-force"
            ]
        }
        return explanations

    @staticmethod
    def format_hash_display(hash_string):
        """Format hash for readable display with line breaks."""
        if len(hash_string) > 40:
            # Split into readable chunks
            return f"{hash_string[:20]}\n{hash_string[20:40]}\n{hash_string[40:]}"
        return hash_string
