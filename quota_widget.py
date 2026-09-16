import tkinter as tk
from tkinter import ttk, simpledialog
import subprocess
import json
import threading
import os
import re
import shutil
from datetime import datetime, timezone

# \u2500\u2500\u2500 Hover Tooltip Engine (Removed) \u2500\u2500\u2500

# \u2500\u2500\u2500 Modern Progress Bar \u2500\u2500\u2500
class ModernProgressBar(tk.Canvas):
    def __init__(self, parent, percentage, *args, **kwargs):
        super().__init__(parent, height=16, bg="#09090B", highlightthickness=0, *args, **kwargs)
        self.percentage = percentage
        self._last_w = 0
        self.bind("<Configure>", self.draw)

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1,  x2-r, y1,  x2, y1,  x2, y1+r,
            x2, y2-r,  x2, y2,  x2-r, y2,  x1+r, y2,
            x1, y2,  x1, y2-r,  x1, y1+r,  x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def draw(self, event=None):
        width = self.winfo_width()
        height = self.winfo_height()
        if width <= 10 or (width == self._last_w): return
        self._last_w = width
        self.delete("all")
        
        if self.percentage < 20:
            outline_color, fill_color, dot_color = "#EF4444", "#991B1B", "#F87171"
        else:
            outline_color, fill_color, dot_color = "#4ADE80", "#16A34A", "#A3E635"
            
        r = height // 2
        self.create_rounded_rect(2, 2, width-2, height-2, r-1, outline=outline_color, fill="#121212", width=1.5)
        fill_w = max(0, (width - 4) * (self.percentage / 100))
        if fill_w > r:
            self.create_rounded_rect(3, 3, 3 + fill_w, height-3, r-2, outline="", fill=fill_color)
            dot_r = r - 2
            cx = 3 + fill_w - dot_r
            cy = height // 2
            self.create_oval(cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r, outline="", fill=dot_color)

# \u2500\u2500\u2500 Unified CLI Helper (FIXED: no shell injection, has timeout) \u2500\u2500\u2500
def run_cli(args, timeout=20):
    """Run antigravity-usage with safe argument list. Returns parsed JSON list or empty list."""
    # On Windows, .cmd wrappers need shell=True OR the full .cmd path
    cli_path = shutil.which("antigravity-usage")
    if not cli_path:
        return []
    cmd = [cli_path] + args
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=timeout, creationflags=flags)
        output = res.stdout.strip()
        if not output: return []
        start = output.find('[')
        end = output.rfind(']')
        if start == -1 or end == -1: return []
        return json.loads(output[start:end+1])
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return []

# \u2500\u2500\u2500 Time Formatting Helper \u2500\u2500\u2500
def format_reset_time(ms):
    """Convert milliseconds to a human-readable countdown string (max 2 units)."""
    if ms is None or ms <= 0: return "Now"
    total_secs = int(ms / 1000)
    days = total_secs // 86400
    hours = (total_secs % 86400) // 3600
    minutes = (total_secs % 3600) // 60
    
    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

