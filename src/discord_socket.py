"""
discord_socket is a module for handling the Discord gateway API easily.

    Created by: Rhyfros
"""

import dataclasses
import datetime
import enum
import functools
import json
import logging
import random
import threading
import time
import typing

import websocket


class ActivityType(enum.Enum):
    """
    Enum used for activity types
    """

    PLAYING = 0
    IDK = 1
    TEST = 2
    WATCHING = 3
    TEST2 = 4


@dataclasses.dataclass()
class DiscordSocketInfo:
    """
    Dataclass used for storing information for the DiscordSocket class
    """

    data: dict
    last_ack: float | None
    last_hb: float
    start_time: float
    sequence: int


@dataclasses.dataclass()
class DiscordSocketSetup:
    """
    Dataclass used to store initializing information.
    """

    token: str
    activity: str
    parser: typing.Callable


class DiscordSocket:
    """
    The core socket for discord_socket
    """

    def __init__(
        self, ds_setup: DiscordSocketSetup, logger: logging.Logger = None
    ) -> None:
        self._logger = logger

        self.ds_setup = ds_setup

        self.ds_info = DiscordSocketInfo(
            data={},
            last_ack=datetime.datetime.now().timestamp(),
            last_hb=datetime.datetime.now().timestamp(),
            start_time=datetime.datetime.now().timestamp(),
            sequence=0,
        )

        self.web_socket = self.get_web_socket_app(gateway=self.gateway)

        self.log(level=logging.DEBUG, msg="DiscordSocket initialized.")

    @functools.cached_property
    def gateway(self) -> str:
        """
        Cached property that returns the gateway websocket URL.

        Returns:
            str: The gateway websocket URL.
        """
        return "wss://gateway.discord.gg/?v=10&encoding=json"

    def log(self, level, msg) -> None:
        """
        Logs the given message (msg) at the given level.

        Args:
            level (int | logging.(LEVEL)): The level to log at.
            msg (str): The message to log.
        """
        if self._logger is not None:
            self._logger.log(level=level, msg="[DiscordSocket_v1]" + msg)

    def connect(self, web_socket: websocket.WebSocketApp) -> None:
        """
        Connects to the Discord gateway API with the given websocket.WebSocketApp (web_socket)

        Args:
            web_socket (websocket.WebSocketApp): The WebSocketApp to connect to.
        """
        self.log(level=logging.DEBUG, msg="Connecting.")
        # print("Connecting...")

        r_url = self.ds_info.data.get("resume_gateway_url", None)
        if r_url is None:
            r_url = self.gateway

        if self.ds_info.data.get("session_id", None) is not None:
            if self.ds_info.data.get("connected", None) is False:
                web_socket.url = r_url

            web_socket.send(
                data=json.dumps(
                    obj={
                        "op": 6,
                        "d": {
                            "token": self.ds_setup.token,
                            "session_id": self.ds_info.data["session_id"],
                            "seq": self.ds_info.data.get("sequence", None),
                        },
                    }
                )
            )

        else:
            if self.ds_info.data.get("connected", None) is False:
                web_socket.url = r_url

            # print(self.ds_setup.activity)

            web_socket.send(
                data=json.dumps(
                    obj={
                        "op": 2,
                        "d": {
                            "token": self.ds_setup.token,
                            "properties": {
                                "os": "linux",
                                "browser": "disco",
                                "device": "disco",
                            },
                            "compress": True,
                            "presence": {
                                "activities": self.ds_setup.activity,
                                "status": "online",
                                "since": self.ds_info.start_time,
                                "afk": False,
                            },
                        },
                    }
                )
            )

    def on_open(self) -> None:
        """
        Ran when the websocket.WebSocketApp opens.
        """

        self.log(level=logging.DEBUG, msg="Websocket opened.")

    def on_error(self, msg: str | None) -> None:
        """
        Ran when the websocket.WebSocketApp receives an error.

        Args:
            msg (str | None): The error message received, if any.
        """

        self.log(level=logging.DEBUG, msg=f"Websocket received an error: {msg}")

    def on_close(
        self,
        web_socket: websocket.WebSocketApp,
        close_code: None | str | float | int,
        close_msg: None | str,
    ) -> None:
        """
        Ran when the websocket.WebSocketApp closes.

        Args:
            web_socket (websocket.WebSocketApp): The WebSocketApp that was closed
            close_code (str | float | int | None): The close code received, if any.
            close_msg (str | None): The close message received, if any.
        """

        self.log(
            level=logging.WARNING,
            msg="Websocket connection closed. "
            + f"close_code: {close_code}, "
            + f"close_msg: {close_msg}",
        )

        time.sleep(2.5)

        self.connect(web_socket)

    def on_message(self, web_socket: websocket.WebSocketApp, msg) -> None:
        """
        Ran when the websocket.WebSocketApp receives a message.

        Args:
            web_socket (websocket.WebSocketApp): The WebSocketApp that received a message.
            msg (str): The JSON encoded message.
        """

        try:
            response = json.loads(msg)
        except json.JSONDecodeError:
            response = {"op": -1}
        opcode = response["op"]

        match opcode:
            case 11:  # Heartbeat ACK
                self.ds_info.last_ack = datetime.datetime.now().timestamp()
                self.ds_info.data["sequence"] = self.ds_info.data.get("sequence", 0) + 1

                if not self.ds_info.data.get("connected", False):
                    self.ds_info.data["connected"] = True
                    self.connect(web_socket)

            case 10:  # Hello
                self.ds_info.data["heartbeat_interval"] = (
                    response["d"]["heartbeat_interval"] / 1000
                )

            case 9:  # Invalid session
                try:
                    web_socket.close()
                except websocket.WebSocketConnectionClosedException as exception:
                    print("Socket close error:", exception, "\n")

                self.ds_info.data["connected"] = False

                self.connect(web_socket=web_socket)

            case 7:  # Reconnect
                try:
                    web_socket.close()
                except websocket.WebSocketConnectionClosedException as exception:
                    print("Socket close error:", exception, "\n")

                self.ds_info.data["connected"] = False

                self.connect(web_socket=web_socket)

            case 1:  # Heartbeat
                web_socket.send(
                    data=json.dumps(
                        obj={"op": 1, "d": self.ds_info.data.get("sequence", None)}
                    )
                )
                self.ds_info.last_hb = datetime.datetime.now().timestamp()

            case 0:  # Ready / Event
                if response.get("t", None) is None:  # Ready
                    if "resume_gateway_url" in response:
                        self.ds_info.data["resume_gateway_url"] = response["d"][
                            "resume_gateway_url"
                        ]

                    if "session_id" in response:
                        self.ds_info.data["session_id"] = response["d"]["session_id"]

                else:  # Event
                    event_type = response["t"]
                    data: dict = response["d"]

                    self.ds_setup.parser(event_type, data)

    def get_web_socket_app(self, gateway) -> websocket.WebSocketApp:
        """
        Creates a new websocket.WebSocketApp with the given gateway.

        Args:
            gateway (str): The gateway websocket URL.

        Returns:
            websocket.WebSocketApp: The websocket app created.
        """

        headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            + "AppleWebKit/537.36 (KHTML, like Gecko) "
            + "Chrome/116.0.0.0 Safari/537.36",
        }

        web_socket = websocket.WebSocketApp(
            url=gateway,
            header=headers,  # type: ignore
            on_open=lambda _: self.on_open(),
            on_message=lambda web_socket, msg: self.on_message(
                web_socket=web_socket, msg=msg
            ),
            on_error=lambda _, msg: self.on_error(msg),
            on_close=lambda web_socket, close_code, close_msg: self.on_close(
                web_socket=web_socket, close_code=close_code, close_msg=close_msg
            ),
        )

        self.log(level=logging.DEBUG, msg="Websocket app created.")

        return web_socket

    def update_presence(self, activity: list[dict], since: int | float) -> None:
        """
        Updates the users presence with the activity provided.

        Args:
            activity (list[dict]): List of dictionaries containing discord activity information.
            since (float | int): The activity "since" parameter.
        """

        self.ds_setup.activity = activity

        self.web_socket.send(
            data=json.dumps(
                obj={
                    "op": 3,
                    "d": {
                        "since": since,
                        "activities": activity,
                        "status": "online",
                        "afk": False,
                    },
                }
            )
        )

        self.log(level=logging.DEBUG, msg="Presence updated.")

    def keep_alive(self) -> None:
        """
        Keeps the socket connection alive.
        """

        while True:
            wait_time = self.ds_info.data.get("heartbeat_interval", None)
            if wait_time is not None:
                wait_time *= random.uniform(0.1, 1)
            else:
                wait_time = 0.05
            time.sleep(wait_time)

            if self.ds_info.data.get("heartbeat_interval", None) is not None:
                if self.ds_info.data.get("connected", True) is True:
                    self.web_socket.send(
                        data=json.dumps(
                            obj={"op": 1, "d": self.ds_info.data.get("sequence", None)}
                        )
                    )

                    self.ds_info.last_hb = datetime.datetime.now().timestamp()

    def run(self) -> None:
        """
        Main function to run the DiscordSocket
        """

        func_list = [
            self.keep_alive,
            lambda: self.web_socket.run_forever(ping_interval=10, ping_timeout=5),
        ]

        for x in func_list:
            t = threading.Thread(target=x)
            t.start()
