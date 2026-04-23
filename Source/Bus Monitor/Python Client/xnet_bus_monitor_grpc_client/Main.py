#!/usr/bin/env python3
"""
Bus Monitor gRPC Client
========================
A Tkinter-based GUI client for the NI-XNET CAN Bus Monitor gRPC API.
Uses the built-in 'alt' ttk theme.

Prerequisites:
    pip install grpcio grpcio-tools

Generate stubs before first run:
    python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. Bus_Monitor_API.proto
"""

"""
Using the attached proto, create a client example in python that connects to my application.  
This client example needs to have a UI that allows the user to set the server IP address and port.  
The client example must have a Connect button that calls the InitializeSettings function.  
The client example needs to have buttons for issuing SetStreamingFilter and GetStreaming Filter.  
The client example must have a button that starts and stops the StreamBus service.  
The Frame data returned from StreamBus must be posted in a table format. 
In the table, put the most recent data at the top. 
Limit the table to 1000 rows. 
Finally, there must be an exit button that calls the StopProcess services and exits the client example. 
For the UI style, use Alt.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import grpc

# Generated proto stubs — run the protoc command above first
import proto.Bus_Monitor_API_pb2 as pb2
import proto.Bus_Monitor_API_pb2_grpc as pb2_grpc

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FRAME_TYPE_LABELS = {
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

DIRECTION_LABELS = {0: "TX + RX", 1: "RX Only", 2: "TX Only"}

CAN_MODE_MAP = {"CAN 2.0": 0, "CAN FD": 1, "CAN FD+BRS": 2}
TERMINATION_MAP = {"Off": 0, "On": 1}
FD_ISO_MAP = {"ISO": 0, "Non-ISO": 1, "ISO Legacy": 2}

COMM_STATE_LABELS = {0: "Error Active", 1: "Error Passive", 2: "Bus Off", 3: "Init"}
LAST_ERR_LABELS = {0: "None", 1: "Stuff", 2: "Form", 3: "ACK", 4: "Bit1", 5: "Bit0", 6: "CRC"}

MAX_TABLE_ROWS = 1000

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------


class BusMonitorClient(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title("CAN Bus Monitor — gRPC Client")
        self.geometry("1280x820")
        self.minsize(1000, 650)

        # State
        self.channel = None
        self.stub = None
        self.session = None
        self.streaming = False
        self._stream_thread = None
        self._frame_counter = 0

        self._build_styles()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_exit)

    # ------------------------------------------------------------------
    # Styles — 'alt' theme with light custom overrides
    # ------------------------------------------------------------------

    def _build_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("alt")

        # General font
        self.style.configure(".", font=("Segoe UI", 10))

        # Status bar
        self.style.configure("Status.TLabel", font=("Consolas", 9),
                             padding=(8, 4), relief="sunken")

        # Green button — Connect / Start Stream
        self.style.configure("Green.TButton", background="#4caf50",
                             foreground="white", font=("Segoe UI", 10, "bold"),
                             padding=(14, 7))
        self.style.map("Green.TButton",
                       background=[("active", "#43a047"), ("disabled", "#a5d6a7")])

        # Red button — Stop / Exit
        self.style.configure("Red.TButton", background="#e53935",
                             foreground="white", font=("Segoe UI", 10, "bold"),
                             padding=(14, 7))
        self.style.map("Red.TButton",
                       background=[("active", "#c62828"), ("disabled", "#ef9a9a")])

        # Blue accent button — Set/Get Filter, Clear
        self.style.configure("Accent.TButton", background="#1976d2",
                             foreground="white", font=("Segoe UI", 10, "bold"),
                             padding=(14, 7))
        self.style.map("Accent.TButton",
                       background=[("active", "#1565c0"), ("disabled", "#90caf9")])

        # LabelFrame heading
        self.style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))

        # Treeview
        self.style.configure("Treeview", rowheight=24, font=("Consolas", 9))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    # ------------------------------------------------------------------
    # UI Layout
    # ------------------------------------------------------------------

    def _build_ui(self):
        # ---- Top bar: Connection ----
        conn_frame = ttk.LabelFrame(self, text="  Connection  ", padding=10)
        conn_frame.pack(fill="x", padx=12, pady=(12, 4))

        ttk.Label(conn_frame, text="Server IP:").grid(row=0, column=0, padx=(0, 4))
        self.entry_ip = ttk.Entry(conn_frame, width=18)
        self.entry_ip.insert(0, "localhost")
        self.entry_ip.grid(row=0, column=1, padx=(0, 12))

        ttk.Label(conn_frame, text="Port:").grid(row=0, column=2, padx=(0, 4))
        self.entry_port = ttk.Entry(conn_frame, width=8)
        self.entry_port.insert(0, "50051")
        self.entry_port.grid(row=0, column=3, padx=(0, 20))

        ttk.Label(conn_frame, text="Session Name:").grid(row=0, column=4, padx=(0, 4))
        self.entry_session = ttk.Entry(conn_frame, width=16)
        self.entry_session.insert(0, "BusMonitor1")
        self.entry_session.grid(row=0, column=5, padx=(0, 20))

        self.btn_connect = ttk.Button(conn_frame, text="Connect",
                                      style="Green.TButton", command=self._on_connect)
        self.btn_connect.grid(row=0, column=6, padx=(0, 6))

        self.lbl_conn_status = ttk.Label(conn_frame, text="● Disconnected",
                                          foreground="red")
        self.lbl_conn_status.grid(row=0, column=7, padx=(12, 0))

        # ---- Middle row: Settings + Filter ----
        mid = ttk.Frame(self)
        mid.pack(fill="x", padx=12, pady=4)

        # -- Initialize Settings --
        settings_frame = ttk.LabelFrame(mid, text="  XNET Settings  ", padding=10)
        settings_frame.pack(side="left", fill="both", expand=True, padx=(0, 6))

        row = 0
        ttk.Label(settings_frame, text="CAN Port:").grid(
            row=row, column=0, sticky="e", padx=(0, 4))
        self.entry_can_port = ttk.Entry(settings_frame, width=14)
        self.entry_can_port.insert(0, "CAN1")
        self.entry_can_port.grid(row=row, column=1, sticky="w")

        ttk.Label(settings_frame, text="CAN Mode:").grid(
            row=row, column=2, sticky="e", padx=(12, 4))
        self.combo_can_mode = ttk.Combobox(
            settings_frame, values=list(CAN_MODE_MAP.keys()),
            state="readonly", width=11)
        self.combo_can_mode.set("CAN 2.0")
        self.combo_can_mode.grid(row=row, column=3, sticky="w")

        row = 1
        ttk.Label(settings_frame, text="Baud Rate:").grid(
            row=row, column=0, sticky="e", padx=(0, 4), pady=4)
        self.entry_baud = ttk.Entry(settings_frame, width=14)
        self.entry_baud.insert(0, "500000")
        self.entry_baud.grid(row=row, column=1, sticky="w", pady=4)

        ttk.Label(settings_frame, text="FD Baud Rate:").grid(
            row=row, column=2, sticky="e", padx=(12, 4))
        self.entry_fd_baud = ttk.Entry(settings_frame, width=12)
        self.entry_fd_baud.insert(0, "2000000")
        self.entry_fd_baud.grid(row=row, column=3, sticky="w")

        row = 2
        ttk.Label(settings_frame, text="Termination:").grid(
            row=row, column=0, sticky="e", padx=(0, 4))
        self.combo_term = ttk.Combobox(
            settings_frame, values=list(TERMINATION_MAP.keys()),
            state="readonly", width=11)
        self.combo_term.set("Off")
        self.combo_term.grid(row=row, column=1, sticky="w")

        ttk.Label(settings_frame, text="FD ISO Mode:").grid(
            row=row, column=2, sticky="e", padx=(12, 4))
        self.combo_iso = ttk.Combobox(
            settings_frame, values=list(FD_ISO_MAP.keys()),
            state="readonly", width=11)
        self.combo_iso.set("ISO")
        self.combo_iso.grid(row=row, column=3, sticky="w")

        # -- Filter --
        filter_frame = ttk.LabelFrame(mid, text="  Streaming Filter  ", padding=10)
        filter_frame.pack(side="left", fill="both", expand=True, padx=(6, 0))

        ttk.Label(filter_frame, text="Direction:").grid(
            row=0, column=0, sticky="e", padx=(0, 4))
        self.combo_dir = ttk.Combobox(
            filter_frame, values=list(DIRECTION_LABELS.values()),
            state="readonly", width=11)
        self.combo_dir.set("TX + RX")
        self.combo_dir.grid(row=0, column=1, sticky="w")

        ttk.Label(filter_frame, text="Frame Type:").grid(
            row=1, column=0, sticky="e", padx=(0, 4), pady=4)
        self.combo_frame_type = ttk.Combobox(
            filter_frame, values=list(FRAME_TYPE_LABELS.values()),
            state="readonly", width=14)
        self.combo_frame_type.set("All")
        self.combo_frame_type.grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(filter_frame, text="Filter IDs (hex, comma-sep):").grid(
            row=2, column=0, columnspan=2, sticky="w")
        self.entry_filter_ids = ttk.Entry(filter_frame, width=28)
        self.entry_filter_ids.grid(row=3, column=0, columnspan=2, sticky="ew",
                                   pady=(0, 6))

        btn_row = ttk.Frame(filter_frame)
        btn_row.grid(row=4, column=0, columnspan=2, sticky="ew")
        self.btn_set_filter = ttk.Button(
            btn_row, text="Set Filter", style="Accent.TButton",
            command=self._on_set_filter)
        self.btn_set_filter.pack(side="left", padx=(0, 6))
        self.btn_get_filter = ttk.Button(
            btn_row, text="Get Filter", style="Accent.TButton",
            command=self._on_get_filter)
        self.btn_get_filter.pack(side="left")

        # ---- Stream Controls ----
        ctrl_frame = ttk.Frame(self)
        ctrl_frame.pack(fill="x", padx=12, pady=6)

        self.btn_stream = ttk.Button(
            ctrl_frame, text="▶  Start Stream", style="Green.TButton",
            command=self._on_toggle_stream)
        self.btn_stream.pack(side="left", padx=(0, 8))

        self.btn_clear = ttk.Button(
            ctrl_frame, text="Clear Table", style="Accent.TButton",
            command=self._on_clear_table)
        self.btn_clear.pack(side="left", padx=(0, 8))

        self.lbl_frame_count = ttk.Label(ctrl_frame, text="Frames: 0")
        self.lbl_frame_count.pack(side="left", padx=(12, 0))

        self.btn_exit = ttk.Button(
            ctrl_frame, text="■  Stop && Exit", style="Red.TButton",
            command=self._on_exit)
        self.btn_exit.pack(side="right")

        # ---- Data Table ----
        table_frame = ttk.LabelFrame(self, text="  Bus Stream Data  ", padding=4)
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        columns = ("idx", "timestamp", "id", "type", "ext", "echo", "dlc",
                   "payload")
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", height=18)
        self.tree.heading("idx", text="#")
        self.tree.heading("timestamp", text="Timestamp (s)")
        self.tree.heading("id", text="Arb ID")
        self.tree.heading("type", text="Frame Type")
        self.tree.heading("ext", text="Ext")
        self.tree.heading("echo", text="Echo")
        self.tree.heading("dlc", text="DLC")
        self.tree.heading("payload", text="Payload (hex)")

        self.tree.column("idx", width=50, anchor="center")
        self.tree.column("timestamp", width=130, anchor="center")
        self.tree.column("id", width=90, anchor="center")
        self.tree.column("type", width=110, anchor="center")
        self.tree.column("ext", width=45, anchor="center")
        self.tree.column("echo", width=50, anchor="center")
        self.tree.column("dlc", width=45, anchor="center")
        self.tree.column("payload", width=360, anchor="w")

        vsb = ttk.Scrollbar(table_frame, orient="vertical",
                            command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # ---- Comm State Bar ----
        comm_frame = ttk.Frame(self)
        comm_frame.pack(fill="x", padx=12, pady=(0, 2))
        self.lbl_comm = ttk.Label(comm_frame, text="Comm: —",
                                   style="Status.TLabel")
        self.lbl_comm.pack(fill="x")

        # ---- Status Bar ----
        self.lbl_status = ttk.Label(self, text="Ready", style="Status.TLabel")
        self.lbl_status.pack(fill="x", padx=12, pady=(0, 8))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_status(self, msg):
        self.lbl_status.configure(text=f"  {msg}")

    def _require_session(self):
        if self.session is None:
            messagebox.showwarning(
                "Not Connected",
                "Please connect to the server first (InitializeSettings).")
            return False
        return True

    def _parse_filter_ids(self):
        raw = self.entry_filter_ids.get().strip()
        if not raw:
            return []
        ids = []
        for token in raw.replace(" ", "").split(","):
            if token:
                ids.append(int(token, 16))
        return ids

    def _direction_value(self):
        label = self.combo_dir.get()
        for k, v in DIRECTION_LABELS.items():
            if v == label:
                return k
        return 0

    def _frame_filter_value(self):
        label = self.combo_frame_type.get()
        for k, v in FRAME_TYPE_LABELS.items():
            if v == label:
                return k
        return 10  # All

    # ------------------------------------------------------------------
    # Connection / InitializeSettings
    # ------------------------------------------------------------------

    def _on_connect(self):
        ip = self.entry_ip.get().strip()
        port = self.entry_port.get().strip()
        target = f"{ip}:{port}"

        try:
            if self.channel:
                self.channel.close()

            self.channel = grpc.insecure_channel(target)
            self.stub = pb2_grpc.Bus_Monitor_APIStub(self.channel)

            connect_settings = pb2.ConnectSettings(
                port=self.entry_can_port.get().strip(),
                can_mode=CAN_MODE_MAP[self.combo_can_mode.get()],
                termination=TERMINATION_MAP[self.combo_term.get()],
                baud_rate=int(self.entry_baud.get().strip()),
                fd_baud_rate=int(self.entry_fd_baud.get().strip()),
                fd_iso_mode=FD_ISO_MAP[self.combo_iso.get()],
            )

            default_ids = self._parse_filter_ids()

            request = pb2.InitializeSettingsRequest(
                name=self.entry_session.get().strip(),
                connect_settings=connect_settings,
                default_filter_ids=default_ids,
            )

            reply = self.stub.InitializeSettings(request, timeout=10)

            if reply.error and reply.error.code != 0:
                messagebox.showerror(
                    "Server Error",
                    f"Code {reply.error.code}: {reply.error.source}")
                self._set_status(
                    f"InitializeSettings failed — code {reply.error.code}")
                return

            self.session = reply.session
            self.lbl_conn_status.configure(
                text=f"● Connected ({target})", foreground="green")
            self._set_status(
                f"Connected — session '{self.session.name}' "
                f"[uid: {self.session.session_uid}]")

        except grpc.RpcError as e:
            messagebox.showerror(
                "Connection Failed",
                f"Could not reach server at {target}.\n\n{e.details()}")
            self._set_status(f"Connection failed: {e.code()}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self._set_status(f"Error: {e}")

    # ------------------------------------------------------------------
    # Set / Get Streaming Filter
    # ------------------------------------------------------------------

    def _on_set_filter(self):
        if not self._require_session():
            return
        try:
            filter_info = pb2.FilterInfo(
                filter_ids=self._parse_filter_ids(),
                direction_filter=self._direction_value(),
                frame_filter=self._frame_filter_value(),
            )
            request = pb2.SetStreamingFilterRequest(
                session=self.session, filter_info=filter_info)
            reply = self.stub.SetStreamingFilter(request, timeout=10)

            if reply.error and reply.error.code != 0:
                messagebox.showerror(
                    "SetStreamingFilter Error",
                    f"Code {reply.error.code}: {reply.error.source}")
            else:
                self._set_status("Streaming filter updated successfully.")
        except grpc.RpcError as e:
            messagebox.showerror("RPC Error", e.details())
            self._set_status(f"SetStreamingFilter failed: {e.code()}")

    def _on_get_filter(self):
        if not self._require_session():
            return
        try:
            request = pb2.GetStreamingFilterRequest(session=self.session)
            reply = self.stub.GetStreamingFilter(request, timeout=10)

            if reply.error and reply.error.code != 0:
                messagebox.showerror(
                    "GetStreamingFilter Error",
                    f"Code {reply.error.code}: {reply.error.source}")
                return

            fi = reply.filter_info
            ids_hex = ", ".join(f"0x{i:X}" for i in fi.filter_ids)
            self.entry_filter_ids.delete(0, tk.END)
            self.entry_filter_ids.insert(0, ids_hex)

            dir_label = DIRECTION_LABELS.get(fi.direction_filter, "TX + RX")
            self.combo_dir.set(dir_label)

            ft_label = FRAME_TYPE_LABELS.get(fi.frame_filter, "All")
            self.combo_frame_type.set(ft_label)

            self._set_status(
                f"Filter retrieved — direction={dir_label}, "
                f"type={ft_label}, IDs=[{ids_hex}]")
        except grpc.RpcError as e:
            messagebox.showerror("RPC Error", e.details())
            self._set_status(f"GetStreamingFilter failed: {e.code()}")

    # ------------------------------------------------------------------
    # Stream Bus
    # ------------------------------------------------------------------

    def _on_toggle_stream(self):
        if not self.streaming:
            if not self._require_session():
                return
            self.streaming = True
            self.btn_stream.configure(text="■  Stop Stream",
                                      style="Red.TButton")
            self._set_status("Streaming started…")
            self._stream_thread = threading.Thread(
                target=self._stream_worker, daemon=True)
            self._stream_thread.start()
        else:
            self.streaming = False
            self.btn_stream.configure(text="▶  Start Stream",
                                      style="Green.TButton")
            self._set_status("Streaming stopped.")

    def _stream_worker(self):
        """Background thread that reads the server-side stream."""
        try:
            request = pb2.StreamBusRequest(session=self.session)
            stream = self.stub.StreamBus(request)

            for reply in stream:
                if not self.streaming:
                    stream.cancel()
                    break

                # Update comm state on UI thread
                if reply.can_comm_state:
                    cs = reply.can_comm_state
                    comm_text = (
                        f"Comm: {COMM_STATE_LABELS.get(cs.comm_state, '?')}  "
                        f"|  Last Err: "
                        f"{LAST_ERR_LABELS.get(cs.last_comm_error, '?')}  "
                        f"|  RX Errs: {cs.receive_error_counter}  "
                        f"|  TX Errs: {cs.transmit_error_counter}  "
                        f"|  Fault: {cs.fault} ({cs.fault_code})"
                    )
                    self.after(0, self.lbl_comm.configure,
                               {"text": comm_text})

                if reply.error and reply.error.code != 0:
                    self.after(
                        0, self._set_status,
                        f"Stream error — code {reply.error.code}: "
                        f"{reply.error.source}")

                for frame in reply.frame:
                    self._frame_counter += 1
                    payload_hex = (frame.payload.hex(" ").upper()
                                   if frame.payload else "")
                    row = (
                        self._frame_counter,
                        f"{frame.timestamp:.6f}",
                        f"0x{frame.identifier:08X}",
                        FRAME_TYPE_LABELS.get(frame.frame_type,
                                              str(frame.frame_type)),
                        "Y" if frame.extended else "N",
                        "Y" if frame.echo else "N",
                        len(frame.payload),
                        payload_hex,
                    )
                    self.after(0, self._insert_row, row)

        except grpc.RpcError as e:
            if self.streaming:
                self.after(0, messagebox.showerror, "Stream Error",
                           str(e.details()))
                self.after(0, self._set_status,
                           f"Stream ended: {e.code()}")
        finally:
            self.streaming = False
            self.after(0, self.btn_stream.configure,
                       {"text": "▶  Start Stream",
                        "style": "Green.TButton"})

    def _insert_row(self, values):
        self.tree.insert("", 0, values=values)
        self.tree.yview_moveto(0.0)  # keep newest row visible at top

        # Trim oldest rows if over the cap
        children = self.tree.get_children()
        if len(children) > MAX_TABLE_ROWS:
            for item in children[MAX_TABLE_ROWS:]:
                self.tree.delete(item)

        self.lbl_frame_count.configure(
            text=f"Frames: {self._frame_counter}")

    def _on_clear_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._frame_counter = 0
        self.lbl_frame_count.configure(text="Frames: 0")
        self._set_status("Table cleared.")

    # ------------------------------------------------------------------
    # Stop & Exit
    # ------------------------------------------------------------------

    def _on_exit(self):
        if self.streaming:
            self.streaming = False
            time.sleep(0.3)

        if self.stub and self.session:
            try:
                request = pb2.StopProcessRequest(session=self.session)
                reply = self.stub.StopProcess(request, timeout=5)
                if reply.error and reply.error.code != 0:
                    print(f"[StopProcess] Error {reply.error.code}: "
                          f"{reply.error.source}")
                else:
                    print(f"[StopProcess] Stopped: {reply.stopped}")
            except grpc.RpcError as e:
                print(f"[StopProcess] RPC error: {e}")

        if self.channel:
            self.channel.close()

        self.destroy()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = BusMonitorClient()
    app.mainloop()