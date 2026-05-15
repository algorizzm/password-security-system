import tkinter as tk
import tkinter.font
from tkinter import ttk, messagebox, scrolledtext
import threading
from login_system import LoginSystem
from strength_checker import PasswordStrengthChecker
from dictionary_attack import DictionaryAttack, FastDictionaryAttack
from brute_force_attack import BruteForceAttack, FastBruteForceAttack
from password_analysis import PasswordAnalyzer

# ══════════════════════════════════════════════════════════════════════
#  DESIGN TOKENS  —  60 / 30 / 10 palette
# ══════════════════════════════════════════════════════════════════════
# 60 % — Base
C_BASE        = "#1E1E2E"   # root window / main background
# 30 % — Secondary
C_CARD        = "#2B2B40"   # cards, panels, labelframes
C_INPUT       = "#181825"   # entry / text widget fill
# 10 % — Accent
C_ACCENT      = "#89B4FA"   # buttons, progress bar, active tab
C_ACCENT_HOV  = "#A6ADC8"   # button hover
# Text
C_TEXT_PRI    = "#FFFFFF"   # titles, button labels
C_TEXT_SEC    = "#CDD6F4"   # body labels, descriptions
C_TEXT_MUT    = "#6C7086"   # placeholder / muted
# Borders / misc
C_BORDER      = "#45475A"
C_SUCCESS     = "#A6E3A1"
C_DANGER      = "#F38BA8"
C_WARNING     = "#FAB387"

# Font tuples — populated inside apply_theme() once a root window exists
# (tkinter.font.families() requires a live Tk instance)
F_TITLE  = None
F_HEADER = None
F_BODY   = None
F_SMALL  = None
F_MONO   = ("Consolas", 9)


