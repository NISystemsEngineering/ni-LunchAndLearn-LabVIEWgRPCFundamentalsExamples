#!/usr/bin/env python3
"""
NI XNET CAN Bus Monitor – gRPC Client
======================================
A tkinter-based GUI client that communicates with the Bus Monitor gRPC
service defined in Bus_Monitor_API.proto.

Prerequisites
-------------
1.  pip install -r requirements.txt
2.  python generate_stubs.py        # creates the *_pb2*.py stubs
3.  python bus_monitor_client.py    # launch the GUI

UI theme: ttk "alt"
"""

from __future__ import annotations

import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# gRPC stub imports – generated from Bus_Monitor_API.proto
# ---------------------------------------------------------------------------
try:
    import grpc
    import proto.Bus_Monitor_API_pb2 as pb2
    import proto.Bus_Monitor_API_pb2_grpc as pb2_grpc
except ImportError as exc:
    print(
        "Could not import gRPC stubs.  Make sure you have run:\n"
        "  pip install -r requirements.txt\n"
        "  python generate_stubs.py\n"
    )
    raise SystemExit(1) from exc

# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

FRAME_TYPE_NAMES = {
    0: "CAN Data",
    1: "CAN Remote",
    2: "CAN Bus Error",
    3: "CAN 2.0 Data",
    4: "CAN FD Data",
    5: "CAN FD+BRS",
    6: "J1939 Data",
    7: "Delay",
    8: "Log Trigger",
    9: "Start Trigger",
    10: "All",
}

COMM_STATE_NAMES = {
    0: "Error Active",
    1: "Error Passive",
    2: "Bus Off",
    3: "Init",
}

LAST_ERROR_NAMES = {
    0: "None",
    1: "Stuff",
    2: "Form",
    3: "ACK",
    4: "Bit1",
    5: "Bit0",
    6: "CRC",
}

DIRECTION_MAP = {"TX + RX": 0, "RX Only": 1, "TX Only": 2}
FRAME_FILTER_MAP = {
    "CAN Data": 0,
    "CAN Remote": 1,
    "CAN Bus Error": 2,
    "CAN 2.0 Data": 3,
    "CAN FD Data": 4,
    "CAN FD+BRS Data": 5,
    "J1939 Data": 6,
    "Delay": 7,
    "Log Trigger": 8,
    "Start Trigger": 9,
    "All": 10,
}

CAN_MODE_MAP = {"CAN 2.0": 0, "CAN FD": 1, "CAN FD+BRS": 2}
FD_ISO_MAP = {"ISO": 0, "Non-ISO": 1, "ISO Legacy": 2}
TERMINATION_MAP = {"Off": 0, "On": 1}

MAX_TABLE_ROWS = 1000

# ---------------------------------------------------------------------------
# Colour palette & styling constants (applied on top of ttk "alt" theme)
# ---------------------------------------------------------------------------

BG           = "#1e1e2e"
BG_PANEL     = "#262637"
BG_ENTRY     = "#2e2e42"
FG           = "#cdd6f4"
FG_DIM       = "#7f849c"
ACCENT       = "#89b4fa"
ACCENT_HOVER = "#74c7ec"
GREEN        = "#a6e3a1"
RED          = "#f38ba8"
YELLOW       = "#f9e2af"
ORANGE       = "#fab387"
BORDER       = "#45475a"
HEADER_BG    = "#313244"
ROW_ALT      = "#2a2a3c"

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

