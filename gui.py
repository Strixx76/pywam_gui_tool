"""GUI for the pywam GUI application."""

from __future__ import annotations

import asyncio
import logging
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox as tkmsgbox
from tkinter import ttk
from typing import TYPE_CHECKING

from pywam.attributes import WamAttributes  # type: ignore
from pywam.lib.api_response import ApiResponse  # type: ignore

if TYPE_CHECKING:
    from app import App


_LOGGER = logging.getLogger()
LOGLEVELS = {
    "DEBUG": "grey",
    "INFO": "black",
    "WARNING": "orange",
    "ERROR": "red",
    "CRITICAL": "red",
}


class TkTextLogHandler(logging.Handler):
    """Custom log handler for logging to TkInter Text."""

    def __init__(self, widget: tk.Text) -> None:
        """Initialize the handler."""
        super().__init__()
        self.widget = widget

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a record."""
        msg = self.format(record)
        self.widget.configure(state=tk.NORMAL)
        self.widget.insert(tk.END, msg + "\n", record.levelname)
        self.widget.configure(state=tk.DISABLED)
        self.widget.yview(tk.END)


class Window(tk.Tk):
    """Root window for the app."""

    def __init__(self, app: App, *args, **kwargs) -> None:
        """Initialize the window."""
        super().__init__(*args, **kwargs)
        self.app = app
        self._show = True

        self.title("pywam API GUI tool")
        self.wm_protocol("WM_DELETE_WINDOW", self.close)

        self.header = Header(self, app)
        self.properties = Properties(self, app)
        self.events = Events(self, app)
        self.logging = Logging(self, app)

        self.header.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.properties.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.events.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.logging.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        if self.app.settings.error:
            tkmsgbox.showerror("Error loading settings", self.app.settings.error)
            self.close()

    async def show(self) -> None:
        """Show gui with asyncio loop and Tkinter main loop."""
        # Set minimum window size to current window size
        self.update()
        self.minsize(self.winfo_width(), self.winfo_height())
        # Run the loop
        while self._show:
            self.update()
            await asyncio.sleep(0)

    def close(self) -> None:
        """Close the gui."""
        self._show = False
        self.destroy()


class Header(tk.Frame):
    """Header frame."""

    def __init__(self, parent: Window, app: App, *args, **kwargs) -> None:
        """Initialize the header frame."""
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.app = app

        self.create_widgets()
        self.layout_widgets()
        self.set_up_widgets()

    def create_widgets(self) -> None:
        """Create widgets."""
        self.lbl_name = ttk.Label(self, text="Name:")
        self.cbx_name = ttk.Combobox(
            self,
            width=25,
            state="readonly",
            values=[spk.name for spk in self.app.settings.hosts],
        )
        self.lbl_ip = ttk.Label(self, text="Speaker ip:")
        self.ent_ip = ttk.Entry(self, width=20)
        self.lbl_port = ttk.Label(self, text="Speaker port:")
        self.ent_port = ttk.Entry(self, width=12)
        self.btn_connect = ttk.Button(self, text="Connect", command=self.connect)
        self.btn_disconnect = ttk.Button(
            self, text="Disconnect", command=self.disconnect
        )
        self.lbl_loglevel = ttk.Label(self, text="Log level:")
        self.cbx_loglevel = ttk.Combobox(
            self, width=25, state="readonly", values=list(LOGLEVELS)
        )
        self.btn_send_api = ttk.Button(
            self, text="Send API", command=self.show_send_api
        )

        self.cbx_name.bind("<<ComboboxSelected>>", self.select_speaker)
        self.cbx_loglevel.bind("<<ComboboxSelected>>", self.select_loglevel)

        self.cbx_name.current(self.app.settings.default_host)
        self.select_speaker(None)
        self.cbx_loglevel.current(self.app.settings.loglevel)
        self.select_loglevel(None)

    def layout_widgets(self) -> None:
        """Layout widgets."""
        self.lbl_name.grid(row=0, column=0, sticky=tk.W, padx=5)
        self.cbx_name.grid(row=1, column=0, sticky=tk.W, padx=5)
        self.lbl_ip.grid(row=0, column=1, sticky=tk.W, padx=5)
        self.ent_ip.grid(row=1, column=1, sticky=tk.W, padx=5)
        self.lbl_port.grid(row=0, column=2, sticky=tk.W, padx=5)
        self.ent_port.grid(row=1, column=2, sticky=tk.W, padx=5)
        self.btn_connect.grid(row=1, column=3, sticky=tk.W, padx=5)
        self.btn_disconnect.grid(row=1, column=4, sticky=tk.W, padx=5)
        self.lbl_loglevel.grid(row=0, column=5, sticky=tk.W, padx=5)
        self.cbx_loglevel.grid(row=1, column=5, sticky=tk.W, padx=5)
        self.btn_send_api.grid(row=1, column=6, sticky=tk.W, padx=5)

    def set_up_widgets(self) -> None:
        """Set up widgets."""
        self.btn_disconnect.configure(state=tk.DISABLED)
        self.btn_send_api.configure(state=tk.DISABLED)

    def select_speaker(self, tkinter_event) -> None:
        """Select speaker."""
        self.ent_ip.delete(0, tk.END)
        self.ent_ip.insert(
            tk.END, self.app.settings.hosts[self.cbx_name.current()].host
        )
        self.ent_port.delete(0, tk.END)
        self.ent_port.insert(
            tk.END, str(self.app.settings.hosts[self.cbx_name.current()].port)
        )
        self.app.settings.default_host = self.cbx_name.current()

    def connect(self) -> None:
        """Connect to speaker."""
        self.btn_connect.configure(state=tk.DISABLED)
        self.btn_disconnect.configure(state=tk.NORMAL)
        self.cbx_name.configure(state=tk.DISABLED)
        self.ent_ip.configure(state=tk.DISABLED)
        self.ent_port.configure(state=tk.DISABLED)
        self.btn_send_api.configure(state=tk.NORMAL)
        try:
            self.app.connect(self.ent_ip.get(), int(self.ent_port.get()))
        except Exception as err:
            tkmsgbox.showerror("Error", repr(err))
            self.disconnect()

    def disconnect(self) -> None:
        """Disconnect from speaker."""
        self.app.disconnect()

        self.btn_connect.configure(state=tk.NORMAL)
        self.btn_disconnect.configure(state=tk.DISABLED)
        self.cbx_name.configure(state="readonly")
        self.ent_ip.configure(state=tk.NORMAL)
        self.ent_port.configure(state=tk.NORMAL)
        self.btn_send_api.configure(state=tk.DISABLED)

    def select_loglevel(self, tkinter_event) -> None:
        """Changer level of logger."""
        level = getattr(logging, self.cbx_loglevel.get())
        _LOGGER.setLevel(level)
        self.app.settings.loglevel = self.cbx_loglevel.current()

    def show_send_api(self) -> None:
        """Show Send API window."""
        if not SendApiWindows._show:
            self.send_api_window = SendApiWindows(self.parent, self.app)
        else:
            self.send_api_window.focus()


class Properties(tk.Frame):
    """Properties frame."""

    def __init__(self, parent: Window, app: App, *args, **kwargs) -> None:
        """Initialize the properties frame."""
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.app = app

        self.create_widgets()
        self.layout_widgets()
        self.set_up_widgets()

    def create_widgets(self) -> None:
        """Create widgets."""
        self.vsb_state = ttk.Scrollbar(self, orient=tk.VERTICAL)
        self.trv_state = ttk.Treeview(
            self,
            columns=("#1", "#2", "#3", "#4"),
            show="headings",
            yscrollcommand=self.vsb_state.set,
        )
        self.trv_state.heading("#1", text="Last updated", anchor=tk.W)
        self.trv_state.column("#1", width=100, stretch=tk.NO)
        self.trv_state.heading("#2", text="Attribute", anchor=tk.W)
        self.trv_state.column("#2", width=150, stretch=tk.NO)
        self.trv_state.heading("#3", text="Type", anchor=tk.W)
        self.trv_state.column("#3", width=100, stretch=tk.NO)
        self.trv_state.heading("#4", text="Value", anchor=tk.W)
        self.trv_state.column("#4", width=600)
        self.vsb_state.configure(command=self.trv_state.yview)

    def layout_widgets(self) -> None:
        """Layout widgets."""
        self.rowconfigure(0, weight=1, minsize=100)
        self.columnconfigure(0, weight=1, minsize=200)

        self.trv_state.grid(row=0, column=0, sticky=tk.NSEW)
        self.vsb_state.grid(row=0, column=1, sticky=tk.NS)

    def set_up_widgets(self) -> None:
        """Set up widgets."""
        # Populate treeview
        ws = WamAttributes()
        states = ws.get_state_copy()
        time_now = datetime.now().strftime("%H:%M:%S")
        for key, value in states.items():
            if value is None:
                var_type = ""
            else:
                var_type = str(type(value))[8:][:-2]
            if isinstance(value, list | tuple):
                value = ", ".join([str(v) for v in value])
            else:
                value = str(value)
            self.trv_state.insert(
                parent="",
                index=tk.END,
                iid=key,
                values=(time_now, key, var_type, value),
            )

    def new_state(self, state: dict):
        """Change the state of the speaker."""
        time_now = datetime.now().strftime("%H:%M:%S")
        for key, value in state.items():
            if value is None:
                var_type = ""
            else:
                var_type = str(type(value))[8:][:-2]
            if isinstance(value, list | tuple):
                value = ", ".join([str(v) for v in value])
            else:
                value = str(value)
            self.trv_state.item(key, values=(time_now, key, var_type, value))


class Events(tk.Frame):
    """Events frame."""

    def __init__(self, parent: Window, app: App, *args, **kwargs) -> None:
        """Initialize the events frame."""
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.app = app

        self.create_widgets()
        self.layout_widgets()

    def create_widgets(self) -> None:
        """Create widgets."""
        # List with all events
        self.vsb_events = ttk.Scrollbar(self, orient=tk.VERTICAL)
        self.lst_events = tk.Listbox(
            self,
            selectmode=tk.SINGLE,
            width=40,
            yscrollcommand=self.vsb_events.set,
        )
        self.vsb_events.config(command=self.lst_events.yview)
        # Treeview for selected event
        self.vsb_event = ttk.Scrollbar(self, orient=tk.VERTICAL)
        self.trv_event = ttk.Treeview(
            self,
            columns=("#1", "#2"),
            show="headings",
            selectmode="browse",
            yscrollcommand=self.vsb_event.set,
        )
        self.trv_event.heading("#1", text="Attribute", anchor=tk.W)
        self.trv_event.column("#1", width=100, stretch=tk.NO)
        self.trv_event.heading("#2", text="Value", anchor=tk.W)
        self.trv_event.column("#2", width=500)
        self.vsb_event.configure(command=self.trv_event.yview)
        # Context menu for event treeview
        self.mnu_trv_event = tk.Menu(self.trv_event, tearoff=0)
        self.mnu_trv_event.add_command(label="View", command=self.view_event_detail)
        self.mnu_trv_event.add_command(label="Copy", command=self.copy_event_detail)
        # Context menu for event list
        self.mnu_lst_event = tk.Menu(self.lst_events, tearoff=0)
        self.mnu_lst_event.add_command(label="Copy", command=self.copy_full_event)

        self.lst_events.bind("<<ListboxSelect>>", self.select_lst_event)
        self.lst_events.bind("<Button-3>", self.right_click_lst_events)
        self.trv_event.bind("<Button-3>", self.right_click_trv_events)

    def layout_widgets(self) -> None:
        """Layout widgets."""
        self.rowconfigure(0, weight=1, minsize=100)
        self.columnconfigure(3, weight=1, minsize=200)

        self.lst_events.grid(row=0, column=0, sticky=tk.NSEW)
        self.vsb_events.grid(row=0, column=1, sticky=tk.NS)
        tk.Label(self, padx=10).grid(row=0, column=2, sticky=tk.NS)
        self.trv_event.grid(row=0, column=3, sticky=tk.NSEW)
        self.vsb_event.grid(row=0, column=4, sticky=tk.NS)

    def new_event(self, event: ApiResponse, trunc: bool = False) -> None:
        """Add a new event in event list."""
        # Add event to list
        time_now = datetime.now().strftime("%H:%M:%S")
        self.lst_events.insert(tk.END, f"{time_now} - {event.method}")
        if trunc:
            self.lst_events.delete(0)
        # Scroll down if not in focus
        focus = self.parent.focus_get()
        if focus in (self.lst_events, self.trv_event):
            self.lst_events.yview(tk.END)
        # Flash list
        background = self.lst_events.cget("background")
        self.lst_events.config(background="red")
        self.parent.update()
        time.sleep(0.1)
        self.lst_events.config(background=background)
        self.parent.update()

    def select_lst_event(self, tkinter_event) -> None:
        """Show selected event in treeview."""
        if not self.lst_events.curselection():
            return
        for row in self.trv_event.get_children():
            self.trv_event.delete(row)
        event = self.app.events[self.lst_events.curselection()[0]]
        for key in event.__slots__:
            value = str(getattr(event, key, ""))
            value = "".join([v.strip() for v in value.splitlines()])
            self.trv_event.insert(parent="", index=tk.END, iid=key, values=(key, value))

    def right_click_trv_events(self, tk_event) -> None:
        """Show context menu for event details."""
        if idx := self.trv_event.identify_row(tk_event.y):
            self.trv_event.selection_set(idx)
            self.mnu_trv_event.post(tk_event.x_root, tk_event.y_root)

    def right_click_lst_events(self, tk_event) -> None:
        """Show context menu for event list."""
        self.lst_events.selection_clear(0, tk.END)
        self.lst_events.selection_set(self.lst_events.nearest(tk_event.y))
        self.lst_events.activate(self.lst_events.nearest(tk_event.y))
        try:
            self.mnu_lst_event.tk_popup(tk_event.x_root, tk_event.y_root)
        finally:
            self.mnu_lst_event.grab_release()

    def get_event_attribute(self) -> tuple[str, str]:
        """Get selected event attribute."""
        if (item := self.trv_event.selection()) is not None and (
            self.lst_events.curselection()
        ):
            idx = self.lst_events.curselection()[0]
            key = self.trv_event.item(item[0], "values")[0]
            method = self.app.events[idx].method
            attribute = self.app.get_pretty_event_attribute(idx, key)
            return (f"{method} - {key}", attribute)
        else:
            return ("", "")

    def copy_event_detail(self) -> None:
        """Copy event details to clipboard."""
        title, data = self.get_event_attribute()
        self.parent.clipboard_clear()
        self.parent.clipboard_append(f"{title}\n\n{data}")

    def view_event_detail(self) -> None:
        """View event detail."""
        title, data = self.get_event_attribute()
        tkmsgbox.showinfo(title=title, message=data)

    def copy_full_event(self) -> None:
        """Copy an event to clipboard."""
        if not self.lst_events.curselection():
            return
        idx = self.lst_events.curselection()[0]
        event = self.app.get_pretty_event(idx)
        self.parent.clipboard_clear()
        self.parent.clipboard_append(event)


class Logging(tk.Frame):
    """Logging frame."""

    def __init__(self, parent: Window, app: App, *args, **kwargs) -> None:
        """Initialize the logging frame."""
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.app = app

        self.create_widgets()
        self.layout_widgets()

        self.init_logger()

    def create_widgets(self) -> None:
        """Create widgets."""
        self.vsb_log = ttk.Scrollbar(self, orient=tk.VERTICAL)
        self.txt_log = tk.Text(
            self,
            width=100,
            height=10,
            yscrollcommand=self.vsb_log.set,
        )
        for tag, color in LOGLEVELS.items():
            self.txt_log.tag_config(tagName=tag, foreground=color)
        self.txt_log.configure(state=tk.DISABLED)
        self.vsb_log.configure(command=self.txt_log.yview)

    def layout_widgets(self) -> None:
        """Layout widgets."""
        self.rowconfigure(0, weight=1, minsize=100)
        self.columnconfigure(0, weight=1, minsize=200)

        self.txt_log.grid(row=0, column=0, sticky=tk.NSEW)
        self.vsb_log.grid(row=0, column=1, sticky=tk.NS)

    def init_logger(self) -> None:
        """Initialize the logger."""
        log_handler = TkTextLogHandler(self.txt_log)
        log_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s: %(name)s - %(message)s"
        )
        log_handler.setFormatter(log_formatter)
        _LOGGER.addHandler(log_handler)
        level = getattr(logging, self.parent.header.cbx_loglevel.get())
        _LOGGER.setLevel(level)


class SendApiWindows(tk.Toplevel):
    """Send API window."""

    _show = False

    def __init__(self, parent: Window, app: App, *args, **kwargs) -> None:
        """Initialize the send API window."""
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.app = app

        self.arguments: list[tuple[str, str | int | list[int], str]] = []

        self.title("Send API")
        self.resizable(False, False)

        self.create_widgets()
        self.layout_widgets()

        self.__class__._show = True
        self.focus()

    def create_widgets(self) -> None:
        """Create widgets."""
        self.lbl_type = ttk.Label(self, text="Type:")
        types = ("UIC", "CPM")
        self.cbx_type = ttk.Combobox(self, width=25, state="readonly", values=types)
        self.lbl_method = ttk.Label(self, text="Method:")
        self.ent_method = ttk.Entry(self, width=50)
        self.lbl_pwron = ttk.Label(self, text="pwron:")
        self.cbx_pwron_state = tk.IntVar(self, value=0)
        self.cbx_pwron = ttk.Checkbutton(
            self, variable=self.cbx_pwron_state, onvalue=1, offvalue=0
        )
        self.lbl_expected_resp = ttk.Label(self, text="Expected response:")
        self.ent_expected_resp = ttk.Entry(self, width=50)
        self.lbl_user_check = ttk.Label(self, text="User check:")
        self.cbx_user_check_state = tk.IntVar(self, value=0)
        self.cbx_user_check = ttk.Checkbutton(
            self, variable=self.cbx_user_check_state, onvalue=1, offvalue=0
        )
        self.lbl_timeout = ttk.Label(self, text="Timeout multiples:")
        self.scl_timeout = ttk.Spinbox(self, width=25, from_=1, to=5)
        self.lbl_args = ttk.Label(self, text="Arguments:")
        self.btn_add = ttk.Button(self, text="Add arg.", command=self.add_argument)
        # Needs own frame due to columnspan
        self.frm_trv_args = ttk.Frame(self)
        self.trv_args = ttk.Treeview(
            self.frm_trv_args,
            columns=("#1", "#2", "#3"),
            show="headings",
        )
        self.trv_args.heading("#1", text="Name", anchor=tk.W)
        self.trv_args.column("#1", width=300, stretch=tk.NO)
        self.trv_args.heading("#2", text="Value", anchor=tk.W)
        self.trv_args.column("#2", width=300, stretch=tk.NO)
        self.trv_args.heading("#3", text="Type", anchor=tk.W)
        self.trv_args.column("#3", width=50, stretch=tk.NO)
        # Needs own frame due to columnspan
        self.frm_buttons = ttk.Frame(self)
        self.btn_cancel = ttk.Button(
            self.frm_buttons, text="Cancel", command=self.destroy
        )
        self.btn_send = ttk.Button(self.frm_buttons, text="Send", command=self.send_api)

    def layout_widgets(self) -> None:
        """Layout widgets."""
        self.lbl_type.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.cbx_type.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.lbl_method.grid(row=1, column=0, sticky=tk.W, padx=5)
        self.ent_method.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        self.lbl_pwron.grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.cbx_pwron.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        self.lbl_expected_resp.grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.ent_expected_resp.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        self.lbl_user_check.grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.cbx_user_check.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        self.lbl_timeout.grid(row=5, column=0, sticky=tk.W, padx=5)
        self.scl_timeout.grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)
        self.lbl_args.grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
        self.btn_add.grid(row=6, column=1, sticky=tk.W, padx=5, pady=5)
        self.frm_trv_args.grid(
            row=7, column=0, columnspan=2, sticky=tk.NSEW, padx=5, pady=5
        )
        self.trv_args.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)
        self.frm_buttons.grid(
            row=8, column=0, columnspan=2, sticky=tk.E, padx=5, pady=5
        )
        self.btn_cancel.pack(side=tk.RIGHT, padx=5, pady=5)
        self.btn_send.pack(side=tk.RIGHT, padx=5, pady=5)

    def add_argument(self) -> None:
        """Show add argument dialog."""
        add_argument_dialog = ArgumentsDialog(self, self.app)
        if args := add_argument_dialog.result:
            self.arguments.append(args)
            self.trv_args.insert(
                parent="",
                index=tk.END,
                iid=len(self.arguments),
                values=(args[0], args[1], args[2]),
            )

    def send_api(self) -> None:
        """Send the API request."""
        api_type = self.cbx_type.get()
        method = self.ent_method.get().strip()
        pwron = bool(self.cbx_pwron_state.get())
        args = self.arguments
        expected_response = self.ent_expected_resp.get().strip()
        user_check = bool(self.cbx_user_check_state.get())
        timeout_multiple = int(self.scl_timeout.get())

        self.app.send_api(
            api_type,
            method,
            pwron,
            args,
            expected_response,
            user_check,
            timeout_multiple,
        )

    def destroy(self) -> None:
        """Destroy the send API windows."""
        self.__class__._show = False
        return super().destroy()


class ArgumentsDialog(tk.Toplevel):
    """Arguments dialog window."""

    def __init__(self, parent: SendApiWindows, app: App, *args, **kwargs) -> None:
        """Initialize the argument dialog window."""
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.app = app

        self.result: tuple[str, str | int | list[int], str] = ("", "", "")

        self.title("Add argument")
        self.resizable(False, False)
        self.wm_protocol("WM_DELETE_WINDOW", self.close)

        self.create_widgets()
        self.layout_widgets()

        self.focus()
        self.wait_visibility()
        self.grab_set()
        self.wait_window()

    def create_widgets(self) -> None:
        """Create widgets."""
        self.lbl_name = ttk.Label(self, text="Name:")
        self.ent_name = tk.Entry(self, width=50)
        self.lbl_value = ttk.Label(self, text="Value:")
        self.ent_value = tk.Entry(self, width=50)
        self.lbl_type = ttk.Label(self, text="Type:")
        types = ("str", "dec", "cdata", "dec_arr")
        self.cbx_type = ttk.Combobox(self, width=15, state="readonly", values=types)
        # Bottom buttons needs a own frame for layout
        self.frm_buttons = ttk.Frame(self)
        self.btn_cancel = ttk.Button(
            self.frm_buttons, text="Cancel", command=self.close
        )
        self.btn_send = ttk.Button(
            self.frm_buttons, text="Add", command=self.add_argument
        )

    def layout_widgets(self) -> None:
        """Layout widgets."""
        self.lbl_name.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.ent_name.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.lbl_value.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.ent_value.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        self.lbl_type.grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.cbx_type.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        self.frm_buttons.grid(
            row=3, column=0, columnspan=2, sticky=tk.E, padx=5, pady=5
        )
        self.btn_cancel.pack(side="right", padx=5, pady=5)
        self.btn_send.pack(side="right", padx=5, pady=5)

    def close(self) -> None:
        """Close the dialog."""
        self.grab_release()
        self.destroy()

    def add_argument(self) -> None:
        """Store the argument in result."""
        name = self.ent_name.get().strip()
        value: str | int | list[int] = ""
        value_type = self.cbx_type.get()
        try:
            if value_type == "dec_arr":
                value = [int(dec) for dec in self.ent_value.get().split(",")]
            elif value_type == "dec":
                value = int(self.ent_value.get().strip())
            else:
                value = self.ent_value.get().strip()
        except Exception:
            value = ""

        args = (name, value, value_type)
        try:
            self.app.validate_api_call_arguments(args)
        except Exception as err:
            tkmsgbox.showerror(title="Error", message=str(err))
            return
        self.result = args
        self.close()