def apply_theme(root: tk.Tk) -> ttk.Style:
    """
    Apply the Dark-Slate SaaS theme to every ttk widget.
    Uses the 'clam' base theme for maximum style-map coverage.
    Call this BEFORE building any widgets.
    """
    # Resolve font family now that a root window exists
    global F_TITLE, F_HEADER, F_BODY, F_SMALL
    _families = tkinter.font.families(root)
    _ff = "Segoe UI Variable" if "Segoe UI Variable" in _families else "Segoe UI"
    F_TITLE  = (_ff, 13, "bold")
    F_HEADER = (_ff, 10, "bold")
    F_BODY   = (_ff, 10)
    F_SMALL  = (_ff,  9)

    style = ttk.Style(root)
    style.theme_use("clam")

    # ── Root window ────────────────────────────────────────────────
    root.configure(bg=C_BASE)

    # ── Global defaults ────────────────────────────────────────────
    style.configure(".",
        background=C_BASE,
        foreground=C_TEXT_SEC,
        font=F_BODY,
        bordercolor=C_BORDER,
        focuscolor=C_ACCENT,
        troughcolor=C_INPUT,
        selectbackground=C_ACCENT,
        selectforeground=C_TEXT_PRI,
        relief="flat",
        borderwidth=0,
    )

    # ══ TFrame ════════════════════════════════════════════════════
    style.configure("TFrame", background=C_BASE)
    # Card.TFrame — secondary elevation (panels, containers)
    style.configure("Card.TFrame",
        background=C_CARD,
        relief="flat",
        borderwidth=0,
    )

    # ══ TLabel ════════════════════════════════════════════════════
    style.configure("TLabel",
        background=C_BASE,
        foreground=C_TEXT_SEC,
        font=F_BODY,
    )
    # Labels that live inside Card.TFrame / LabelFrame must share the card bg
    style.configure("Card.TLabel",
        background=C_CARD,
        foreground=C_TEXT_SEC,
        font=F_BODY,
    )
    style.configure("Title.TLabel",
        background=C_BASE,
        foreground=C_TEXT_PRI,
        font=F_TITLE,
    )
    style.configure("Header.TLabel",
        background=C_CARD,
        foreground=C_TEXT_PRI,
        font=F_HEADER,
    )
    style.configure("Muted.TLabel",
        background=C_BASE,
        foreground=C_TEXT_MUT,
        font=F_SMALL,
    )
    style.configure("CardMuted.TLabel",
        background=C_CARD,
        foreground=C_TEXT_MUT,
        font=F_SMALL,
    )
    style.configure("Success.TLabel",
        background=C_BASE,
        foreground=C_SUCCESS,
        font=F_HEADER,
    )
    style.configure("Danger.TLabel",
        background=C_BASE,
        foreground=C_DANGER,
        font=F_HEADER,
    )
    style.configure("Warning.TLabel",
        background=C_BASE,
        foreground=C_WARNING,
        font=F_HEADER,
    )

    # ══ TLabelFrame ═══════════════════════════════════════════════
    # Flat elevation: card bg + accent-coloured title text
    style.configure("TLabelframe",
        background=C_CARD,
        foreground=C_ACCENT,
        font=F_HEADER,
        bordercolor=C_BORDER,
        relief="solid",
        borderwidth=1,
        padding=10,
    )
    style.configure("TLabelframe.Label",
        background=C_CARD,
        foreground=C_ACCENT,
        font=F_HEADER,
        padding=(4, 2),
    )

    # ══ TNotebook ═════════════════════════════════════════════════
    style.configure("TNotebook",
        background=C_BASE,
        bordercolor=C_BORDER,
        tabmargins=[2, 5, 2, 0],
        relief="flat",
        borderwidth=0,
    )
    style.configure("TNotebook.Tab",
        background=C_INPUT,
        foreground=C_TEXT_MUT,
        font=F_BODY,
        padding=[14, 7],
        borderwidth=0,
        focuscolor=C_BASE,
    )
    style.map("TNotebook.Tab",
        background=[("selected", C_CARD),  ("active", C_CARD)],
        foreground=[("selected", C_TEXT_PRI), ("active", C_TEXT_SEC)],
        expand=[("selected", [1, 1, 1, 0])],
    )

    # ══ TButton ═══════════════════════════════════════════════════
    style.configure("TButton",
        background=C_ACCENT,
        foreground=C_TEXT_PRI,
        font=F_HEADER,
        padding=[14, 7],
        borderwidth=0,
        relief="flat",
        focusthickness=0,
        anchor="center",
    )
    style.map("TButton",
        background=[
            ("active",   C_ACCENT_HOV),
            ("disabled", C_CARD),
            ("pressed",  C_BORDER),
        ],
        foreground=[
            ("disabled", C_TEXT_MUT),
        ],
        relief=[("pressed", "flat")],
    )
    # Ghost / secondary button
    style.configure("Ghost.TButton",
        background=C_CARD,
        foreground=C_TEXT_SEC,
        font=F_SMALL,
        padding=[10, 5],
        borderwidth=1,
        relief="solid",
        focusthickness=0,
    )
    style.map("Ghost.TButton",
        background=[("active", C_BORDER), ("disabled", C_INPUT)],
        foreground=[("disabled", C_TEXT_MUT)],
    )
    # Danger button (Stop Attack)
    style.configure("Danger.TButton",
        background="#313244",
        foreground=C_DANGER,
        font=F_HEADER,
        padding=[14, 7],
        borderwidth=1,
        relief="solid",
        focusthickness=0,
    )
    style.map("Danger.TButton",
        background=[("active", "#45475A"), ("disabled", C_INPUT)],
        foreground=[("disabled", C_TEXT_MUT)],
    )

    # ══ TEntry ════════════════════════════════════════════════════
    style.configure("TEntry",
        fieldbackground=C_INPUT,
        foreground=C_TEXT_PRI,
        insertcolor=C_TEXT_PRI,
        selectbackground=C_ACCENT,
        selectforeground=C_TEXT_PRI,
        bordercolor=C_BORDER,
        lightcolor=C_BORDER,
        darkcolor=C_BORDER,
        font=F_BODY,
        padding=[8, 5],
        relief="solid",
        borderwidth=1,
    )
    style.map("TEntry",
        bordercolor=[("focus", C_ACCENT)],
        lightcolor=[("focus", C_ACCENT)],
        darkcolor=[("focus", C_ACCENT)],
    )

    # ══ TCombobox ═════════════════════════════════════════════════
    style.configure("TCombobox",
        fieldbackground=C_INPUT,
        background=C_CARD,
        foreground=C_TEXT_PRI,
        selectbackground=C_ACCENT,
        selectforeground=C_TEXT_PRI,
        arrowcolor=C_ACCENT,
        bordercolor=C_BORDER,
        lightcolor=C_BORDER,
        darkcolor=C_BORDER,
        font=F_BODY,
        padding=[8, 5],
        relief="solid",
        borderwidth=1,
    )
    style.map("TCombobox",
        fieldbackground=[("readonly", C_INPUT)],
        foreground=[("readonly", C_TEXT_PRI)],
        bordercolor=[("focus", C_ACCENT)],
        lightcolor=[("focus", C_ACCENT)],
        darkcolor=[("focus", C_ACCENT)],
    )
    # Dropdown list colours (option_add is the only reliable way)
    root.option_add("*TCombobox*Listbox.background",       C_CARD)
    root.option_add("*TCombobox*Listbox.foreground",       C_TEXT_SEC)
    root.option_add("*TCombobox*Listbox.selectBackground", C_ACCENT)
    root.option_add("*TCombobox*Listbox.selectForeground", C_TEXT_PRI)
    root.option_add("*TCombobox*Listbox.font",             F_BODY)

    # ══ TScrollbar ════════════════════════════════════════════════
    style.configure("TScrollbar",
        background=C_CARD,
        troughcolor=C_INPUT,
        arrowcolor=C_TEXT_MUT,
        bordercolor=C_BASE,
        relief="flat",
        borderwidth=0,
        arrowsize=12,
    )
    style.map("TScrollbar",
        background=[("active", C_ACCENT)],
        arrowcolor=[("active", C_TEXT_PRI)],
    )

    # ══ TProgressbar ══════════════════════════════════════════════
    # Sleek thin bar — accent fill on dark trough
    style.configure("Accent.Horizontal.TProgressbar",
        troughcolor=C_INPUT,
        background=C_ACCENT,
        bordercolor=C_BASE,
        lightcolor=C_ACCENT,
        darkcolor=C_ACCENT,
        thickness=10,
        relief="flat",
        borderwidth=0,
    )

    # ══ TScale (speed slider) ══════════════════════════════════════
    style.configure("TScale",
        background=C_BASE,
        troughcolor=C_INPUT,
        sliderlength=18,
        sliderrelief="flat",
        borderwidth=0,
    )
    style.map("TScale",
        background=[("active", C_BASE)],
        troughcolor=[("active", C_INPUT)],
    )

    # ══ TCheckbutton ══════════════════════════════════════════════
    style.configure("TCheckbutton",
        background=C_BASE,
        foreground=C_TEXT_SEC,
        font=F_SMALL,
        focusthickness=0,
        indicatorcolor=C_INPUT,
        indicatorbackground=C_INPUT,
    )
    style.map("TCheckbutton",
        background=[("active", C_BASE)],
        foreground=[("active", C_TEXT_PRI)],
        indicatorcolor=[("selected", C_ACCENT)],
    )

    # ══ TSeparator ════════════════════════════════════════════════
    style.configure("TSeparator", background=C_BORDER)

    # ══ Listbox (classic widget — option_add only) ═════════════════
    root.option_add("*Listbox.background",       C_INPUT)
    root.option_add("*Listbox.foreground",       C_TEXT_SEC)
    root.option_add("*Listbox.selectBackground", C_ACCENT)
    root.option_add("*Listbox.selectForeground", C_TEXT_PRI)
    root.option_add("*Listbox.font",             F_BODY)
    root.option_add("*Listbox.borderWidth",      "0")
    root.option_add("*Listbox.relief",           "flat")
    root.option_add("*Listbox.activestyle",      "none")

    # ══ tk.Text / ScrolledText (classic widget) ════════════════════
    root.option_add("*Text.background",       C_INPUT)
    root.option_add("*Text.foreground",       C_TEXT_PRI)
    root.option_add("*Text.insertBackground", C_TEXT_PRI)
    root.option_add("*Text.selectBackground", C_ACCENT)
    root.option_add("*Text.selectForeground", C_TEXT_PRI)
    root.option_add("*Text.font",             F_MONO)
    root.option_add("*Text.relief",           "flat")
    root.option_add("*Text.borderWidth",      "0")
    root.option_add("*Text.highlightThickness", "0")

    # ══ Canvas (strength bar background) ══════════════════════════
    root.option_add("*Canvas.background",         C_INPUT)
    root.option_add("*Canvas.highlightThickness", "0")

    return style