# \u2500\u2500\u2500 Main Widget \u2500\u2500\u2500
class QuotaWidget(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Antigravity Quota Tracker")
        self.geometry("380x360")
        self.configure(bg="#09090B")
        self.attributes("-alpha", 1.0)
        self.overrideredirect(True)
        
        # \u2500\u2500 Asset Loading with Fallbacks \u2500\u2500
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, "quota_icon.ico")
        if os.path.exists(icon_path):
            try: self.iconbitmap(icon_path)
            except tk.TclError: pass
        
        refresh_path = os.path.join(base_dir, "refresh_icon.png")
        if os.path.exists(refresh_path):
            self.img_refresh = tk.PhotoImage(file=refresh_path)
        else:
            self.img_refresh = None
            
        self.img_spinner_frames = []
        for i in range(8):
            fp = os.path.join(base_dir, f"spinner_frame_{i}.png")
            if os.path.exists(fp):
                self.img_spinner_frames.append(tk.PhotoImage(file=fp))
        
        # \u2500\u2500 Thread Safety \u2500\u2500
        self._data_lock = threading.Lock()
        self.current_data = []
        self.is_fetching = False
        self.spinners = {}
        self._countdown_job = None
        
        # \u2500\u2500 CLI Pre-flight \u2500\u2500
        self._cli_available = shutil.which("antigravity-usage") is not None
            
        # \u2500\u2500 Sizegrip \u2500\u2500
        self.sizegrip = ttk.Sizegrip(self)
        self.sizegrip.place(relx=1.0, rely=1.0, anchor="se")
        self.sizegrip.lift()
        
        # \u2500\u2500 Dark Orange Title Bar \u2500\u2500
        title_bg = "#9A3412" 
        title_fg = "white"
        self._title_bg = title_bg
        self._title_fg = title_fg
        
        self.title_bar = tk.Frame(self, bg=title_bg, relief="flat", bd=0)
        self.title_bar.pack(expand=0, fill="x")
        self.title_bar.bind("<B1-Motion>", self.move_window)
        self.title_bar.bind("<Button-1>", self.get_pos)
        
        icon_label = tk.Label(self.title_bar, text="\U0001f680", bg=title_bg, fg=title_fg, font=("Segoe UI Emoji", 15))
        icon_label.pack(side="left", padx=(5, 0), pady=4)
        title_label = tk.Label(self.title_bar, text="Quotas", bg=title_bg, fg=title_fg, font=("Candara", 10, "bold"))
        title_label.pack(side="left", padx=(2, 5), pady=8)
        
        btn_frame = tk.Frame(self.title_bar, bg=title_bg)
        btn_frame.pack(side="right", padx=5)
        
        # Ghost buttons
        def create_text_btn(parent, text, cmd, is_close=False):
            active_bg = "#EF4444" if is_close else title_bg
            btn = tk.Button(parent, text=text, bg=title_bg, fg=title_fg,
                            activebackground=active_bg, activeforeground="white",
                            bd=0, relief="flat", highlightthickness=0,
                            command=cmd, cursor="hand2", font=("Candara", 10))
            btn.pack(side="left", padx=2)
            hover_bg = "#EF4444" if is_close else title_bg
            btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg, fg="white"))
            btn.bind("<Leave>", lambda e: btn.config(bg=title_bg, fg=title_fg))
            return btn
            
        self.btn_add = create_text_btn(btn_frame, "\u2795", self.add_account)
        self.btn_rem = create_text_btn(btn_frame, "\u2796", self.remove_account)
        
        # Image-based refresh button
        if self.img_refresh:
            self.btn_ref = tk.Button(btn_frame, image=self.img_refresh, bg=title_bg,
                                     activebackground=title_bg, bd=0, relief="flat",
                                     highlightthickness=0, command=self.manual_refresh_all, cursor="hand2")
        else:
            self.btn_ref = tk.Button(btn_frame, text="\u27f3", bg=title_bg, fg=title_fg,
                                     activebackground=title_bg, bd=0, relief="flat",
                                     highlightthickness=0, command=self.manual_refresh_all,
                                     cursor="hand2", font=("Candara", 12, "bold"))
        self.btn_ref.pack(side="left", padx=2)
        
        self.btn_close = create_text_btn(btn_frame, "\u2715", self.destroy, is_close=True)
        
        # \u2500\u2500 Scrollable Content Area (FIXED: scrollbar actually packed) \u2500\u2500
        content_container = tk.Frame(self, bg="#09090B")
        content_container.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(content_container, bg="#09090B", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(content_container, orient="vertical", command=self.canvas.yview)
        self.content_frame = tk.Frame(self.canvas, bg="#09090B")
        
        self._last_canvas_w = 0
        self.content_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        
        # \u2500\u2500 Initial Status \u2500\u2500
        if not self._cli_available:
            self.status_label = tk.Label(self.content_frame, text="\u274c antigravity-usage CLI not found in PATH.\nInstall it first.", bg="#09090B", fg="#EF4444", font=("Candara", 10, "bold"))
        else:
            self.status_label = tk.Label(self.content_frame, text="Fetching live quota data...", bg="#09090B", fg="#EA580C", font=("Candara", 10))
        self.status_label.pack(pady=40)
        
        if self._cli_available:
            self.refresh_data_initial()
        
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def on_canvas_configure(self, event):
        if event.width != self._last_canvas_w:
            self._last_canvas_w = event.width
            self.canvas.itemconfig(self.canvas_window, width=event.width)

    def get_pos(self, event):
        self.xwin = event.x
        self.ywin = event.y

    def move_window(self, event):
        self.geometry(f'+{event.x_root - self.xwin}+{event.y_root - self.ywin}')

    # \u2500\u2500\u2500 ANIMATION ENGINE \u2500\u2500\u2500
    def animate_spinner(self, widget, unique_key, idx=0):
        if not self.spinners.get(unique_key, False):
            try:
                if self.img_refresh:
                    widget.config(image=self.img_refresh, state="normal")
                else:
                    widget.config(text="\u27f3", state="normal")
            except tk.TclError: pass
            return
        if not self.img_spinner_frames:
            # Fallback text animation
            frames = ["\u25f4", "\u25f7", "\u25f6", "\u25f5"]
            try:
                widget.config(text=frames[idx % len(frames)])
                self.after(100, self.animate_spinner, widget, unique_key, idx+1)
            except tk.TclError: pass
            return
        try:
            widget.config(image=self.img_spinner_frames[idx % len(self.img_spinner_frames)], state="disabled")
            self.after(80, self.animate_spinner, widget, unique_key, idx+1)
        except tk.TclError: pass

    # \u2500\u2500\u2500 LIVE COUNTDOWN TIMER \u2500\u2500\u2500
    def _tick_countdowns(self):
        """Decrement all timeUntilResetMs by 1000ms and refresh displayed timers."""
        with self._data_lock:
            for account in self.current_data:
                snapshot = account.get("snapshot")
                if not snapshot: continue
                for model in snapshot.get("models", []):
                    ms = model.get("timeUntilResetMs")
                    if ms is not None and ms > 0:
                        model["timeUntilResetMs"] = max(0, ms - 1000)
        
        # Update only the timer labels without rebuilding everything
        self._update_timer_labels()
        self._countdown_job = self.after(1000, self._tick_countdowns)

    def _update_timer_labels(self):
        """Update just the countdown text on existing timer labels."""
        if not hasattr(self, '_timer_label_map'): return
        with self._data_lock:
            for key, lbl in self._timer_label_map.items():
                email, model_id = key
                for account in self.current_data:
                    if account.get("email") != email: continue
                    snapshot = account.get("snapshot")
                    if not snapshot: continue
                    for model in snapshot.get("models", []):
                        if model.get("modelId") == model_id:
                            ms = model.get("timeUntilResetMs", 0)
                            txt = format_reset_time(ms)
                            color = "#FCD34D" if ms and ms > 0 else "#4ADE80"
                            try: lbl.config(text=f"\u23f1{txt}", fg=color)
                            except tk.TclError: pass

    # \u2500\u2500\u2500 REFRESH LOGIC (FIXED: thread-safe, no shell injection) \u2500\u2500\u2500
    def manual_refresh_all(self):
        if self.is_fetching: return
        threading.Thread(target=self._fetch_bulk, daemon=True).start()

    def manual_refresh_single(self, email):
        if self.spinners.get(email, False) or self.is_fetching: return
        self.spinners[email] = True
        self._update_ui()
        threading.Thread(target=self._fetch_single_thread, args=(email,), daemon=True).start()

    def _fetch_single_thread(self, email):
        try:
            new_data = run_cli(["quota", "-a", email, "--json", "--refresh"])
            if new_data and isinstance(new_data, list):
                with self._data_lock:
                    for i, acc in enumerate(self.current_data):
                        if acc.get("email") == email:
                            if "snapshot" not in self.current_data[i]:
                                self.current_data[i]["snapshot"] = {}
                            self.current_data[i]["snapshot"]["models"] = new_data
                            break
        except Exception: pass
        finally:
            self.spinners[email] = False
            self.after(0, self._update_ui)

    def _fetch_cascade(self):
        self.is_fetching = True
        self.spinners["global"] = True
        self.after(0, lambda: self.animate_spinner(self.btn_ref, "global"))
        
        with self._data_lock:
            emails = [acc.get("email") for acc in self.current_data]
        
        for email in emails:
            self.spinners[email] = True
            self.after(0, self._update_ui)
            
            try:
                new_data = run_cli(["quota", "-a", email, "--json", "--refresh"])
                if new_data and isinstance(new_data, list):
                    with self._data_lock:
                        for i, acc in enumerate(self.current_data):
                            if acc.get("email") == email:
                                if "snapshot" not in self.current_data[i]:
                                    self.current_data[i]["snapshot"] = {}
                                self.current_data[i]["snapshot"]["models"] = new_data
                                break
            except Exception: pass
            
            self.spinners[email] = False
            self.after(0, self._update_ui)
            
        self.spinners["global"] = False
        self.is_fetching = False

    def refresh_data_initial(self):
        threading.Thread(target=self._fetch_bulk, daemon=True).start()
        
    def _fetch_bulk(self):
        self.is_fetching = True
        self.spinners["global"] = True
        self.after(0, lambda: self.animate_spinner(self.btn_ref, "global"))
        try:
            data = run_cli(["quota", "--all", "--json"])
            if data:
                with self._data_lock:
                    self.current_data = data
                self.after(0, self._update_ui)
            else:
                if not self.current_data:
                    self.after(0, self._show_error, "\U0001f534 Could not fetch quota data.\nCheck your CLI & network.")
        except Exception:
            if not self.current_data:
                self.after(0, self._show_error, "\U0001f534 Connection Error")
        finally:
            self.spinners["global"] = False
            self.is_fetching = False

    # \u2500\u2500\u2500 ADD/REMOVE (FIXED: Auto-refresh on close) \u2500\u2500\u2500
    def add_account(self):
        def _add_task():
            # Use start /wait so it blocks until the user closes the terminal window
            subprocess.run(["cmd", "/c", "start", "/wait", "cmd", "/c", "antigravity-usage accounts add & pause"])
            threading.Thread(target=self._fetch_bulk, daemon=True).start()
        threading.Thread(target=_add_task, daemon=True).start()
        
    def remove_account(self):
        email = simpledialog.askstring("Remove Account", "Enter the exact email to remove:", parent=self)
        if not email: return
        if not re.match(r"^[\w.\-+]+@[\w.\-]+\.\w+$", email):
            simpledialog.messagebox.showerror("Invalid Email", "Please enter a valid email address.", parent=self)
            return
            
        def _rem_task():
            subprocess.run(["cmd", "/c", "start", "/wait", "cmd", "/c", f"antigravity-usage accounts remove {email} & echo Account removed. & pause"])
            threading.Thread(target=self._fetch_bulk, daemon=True).start()
        threading.Thread(target=_rem_task, daemon=True).start()
    # \u2500\u2500\u2500 UI RENDERING \u2500\u2500\u2500
    def _update_ui(self):
        # Cancel previous countdown loop
        if self._countdown_job:
            self.after_cancel(self._countdown_job)
            self._countdown_job = None
            
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            self.status_label.destroy()
            
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Map to track timer labels for live countdown updates
        self._timer_label_map = {}
        
        # Dynamic model list: show all non-autocomplete models
        with self._data_lock:
            data_snapshot = json.loads(json.dumps(self.current_data))  # Deep copy
        
        if not data_snapshot:
            tk.Label(self.content_frame, text="No accounts found.\nClick \u2795 to add one.",
                     bg="#09090B", fg="#EA580C", font=("Candara", 10)).pack(pady=20)
            return

        for account in data_snapshot:
            email = account.get("email", "Unknown") if account.get("email") else "Unknown"
            email_short = email.split("@")[0] if "@" in email else email
            
            # \u2500\u2500 Account Header \u2500\u2500
            header = tk.Frame(self.content_frame, bg="#18181B", pady=4)
            header.pack(fill="x", pady=(0, 3))
            tk.Label(header, text=f"\U0001f464 {email_short}", bg="#18181B", fg="#EA580C",
                     font=("Candara", 10, "bold"), anchor="w").pack(side="left", padx=10)
            
            # Per-account refresh button (image-based)
            if self.img_refresh:
                btn_single = tk.Button(header, image=self.img_refresh, bg="#18181B",
                                       activebackground="#18181B", bd=0, relief="flat",
                                       highlightthickness=0, cursor="hand2")
            else:
                btn_single = tk.Button(header, text="\u27f3", bg="#18181B", fg="#EA580C",
                                       activebackground="#18181B", bd=0, relief="flat",
                                       highlightthickness=0, cursor="hand2", font=("Candara", 10))
            btn_single.config(command=lambda e=email: self.manual_refresh_single(e))
            btn_single.pack(side="right", padx=10)
            
            if self.spinners.get(email, False):
                self.animate_spinner(btn_single, email)
            
            # \u2500\u2500 Group models into 4 clean categories \u2500\u2500
            snapshot = account.get("snapshot")
            if not snapshot: continue
            models = snapshot.get("models", [])
            if not models: continue
            

            
            categories = {}  # { "Claude": {pct, reset_ms, model_id, used, limit, resetTime} }
            
            for model in models:
                if model.get("isAutocompleteOnly", False): continue
                label = model.get("label", "") or ""
                label_lower = label.lower()
                
                # Classify into category
                if "claude" in label_lower:
                    cat = "Claude"
                elif "pro" in label_lower:
                    cat = "Gemini Pro"
                elif "flash" in label_lower or "gemini" in label_lower:
                    cat = "Gemini Flash"
                else:
                    continue  # Skip unknown models
                
                pct_raw = model.get("remainingPercentage")
                pct = int((pct_raw if pct_raw is not None else 0) * 100)
                reset_ms = model.get("timeUntilResetMs", 0) or 0
                
                # Keep the LOWEST percentage per category (the bottleneck)
                if cat not in categories or pct < categories[cat]["pct"]:
                    categories[cat] = {
                        "pct": pct,
                        "reset_ms": reset_ms,
                        "model_id": model.get("modelId", ""),
                        "used": model.get("used", "?"),
                        "limit": model.get("limit", "?"),
                        "resetTime": model.get("resetTime", "Unknown"),
                        "exhausted": model.get("isExhausted", False),
                    }
            
            # Render in fixed order with strict alignment
            for cat in ["Claude", "Gemini Pro", "Gemini Flash"]:
                if cat not in categories: continue
                info = categories[cat]
                pct = info["pct"]
                reset_ms = info["reset_ms"]
                
                row = tk.Frame(self.content_frame, bg="#09090B")
                row.pack(fill="x", padx=10, pady=2)
                
                # 1. Category name (fixed 12 chars, packed left)
                tk.Label(row, text=cat, bg="#09090B", fg="#F97316",
                         font=("Candara", 10), width=12, anchor="w").pack(side="left")
                
                # 2. Percentage (fixed 5 chars, packed right)
                pct_color = "#4ADE80" if pct > 20 else ("#FCD34D" if pct > 5 else "#EF4444")
                if info["exhausted"]: pct_color = "#EF4444"
                tk.Label(row, text=f"{pct}%", bg="#09090B", fg=pct_color,
                         font=("Candara", 10, "bold"), width=5, anchor="e").pack(side="right")
                
                # 3. Timer (fixed 10 chars, packed right)
                timer_text = format_reset_time(reset_ms)
                timer_color = "#FCD34D" if reset_ms > 0 else "#4ADE80"
                timer_lbl = tk.Label(row, text=f"\u23f1{timer_text}", bg="#09090B", fg=timer_color,
                                     font=("Candara", 9), width=10, anchor="w")
                timer_lbl.pack(side="right", padx=(4, 0))
                self._timer_label_map[(email, info["model_id"])] = timer_lbl
                
                # 4. Progress bar (flexible fill in the middle, packed last)
                bar = ModernProgressBar(row, percentage=pct)
                bar.pack(side="left", fill="x", expand=True, padx=(4, 4))
                    
            tk.Frame(self.content_frame, bg="#09090B", height=8).pack()
        
        # Start live countdown ticker
        self._countdown_job = self.after(1000, self._tick_countdowns)

    def _show_error(self, err):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        tk.Label(self.content_frame, text=err, bg="#09090B", fg="#EF4444",
                 font=("Candara", 10, "bold")).pack(pady=40)

if __name__ == "__main__":
    app = QuotaWidget()
    app.mainloop()
