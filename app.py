"""Application for exploring WAM API."""

from __future__ import annotations

import asyncio
import contextlib
import xml.etree.ElementTree as ET
from pprint import pformat

from pywam.lib.api_call import ApiCall  # type: ignore
from pywam.lib.api_response import ApiResponse  # type: ignore
from pywam.speaker import Speaker  # type: ignore

from gui import Window
from settings import Settings


class App:
    """Application for exploring WAM API."""

    gui: Window
    aio_loop: asyncio.AbstractEventLoop
    speaker: Speaker
    events: list[ApiResponse]

    def __init__(self) -> None:
        """Initialize the app."""
        self.settings: Settings = Settings()
        self.settings.load_settings()

    async def run(self):
        """Run the application."""
        self.aio_loop = asyncio.get_event_loop()
        self.gui = Window(self)
        await self.gui.show()
        if self.speaker:
            await self.async_disconnect()

    def connect(self, ip: str, port: int) -> None:
        """Connect to speaker."""
        self.aio_loop.create_task(self.async_connect(ip, port))

    async def async_connect(self, ip: str, port: int) -> None:
        """Connect to speaker."""
        try:
            self.speaker = Speaker(ip, port)
            self.speaker.events.register_subscriber(self.state_receiver, 1)
            self.speaker.client.register_subscriber(self.event_receiver)
            await self.speaker.connect()
            await self.speaker.update()
        except Exception:
            if self.speaker:
                with contextlib.suppress(Exception):
                    await self.speaker.client.disconnect()
                self.speaker = None
            raise

    def disconnect(self) -> None:
        """Disconnect to speaker."""
        self.aio_loop.create_task(self.async_disconnect())

    async def async_disconnect(self) -> None:
        """Disconnect from speaker."""
        with contextlib.suppress(Exception):
            await self.speaker.client.disconnect()
        self.speaker = None

    def event_receiver(self, event: ApiResponse) -> None:
        """Receiver for all speaker events."""
        self.events.append(event)
        trunc = False
        if len(self.events) > 1000:
            del self.events[0]
            trunc = True
        self.gui.events.new_event(event, trunc)

    def state_receiver(self, state: dict) -> None:
        """Receiver for state changes on the speaker."""
        self.gui.properties.new_state(state)

    def validate_api_call(self, api_call: ApiCall) -> None:
        """Validate API call."""
        if api_call.api_type not in ("UIC", "CPM"):
            raise ValueError("API type not supported.")
        if not api_call.method:
            raise ValueError("No method specified.")
        if not isinstance(api_call.args, list):
            raise TypeError("args is not a list.")
        if not isinstance(api_call.pwron, bool):
            raise TypeError("pwron is not a boolean.")
        if not isinstance(api_call.user_check, bool):
            raise TypeError("user_check is not a boolean.")
        if not isinstance(api_call.timeout_multiple, int):
            raise TypeError("timeout_multiple is not an integer.")
        if api_call.timeout_multiple > 5:
            raise ValueError("timeout_multiple is too high.")

    def validate_api_call_arguments(  # noqa: C901
        self, args: tuple[str, str | int | list[int], str]
    ) -> None:
        """Validate API call arguments."""
        if not isinstance(args, tuple):
            raise TypeError("args is not a list of tuples.")
        if len(args) != 3:
            raise ValueError("args is not a list of tuples of length 3.")
        # Argument name
        if not isinstance(args[0], str):
            raise TypeError("Argument name is not a string.")
        if not args[0]:
            raise ValueError("Argument name cannot be empty.")
        # Argument type
        if not isinstance(args[2], str):
            raise TypeError("Argument type is not a string.")
        if args[2] not in ("str", "dec", "cdata", "dec_arr"):
            raise ValueError("Argument type not supported.")
        # Argument values
        if not isinstance(args[1], (str, int, list)):
            raise TypeError("Argument value is not a string, int, or list.")
        if args[2] == "dec_arr":
            if not isinstance(args[1], list):
                raise TypeError("Argument value is not a list.")
            for value in args[1]:
                if not isinstance(value, int):
                    raise TypeError("Argument value is not a list of integers.")
        if args[2] == "dec":
            if not isinstance(args[1], int):
                raise TypeError("Argument value is not an integer.")
        if args[2] == "str":
            if not isinstance(args[1], str):
                raise TypeError("Argument value is not a string.")
        if args[2] == "cdata":
            if not isinstance(args[1], str):
                raise TypeError("Argument value is not a string.")

    def send_api(
        self,
        api_type: str,
        method: str,
        pwron: bool = False,
        args: list[tuple[str, str | int | list[int], str]] = [],
        expected_response: str = "",
        user_check: bool = False,
        timeout: int = 1,
    ) -> None:
        """Send an API request."""
        api_call = ApiCall(
            api_type=api_type,
            method=method,
            pwron=pwron,
            args=args,
            expected_response=expected_response,
            user_check=user_check,
            timeout_multiple=timeout,
        )
        self.aio_loop.create_task(self.async_send_api(api_call))

    async def async_send_api(self, api_call):
        """Send an API request."""
        await self.speaker.client.request(api_call)

    def get_pretty_event(self, event_idx: int) -> str:
        """Get a prettified event."""
        event = self.events[event_idx]
        event_as_dict = {
            "raw_response": event.raw_response,
            "api_type": event.api_type,
            "method": event.method,
            "user": event.user,
            "version": event.version,
            "speaker_ip": event.speaker_ip,
            "success": str(event.success),
            "data": str(event.data),
            "err_msg": event.err_msg,
            "err_repr": event.err_repr,
        }
        return pformat(event_as_dict)

    def get_pretty_event_attribute(self, event_idx: int, attribute: str) -> str:
        """Get a prettified event attribute."""
        event = self.events[event_idx]

        raw_response = ET.XML(event.raw_response)
        ET.indent(raw_response)
        formatted_raw_response = ET.tostring(raw_response, encoding="unicode")

        formatted_data = pformat(event.data)

        event_as_dict = {
            "raw_response": formatted_raw_response,
            "api_type": event.api_type,
            "method": event.method,
            "user": event.user,
            "version": event.version,
            "speaker_ip": event.speaker_ip,
            "success": str(event.success),
            "data": formatted_data,
            "err_msg": event.err_msg,
            "err_repr": event.err_repr,
        }

        return event_as_dict.get(attribute, "")


if __name__ == "__main__":
    app = App()
    asyncio.run(app.run())
