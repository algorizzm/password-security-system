import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from login_system import LoginSystem
from strength_checker import PasswordStrengthChecker
from attacks import DictionaryAttack, BruteForceAttack
from password_analysis import PasswordAnalyzer

class PasswordDefenseSimulator:
    """Main GUI application for password attack/defense simulation."""

    def __init__(self, root):
        self.root = root
        self.root.title("Password Attack & Defense Simulator")

        # Start maximized (not true fullscreen)
        self.root.state('zoomed')

        # Allow resizing/minimize/maximize
        self.root.resizable(True, True)

        # Initialize core systems
        self.login_system = LoginSystem()
        self.strength_checker = PasswordStrengthChecker()
        self.dict_attack = DictionaryAttack()

        # Attack state
        self.attack_running = False
        self.attack_thread = None
        self.attack_stop_event = threading.Event()

        self.setup_ui()

    def setup_ui(self):
        """Setup the main UI with two main panels."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel: Target system
        left_panel = ttk.LabelFrame(main_frame, text="TARGET SYSTEM - User Registration & Login", padding="10")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.setup_target_system(left_panel)

        # Right panel: Attack simulator
        right_panel = ttk.LabelFrame(main_frame, text="ATTACK SIMULATOR - Educational Demo", padding="10")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.setup_attack_simulator(right_panel)

    def setup_target_system(self, parent):
        """Setup user registration and login interface."""
        # Notebook for tabs
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Registration tab
        reg_frame = ttk.Frame(notebook, padding="10")
        notebook.add(reg_frame, text="Register")
        self.setup_registration_tab(reg_frame)

        # Login tab
        login_frame = ttk.Frame(notebook, padding="10")
        notebook.add(login_frame, text="Login")
        self.setup_login_tab(login_frame)

        # Users tab
        users_frame = ttk.Frame(notebook, padding="10")
        notebook.add(users_frame, text="Users")
        self.setup_users_tab(users_frame)

    def setup_registration_tab(self, parent):
        """Setup user registration form."""
        # Username
        ttk.Label(parent, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.reg_username = ttk.Entry(parent, width=30)
        self.reg_username.grid(row=0, column=1, sticky=tk.EW, pady=5)

        # Password
        ttk.Label(parent, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.reg_password = ttk.Entry(parent, width=30, show="*")
        self.reg_password.grid(row=1, column=1, sticky=tk.EW, pady=5)
        self.reg_password.bind('<KeyRelease>', self.update_strength_meter)

        # Strength meter
        ttk.Label(parent, text="Strength:").grid(row=2, column=0, sticky=tk.W, pady=5)
        strength_frame = ttk.Frame(parent)
        strength_frame.grid(row=2, column=1, sticky=tk.EW, pady=5)

        self.strength_canvas = tk.Canvas(strength_frame, height=20, bg="white", highlightthickness=1)
        self.strength_canvas.pack(fill=tk.X)

        self.strength_label = ttk.Label(parent, text="Weak")
        self.strength_label.grid(row=3, column=1, sticky=tk.W, pady=2)

        # Feedback
        ttk.Label(parent, text="Feedback:").grid(row=4, column=0, sticky=tk.NW, pady=5)
        self.feedback_text = tk.Text(parent, height=6, width=35, wrap=tk.WORD)
        self.feedback_text.grid(row=4, column=1, sticky=tk.EW, pady=5)

        # Register button
        ttk.Button(parent, text="Register User", command=self.register_user).grid(row=5, column=1, sticky=tk.E, pady=10)

        parent.columnconfigure(1, weight=1)

    def setup_login_tab(self, parent):
        """Setup user login form."""
        ttk.Label(parent, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.login_username = ttk.Entry(parent, width=30)
        self.login_username.grid(row=0, column=1, sticky=tk.EW, pady=5)

        ttk.Label(parent, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.login_password = ttk.Entry(parent, width=30, show="*")
        self.login_password.grid(row=1, column=1, sticky=tk.EW, pady=5)

        ttk.Button(parent, text="Login", command=self.login_user).grid(row=2, column=1, sticky=tk.E, pady=10)

        self.login_status = ttk.Label(parent, text="", foreground="green")
        self.login_status.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=10)

        parent.columnconfigure(1, weight=1)

    def setup_users_tab(self, parent):
        """Display registered users with sub-tabs for analysis."""
        users_notebook = ttk.Notebook(parent)
        users_notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Registered Users List
        users_list_frame = ttk.Frame(users_notebook, padding="10")
        users_notebook.add(users_list_frame, text="Registered Users")

        ttk.Label(users_list_frame, text="Registered Users:").pack(anchor=tk.W, pady=5)
        self.users_listbox = tk.Listbox(users_list_frame, height=12, width=35)
        self.users_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.users_listbox.bind('<<ListboxSelect>>', self.on_user_selected)

        ttk.Button(users_list_frame, text="Refresh List", command=self.refresh_users_list).pack(pady=5)

        # Tab 2: Password Storage Analysis
        analysis_frame = ttk.Frame(users_notebook, padding="10")
        users_notebook.add(analysis_frame, text="Password Storage Analysis")
        self.setup_password_analysis_tab(analysis_frame)

        self.refresh_users_list()   

    def setup_password_analysis_tab(self, parent):
        """Setup password storage analysis and education interface."""
        # Create canvas with scrollbar for better layout
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # User Selection Section
        select_frame = ttk.LabelFrame(scrollable_frame, text="Select User for Analysis", padding="10")
        select_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(select_frame, text="User:").pack(side=tk.LEFT, padx=5)
        self.analysis_user_combo = ttk.Combobox(select_frame, state='readonly', width=30)
        self.analysis_user_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.analysis_user_combo.bind('<<ComboboxSelected>>', self.on_analysis_user_selected)

        ttk.Button(select_frame, text="Analyze", command=self.update_analysis_display).pack(side=tk.LEFT, padx=5)

        # Hash Display Section
        hash_frame = ttk.LabelFrame(scrollable_frame, text="Stored Password Hash (Read-Only)", padding="10")
        hash_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(hash_frame, text="Username:").pack(anchor=tk.W)
        self.analysis_username_label = ttk.Label(hash_frame, text="[None selected]", foreground="gray")
        self.analysis_username_label.pack(anchor=tk.W, padx=20, pady=5)

        ttk.Label(hash_frame, text="bcrypt Hash:").pack(anchor=tk.W, pady=(10, 0))
        self.analysis_hash_text = tk.Text(hash_frame, height=4, width=50, wrap=tk.WORD, bg="light gray")
        self.analysis_hash_text.pack(fill=tk.X, padx=20, pady=5)
        self.analysis_hash_text.config(state=tk.DISABLED)

        ttk.Label(hash_frame, text="Hash Length:").pack(anchor=tk.W)
        self.analysis_hash_length = ttk.Label(hash_frame, text="0 characters")
        self.analysis_hash_length.pack(anchor=tk.W, padx=20, pady=5)

        # Hash Structure Breakdown
        structure_frame = ttk.LabelFrame(scrollable_frame, text="bcrypt Hash Structure Breakdown", padding="10")
        structure_frame.pack(fill=tk.X, padx=5, pady=5)

        self.analysis_structure_text = tk.Text(structure_frame, height=6, width=50, wrap=tk.WORD, bg="lightyellow")
        self.analysis_structure_text.pack(fill=tk.X, padx=5, pady=5)
        self.analysis_structure_text.config(state=tk.DISABLED)

        # Salt Demonstration
        demo_frame = ttk.LabelFrame(scrollable_frame, text="Salt Uniqueness Demonstration", padding="10")
        demo_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(demo_frame, text="Click to generate multiple hashes of the same password:").pack(anchor=tk.W, pady=5)
        ttk.Button(demo_frame, text="Generate Example Hashes", command=self.show_example_hashes).pack(pady=5)

        self.demo_result_text = tk.Text(demo_frame, height=8, width=50, wrap=tk.WORD, bg="lightblue")
        self.demo_result_text.pack(fill=tk.X, padx=5, pady=5)
        self.demo_result_text.config(state=tk.DISABLED)

        # Security Comparison
        comparison_frame = ttk.LabelFrame(scrollable_frame, text="Plaintext vs bcrypt Storage Comparison", padding="10")
        comparison_frame.pack(fill=tk.X, padx=5, pady=5)

        self.comparison_text = tk.Text(comparison_frame, height=10, width=50, wrap=tk.WORD, bg="#fff5e1")
        self.comparison_text.pack(fill=tk.X, padx=5, pady=5)
        self.comparison_text.config(state=tk.DISABLED)

        self.show_security_comparison()
        self.refresh_analysis_users()

    def refresh_analysis_users(self):
        """Refresh user list in analysis dropdown."""
        users = self.login_system.get_all_users()
        self.analysis_user_combo['values'] = users
        if users:
            self.analysis_user_combo.current(0)
            self.on_analysis_user_selected()
        else:
            self.clear_analysis_display()

    def on_analysis_user_selected(self, event=None):
        """Handle user selection in analysis tab."""
        self.update_analysis_display()

    def on_user_selected(self, event=None):
        """Handle user selection in users list (for sync)."""
        selection = self.users_listbox.curselection()
        if selection:
            user = self.users_listbox.get(selection[0])
            idx = self.analysis_user_combo['values'].index(user)
            self.analysis_user_combo.current(idx)
            self.update_analysis_display()

    def update_analysis_display(self):
        """Update analysis display with selected user's hash info."""
        user = self.analysis_user_combo.get()
        if not user:
            self.clear_analysis_display()
            return

        user_hash = self.login_system.get_user_hash(user)
        if not user_hash:
            self.clear_analysis_display()
            return

        # Update username
        self.analysis_username_label.config(text=user, foreground="black")

        # Update hash display
        self.analysis_hash_text.config(state=tk.NORMAL)
        self.analysis_hash_text.delete(1.0, tk.END)
        self.analysis_hash_text.insert(tk.END, user_hash)
        self.analysis_hash_text.config(state=tk.DISABLED)

        # Update hash length
        self.analysis_hash_length.config(text=f"{len(user_hash)} characters (standard bcrypt: 60 chars)")

        # Update structure breakdown
        analysis = PasswordAnalyzer.parse_bcrypt_hash(user_hash)
        if analysis:
            self.analysis_structure_text.config(state=tk.NORMAL)
            self.analysis_structure_text.delete(1.0, tk.END)
            breakdown_text = "🔐 BCRYPT HASH STRUCTURE:\n\n"
            for line in analysis['breakdown']:
                breakdown_text += line + "\n"
            self.analysis_structure_text.insert(tk.END, breakdown_text)
            self.analysis_structure_text.config(state=tk.DISABLED)

    def clear_analysis_display(self):
        """Clear analysis display when no user selected."""
        self.analysis_username_label.config(text="[No user selected]", foreground="gray")

        self.analysis_hash_text.config(state=tk.NORMAL)
        self.analysis_hash_text.delete(1.0, tk.END)
        self.analysis_hash_text.insert(tk.END, "[No user selected]")
        self.analysis_hash_text.config(state=tk.DISABLED)

        self.analysis_hash_length.config(text="0 characters")

        self.analysis_structure_text.config(state=tk.NORMAL)
        self.analysis_structure_text.delete(1.0, tk.END)
        self.analysis_structure_text.insert(tk.END, "Select a user to view hash structure")
        self.analysis_structure_text.config(state=tk.DISABLED)

    def show_example_hashes(self):
        """Generate and display multiple hashes of the same password."""
        demo_result = PasswordAnalyzer.generate_example_hashes("admin123", count=3)

        display_text = "📊 EXAMPLE: Hashing 'admin123' three times:\n\n"

        for i, hash_val in enumerate(demo_result['hashes'], 1):
            display_text += f"Hash {i}:\n{hash_val}\n\n"

        display_text += "━" * 48 + "\n"
        display_text += "🔑 WHY THEY'RE DIFFERENT:\n\n"
        for explanation in demo_result['explanation']:
            display_text += f"• {explanation}\n"

        self.demo_result_text.config(state=tk.NORMAL)
        self.demo_result_text.delete(1.0, tk.END)
        self.demo_result_text.insert(tk.END, display_text)
        self.demo_result_text.config(state=tk.DISABLED)

    def show_security_comparison(self):
        """Display plaintext vs bcrypt security comparison."""
        comparison_text = "⚠️ PLAINTEXT STORAGE (INSECURE):\n"
        comparison_text += "  password: 'MyPassword123'\n\n"
        comparison_text += "If database is leaked:\n"
        comparison_text += "✗ Attacker immediately knows the password\n"
        comparison_text += "✗ Can access account instantly\n"
        comparison_text += "✗ No computational cost to crack\n"
        comparison_text += "\n" + "─" * 48 + "\n\n"

        comparison_text += "✓ BCRYPT STORAGE (SECURE):\n"
        comparison_text += "  password_hash: '$2b$12$kjasdhfkasjdfhkjasdf...'\n\n"
        comparison_text += "If database is leaked:\n"
        comparison_text += "✓ Attacker sees only the hash, not the password\n"
        comparison_text += "✓ Bcrypt designed to be computationally expensive\n"
        comparison_text += "✓ Each hash has unique random salt\n"
        comparison_text += "✓ Even weak passwords take time to crack\n"
        comparison_text += "✓ Each password must be cracked individually\n\n"

        comparison_text += "💡 KEY TAKEAWAY:\n"
        comparison_text += "Bcrypt + Strong Password = Maximum Security"

        self.comparison_text.config(state=tk.NORMAL)
        self.comparison_text.delete(1.0, tk.END)
        self.comparison_text.insert(tk.END, comparison_text)
        self.comparison_text.config(state=tk.DISABLED)

    def setup_attack_simulator(self, parent):
        """Setup attack simulation interface."""
        # Target selection
        ttk.Label(parent, text="Target User:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.attack_target = ttk.Combobox(parent, width=25, state='readonly')
        self.attack_target.grid(row=0, column=1, sticky=tk.EW, pady=5)
        ttk.Button(parent, text="Refresh", command=self.refresh_attack_targets).grid(row=0, column=2, pady=5)

        # Attack type selection
        ttk.Label(parent, text="Attack Type:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.attack_type = ttk.Combobox(parent, values=["Dictionary Attack", "Brute Force (4 chars)"], state='readonly', width=25)
        self.attack_type.set("Dictionary Attack")
        self.attack_type.grid(row=1, column=1, columnspan=2, sticky=tk.EW, pady=5)

        # Attack buttons
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=10)

        self.attack_button = ttk.Button(button_frame, text="Start Attack", command=self.start_attack)
        self.attack_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.stop_attack_button = ttk.Button(button_frame, text="Stop Attack", command=self.stop_attack, state=tk.DISABLED)
        self.stop_attack_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Progress display
        ttk.Label(parent, text="Attack Progress:").grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))

        self.progress_text = scrolledtext.ScrolledText(parent, height=15, width=45, wrap=tk.WORD)
        self.progress_text.grid(row=4, column=0, columnspan=3, sticky=tk.NSEW, pady=5)

        # Results summary
        ttk.Label(parent, text="Results:").grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))

        self.results_label = ttk.Label(parent, text="Waiting for attack...", foreground="blue")
        self.results_label.grid(row=6, column=0, columnspan=3, sticky=tk.W, pady=5)

        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(4, weight=1)

    def update_strength_meter(self, event=None):
        """Update password strength meter in real-time."""
        password = self.reg_password.get()
        strength, score, feedback = self.strength_checker.get_strength_level(password)
        color = self.strength_checker.get_strength_color(password)

        # Update canvas
        self.strength_canvas.delete("all")
        bar_width = (score / 100) * 200
        self.strength_canvas.create_rectangle(0, 0, bar_width, 20, fill=color)

        # Update label
        self.strength_label.config(text=f"{strength} ({score}/100)")

        # Update feedback
        self.feedback_text.config(state=tk.NORMAL)
        self.feedback_text.delete(1.0, tk.END)
        if feedback:
            self.feedback_text.insert(tk.END, "\n".join(feedback))
        self.feedback_text.config(state=tk.DISABLED)

    def register_user(self):
        """Handle user registration."""
        username = self.reg_username.get()
        password = self.reg_password.get()

        if not username or not password:
            messagebox.showerror("Error", "Username and password required")
            return

        success, message = self.login_system.register_user(username, password)

        if success:
            messagebox.showinfo("Success", message)
            self.reg_username.delete(0, tk.END)
            self.reg_password.delete(0, tk.END)
            self.feedback_text.config(state=tk.NORMAL)
            self.feedback_text.delete(1.0, tk.END)
            self.feedback_text.config(state=tk.DISABLED)
            self.strength_canvas.delete("all")
            self.refresh_users_list()
            self.refresh_attack_targets()
        else:
            messagebox.showerror("Error", message)

    def login_user(self):
        """Handle user login."""
        username = self.login_username.get()
        password = self.login_password.get()

        success, message = self.login_system.login_user(username, password)

        if success:
            self.login_status.config(text=f"✓ {message}", foreground="green")
            self.login_password.delete(0, tk.END)
        else:
            self.login_status.config(text=f"✗ {message}", foreground="red")

    def refresh_users_list(self):
        """Refresh the users listbox and analysis dropdown."""
        self.users_listbox.delete(0, tk.END)
        users = self.login_system.get_all_users()
        for user in users:
            self.users_listbox.insert(tk.END, user)
        self.refresh_analysis_users()

    def refresh_attack_targets(self):
        """Refresh attack target dropdown."""
        users = self.login_system.get_all_users()
        self.attack_target['values'] = users
        if users:
            self.attack_target.current(0)

    def start_attack(self):
        """Start attack simulation in separate thread."""
        if self.attack_running:
            messagebox.showwarning("Warning", "Attack already in progress")
            return

        target = self.attack_target.get()
        attack_type = self.attack_type.get()

        if not target:
            messagebox.showerror("Error", "Select a target user")
            return

        self.attack_running = True
        self.attack_stop_event.clear()
        self.attack_button.config(state=tk.DISABLED)
        self.stop_attack_button.config(state=tk.NORMAL)
        self.progress_text.config(state=tk.NORMAL)
        self.progress_text.delete(1.0, tk.END)

        if attack_type == "Dictionary Attack":
            self.attack_thread = threading.Thread(
                target=self.run_dictionary_attack,
                args=(target,),
                daemon=True
            )
        else:
            self.attack_thread = threading.Thread(
                target=self.run_brute_force_attack,
                args=(target,),
                daemon=True
            )

        self.attack_thread.start()

    def run_dictionary_attack(self, target):
        """Run dictionary attack in thread."""
        def callback(attempts, elapsed, success, password):
            msg = f"Attempts: {attempts} | Time: {elapsed:.2f}s"
            if success:
                msg += f" | SUCCESS! Password: {password}"
            self.root.after(0, lambda: self.update_progress(msg, success))

        success, attempts, elapsed, password = self.dict_attack.attack(
            target, self.login_system, callback, self.attack_stop_event
        )
        self.finalize_attack(success, attempts, elapsed, password)

    def run_brute_force_attack(self, target):
        """Run brute-force attack in thread."""
        attack = BruteForceAttack(max_length=4)

        def callback(attempts, elapsed, current, success, password):
            msg = f"Trying: {current} | Attempts: {attempts} | Time: {elapsed:.2f}s"
            if success:
                msg += f" | SUCCESS! Password: {password}"
            self.root.after(0, lambda: self.update_progress(msg, success))

        success, attempts, elapsed, password = attack.attack(
            target, self.login_system, callback, self.attack_stop_event
        )
        self.finalize_attack(success, attempts, elapsed, password)

    def update_progress(self, message, success=False):
        """Update progress display."""
        self.progress_text.insert(tk.END, message + "\n")
        self.progress_text.see(tk.END)
        if success:
            self.progress_text.config(foreground="green")

    def stop_attack(self):
        """Stop the currently running attack."""
        if self.attack_running:
            self.attack_stop_event.set()
            self.stop_attack_button.config(state=tk.DISABLED)
            self.progress_text.insert(tk.END, "\n[Attack stopped by user]\n")
            self.progress_text.see(tk.END)

    def finalize_attack(self, success, attempts, elapsed, password):
        """Finalize attack and show results."""
        def finish():
            self.attack_running = False
            self.attack_button.config(state=tk.NORMAL)
            self.stop_attack_button.config(state=tk.DISABLED)

            is_stopped = self.attack_stop_event.is_set()

            if success:
                result = f"✓ ATTACK SUCCESSFUL! Password cracked: '{password}'"
                self.results_label.config(text=result, foreground="red")
            elif is_stopped:
                result = "⏹ Attack stopped by user."
                self.results_label.config(text=result, foreground="orange")
            else:
                result = "✗ Attack failed. Password not found in wordlist/brute-force space."
                self.results_label.config(text=result, foreground="blue")

            self.progress_text.insert(tk.END, f"\n\n--- Attack Summary ---\n")
            self.progress_text.insert(tk.END, f"Total Attempts: {attempts}\n")
            self.progress_text.insert(tk.END, f"Time Elapsed: {elapsed:.2f} seconds\n")
            if success:
                self.progress_text.insert(tk.END, f"Result: SUCCESS\n")
            elif is_stopped:
                self.progress_text.insert(tk.END, f"Result: STOPPED BY USER\n")
            else:
                self.progress_text.insert(tk.END, f"Result: FAILED\n")
            self.progress_text.see(tk.END)
            self.progress_text.config(state=tk.DISABLED)

        self.root.after(0, finish)

def main():
    """Launch the application."""
    root = tk.Tk()
    app = PasswordDefenseSimulator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
