import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from login_system import LoginSystem
from strength_checker import PasswordStrengthChecker
from attacks import DictionaryAttack, BruteForceAttack

class PasswordDefenseSimulator:
    """Main GUI application for password attack/defense simulation."""

    def __init__(self, root):
        self.root = root
        self.root.title("Password Attack & Defense Simulator")
        self.root.geometry("1000x700")
        self.root.resizable(False, False)

        # Initialize core systems
        self.login_system = LoginSystem()
        self.strength_checker = PasswordStrengthChecker()
        self.dict_attack = DictionaryAttack()

        # Attack state
        self.attack_running = False
        self.attack_thread = None

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
        """Display registered users."""
        ttk.Label(parent, text="Registered Users:").pack(anchor=tk.W, pady=5)

        self.users_listbox = tk.Listbox(parent, height=12, width=35)
        self.users_listbox.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Button(parent, text="Refresh List", command=self.refresh_users_list).pack(pady=5)

        self.refresh_users_list()

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

        # Attack button
        self.attack_button = ttk.Button(parent, text="Start Attack", command=self.start_attack)
        self.attack_button.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=10)

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
        """Refresh the users listbox."""
        self.users_listbox.delete(0, tk.END)
        users = self.login_system.get_all_users()
        for user in users:
            self.users_listbox.insert(tk.END, user)

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
        self.attack_button.config(state=tk.DISABLED)
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

        success, attempts, elapsed, password = self.dict_attack.attack(target, self.login_system, callback)
        self.finalize_attack(success, attempts, elapsed, password)

    def run_brute_force_attack(self, target):
        """Run brute-force attack in thread."""
        attack = BruteForceAttack(max_length=4)

        def callback(attempts, elapsed, current, success, password):
            msg = f"Trying: {current} | Attempts: {attempts} | Time: {elapsed:.2f}s"
            if success:
                msg += f" | SUCCESS! Password: {password}"
            self.root.after(0, lambda: self.update_progress(msg, success))

        success, attempts, elapsed, password = attack.attack(target, self.login_system, callback)
        self.finalize_attack(success, attempts, elapsed, password)

    def update_progress(self, message, success=False):
        """Update progress display."""
        self.progress_text.insert(tk.END, message + "\n")
        self.progress_text.see(tk.END)
        if success:
            self.progress_text.config(foreground="green")

    def finalize_attack(self, success, attempts, elapsed, password):
        """Finalize attack and show results."""
        def finish():
            self.attack_running = False
            self.attack_button.config(state=tk.NORMAL)

            if success:
                result = f"✓ ATTACK SUCCESSFUL! Password cracked: '{password}'"
                self.results_label.config(text=result, foreground="red")
            else:
                result = "✗ Attack failed. Password not found in wordlist/brute-force space."
                self.results_label.config(text=result, foreground="blue")

            self.progress_text.insert(tk.END, f"\n\n--- Attack Summary ---\n")
            self.progress_text.insert(tk.END, f"Total Attempts: {attempts}\n")
            self.progress_text.insert(tk.END, f"Time Elapsed: {elapsed:.2f} seconds\n")
            self.progress_text.insert(tk.END, f"Result: {'SUCCESS' if success else 'FAILED'}\n")
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
