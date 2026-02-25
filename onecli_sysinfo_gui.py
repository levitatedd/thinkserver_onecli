import os
import sys
import subprocess
import threading
import tkinter as tk
import webbrowser
from tkinter import ttk, filedialog, messagebox

APP_NAME = "OneCli System Product Data Tool"
APP_VERSION = "1.2.0"

ONECLI_DEFAULT_NAME = "OneCli.exe"


def app_dir() -> str:
    """Return the directory where the app is running from (works for PyInstaller too)."""
    # When frozen by PyInstaller, sys.executable is the path to the .exe
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def find_onecli_nearby() -> str | None:
    """Try to find OneCli.exe in the app folder."""
    candidate = os.path.join(app_dir(), ONECLI_DEFAULT_NAME)
    return candidate if os.path.isfile(candidate) else None


def quote_arg(a: str) -> str:
    """Display-only quoting. subprocess is called with a list (no shell)."""
    if any(ch.isspace() for ch in a):
        return f'"{a}"'
    return a


class OneCliSysInfoGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.bmc_test_status = tk.StringVar(value="❔")
        self.minsize(780, 540)

        # Variables
        self.onecli_path = tk.StringVar(value=find_onecli_nearby() or "")
        self.bmc_ip = tk.StringVar()
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.identifier = tk.StringVar(value="ThinkSystem SR850 V2")
        self.product_name = tk.StringVar(value="7D32CTO1WW")
        self.serial_number = tk.StringVar(value="J1003NP6")
        
        for var in (self.bmc_ip, self.username, self.password):
            var.trace_add("write", lambda *args: self.invalidate_bmc_test())

        self.onecli_path.trace_add("write", lambda *args: self.refresh_onecli_ui_state())

        self._build_ui()
        self.refresh_onecli_ui_state()

        # If OneCli not found, prompt user immediately.
        if not self.onecli_path.get():
            self.after(200, self.prompt_for_onecli_if_missing)
       
    def on_test_bmc_clicked(self):
        if not self.validate_inputs():
            return

        self.bmc_test_status.set("⏳")
        self.status.set("Status: Testing BMC connection...")

        thread = threading.Thread(target=self.test_bmc_thread, daemon=True)
        thread.start()
    
    def test_bmc_thread(self):
        onecli = self.onecli_path.get().strip()
        bmc = f"{self.username.get()}:{self.password.get()}@{self.bmc_ip.get().strip()}"

        cmd = [
            onecli,
            "misc",
            "show",
            "system",
            "--bmc",
            bmc
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15
            )

            success = proc.returncode == 0

        except Exception:
            success = False

        self.after(0, lambda: self.on_bmc_test_finished(success))
    
    def on_bmc_test_finished(self, success: bool):
        if success:
            self.bmc_test_status.set("✅")
            self.status.set("Status: BMC connection successful (ready to run)")
            self.run_btn.configure(state="normal")
        else:
            self.bmc_test_status.set("❌")
            self.status.set("Status: BMC connection failed")
            self.run_btn.configure(state="disabled")
    
    def invalidate_bmc_test(self):
        self.bmc_test_status.set("❔")
        self.status.set("Status: Not tested")
        self.run_btn.configure(state="disabled")
    
    def open_onecli_download(self, event=None):
        webbrowser.open("https://download.lenovo.com/servers/mig/2023/11/16/58699/lnvgy_utl_lxce_onecli01l-4.3.0_winsrv_x86-64.zip")
    
    def refresh_onecli_ui_state(self):
        p = self.onecli_path.get().strip()
        missing = (not p) or (not os.path.isfile(p))

        if missing:
            # show link if not already visible
            if not self.onecli_download_link.winfo_ismapped():
                self.onecli_download_link.pack(anchor="w", padx=12, pady=(0, 6))
        else:
            # hide link if visible
            if self.onecli_download_link.winfo_ismapped():
                self.onecli_download_link.pack_forget()
    
    def _build_ui(self):
        pad = 10
        main = ttk.Frame(self, padding=pad)
        main.pack(fill="both", expand=True)
        
        style = ttk.Style()
        style.configure("Footer.TLabel", foreground="gray")

        # --- OneCli path row
        path_frame = ttk.LabelFrame(main, text="OneCli.exe Path")
        path_frame.pack(fill="x", padx=0, pady=(0, pad))

        path_row = ttk.Frame(path_frame)
        path_row.pack(fill="x", padx=pad, pady=pad)

        ttk.Label(path_row, text="Path:").pack(side="left")
        self.path_entry = ttk.Entry(path_row, textvariable=self.onecli_path)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(8, 8))

        ttk.Button(path_row, text="Browse...", command=self.browse_onecli).pack(side="left")

    # --- Download link (hidden unless OneCli is missing) ---
        self.onecli_download_link = ttk.Label(
            path_frame,
            text="Download Lenovo OneCli",
            foreground="blue",
            cursor="hand2"
        )
        self.onecli_download_link.bind("<Button-1>", self.open_onecli_download)

        # start hidden
        self.onecli_download_link.pack_forget()    

        # --- Credentials frame
        cred = ttk.LabelFrame(main, text="BMC Credentials")
        cred.pack(fill="x", pady=(0, pad))

        grid = ttk.Frame(cred, padding=pad)
        grid.pack(fill="x")

        self._labeled_entry(grid, "BMC IP / Hostname", self.bmc_ip, 0, placeholder="10.0.0.25")
        self._labeled_entry(grid, "Username", self.username, 1, placeholder="USERID")
        self._labeled_entry(grid, "Password", self.password, 2, placeholder="PASSW0RD")

        # --- Sysinfo frame
        sysinfo = ttk.LabelFrame(main, text="System Product Data")
        sysinfo.pack(fill="x", pady=(0, pad))

        grid2 = ttk.Frame(sysinfo, padding=pad)
        grid2.pack(fill="x")

        self._labeled_entry(grid2, "System Identifier", self.identifier, 0, placeholder="ThinkSystem SR850 V2")
        self._labeled_entry(grid2, "System Product Number", self.product_name, 1, placeholder="7D32CTO1WW")
        self._labeled_entry(grid2, "System Serial Number", self.serial_number, 2, placeholder="J1003NP6")

        # --- Buttons
        btns = ttk.Frame(main)
        btns.pack(fill="x", pady=(0, pad))

        ttk.Button(
        btns,
        text="Test BMC Connection",
        command=self.on_test_bmc_clicked
        ).pack(side="left", padx=(0, 8))

        self.run_btn = ttk.Button(
            btns,
            text="Run Commands",
            command=self.on_run_clicked,
            state="disabled"
        )
        self.run_btn.pack(side="left")

        ttk.Button(btns, text="Show Commands (Preview)", command=self.preview_commands).pack(side="left", padx=(8, 0))
        ttk.Button(btns, text="Clear Output", command=self.clear_output).pack(side="left", padx=(8, 8))

        # Status area (emoji + text together on the right)
        self.status = tk.StringVar(value="Status: Not tested")

        status_frame = ttk.Frame(btns)
        status_frame.pack(side="right")

        self.bmc_status_label = ttk.Label(
            status_frame,
            textvariable=self.bmc_test_status,
            font=("Segoe UI", 14)
        )
        self.bmc_status_label.pack(side="left", padx=(0, 4))

        ttk.Label(status_frame, textvariable=self.status).pack(side="left")

        # --- Output area
        out_frame = ttk.LabelFrame(main, text="Output")
        out_frame.pack(fill="both", expand=True)

        self.output = tk.Text(out_frame, height=14, wrap="word")
        self.output.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(out_frame, orient="vertical", command=self.output.yview)
        sb.pack(side="right", fill="y")
        self.output.configure(yscrollcommand=sb.set)

        # --- Footer ---
        footer = ttk.Frame(main)
        footer.pack(fill="x", pady=(2, 0))

        ttk.Label(
        footer,
        text=f"v{APP_VERSION} | Tested with Lenovo OneCli v4.3.0",
        style="Footer.TLabel"
        ).pack(side="right", padx=8)

        # A little nicer on Windows
        try:
            style = ttk.Style()
            style.theme_use("vista")
        except Exception:
            pass
        
    def _labeled_entry(self, parent, label, var, row, show=None, placeholder=""):
        ttk.Label(parent, text=label + ":").grid(row=row, column=0, sticky="w", pady=4)
        entry = ttk.Entry(parent, textvariable=var, show=show or "")
        entry.grid(row=row, column=1, sticky="ew", pady=4, padx=(8, 0))
        parent.grid_columnconfigure(1, weight=1)

        # (Optional) placeholder behavior: do nothing by default, just a hint in UI label.

    def log(self, text: str):
        self.output.insert("end", text + "\n")
        self.output.see("end")
        self.update_idletasks()

    def clear_output(self):
        self.output.delete("1.0", "end")

    def browse_onecli(self):
        start_dir = app_dir()
        path = filedialog.askopenfilename(
            title="Select OneCli.exe",
            initialdir=start_dir,
            filetypes=[
                ("OneCli executable", "OneCli.exe"),
                ("Executable", "*.exe"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.onecli_path.set(path)
            self.refresh_onecli_ui_state()

    def prompt_for_onecli_if_missing(self):
        # If OneCli isn't found, ask user if they want to browse for it now.
        if not self.onecli_path.get() or not os.path.isfile(self.onecli_path.get()):
            resp = messagebox.askyesno(
                "OneCli.exe not found",
                "I couldn't find OneCli.exe in the same folder as this app.\n\n"
                "Do you want to browse for OneCli.exe now?",
            )
            if resp:
                self.browse_onecli()

    def validate_inputs(self) -> bool:
        # Validate OneCli
        p = self.onecli_path.get().strip()
        if not p or not os.path.isfile(p):
            messagebox.showerror(
                "Missing OneCli.exe",
                "OneCli.exe path is missing or invalid.\n\n"
                "Place OneCli.exe in the same folder as this app\n"
                "or click Browse... to select it.",
            )
            return False

        # Required fields
        required = {
            "BMC IP / Hostname": self.bmc_ip.get().strip(),
            "Username": self.username.get().strip(),
            "Password": self.password.get(),  # allow spaces
            "System Identifier": self.identifier.get().strip(),
            "System Product Number": self.product_name.get().strip(),
            "System Serial Number": self.serial_number.get().strip(),
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            messagebox.showerror("Missing fields", "Please fill in:\n- " + "\n- ".join(missing))
            return False

        return True

    def build_commands(self):
        onecli = self.onecli_path.get().strip()
        bmc = f"{self.username.get()}:{self.password.get()}@{self.bmc_ip.get().strip()}"

        return [
            [
                onecli,
                "config",
                "set",
                "SYSTEM_PROD_DATA.SysInfoProdIdentifier",
                self.identifier.get().strip(),
                "--bmc",
                bmc,
            ],
            [
                onecli,
                "config",
                "set",
                "SYSTEM_PROD_DATA.SysInfoProdName",
                self.product_name.get().strip(),
                "--bmc",
                bmc,
            ],
            [
                onecli,
                "config",
                "set",
                "SYSTEM_PROD_DATA.SysInfoSerialNum",
                self.serial_number.get().strip(),
                "--bmc",
                bmc,
            ],
        ]

    def preview_commands(self):
        if not self.validate_inputs():
            return
        cmds = self.build_commands()
        lines = [" ".join(quote_arg(x) for x in c) for c in cmds]
        messagebox.showinfo("Command Preview", "\n\n".join(lines))

    def on_run_clicked(self):
        if not self.validate_inputs():
            return

        if not messagebox.askyesno("Confirm", "Run the 3 OneCli commands now?"):
            return

        self.run_btn.configure(state="disabled")
        self.status.set("Status: Running commands...")
        self.log("=== Running OneCli commands ===")

        thread = threading.Thread(target=self.run_commands_thread, daemon=True)
        thread.start()

    def run_commands_thread(self):
        cmds = self.build_commands()
        any_fail = False

        for idx, cmd in enumerate(cmds, start=1):
            self.log(f"\n--- Command {idx}/3 ---")
            self.log(" ".join(quote_arg(x) for x in cmd))

            try:
                proc = subprocess.run(cmd, capture_output=True, text=True)
                if proc.stdout:
                    self.log(proc.stdout.rstrip())
                if proc.stderr:
                    self.log(proc.stderr.rstrip())

                if proc.returncode != 0:
                    any_fail = True
                    self.log(f"[ERROR] Exit code: {proc.returncode}")
                else:
                    self.log("[OK]")

            except FileNotFoundError:
                any_fail = True
                self.log("[ERROR] OneCli.exe was not found at the selected path.")
                break
            except Exception as e:
                any_fail = True
                self.log(f"[ERROR] {type(e).__name__}: {e}")
                break

        self.after(0, lambda: self.on_run_finished(any_fail))

    def on_run_finished(self, any_fail: bool):
        self.run_btn.configure(state="normal")
        self.status.set(
            "Status: Completed successfully"
            if not any_fail
            else "Status: Completed with errors"
        )
        if any_fail:
            messagebox.showwarning("Finished", "Completed with errors. Check Output for details.")
        else:
            messagebox.showinfo("Finished", "All commands completed successfully.")


if __name__ == "__main__":
    OneCliSysInfoGUI().mainloop()