class PasswordDefenseSimulator:
    """Main GUI application for password attack/defense simulation."""

    # Maps slider integer → display label
    _SPEED_LABELS = {
        1: "1x  (1 thread)",
        2: "2x  (2 threads)",
        3: "3x  (4 threads)",
        4: "4x  (6 threads)",
        5: "5x  (8 threads)",
        6: "6x  (12 threads)",
        7: "7x  (16 threads)",
        8: "8x  (24 threads)",
        9: "9x  (32 threads)",
        10: "10x (48 threads)",
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Password Attack & Defense Simulator")
        self.root.state("zoomed")
        self.root.resizable(True, True)

        # Apply theme BEFORE any widgets are created
        self.style = apply_theme(root)

        # Core systems
        self.login_system = LoginSystem()
        self.strength_checker = PasswordStrengthChecker()
        self.dict_attack = DictionaryAttack()

        # Attack state
        self.attack_running = False
        self.attack_paused = False
        self.attack_thread = None
        self.attack_stop_event = threading.Event()
        self._active_attack = None   # holds the live Fast* instance mid-attack

        self.setup_ui()
        self.refresh_attack_targets()

    # ------------------------------------------------------------------
    # Top-level layout
    # ------------------------------------------------------------------

    def setup_ui(self):
        # ══ HEADER ════════════════════════════════════════════════════
        header = tk.Frame(self.root, bg="#13131f")
        header.pack(fill=tk.X, side=tk.TOP)

        # top accent line
        tk.Frame(header, bg=C_ACCENT, height=3).pack(fill=tk.X)

        # centre block
        centre = tk.Frame(header, bg="#13131f")
        centre.pack(anchor=tk.CENTER, pady=(18, 14))

        tk.Label(
            centre,
            text="🔐  Password Attack & Defense Simulator",
            bg="#13131f", fg=C_TEXT_PRI,
            font=(F_TITLE[0], 20, "bold"),
            anchor="center",
        ).pack()

        tk.Label(
            centre,
            text="For educational and academic purposes only  •  Unauthorized use against real systems is illegal and unethical",
            bg="#13131f", fg=C_ACCENT,
            font=(F_SMALL[0], 10),
            anchor="center",
        ).pack(pady=(5, 0))

        tk.Label(
            centre,
            text="⚠  This tool is strictly a cybersecurity learning demo. All simulations run locally against accounts you create.",
            bg="#13131f", fg=C_WARNING,
            font=(F_SMALL[0], 9),
            anchor="center",
        ).pack(pady=(4, 0))

        # bottom divider
        tk.Frame(header, bg=C_BORDER, height=1).pack(fill=tk.X, pady=(14, 0))

        # ══ MAIN CONTENT ══════════════════════════════════════════════
        main_frame = ttk.Frame(self.root, padding="12")
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_panel = ttk.LabelFrame(
            main_frame, text="  TARGET SYSTEM — User Registration & Login  ", padding="12"
        )
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))
        self.setup_target_system(left_panel)

        right_panel = ttk.LabelFrame(
            main_frame, text="  ATTACK SIMULATOR — Educational Demo  ", padding="12"
        )
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(6, 0))
        self.setup_attack_simulator(right_panel)

    # ------------------------------------------------------------------
    # Left panel — target system
    # ------------------------------------------------------------------

    def setup_target_system(self, parent):
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        reg_frame = ttk.Frame(notebook, padding="12")
        notebook.add(reg_frame, text="  Register  ")
        self.setup_registration_tab(reg_frame)

        login_frame = ttk.Frame(notebook, padding="12")
        notebook.add(login_frame, text="  Login  ")
        self.setup_login_tab(login_frame)

        users_frame = ttk.Frame(notebook, padding="12")
        notebook.add(users_frame, text="  Users  ")
        self.setup_users_tab(users_frame)

    def setup_registration_tab(self, parent):
        ttk.Label(parent, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=(0, 4))
        self.reg_username = ttk.Entry(parent, width=30)
        self.reg_username.grid(row=0, column=1, sticky=tk.EW, pady=(0, 4))

        ttk.Label(parent, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=(8, 4))
        password_frame = ttk.Frame(parent)
        password_frame.grid(row=1, column=1, sticky=tk.EW, pady=(8, 4))

        self.reg_password = ttk.Entry(password_frame, width=30, show="*")
        self.reg_password.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.reg_password.bind("<KeyRelease>", self.update_strength_meter)

        self.reg_password_show = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            password_frame, text="Show",
            variable=self.reg_password_show,
            command=self.toggle_password_visibility,
        ).pack(side=tk.LEFT)

        ttk.Label(parent, text="Strength:").grid(row=2, column=0, sticky=tk.W, pady=(8, 4))
        strength_frame = ttk.Frame(parent)
        strength_frame.grid(row=2, column=1, sticky=tk.EW, pady=(8, 4))
        self.strength_canvas = tk.Canvas(
            strength_frame, height=14,
            bg=C_INPUT, highlightthickness=0,
        )
        self.strength_canvas.pack(fill=tk.X)

        self.strength_label = ttk.Label(parent, text="Enter a password…", style="Muted.TLabel")
        self.strength_label.grid(row=3, column=1, sticky=tk.W, pady=2)

        ttk.Label(parent, text="Feedback:").grid(row=4, column=0, sticky=tk.NW, pady=(8, 4))
        self.feedback_text = tk.Text(
            parent, height=6, width=35, wrap=tk.WORD,
            bg=C_INPUT, fg=C_TEXT_SEC, font=F_SMALL,
            relief="flat", bd=0, padx=8, pady=6,
            insertbackground=C_TEXT_PRI,
            highlightthickness=1, highlightbackground=C_BORDER,
            highlightcolor=C_ACCENT,
        )
        self.feedback_text.grid(row=4, column=1, sticky=tk.EW, pady=(8, 4))

        ttk.Button(parent, text="Register User", command=self.register_user).grid(
            row=5, column=1, sticky=tk.EW, pady=(12, 0)
        )
        parent.columnconfigure(1, weight=1)

    def setup_login_tab(self, parent):
        ttk.Label(parent, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=(0, 4))
        self.login_username = ttk.Entry(parent, width=30)
        self.login_username.grid(row=0, column=1, sticky=tk.EW, pady=(0, 4))

        ttk.Label(parent, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=(8, 4))
        self.login_password = ttk.Entry(parent, width=30, show="*")
        self.login_password.grid(row=1, column=1, sticky=tk.EW, pady=(8, 4))

        ttk.Button(parent, text="Login", command=self.login_user).grid(
            row=2, column=1, sticky=tk.EW, pady=(12, 0)
        )
        self.login_status = ttk.Label(parent, text="")
        self.login_status.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        parent.columnconfigure(1, weight=1)

    def setup_users_tab(self, parent):
        users_notebook = ttk.Notebook(parent)
        users_notebook.pack(fill=tk.BOTH, expand=True)

        users_list_frame = ttk.Frame(users_notebook, padding="12")
        users_notebook.add(users_list_frame, text="  Registered Users  ")

        ttk.Label(users_list_frame, text="Registered Users:").pack(anchor=tk.W, pady=(0, 6))
        self.users_listbox = tk.Listbox(
            users_list_frame, height=12, width=35,
            bg=C_INPUT, fg=C_TEXT_SEC,
            selectbackground=C_ACCENT, selectforeground=C_TEXT_PRI,
            font=F_BODY, relief="flat", bd=0,
            activestyle="none", highlightthickness=0,
        )
        self.users_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        self.users_listbox.bind("<<ListboxSelect>>", self.on_user_selected)
        ttk.Button(users_list_frame, text="Refresh List",
                   command=self.refresh_users_list, style="Ghost.TButton").pack(pady=4)

        analysis_frame = ttk.Frame(users_notebook, padding="12")
        users_notebook.add(analysis_frame, text="  Password Storage Analysis  ")
        self.setup_password_analysis_tab(analysis_frame)

        self.refresh_users_list()

    def setup_password_analysis_tab(self, parent):
        canvas = tk.Canvas(parent, bg=C_BASE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        select_frame = ttk.LabelFrame(scrollable_frame, text="  Select User for Analysis  ", padding="10")
        select_frame.pack(fill=tk.X, padx=6, pady=6)
        ttk.Label(select_frame, text="User:", style="Card.TLabel").pack(side=tk.LEFT, padx=(0, 6))
        self.analysis_user_combo = ttk.Combobox(select_frame, state="readonly", width=30)
        self.analysis_user_combo.pack(side=tk.LEFT, padx=(0, 6), fill=tk.X, expand=True)
        self.analysis_user_combo.bind("<<ComboboxSelected>>", self.on_analysis_user_selected)
        ttk.Button(select_frame, text="Analyze", command=self.update_analysis_display).pack(side=tk.LEFT)

        hash_frame = ttk.LabelFrame(scrollable_frame, text="  Stored Password Hash (Read-Only)  ", padding="10")
        hash_frame.pack(fill=tk.X, padx=6, pady=6)
        ttk.Label(hash_frame, text="Username:", style="Card.TLabel").pack(anchor=tk.W)
        self.analysis_username_label = ttk.Label(hash_frame, text="[None selected]",
                                                  style="CardMuted.TLabel")
        self.analysis_username_label.pack(anchor=tk.W, padx=16, pady=(2, 8))
        ttk.Label(hash_frame, text="bcrypt Hash:", style="Card.TLabel").pack(anchor=tk.W, pady=(6, 0))
        self.analysis_hash_text = tk.Text(
            hash_frame, height=4, width=50, wrap=tk.WORD,
            bg=C_INPUT, fg=C_TEXT_SEC, font=F_MONO,
            relief="flat", bd=0, padx=8, pady=6,
            insertbackground=C_TEXT_PRI, highlightthickness=0,
        )
        self.analysis_hash_text.pack(fill=tk.X, padx=16, pady=(4, 8))
        self.analysis_hash_text.config(state=tk.DISABLED)
        ttk.Label(hash_frame, text="Hash Length:", style="Card.TLabel").pack(anchor=tk.W)
        self.analysis_hash_length = ttk.Label(hash_frame, text="0 characters", style="CardMuted.TLabel")
        self.analysis_hash_length.pack(anchor=tk.W, padx=16, pady=(2, 4))

        structure_frame = ttk.LabelFrame(scrollable_frame, text="  bcrypt Hash Structure Breakdown  ", padding="10")
        structure_frame.pack(fill=tk.X, padx=6, pady=6)
        self.analysis_structure_text = tk.Text(
            structure_frame, height=6, width=50, wrap=tk.WORD,
            bg=C_INPUT, fg=C_TEXT_SEC, font=F_MONO,
            relief="flat", bd=0, padx=8, pady=6,
            insertbackground=C_TEXT_PRI, highlightthickness=0,
        )
        self.analysis_structure_text.pack(fill=tk.X, padx=4, pady=4)
        self.analysis_structure_text.config(state=tk.DISABLED)

        demo_frame = ttk.LabelFrame(scrollable_frame, text="  Salt Uniqueness Demonstration  ", padding="10")
        demo_frame.pack(fill=tk.X, padx=6, pady=6)
        ttk.Label(demo_frame, text="Click to generate multiple hashes of the same password:",
                  style="Card.TLabel").pack(anchor=tk.W, pady=(0, 6))
        ttk.Button(demo_frame, text="Generate Example Hashes",
                   command=self.show_example_hashes).pack(anchor=tk.W, pady=(0, 6))
        self.demo_result_text = tk.Text(
            demo_frame, height=8, width=50, wrap=tk.WORD,
            bg=C_INPUT, fg=C_TEXT_SEC, font=F_MONO,
            relief="flat", bd=0, padx=8, pady=6,
            insertbackground=C_TEXT_PRI, highlightthickness=0,
        )
        self.demo_result_text.pack(fill=tk.X, padx=4, pady=4)
        self.demo_result_text.config(state=tk.DISABLED)

        comparison_frame = ttk.LabelFrame(scrollable_frame, text="  Plaintext vs bcrypt Storage Comparison  ", padding="10")
        comparison_frame.pack(fill=tk.X, padx=6, pady=6)
        self.comparison_text = tk.Text(
            comparison_frame, height=10, width=50, wrap=tk.WORD,
            bg=C_INPUT, fg=C_TEXT_SEC, font=F_MONO,
            relief="flat", bd=0, padx=8, pady=6,
            insertbackground=C_TEXT_PRI, highlightthickness=0,
        )
        self.comparison_text.pack(fill=tk.X, padx=4, pady=4)
        self.comparison_text.config(state=tk.DISABLED)

        self.show_security_comparison()
        self.refresh_analysis_users()

    # ------------------------------------------------------------------
    # Right panel — attack simulator
    # ------------------------------------------------------------------

    def setup_attack_simulator(self, parent):
        # ── Row 0: target user ────────────────────────────────────────
        ttk.Label(parent, text="Target User:").grid(row=0, column=0, sticky=tk.W, pady=(0, 4))
        self.attack_target = ttk.Combobox(parent, width=25, state="readonly")
        self.attack_target.grid(row=0, column=1, sticky=tk.EW, pady=(0, 4))
        ttk.Button(parent, text="↻ Refresh", command=self.refresh_attack_targets,
                   style="Ghost.TButton").grid(row=0, column=2, pady=(0, 4), padx=(6, 0))

        # ── Row 1: attack type ────────────────────────────────────────
        ttk.Label(parent, text="Attack Type:").grid(row=1, column=0, sticky=tk.W, pady=(8, 4))
        self.attack_type = ttk.Combobox(
            parent,
            values=["Dictionary Attack", "Brute Force Attack"],
            state="readonly",
            width=25,
        )
        self.attack_type.set("Dictionary Attack")
        self.attack_type.grid(row=1, column=1, columnspan=2, sticky=tk.EW, pady=(8, 4))
        self.attack_type.bind("<<ComboboxSelected>>", self._on_attack_type_changed)

        # ── Row 2: speed slider ───────────────────────────────────────
        ttk.Label(parent, text="Speed:").grid(row=2, column=0, sticky=tk.W, pady=(8, 2))

        slider_frame = ttk.Frame(parent)
        slider_frame.grid(row=2, column=1, columnspan=2, sticky=tk.EW, pady=(8, 2))

        self._speed_var = tk.IntVar(value=1)

        self.speed_slider = ttk.Scale(
            slider_frame,
            from_=1, to=10,
            orient=tk.HORIZONTAL,
            variable=self._speed_var,
            command=self._on_speed_changed,
        )
        self.speed_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.speed_slider.bind("<ButtonRelease-1>", self._on_speed_released)

        self.speed_value_label = ttk.Label(
            slider_frame,
            text=self._SPEED_LABELS[1],
            width=18,
            anchor=tk.W,
        )
        self.speed_value_label.pack(side=tk.LEFT, padx=(8, 0))

        # ── Row 3: speed note ─────────────────────────────────────────
        self.speed_note_label = ttk.Label(
            parent,
            text="ℹ Speed control is available for both attack types.",
            style="Muted.TLabel",
        )
        self.speed_note_label.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(0, 8))

        # ── Row 4: control buttons ────────────────────────────────────
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=4, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))

        self.attack_button = ttk.Button(
            button_frame, text="▶  Start Attack", command=self.start_attack
        )
        self.attack_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.pause_attack_button = ttk.Button(
            button_frame, text="⏸  Pause", command=self.toggle_pause,
            state=tk.DISABLED, style="Ghost.TButton"
        )
        self.pause_attack_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.stop_attack_button = ttk.Button(
            button_frame, text="⏹  Stop Attack", command=self.stop_attack,
            state=tk.DISABLED, style="Danger.TButton"
        )
        self.stop_attack_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # ── Row 5: progress bar ───────────────────────────────────────
        prog_header = ttk.Frame(parent)
        prog_header.grid(row=5, column=0, columnspan=3, sticky=tk.EW, pady=(4, 2))
        ttk.Label(prog_header, text="Attack Progress:").pack(side=tk.LEFT)
        self._prog_status = ttk.Label(prog_header, text="", style="Muted.TLabel")
        self._prog_status.pack(side=tk.RIGHT)

        self.attack_progressbar = ttk.Progressbar(
            parent,
            orient=tk.HORIZONTAL,
            mode="indeterminate",
            style="Accent.Horizontal.TProgressbar",
        )
        self.attack_progressbar.grid(row=6, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))

        # ── Row 7: live console label ─────────────────────────────────
        ttk.Label(parent, text="Live Console:").grid(
            row=7, column=0, columnspan=3, sticky=tk.W, pady=(4, 4)
        )

        # ── Row 8: scrolled console ───────────────────────────────────
        self.progress_text = scrolledtext.ScrolledText(
            parent, height=15, width=45, wrap=tk.WORD,
            bg="#181825", fg=C_TEXT_PRI, font=F_MONO,
            relief="flat", bd=0,
            padx=10, pady=8,
            insertbackground=C_TEXT_PRI,
            selectbackground=C_ACCENT,
            selectforeground=C_TEXT_PRI,
        )
        self.progress_text.grid(row=8, column=0, columnspan=3, sticky=tk.NSEW, pady=(0, 10))
        # Style the embedded scrollbar
        self.progress_text.vbar.configure(
            bg=C_CARD, troughcolor=C_INPUT,
            activebackground=C_ACCENT, relief="flat", bd=0,
        )

        # ── Row 9: results summary ────────────────────────────────────
        ttk.Label(parent, text="Results:").grid(
            row=9, column=0, columnspan=3, sticky=tk.W, pady=(4, 2)
        )
        self.results_label = ttk.Label(
            parent, text="Waiting for attack…", style="Muted.TLabel"
        )
        self.results_label.grid(row=10, column=0, columnspan=3, sticky=tk.W, pady=(0, 4))

        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(8, weight=1)

        self._on_attack_type_changed()

    # ------------------------------------------------------------------
    # Speed slider callbacks
    # ------------------------------------------------------------------

    def _on_speed_changed(self, _event=None):
        """Keep speed label in sync with slider position (fires while dragging)."""
        val = int(round(self._speed_var.get()))
        self._speed_var.set(val)
        self.speed_value_label.config(text=self._SPEED_LABELS[val])

    def _on_speed_released(self, _event=None):
        """Apply the new speed to the live attack once the user releases the slider."""
        if self.attack_running and self._active_attack is not None:
            self._active_attack.set_speed(self._current_speed())
            self.progress_text.config(state=tk.NORMAL)
            self.progress_text.insert(
                tk.END,
                f"[Speed changed → {self._SPEED_LABELS[self._current_speed()]}]\n"
            )
            self.progress_text.see(tk.END)

    def _on_attack_type_changed(self, _event=None):
        """
        The slider is always visible but the note text updates to reflect
        whether threading will help for the selected type.
        """
        attack = self.attack_type.get()
        if attack == "Brute Force Attack":
            note = (
                "ℹ  Brute-force + bcrypt (12 rounds) ≈ 250 ms/check. "
                "Higher speed adds threads; still very slow for long passwords."
            )
        else:
            note = (
                "ℹ  Higher speed splits the wordlist across more threads "
                "for faster parallel checking."
            )
        self.speed_note_label.config(text=note)

    def _current_speed(self) -> int:
        """Return the slider value as a snapped integer (1–10)."""
        return max(1, min(10, int(round(self._speed_var.get()))))

    # ------------------------------------------------------------------
    # Attack orchestration
    # ------------------------------------------------------------------

    def start_attack(self):
        if self.attack_running:
            messagebox.showwarning("Warning", "Attack already in progress")
            return

        target = self.attack_target.get()
        attack_type = self.attack_type.get()

        if not target:
            messagebox.showerror("Error", "Select a target user")
            return

        self.attack_running = True
        self.attack_paused = False
        self.attack_stop_event.clear()
        self.attack_button.config(state=tk.DISABLED)
        self.pause_attack_button.config(state=tk.NORMAL, text="⏸  Pause")
        self.stop_attack_button.config(state=tk.NORMAL)
        self.progress_text.config(state=tk.NORMAL)
        self.progress_text.delete(1.0, tk.END)

        # Start indeterminate progress bar
        self.attack_progressbar.config(mode="indeterminate")
        self.attack_progressbar.start(12)
        self._prog_status.config(text="Running…")
        self.results_label.config(text="Attack in progress…", foreground=C_WARNING)

        speed = self._current_speed()

        if attack_type == "Dictionary Attack":
            self.attack_thread = threading.Thread(
                target=self.run_dictionary_attack,
                args=(target, speed),
                daemon=True,
            )
        else:
            self.attack_thread = threading.Thread(
                target=self.run_brute_force_attack,
                args=(target, speed),
                daemon=True,
            )

        self.attack_thread.start()

    def run_dictionary_attack(self, target: str, speed: int):
        """Run dictionary attack against rockyou.txt.gz."""
        attack = FastDictionaryAttack(wordlist_file="rockyou.txt.gz", speed_multiplier=speed)
        self._active_attack = attack

        def callback(attempts, elapsed, success, password):
            msg = f"Attempts: {attempts} | Time: {elapsed:.2f}s"
            if success:
                msg += f" | ✓ SUCCESS! Password: {password}"
            self.root.after(0, lambda m=msg, s=success: self.update_progress(m, s))

        success, attempts, elapsed, password = attack.attack(
            target, self.login_system, callback, self.attack_stop_event
        )
        self._active_attack = None
        self.root.after(0, lambda: self.finalize_attack(success, attempts, elapsed, password))

    def run_brute_force_attack(self, target: str, speed: int):
        """Run brute-force attack (fast-forwarded when speed > 1)."""
        attack = FastBruteForceAttack(max_length=4, speed_multiplier=speed)
        self._active_attack = attack

        def callback(attempts, elapsed, current, success, password):
            msg = f"Trying: {current} | Attempts: {attempts} | Time: {elapsed:.2f}s"
            if success:
                msg += f" | ✓ SUCCESS! Password: {password}"
            self.root.after(0, lambda m=msg, s=success: self.update_progress(m, s))

        success, attempts, elapsed, password = attack.attack(
            target, self.login_system, callback, self.attack_stop_event
        )
        self._active_attack = None
        self.root.after(0, lambda: self.finalize_attack(success, attempts, elapsed, password))

    def update_progress(self, message: str, success: bool = False):
        self.progress_text.insert(tk.END, message + "\n")
        self.progress_text.see(tk.END)
        if success:
            # Tag the success line green without changing the whole widget fg
            last_line_start = self.progress_text.index("end-2l linestart")
            last_line_end   = self.progress_text.index("end-1l lineend")
            self.progress_text.tag_add("success", last_line_start, last_line_end)
            self.progress_text.tag_config("success", foreground=C_SUCCESS)

    def stop_attack(self):
        if self.attack_running:
            self.attack_stop_event.set()
            # Resume first so workers can unblock and see the stop signal
            if self.attack_paused and self._active_attack:
                self._active_attack.resume()
            self.attack_paused = False
            self.pause_attack_button.config(state=tk.DISABLED, text="⏸  Pause")
            self.stop_attack_button.config(state=tk.DISABLED)
            self.progress_text.insert(tk.END, "\n[Attack stopped by user]\n")
            self.progress_text.see(tk.END)

    def toggle_pause(self):
        """Pause or resume the running attack."""
        if not self.attack_running or self._active_attack is None:
            return

        if not self.attack_paused:
            self.attack_paused = True
            self._active_attack.pause()
            self.pause_attack_button.config(text="▶  Resume")
            self.progress_text.config(state=tk.NORMAL)
            self.progress_text.insert(tk.END, "\n[Attack paused]\n")
            self.progress_text.see(tk.END)
        else:
            self.attack_paused = False
            self._active_attack.resume()
            self.pause_attack_button.config(text="⏸  Pause")
            self.progress_text.config(state=tk.NORMAL)
            self.progress_text.insert(tk.END, "[Attack resumed]\n")
            self.progress_text.see(tk.END)

    def finalize_attack(self, success: bool, attempts: int, elapsed: float, password):
        self.attack_running = False
        self.attack_paused = False
        self._active_attack = None
        self.attack_button.config(state=tk.NORMAL)
        self.pause_attack_button.config(state=tk.DISABLED, text="⏸  Pause")
        self.stop_attack_button.config(state=tk.DISABLED)

        # Stop progress bar
        self.attack_progressbar.stop()
        self.attack_progressbar.config(mode="determinate", value=100)
        self._prog_status.config(text="Done")

        is_stopped = self.attack_stop_event.is_set()

        if success:
            result = f"✓ ATTACK SUCCESSFUL!  Password cracked: '{password}'"
            self.results_label.config(text=result, foreground=C_DANGER)
        elif is_stopped:
            result = "⏹ Attack stopped by user."
            self.results_label.config(text=result, foreground=C_WARNING)
        else:
            result = "✗ Attack failed. Password not found in wordlist / brute-force space."
            self.results_label.config(text=result, foreground=C_ACCENT)

        divider = "─" * 50
        self.progress_text.insert(tk.END, f"\n{divider}\n")
        self.progress_text.insert(tk.END, "  ATTACK SUMMARY\n")
        self.progress_text.insert(tk.END, f"{divider}\n")
        self.progress_text.insert(tk.END, f"  Total Attempts : {attempts}\n")
        self.progress_text.insert(tk.END, f"  Time Elapsed   : {elapsed:.2f} seconds\n")
        self.progress_text.insert(tk.END, f"  Speed Setting  : {self._SPEED_LABELS[self._current_speed()]}\n")
        status = "SUCCESS ✓" if success else ("STOPPED ⏹" if is_stopped else "FAILED ✗")
        self.progress_text.insert(tk.END, f"  Result         : {status}\n")
        self.progress_text.insert(tk.END, f"{divider}\n")
        self.progress_text.see(tk.END)
        self.progress_text.config(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Helper / shared methods (unchanged logic, kept intact)
    # ------------------------------------------------------------------

    def refresh_analysis_users(self):
        users = self.login_system.get_all_users()
        self.analysis_user_combo["values"] = users
        if users:
            self.analysis_user_combo.current(0)
            self.on_analysis_user_selected()
        else:
            self.clear_analysis_display()

    def on_analysis_user_selected(self, event=None):
        self.update_analysis_display()

    def on_user_selected(self, event=None):
        selection = self.users_listbox.curselection()
        if selection:
            user = self.users_listbox.get(selection[0])
            values = self.analysis_user_combo["values"]
            if user in values:
                self.analysis_user_combo.current(list(values).index(user))
                self.update_analysis_display()

    def update_analysis_display(self):
        user = self.analysis_user_combo.get()
        if not user:
            self.clear_analysis_display()
            return
        user_hash = self.login_system.get_user_hash(user)
        if not user_hash:
            self.clear_analysis_display()
            return

        self.analysis_username_label.config(text=user, foreground=C_TEXT_PRI)

        self.analysis_hash_text.config(state=tk.NORMAL)
        self.analysis_hash_text.delete(1.0, tk.END)
        self.analysis_hash_text.insert(tk.END, user_hash)
        self.analysis_hash_text.config(state=tk.DISABLED)

        self.analysis_hash_length.config(
            text=f"{len(user_hash)} characters (standard bcrypt: 60 chars)",
            foreground=C_TEXT_SEC,
        )

        analysis = PasswordAnalyzer.parse_bcrypt_hash(user_hash)
        if analysis:
            self.analysis_structure_text.config(state=tk.NORMAL)
            self.analysis_structure_text.delete(1.0, tk.END)
            breakdown_text = "🔐 BCRYPT HASH STRUCTURE:\n\n"
            for line in analysis["breakdown"]:
                breakdown_text += line + "\n"
            self.analysis_structure_text.insert(tk.END, breakdown_text)
            self.analysis_structure_text.config(state=tk.DISABLED)

    def clear_analysis_display(self):
        self.analysis_username_label.config(text="[No user selected]", foreground=C_TEXT_MUT)
        self.analysis_hash_text.config(state=tk.NORMAL)
        self.analysis_hash_text.delete(1.0, tk.END)
        self.analysis_hash_text.insert(tk.END, "[No user selected]")
        self.analysis_hash_text.config(state=tk.DISABLED)
        self.analysis_hash_length.config(text="0 characters", foreground=C_TEXT_MUT)
        self.analysis_structure_text.config(state=tk.NORMAL)
        self.analysis_structure_text.delete(1.0, tk.END)
        self.analysis_structure_text.insert(tk.END, "Select a user to view hash structure")
        self.analysis_structure_text.config(state=tk.DISABLED)

    def show_example_hashes(self):
        demo_result = PasswordAnalyzer.generate_example_hashes("admin123", count=3)
        display_text = "📊 EXAMPLE: Hashing 'admin123' three times:\n\n"
        for i, hash_val in enumerate(demo_result["hashes"], 1):
            display_text += f"Hash {i}:\n{hash_val}\n\n"
        display_text += "━" * 48 + "\n🔑 WHY THEY'RE DIFFERENT:\n\n"
        for explanation in demo_result["explanation"]:
            display_text += f"• {explanation}\n"
        self.demo_result_text.config(state=tk.NORMAL)
        self.demo_result_text.delete(1.0, tk.END)
        self.demo_result_text.insert(tk.END, display_text)
        self.demo_result_text.config(state=tk.DISABLED)

    def show_security_comparison(self):
        comparison_text = (
            "⚠️ PLAINTEXT STORAGE (INSECURE):\n"
            "  password: 'MyPassword123'\n\n"
            "If database is leaked:\n"
            "✗ Attacker immediately knows the password\n"
            "✗ Can access account instantly\n"
            "✗ No computational cost to crack\n\n"
            + "─" * 48 + "\n\n"
            "✓ BCRYPT STORAGE (SECURE):\n"
            "  password_hash: '$2b$12$kjasdhfkasjdfhkjasdf...'\n\n"
            "If database is leaked:\n"
            "✓ Attacker sees only the hash, not the password\n"
            "✓ Bcrypt designed to be computationally expensive\n"
            "✓ Each hash has unique random salt\n"
            "✓ Even weak passwords take time to crack\n"
            "✓ Each password must be cracked individually\n\n"
            "💡 KEY TAKEAWAY:\n"
            "Bcrypt + Strong Password = Maximum Security"
        )
        self.comparison_text.config(state=tk.NORMAL)
        self.comparison_text.delete(1.0, tk.END)
        self.comparison_text.insert(tk.END, comparison_text)
        self.comparison_text.config(state=tk.DISABLED)

    def update_strength_meter(self, event=None):
        password = self.reg_password.get()
        strength, score, feedback = self.strength_checker.get_strength_level(password)
        color = self.strength_checker.get_strength_color(password)

        self.strength_canvas.delete("all")
        bar_width = (score / 100) * 200
        self.strength_canvas.create_rectangle(0, 0, bar_width, 20, fill=color)
        self.strength_label.config(text=f"{strength} ({score}/100)")

        self.feedback_text.config(state=tk.NORMAL)
        self.feedback_text.delete(1.0, tk.END)
        if feedback:
            self.feedback_text.insert(tk.END, "\n".join(feedback))
        self.feedback_text.config(state=tk.DISABLED)

    def toggle_password_visibility(self):
        self.reg_password.config(show="" if self.reg_password_show.get() else "*")

    def register_user(self):
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
            self.reg_password_show.set(False)
            self.reg_password.config(show="*")
            self.feedback_text.config(state=tk.NORMAL)
            self.feedback_text.delete(1.0, tk.END)
            self.feedback_text.config(state=tk.DISABLED)
            self.strength_canvas.delete("all")
            self.refresh_users_list()
            self.refresh_attack_targets()
        else:
            messagebox.showerror("Error", message)

    def login_user(self):
        username = self.login_username.get()
        password = self.login_password.get()
        success, message = self.login_system.login_user(username, password)
        if success:
            self.login_status.config(text=f"✓ {message}", foreground=C_SUCCESS)
            self.login_password.delete(0, tk.END)
        else:
            self.login_status.config(text=f"✗ {message}", foreground=C_DANGER)

    def refresh_users_list(self):
        self.users_listbox.delete(0, tk.END)
        for user in self.login_system.get_all_users():
            self.users_listbox.insert(tk.END, user)
        self.refresh_analysis_users()

    def refresh_attack_targets(self):
        users = self.login_system.get_all_users()
        self.attack_target["values"] = users
        if users:
            self.attack_target.current(0)


def main():
    root = tk.Tk()
    PasswordDefenseSimulator(root)
    root.mainloop()


if __name__ == "__main__":
    main()