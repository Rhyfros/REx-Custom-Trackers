"""
Hi i do the things that do the bot things
"""


import logging

import requests

import discord_socket
import MessageInfo
from settings import TOKEN, WEBHOOK_URL


TIERS = {
    "16744449": "Rare",
    "10092774": "Master",
    "1955753": "Surreal",
    "16711915": "Mythic",
    "16173376": "Exotic",
    "5686117": "Exquisite",
    "33023": "Transcendent",
    "13497856": "Enigmatic",
    "207993": "Unfathomable",
    "6164018": "Otherworldly",
    "0": "Zenith",
}

TIER_RANKS = {
    "16744449": 1,
    "10092774": 2,
    "1955753": 3,
    "16711915": 4,
    "16173376": 5,
    "5686117": 6,
    "33023": 7,
    "13497856": 8,
    "207993": 9,
    "6164018": 10,
    "0": 11,
}

VALID_CHANNEL_IDS = ["967252613227769876", "967252672170299402", "967252684807749752"]
VALID_AUTHOR_IDS = ["967275823407173632", "967275686798716928", "967275962762932244"]


def parser(event_type, data) -> None:
    """
    Parses the events and their data

    Args:
        event_type (str): The string of the event type
        data (dict | list): The data response from discord
    """

    print(event_type)

    if event_type == "MESSAGE_CREATE":
        msg = MessageInfo.Message(message=data)

        if (
            msg.message_data.channel_id in VALID_CHANNEL_IDS
            and msg.author.id in VALID_AUTHOR_IDS
        ):
            embed = msg.message_data.embeds[0]

            title = embed["title"].replace("*", "")
            world = embed["description"]
            fields = embed["fields"]

            username = title.split()[0]
            ore_name = (
                title.split("has found")[1]
                .replace(" an", "")
                .replace(" a", "")
                .strip()
                .split(" (")[0]
            )

            cave_type = title.split("(")

            if len(cave_type) != 1:
                cave_type = cave_type[1].replace(")", "")
            else:
                cave_type = None

            tier: str = TIERS.get(str(embed["color"]), "NOT FOUND?")

            rarity: str = fields[0]["value"].split()[0].replace("1/", "")
            blocks_mined: str = fields[1]["value"]
            pickaxe: str = fields[2]["value"]
            event: str = fields[3]["value"]

            new_data = {
                "embeds": [
                    {
                        "title": f"**{ore_name[0].upper() + ore_name[1:]}** "
                        + f"{('' if cave_type is None else '(' + cave_type + ') ')}"
                        + f"has been found by **{username}** [**{tier}**]",
                        "description": f"Found in {world}",
                        "fields": [
                            {
                                "name": "Rarity",
                                "value": f"1/**{rarity}**",
                                "inline": True,
                            },
                            {
                                "name": "Blocks Mined",
                                "value": blocks_mined,
                                "inline": True,
                            },
                            {"name": "Pickaxe", "value": pickaxe, "inline": True},
                            {"name": "Event", "value": event, "inline": True},
                        ],
                        "color": embed["color"],
                    }
                ]
            }

            requests.post(url=WEBHOOK_URL, json=new_data, timeout=2)


class Client:
    """
    The core Discord client
    """

    def __init__(self) -> None:
        logger = logging.getLogger(name="logger")
        logging.basicConfig(filename="log.log", filemode="a", level=logging.DEBUG)

        self.discord_socket = discord_socket.DiscordSocket(
            ds_setup=discord_socket.DiscordSocketSetup(
                token=TOKEN,
                activity=[
                    {
                        "type": 3,
                        "name": "tracking",
                        "details": "dm me for info, might not check often",
                    }
                ],
                parser=parser,
            ),
            logger=logger,
        )

    def connect(self) -> None:
        """
        Connects to Discord
        """
        self.discord_socket.run()


def main():
    """
    Main function
    """

    client = Client()
    client.connect()


if __name__ == "__main__":
    main()