class BusMonitorClient(tk.Tk):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()

        self.title("NI XNET CAN Bus Monitor – gRPC Client")
        self.configure(bg=BG)
        self.minsize(1100, 740)
        self.geometry("1280x800")

        # ---- State ----
        self.channel: Optional[grpc.Channel] = None
        self.stub: Optional[pb2_grpc.Bus_Monitor_APIStub] = None
        self.session: Optional[pb2.Session] = None
        self.streaming = False
        self._stream_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._frame_buffer: deque = deque(maxlen=MAX_TABLE_ROWS)

        # ---- Style ----
        self._setup_styles()

        # ---- Layout ----
        self._build_ui()

        # ---- Close handler ----
        self.protocol("WM_DELETE_WINDOW", self._on_exit)

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("alt")

        # Global defaults
        style.configure(".", background=BG, foreground=FG, fieldbackground=BG_ENTRY,
                         borderwidth=0, font=("Segoe UI", 10))

        # Frames / Label‑frames
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=BG_PANEL)
        style.configure("TLabelframe", background=BG_PANEL, foreground=ACCENT,
                         font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe.Label", background=BG_PANEL, foreground=ACCENT,
                         font=("Segoe UI", 10, "bold"))

        # Labels
        style.configure("TLabel", background=BG_PANEL, foreground=FG)
        style.configure("Heading.TLabel", font=("Segoe UI", 13, "bold"), foreground=ACCENT,
                         background=BG)
        style.configure("Status.TLabel", font=("Segoe UI", 9), foreground=FG_DIM,
                         background=BG)
        style.configure("Good.TLabel", foreground=GREEN, background=BG_PANEL)
        style.configure("Warn.TLabel", foreground=YELLOW, background=BG_PANEL)
        style.configure("Bad.TLabel",  foreground=RED,    background=BG_PANEL)
        style.configure("Val.TLabel",  foreground=FG, background=BG_PANEL,
                         font=("Consolas", 10))

        # Buttons
        style.configure("Accent.TButton", background=ACCENT, foreground="#11111b",
                         font=("Segoe UI", 10, "bold"), padding=(14, 6))
        style.map("Accent.TButton",
                   background=[("active", ACCENT_HOVER), ("disabled", BORDER)],
                   foreground=[("disabled", FG_DIM)])

        style.configure("Green.TButton", background=GREEN, foreground="#11111b",
                         font=("Segoe UI", 10, "bold"), padding=(14, 6))
        style.map("Green.TButton",
                   background=[("active", "#b5f0b0"), ("disabled", BORDER)])

        style.configure("Red.TButton", background=RED, foreground="#11111b",
                         font=("Segoe UI", 10, "bold"), padding=(14, 6))
        style.map("Red.TButton",
                   background=[("active", "#f7a0b8"), ("disabled", BORDER)])

        style.configure("Orange.TButton", background=ORANGE, foreground="#11111b",
                         font=("Segoe UI", 10, "bold"), padding=(14, 6))
        style.map("Orange.TButton",
                   background=[("active", "#fcc5a0"), ("disabled", BORDER)])

        # Entry
        style.configure("TEntry", fieldbackground=BG_ENTRY, foreground=FG,
                         insertcolor=FG, padding=5)

        # Combobox
        style.configure("TCombobox", fieldbackground=BG_ENTRY, foreground=FG,
                         selectbackground=ACCENT, selectforeground="#11111b",
                         padding=4)
        style.map("TCombobox", fieldbackground=[("readonly", BG_ENTRY)])
        self.option_add("*TCombobox*Listbox.background", BG_ENTRY)
        self.option_add("*TCombobox*Listbox.foreground", FG)
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT)

        # Treeview (frame table)
        style.configure("Treeview",
                         background=BG_PANEL,
                         foreground=FG,
                         fieldbackground=BG_PANEL,
                         rowheight=24,
                         font=("Consolas", 9))
        style.configure("Treeview.Heading",
                         background=HEADER_BG,
                         foreground=ACCENT,
                         font=("Segoe UI", 9, "bold"))
        style.map("Treeview",
                   background=[("selected", ACCENT)],
                   foreground=[("selected", "#11111b")])

        # Separator
        style.configure("TSeparator", background=BORDER)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # Header
        hdr = ttk.Frame(self)
        hdr.pack(fill="x", padx=16, pady=(12, 4))
        ttk.Label(hdr, text="CAN Bus Monitor", style="Heading.TLabel",
                   background=BG).pack(side="left")
        self.status_lbl = ttk.Label(hdr, text="Disconnected", style="Status.TLabel")
        self.status_lbl.pack(side="right")

        ttk.Separator(self).pack(fill="x", padx=16, pady=4)

        # Body: left panel + right table
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=16, pady=4)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        left = ttk.Frame(body, style="Panel.TFrame", width=340)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        left.grid_propagate(False)
        left.configure(width=340)

        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)

        self._build_connection_panel(left)
        self._build_filter_panel(left)
        self._build_stream_panel(left)
        self._build_comm_state_panel(right)
        self._build_frame_table(right)

        # Footer
        foot = ttk.Frame(self)
        foot.pack(fill="x", padx=16, pady=(4, 12))
        ttk.Button(foot, text="✕  Exit", style="Red.TButton",
                    command=self._on_exit).pack(side="right")

    # ---- Connection ----

    def _build_connection_panel(self, parent: ttk.Frame) -> None:
        grp = ttk.LabelFrame(parent, text="  Connection  ", padding=10)
        grp.pack(fill="x", padx=8, pady=(8, 4))

        r = 0
        # Server
        ttk.Label(grp, text="Server IP").grid(row=r, column=0, sticky="w", pady=2)
        self.server_ip = ttk.Entry(grp, width=22)
        self.server_ip.insert(0, "localhost")
        self.server_ip.grid(row=r, column=1, sticky="ew", padx=(6, 0), pady=2)
        r += 1

        ttk.Label(grp, text="Port").grid(row=r, column=0, sticky="w", pady=2)
        self.server_port = ttk.Entry(grp, width=22)
        self.server_port.insert(0, "50051")
        self.server_port.grid(row=r, column=1, sticky="ew", padx=(6, 0), pady=2)
        r += 1

        ttk.Separator(grp).grid(row=r, column=0, columnspan=2, sticky="ew", pady=6); r += 1

        # Session name
        ttk.Label(grp, text="Session Name").grid(row=r, column=0, sticky="w", pady=2)
        self.session_name = ttk.Entry(grp, width=22)
        self.session_name.insert(0, "session0")
        self.session_name.grid(row=r, column=1, sticky="ew", padx=(6, 0), pady=2)
        r += 1

        # CAN port
        ttk.Label(grp, text="CAN Port").grid(row=r, column=0, sticky="w", pady=2)
        self.can_port = ttk.Entry(grp, width=22)
        self.can_port.insert(0, "CAN1")
        self.can_port.grid(row=r, column=1, sticky="ew", padx=(6, 0), pady=2)
        r += 1

        # CAN mode
        ttk.Label(grp, text="CAN Mode").grid(row=r, column=0, sticky="w", pady=2)
        self.can_mode = ttk.Combobox(grp, values=list(CAN_MODE_MAP.keys()),
                                      state="readonly", width=19)
        self.can_mode.current(0)
        self.can_mode.grid(row=r, column=1, sticky="ew", padx=(6, 0), pady=2)
        r += 1

        # Baud rate
        ttk.Label(grp, text="Baud Rate").grid(row=r, column=0, sticky="w", pady=2)
        self.baud_rate = ttk.Combobox(grp,
                                       values=["125000", "250000", "500000", "1000000"],
                                       width=19)
        self.baud_rate.set("500000")
        self.baud_rate.grid(row=r, column=1, sticky="ew", padx=(6, 0), pady=2)
        r += 1

        # FD Baud rate
        ttk.Label(grp, text="FD Baud Rate").grid(row=r, column=0, sticky="w", pady=2)
        self.fd_baud = ttk.Combobox(grp,
                                     values=["1000000", "2000000", "4000000", "5000000", "8000000"],
                                     width=19)
        self.fd_baud.set("2000000")
        self.fd_baud.grid(row=r, column=1, sticky="ew", padx=(6, 0), pady=2)
        r += 1

        # FD ISO mode
        ttk.Label(grp, text="FD ISO Mode").grid(row=r, column=0, sticky="w", pady=2)
        self.fd_iso = ttk.Combobox(grp, values=list(FD_ISO_MAP.keys()),
                                    state="readonly", width=19)
        self.fd_iso.current(0)
        self.fd_iso.grid(row=r, column=1, sticky="ew", padx=(6, 0), pady=2)
        r += 1

        # Termination
        ttk.Label(grp, text="Termination").grid(row=r, column=0, sticky="w", pady=2)
        self.termination = ttk.Combobox(grp, values=list(TERMINATION_MAP.keys()),
                                         state="readonly", width=19)
        self.termination.current(0)
        self.termination.grid(row=r, column=1, sticky="ew", padx=(6, 0), pady=2)
        r += 1

        # Default filter IDs
        ttk.Label(grp, text="Default Filter IDs").grid(row=r, column=0, sticky="w", pady=2)
        self.default_ids = ttk.Entry(grp, width=22)
        self.default_ids.insert(0, "")
        self.default_ids.grid(row=r, column=1, sticky="ew", padx=(6, 0), pady=2)
        r += 1

        grp.columnconfigure(1, weight=1)

        # Connect button
        self.connect_btn = ttk.Button(grp, text="Connect", style="Green.TButton",
                                       command=self._on_connect)
        self.connect_btn.grid(row=r, column=0, columnspan=2, sticky="ew", pady=(10, 0))

    # ---- Filter ----

    def _build_filter_panel(self, parent: ttk.Frame) -> None:
        grp = ttk.LabelFrame(parent, text="  Streaming Filter  ", padding=10)
        grp.pack(fill="x", padx=8, pady=4)

        r = 0
        ttk.Label(grp, text="Arb IDs (hex, csv)").grid(row=r, column=0, sticky="w", pady=2)
        self.filter_ids = ttk.Entry(grp, width=22)
        self.filter_ids.grid(row=r, column=1, sticky="ew", padx=(6, 0), pady=2)
        r += 1

        ttk.Label(grp, text="Direction").grid(row=r, column=0, sticky="w", pady=2)
        self.dir_filter = ttk.Combobox(grp, values=list(DIRECTION_MAP.keys()),
                                        state="readonly", width=19)
        self.dir_filter.current(0)
        self.dir_filter.grid(row=r, column=1, sticky="ew", padx=(6, 0), pady=2)
        r += 1

        ttk.Label(grp, text="Frame Type").grid(row=r, column=0, sticky="w", pady=2)
        self.frame_filter = ttk.Combobox(grp, values=list(FRAME_FILTER_MAP.keys()),
                                          state="readonly", width=19)
        self.frame_filter.current(0)
        self.frame_filter.grid(row=r, column=1, sticky="ew", padx=(6, 0), pady=2)
        r += 1

        grp.columnconfigure(1, weight=1)

        btn_row = ttk.Frame(grp, style="Panel.TFrame")
        btn_row.grid(row=r, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        btn_row.columnconfigure(0, weight=1)
        btn_row.columnconfigure(1, weight=1)

        self.set_filter_btn = ttk.Button(btn_row, text="Set Filter",
                                          style="Accent.TButton",
                                          command=self._on_set_filter, state="disabled")
        self.set_filter_btn.grid(row=0, column=0, sticky="ew", padx=(0, 3))

        self.get_filter_btn = ttk.Button(btn_row, text="Get Filter",
                                          style="Accent.TButton",
                                          command=self._on_get_filter, state="disabled")
        self.get_filter_btn.grid(row=0, column=1, sticky="ew", padx=(3, 0))

    # ---- Stream ----

    def _build_stream_panel(self, parent: ttk.Frame) -> None:
        grp = ttk.LabelFrame(parent, text="  Stream Control  ", padding=10)
        grp.pack(fill="x", padx=8, pady=4)

        self.stream_btn = ttk.Button(grp, text="▶  Start Stream",
                                      style="Green.TButton",
                                      command=self._on_toggle_stream, state="disabled")
        self.stream_btn.pack(fill="x")

        self.stream_status = ttk.Label(grp, text="Idle", style="Status.TLabel")
        self.stream_status.pack(anchor="w", pady=(6, 0))

    # ---- CAN Comm State ----

    def _build_comm_state_panel(self, parent: ttk.Frame) -> None:
        grp = ttk.LabelFrame(parent, text="  CAN Communication State  ", padding=10)
        grp.pack(fill="x", pady=(0, 6))
        grp.configure(style="TLabelframe")

        # Build a 2‑column grid of state indicators
        labels = [
            ("Comm State",      "comm_state"),
            ("Last Error",      "last_error"),
            ("Fault",           "fault"),
            ("Fault Code",      "fault_code"),
            ("RX Error Count",  "rx_err"),
            ("TX Error Count",  "tx_err"),
            ("Transceiver Err", "xcvr_err"),
            ("Sleep",           "sleep"),
        ]
        self._cs_vars: dict[str, tk.StringVar] = {}
        self._cs_labels: dict[str, ttk.Label] = {}
        for i, (text, key) in enumerate(labels):
            col_base = 0 if i < 4 else 2
            row = i % 4
            ttk.Label(grp, text=text, foreground=FG_DIM,
                       font=("Segoe UI", 9)).grid(row=row, column=col_base, sticky="w",
                                                    padx=(8, 4), pady=1)
            var = tk.StringVar(value="—")
            self._cs_vars[key] = var
            lbl = ttk.Label(grp, textvariable=var, style="Val.TLabel")
            lbl.grid(row=row, column=col_base + 1, sticky="w", padx=(0, 20), pady=1)
            self._cs_labels[key] = lbl

        grp.columnconfigure(1, weight=1)
        grp.columnconfigure(3, weight=1)

    # ---- Frame Table ----

    def _build_frame_table(self, parent: ttk.Frame) -> None:
        tbl_frame = ttk.Frame(parent)
        tbl_frame.pack(fill="both", expand=True, pady=(0, 0))
        tbl_frame.rowconfigure(0, weight=1)
        tbl_frame.columnconfigure(0, weight=1)

        columns = ("timestamp", "arb_id", "type", "ext", "echo", "dlc", "data")
        self.tree = ttk.Treeview(tbl_frame, columns=columns, show="headings",
                                  selectmode="browse")
        headings = {
            "timestamp": ("Timestamp", 140),
            "arb_id":    ("Arb ID",     80),
            "type":      ("Type",      100),
            "ext":       ("Ext",        40),
            "echo":      ("Echo",       44),
            "dlc":       ("DLC",        40),
            "data":      ("Payload (hex)", 320),
        }
        for col, (label, w) in headings.items():
            self.tree.heading(col, text=label, anchor="w")
            self.tree.column(col, width=w, minwidth=w, anchor="w")

        # Scrollbar
        vsb = ttk.Scrollbar(tbl_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        # Row‑count label
        self.row_count_lbl = ttk.Label(parent, text="0 frames", style="Status.TLabel")
        self.row_count_lbl.pack(anchor="e", pady=(2, 0))

    # ------------------------------------------------------------------
    # gRPC helpers
    # ------------------------------------------------------------------

    def _make_channel(self) -> grpc.Channel:
        target = f"{self.server_ip.get().strip()}:{self.server_port.get().strip()}"
        return grpc.insecure_channel(target)

    def _require_session(self) -> bool:
        if self.session is None:
            messagebox.showwarning("Not Connected",
                                    "Please connect first (InitializeSettings).")
            return False
        return True

    def _parse_hex_ids(self, text: str) -> list[int]:
        """Parse a comma‑separated list of hex arb IDs."""
        ids: list[int] = []
        for token in text.replace(" ", "").split(","):
            if token:
                ids.append(int(token, 16))
        return ids

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def _on_connect(self) -> None:
        """Call InitializeSettings and establish a session."""
        try:
            self.channel = self._make_channel()
            self.stub = pb2_grpc.Bus_Monitor_APIStub(self.channel)

            settings = pb2.ConnectSettings(
                port=self.can_port.get().strip(),
                can_mode=CAN_MODE_MAP[self.can_mode.get()],
                termination=TERMINATION_MAP[self.termination.get()],
                baud_rate=int(self.baud_rate.get()),
                fd_baud_rate=int(self.fd_baud.get()),
                fd_iso_mode=FD_ISO_MAP[self.fd_iso.get()],
            )

            default_ids = self._parse_hex_ids(self.default_ids.get())

            request = pb2.InitializeSettingsRequest(
                name=self.session_name.get().strip(),
                connect_settings=settings,
                default_filter_ids=default_ids,
            )

            reply: pb2.InitializeSettingsReply = self.stub.InitializeSettings(request)

            if reply.error and reply.error.code != 0:
                messagebox.showerror("InitializeSettings Error",
                                      f"Code {reply.error.code}: {reply.error.source}")
                return

            self.session = reply.session
            self.status_lbl.configure(text=f"Connected  ·  {self.session.session_uid}",
                                       foreground=GREEN)
            # Enable buttons
            for btn in (self.set_filter_btn, self.get_filter_btn, self.stream_btn):
                btn.configure(state="normal")

            self.connect_btn.configure(text="Reconnect")
            self._log("Connected – session: " + self.session.session_uid)

        except grpc.RpcError as e:
            messagebox.showerror("gRPC Error", str(e))

    def _on_set_filter(self) -> None:
        if not self._require_session():
            return
        try:
            ids = self._parse_hex_ids(self.filter_ids.get())
            info = pb2.FilterInfo(
                filter_ids=ids,
                direction_filter=DIRECTION_MAP[self.dir_filter.get()],
                frame_filter=FRAME_FILTER_MAP[self.frame_filter.get()],
            )
            request = pb2.SetStreamingFilterRequest(
                session=self.session,
                filter_info=info,
            )
            reply = self.stub.SetStreamingFilter(request)

            if reply.error and reply.error.code != 0:
                messagebox.showerror("SetStreamingFilter Error",
                                      f"Code {reply.error.code}: {reply.error.source}")
                return
            self._log("Filter set successfully.")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_get_filter(self) -> None:
        if not self._require_session():
            return
        try:
            request = pb2.GetStreamingFilterRequest(session=self.session)
            reply = self.stub.GetStreamingFilter(request)

            if reply.error and reply.error.code != 0:
                messagebox.showerror("GetStreamingFilter Error",
                                      f"Code {reply.error.code}: {reply.error.source}")
                return

            fi = reply.filter_info
            hex_ids = ", ".join(f"0x{i:X}" for i in fi.filter_ids)
            # Push values back into the UI fields
            self.filter_ids.delete(0, tk.END)
            self.filter_ids.insert(0, ", ".join(f"{i:X}" for i in fi.filter_ids))

            direction_name = {v: k for k, v in DIRECTION_MAP.items()}.get(
                fi.direction_filter, "TX + RX")
            self.dir_filter.set(direction_name)

            frame_name = {v: k for k, v in FRAME_FILTER_MAP.items()}.get(
                fi.frame_filter, "CAN Data")
            self.frame_filter.set(frame_name)

            self._log(f"Filter received – IDs: [{hex_ids}], "
                       f"Dir: {direction_name}, Type: {frame_name}")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---- Streaming ----

    def _on_toggle_stream(self) -> None:
        if not self._require_session():
            return
        if self.streaming:
            self._stop_stream()
        else:
            self._start_stream()

    def _start_stream(self) -> None:
        self.streaming = True
        self._stop_event.clear()
        self.stream_btn.configure(text="■  Stop Stream", style="Orange.TButton")
        self.stream_status.configure(text="Streaming…", foreground=GREEN)
        self._stream_thread = threading.Thread(target=self._stream_worker, daemon=True)
        self._stream_thread.start()

    def _stop_stream(self) -> None:
        self._stop_event.set()
        self.streaming = False
        self.stream_btn.configure(text="▶  Start Stream", style="Green.TButton")
        self.stream_status.configure(text="Stopped", foreground=FG_DIM)

    def _stream_worker(self) -> None:
        """Background thread: consume StreamBus server‑streaming RPC."""
        try:
            request = pb2.StreamBusRequest(session=self.session)
            stream = self.stub.StreamBus(request)

            for reply in stream:
                if self._stop_event.is_set():
                    stream.cancel()
                    break

                # Schedule UI updates on the main thread
                self.after(0, self._process_stream_reply, reply)

        except grpc.RpcError as e:
            if not self._stop_event.is_set():
                self.after(0, lambda: messagebox.showerror("Stream Error", str(e)))
        finally:
            self.after(0, self._stop_stream)

    def _process_stream_reply(self, reply: pb2.StreamBusReply) -> None:
        """Handle one StreamBusReply on the main thread."""
        # Update CAN comm state
        cs = reply.can_comm_state
        if cs:
            self._update_comm_state(cs)

        # Insert frames (newest first)
        for frame in reply.frame:
            self._insert_frame(frame)

        self.row_count_lbl.configure(text=f"{min(len(self._frame_buffer), MAX_TABLE_ROWS)} frames")

    def _update_comm_state(self, cs: pb2.CanCommState) -> None:
        state_name = COMM_STATE_NAMES.get(cs.comm_state, str(cs.comm_state))
        self._cs_vars["comm_state"].set(state_name)
        # Colour‑code
        if cs.comm_state == 0:
            self._cs_labels["comm_state"].configure(style="Good.TLabel")
        elif cs.comm_state == 1:
            self._cs_labels["comm_state"].configure(style="Warn.TLabel")
        else:
            self._cs_labels["comm_state"].configure(style="Bad.TLabel")

        self._cs_vars["last_error"].set(LAST_ERROR_NAMES.get(cs.last_comm_error,
                                                              str(cs.last_comm_error)))
        self._cs_vars["fault"].set("YES" if cs.fault else "No")
        self._cs_labels["fault"].configure(style="Bad.TLabel" if cs.fault else "Good.TLabel")
        self._cs_vars["fault_code"].set(str(cs.fault_code))
        self._cs_vars["rx_err"].set(str(cs.receive_error_counter))
        self._cs_vars["tx_err"].set(str(cs.transmit_error_counter))
        self._cs_vars["xcvr_err"].set("YES" if cs.transceiver_error else "No")
        self._cs_labels["xcvr_err"].configure(
            style="Bad.TLabel" if cs.transceiver_error else "Good.TLabel")
        self._cs_vars["sleep"].set("YES" if cs.sleep else "No")

    def _insert_frame(self, frame: pb2.Frame) -> None:
        ts = f"{frame.timestamp:.6f}"
        arb = f"0x{frame.identifier:X}"
        ftype = FRAME_TYPE_NAMES.get(frame.frame_type, str(frame.frame_type))
        ext = "Y" if frame.extended else "N"
        echo = "Y" if frame.echo else "N"
        payload_bytes = bytes(frame.payload)
        dlc = str(len(payload_bytes))
        data_hex = " ".join(f"{b:02X}" for b in payload_bytes)

        values = (ts, arb, ftype, ext, echo, dlc, data_hex)
        self._frame_buffer.appendleft(values)

        # Insert at top of treeview
        self.tree.insert("", 0, values=values)

        # Trim beyond MAX_TABLE_ROWS
        children = self.tree.get_children()
        if len(children) > MAX_TABLE_ROWS:
            for iid in children[MAX_TABLE_ROWS:]:
                self.tree.delete(iid)

    # ------------------------------------------------------------------
    # Exit
    # ------------------------------------------------------------------

    def _on_exit(self) -> None:
        """Call StopProcess, tear down, and exit."""
        # Stop the stream first
        if self.streaming:
            self._stop_stream()
            time.sleep(0.2)

        # Call StopProcess if we have a session
        if self.stub and self.session:
            try:
                request = pb2.StopProcessRequest(session=self.session)
                reply = self.stub.StopProcess(request)
                if reply.error and reply.error.code != 0:
                    print(f"StopProcess error: {reply.error.code} – {reply.error.source}")
            except grpc.RpcError as e:
                print(f"StopProcess gRPC error: {e}")

        if self.channel:
            try:
                self.channel.close()
            except Exception:
                pass

        self.destroy()

    # ------------------------------------------------------------------
    # Logging (status bar)
    # ------------------------------------------------------------------

    def _log(self, msg: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.status_lbl.configure(text=f"[{stamp}]  {msg}", foreground=FG)


# -----------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------

if __name__ == "__main__":
    app = BusMonitorClient()
    app.mainloop()
