import dataclasses
import json
import typing


@dataclasses.dataclass(frozen=True)
class Author:
    """
    Author dataclass storing message author information.
    """

    username: str
    discriminator: str
    id: str

    def to_dict(self) -> dict[str, typing.Any]:
        """
        Returns dictionary of the data.

        Returns:
            dict: Dictionary containing author information.
        """

        return {
            "username": self.username,
            "discriminator": self.discriminator,
            "id": self.id,
        }

    def to_json(self) -> str:
        """
        Returns a dumped string of the data.

        Returns:
            str: The dumped JSON string.
        """

        return json.dumps(self.to_dict())

    def __str__(self) -> str:
        return f"@{self.username} ({self.id})"


@dataclasses.dataclass(frozen=True)
class MessageData:
    """
    MessageData dataclass storing message information.
    """

    sent_timestamp: str

    pinned: bool

    message_id: str
    channel_id: str
    guild_id: str

    content: str
    embeds: list[dict]
    attachments: list[str]

    def __str__(self) -> str:
        return f'"{self.content}" ({self.message_id})'

    def to_dict(self) -> dict[str, typing.Any]:
        """
        Returns a dictionary containing information about the message.

        Returns:
            dict: Dictionary containing message info.
        """

        return {
            "timestamp": self.sent_timestamp,
            "pinned": self.pinned,
            "message_id": self.message_id,
            "channel_id": self.channel_id,
            "guild_id": self.guild_id,
            "content": self.content,
            "embeds": self.embeds,
            "attachments": self.attachments,
        }

    def to_json(self) -> str:
        """
        Returns a JSON string of the message info

        Returns:
            str: JSON dumped info.
        """

        return json.dumps(self.to_dict())


class Message:
    def __init__(self, message: dict) -> None:
        """
        Creates a Message class from a discord message response

        Args:
            message (dict): The discord message response
        """

        # with open("testtest.json", "w") as ajsdlfljkjkl:
        #    json.dump(message, ajsdlfljkjkl)

        self.message_data = MessageData(
            message["timestamp"],
            message["pinned"],
            message["id"],
            message["channel_id"],
            message["guild_id"],
            message["content"],
            message["embeds"],
            message["attachments"],
        )

        if "author" in message:
            _author: dict = message["author"]
        else:
            print("??? Author not found")

        self.author: Author = Author(
            _author["username"],
            str(_author["discriminator"]),
            str(_author["id"]),
        )

    def to_dict(self) -> dict[str, dict[str, typing.Any]]:
        return {
            "message_data": self.message_data.to_dict(),
            "author": self.author.to_dict(),
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def __repr__(self) -> str:
        return (
            "Message ("
            + f"message_id: {self.message_data.message_id}, "
            + f"author: {self.author.username} ({self.author.id}), "
            + f"content: {self.message_data.content}"
            + ")"
        )

    def __str__(self) -> str:
        return f'"{self.message_data.content}" sent by {self.author.username}'

    def __hash__(self) -> int:
        return hash(self.message_data.message_id)
