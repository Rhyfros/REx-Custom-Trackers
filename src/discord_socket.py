"""
Used to handle Discord gateway API easily.

Created by: Rhyfros
"""


import asyncio
import dataclasses
import functools
import json
import logging
import random
import threading
import time
import typing

import websocket


@dataclasses.dataclass()
class DiscordSocketInfo:
    """
    Dataclass used for storing information for the DiscordSocket class
    """

    heartbeat_interval: float | int
    sequence: int
    session_id: typing.Any
    resume_gateway_url: str | None
    last_hb: int | float | None


@dataclasses.dataclass()
class DiscordSocketSetup:
    """
    Dataclass used to store initializing information.
    """

    token: str
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
            last_hb=time.time(),
            sequence=0,
            session_id=None,
            resume_gateway_url=None,
            heartbeat_interval=None,
        )

        self.web_socket: websocket.WebSocket = websocket.WebSocket()

        # print("DiscordSocket initialized.")

        self.log(level=logging.DEBUG, msg="DiscordSocket initialized.")

    @functools.cached_property
    def gateway(self) -> str:
        """
        Cached property that returns the gateway websocket URL.

        Returns:
            str: The gateway websocket URL.
        """
        return "wss://gateway.discord.gg/?v=10&encoding=json"

    async def connect(self):
        # print("Testing if connected")
        if self.web_socket.connected is False:
            # print("Connecting")

            try:
                if self.ds_info.resume_gateway_url is not None:
                    self.web_socket.connect(url=self.ds_info.resume_gateway_url)

                else:
                    self.web_socket.connect(url=self.gateway)

            except Exception as e:
                self.log(logging.WARNING, f"Error reconnecting: {e}")
                print(f"Error reconnecting: {e}")

            # print("Connected")

    def log(self, level, msg) -> None:
        """
        Logs the given message (msg) at the given level.

        Args:
            level (int | logging.(LEVEL)): The level to log at.
            msg (str): The message to log.
        """
        if self._logger is not None:
            self._logger.log(level=level, msg="[DiscordSocket_v1] " + msg)

    async def on_message(self, msg) -> None:
        """
        Ran when the websocket receives a message.

        Args:
            web_socket (websocket.WebSocket): The websocket that received a message.
            msg (str): The JSON encoded message.
        """

        try:
            response = json.loads(msg)
        except Exception:
            response = {"op": -1}
        opcode = response["op"]

        match opcode:
            case 11:  # Heartbeat ACK
                # print("Heartbeat ACK")
                self.ds_info.sequence = self.ds_info.sequence + 1

            case 10:  # Hello
                self.log(
                    logging.INFO,
                    "Hello event received.",
                )

                self.ds_info.heartbeat_interval = (
                    response["d"]["heartbeat_interval"] / 1000
                )

                self.web_socket.send(
                    payload=json.dumps(
                        obj={
                            "op": 2,
                            "d": {
                                "token": self.ds_setup.token,
                                "properties": {
                                    "os": "linux",
                                    "browser": "serve",
                                    "device": "serve",
                                },
                            },
                        }
                    )
                )

                self.ds_info.last_hb = time.time()

            case 9:  # Invalid session
                self.log(
                    logging.WARNING,
                    "Invalid session event received.",
                )

            case 7:  # Reconnect
                self.log(
                    logging.INFO,
                    "Reconnect event received.",
                )

                await self.connect()

            case 1:  # Heartbeat
                # print("Heartbeat")

                self.web_socket.send(
                    payload=json.dumps(obj={"op": 1, "d": self.ds_info.sequence})
                )

                self.ds_info.last_hb = time.time()

            case 0:  # Ready / Event
                if response.get("t", None) is None:  # Ready
                    self.log(
                        logging.INFO,
                        "Ready event received.",
                    )

                    if "resume_gateway_url" in response:
                        self.ds_info.resume_gateway_url = response["d"][
                            "resume_gateway_url"
                        ]

                    if "session_id" in response:
                        self.ds_info.session_id = response["d"]["session_id"]

                else:  # Event
                    # print("Event")
                    event_type: str = response["t"]
                    data: typing.Any = response["d"]

                    asyncio.create_task(self.ds_setup.parser(event_type, data))

    def keep_alive(self):
        self.log(
            logging.DEBUG,
            "Started keep_alive",
        )
        # print("Keeping alive")

        while True:
            wait_time = self.ds_info.heartbeat_interval
            if wait_time is not None:
                wait_time *= random.uniform(0.1, 0.9)

            time.sleep(0.05)

            if wait_time is not None:
                if self.web_socket.connected is True:
                    if (time.time() - self.ds_info.last_hb) >= wait_time:
                        # print("Past wait")

                        try:
                            self.web_socket.send(
                                payload=json.dumps(
                                    obj={"op": 1, "d": self.ds_info.sequence}
                                )
                            )

                            self.log(
                                logging.DEBUG,
                                "Heartbeat sent",
                            )

                        except Exception as e:
                            print("Error while sending heartbeat:", e)
                            self.log(
                                logging.ERROR,
                                f"Error while sending hearbeat: {e}",
                            )

                        self.ds_info.last_hb = time.time()

    async def receiver(self):
        # print("Receiving")
        while True:
            await asyncio.sleep(0.025)

            try:
                if self.web_socket.connected is True:
                    new_data = self.web_socket.recv()

                    if new_data is not None:
                        asyncio.create_task(self.on_message(new_data))  # New event

                else:
                    print("Websocket not connected, heatbeat not sendable.")
                    self.log(
                        logging.WARNING,
                        "Websocket not connected, heatbeat not sendable.",
                    )

                    await asyncio.sleep(10)

                    if self.web_socket.connected is False:
                        await self.connect()  # Reconnects to the Discord gateway

            except Exception as e:
                print("Receiver error:", e)
                self.log(logging.ERROR, f"Receiver error: {e}")

    async def _start(self):
        await self.connect()

        threading.Thread(target=self.keep_alive).start()

        await asyncio.get_event_loop().run_until_complete(
            asyncio.create_task(self.receiver())
        )

    def start(self):
        asyncio.gather(self._start())
