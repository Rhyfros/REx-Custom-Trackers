"""
Used to run the bot and client.

Made by Rhyfros
"""

import asyncio
import json
import logging
import random
import sqlite3

import discord
import discord.ext.commands.errors as pycord_errors
from discord.ext import commands

import discord_socket
import message_info
from settings import BOT_TOKEN, TOKEN

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

TIER_RANKS_BY_INT = {
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

TIER_RANKS_BY_STR = {
    "Rare": 1,
    "Master": 2,
    "Surreal": 3,
    "Mythic": 4,
    "Exotic": 5,
    "Exquisite": 6,
    "Transcendent": 7,
    "Enigmatic": 8,
    "Unfathomable": 9,
    "Otherworldly": 10,
    "Zenith": 11,
}

TYPE_BY_CHANNEL_IDS = {
    "967252613227769876": "NORMAL",
    "967252672170299402": "IONIZED",
    "967252684807749752": "SPECTRAL",
}

TYPE_INDEX = {"NORMAL": 0, "IONIZED": 1, "SPECTRAL": 2}

with open("cave_ores.json", "r", encoding="utf-8") as cave_ores_json:
    CAVE_ORES: dict = json.load(cave_ores_json)


VALID_CHANNEL_IDS = ["967252613227769876", "967252672170299402", "967252684807749752"]
VALID_AUTHOR_IDS = ["967275823407173632", "967275686798716928", "967275962762932244"]


# Main
def main():
    """
    Main function
    """
    print("Starting main")

    # Parser
    async def parse_sender(
        ore_name: str,
        base_rarity: int,
        blocks_mined: int,
        username: str,
        tier: str,
        ore_type: str,
        world: str,
        event: str,
        pickaxe: str,
        cave_type: str | None = None,
    ):
        ore_name = " ".join(ore_name) if isinstance(ore_name, list) else ore_name

        text = (
            "--------------------------------------------------"
            + f"\n**{(ore_type.capitalize() + ' ' if ore_type != 'NORMAL' else '')}{' '.join(ore_name) if isinstance(ore_name, list) else ore_name}** "
            + f"{('' if cave_type is None else '(' + str(cave_type) + ') ')}"
            + f"has been found by **{username}** [**{tier}**]"
            + f"\nWorld: {world}"
            + f"\nBase Rarity: {base_rarity:,}"
            + f"\nBlocks Mined: {blocks_mined:,}"
            + f"\nPickaxe: {pickaxe}"
            + f"\nEvent: {event}"
            + (
                f"\nAdjusted: {int(CAVE_ORES[str(cave_type)]['rarity'] * 1.88 * (CAVE_ORES[str(cave_type)]['ores'][ore_name][TYPE_INDEX[ore_type]]) if cave_type != 'Gilded Cave' else base_rarity):,}"
                if (cave_type is not None and cave_type != "")
                else ""
            )
            + "\n--------------------------------------------------"
        )

        tier_rank = TIER_RANKS_BY_STR.get(tier, -1)

        db_cursor.execute(
            """
            SELECT * FROM "ChannelsPerGuild"
            """
        )
        cselect = db_cursor.fetchall()

        for guild_id, channel_id in cselect:
            this_text = text

            db_cursor.execute(
                """
                SELECT username FROM "PlayersPerGuild"
                WHERE guild_id = ?
                """,
                (guild_id,),
            )
            playerselect = db_cursor.fetchall()

            if username.lower() in [x[0].lower() for x in playerselect]:
                db_cursor.execute(
                    """
                    SELECT member_id FROM "PlayerPingPerMember"
                    WHERE guild_id = ? AND username = ?
                    """,
                    (guild_id, username),
                )
                pingselect = db_cursor.fetchall()

                db_cursor.execute(
                    """
                    SELECT global_message FROM "GlobalMessagePerGuild"
                    WHERE guild_id = ?
                    """,
                    (guild_id,),
                )
                global_select = db_cursor.fetchall()

                if len(global_select) > 0:
                    if tier_rank is not None:
                        if tier_rank >= 9:
                            this_text = this_text + f"\n\n{global_select[0][0]}\n"

                        elif tier_rank >= 7:
                            if ore_type == "SPECTRAL":
                                this_text = this_text + f"\n\n{global_select[0][0]}\n"

                            elif (tier_rank >= 8) and (ore_type == "IONIZED"):
                                this_text = this_text + f"\n\n{global_select[0][0]}\n"

                if len(pingselect) > 0:
                    print("Tracking")
                    try:
                        s_channel = bot_client.get_channel(channel_id)
                        if s_channel is not None:
                            await s_channel.send(
                                this_text
                                + "\n"
                                + "".join(
                                    ["\n<@" + str(x[0]) + ">" for x in pingselect]
                                )
                            )
                            print("Tracked")

                        else:
                            logger.log(logging.INFO, f"Removing channel: {channel_id}")

                            db_cursor.execute(
                                """
                                DELETE FROM "ChannelsPerGuild"
                                WHERE channel_id = ? AND guild_id = ?
                                """,
                                (channel_id, guild_id),
                            )
                    except Exception as e:
                        if isinstance(e, AttributeError):
                            logger.log(
                                logging.WARNING, f"Maybe remove this server idk? {e}"
                            )
                        logger.log(logging.ERROR, f"Errored trying to send ping: {e}")

                else:
                    print("Tracking")
                    try:
                        s_channel = bot_client.get_channel(channel_id)
                        if s_channel is not None:
                            await s_channel.send(this_text)
                            print("Tracked")

                        else:
                            logger.log(logging.INFO, f"Removing channel: {channel_id}")

                            db_cursor.execute(
                                """
                                DELETE FROM "ChannelsPerGuild"
                                WHERE channel_id = ? AND guild_id = ?
                                """,
                                (channel_id, guild_id),
                            )

                    except Exception:
                        pass

    async def parser(event_type, data) -> None:
        """
        Used to parse the events and their data

        Args:
            event_type (str): The string of the event type
            data (dict | list): The data response from discord
        """

        print(event_type)

        if event_type == "MESSAGE_CREATE":
            msg = message_info.Message(message=data)

            if (
                msg.message_data.channel_id in VALID_CHANNEL_IDS
                and msg.author.id in VALID_AUTHOR_IDS
            ):
                if bot_client.is_ready() is True:
                    embed_data = msg.message_data.embeds[0]

                    title = embed_data["title"].replace("*", "")
                    world = embed_data["description"]
                    fields = embed_data["fields"]

                    username = title.split()[0]
                    ore_type = TYPE_BY_CHANNEL_IDS.get(
                        str(msg.message_data.channel_id), None
                    )
                    if ore_type is None:  # If failed
                        print(msg.message_data.channel_id)

                    ore_name = (
                        " ".join(
                            title.split("has found")[1].split(" ")[
                                (0 if ore_type == "NORMAL" else 1) :
                            ]
                        )
                        .strip()
                        .split(" (")[0]
                    )

                    cave_type = title.split("(")

                    if len(cave_type) != 1:
                        cave_type = cave_type[1].replace(")", "")
                    else:
                        cave_type = None

                    tier: str = TIERS.get(str(embed_data["color"]), None)

                    base_rarity: int = int(
                        float(
                            fields[0]["value"]
                            .split()[0]
                            .replace("1/", "")
                            .replace(",", "")
                        )
                    )
                    blocks_mined: int = int(fields[1]["value"].replace(",", ""))
                    pickaxe: str = fields[2]["value"]
                    event: str = fields[3]["value"]

                    if ore_type != "NORMAL":
                        ore_name = (
                            title.split("has found")[1]
                            .replace(" an", "")
                            .replace(" a", "")
                            .strip()
                            .split(" (")[0]
                        ).split()[1:]

                    await parse_sender(
                        ore_name=ore_name,
                        base_rarity=base_rarity,
                        blocks_mined=blocks_mined,
                        pickaxe=pickaxe,
                        event=event,
                        tier=tier,
                        username=username,
                        world=(" ".join(world) if isinstance(world, list) else world),
                        cave_type=cave_type,
                        ore_type=ore_type,
                    )

    # Setup SQL DB
    db_conn = sqlite3.connect("db_v1.db")
    db_cursor = db_conn.cursor()

    # Initialize the tables
    db_cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS "PlayersPerGuild"
        (
            guild_id INTEGER,
            username TEXT
        )
        """
    )
    db_cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS "GlobalMessagePerGuild"
        (
            guild_id INTEGER,
            global_message TEXT
        )
        """
    )
    db_cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS "ChannelsPerGuild"
        (
            guild_id INTEGER,
            channel_id INTEGER
        )
        """
    )
    db_cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS "PlayerPingPerMember"
        (
            username TEXT,
            member_id INTEGER,
            guild_id INTEGER
        )
        """
    )

    db_conn.commit()

    # Setup logger
    logger = logging.getLogger(name="logger")
    logging.basicConfig(
        filename="log.log",
        filemode="a",
        level=logging.INFO,
        format="%(asctime)s;%(levelname)s;%(message)s",
    )

    # Bot
    bot_client = discord.Bot()

    @bot_client.slash_command(
        name="epinephrine",
        description="Nope...",
    )
    async def _bot_scmd_epinephrine(
        ctx: discord.ApplicationContext,
    ):  # /epinephrine scmd
        try:
            await ctx.defer()
            random_int = random.randint(1, 999_999_999)
            if random_int == 1:
                await ctx.followup.send(content="I am so sorry...\nRolled a 1.")

            elif random_int == 999_999_999:
                await ctx.followup.send(
                    "Money money kaching!!!!!!!!!!!\nJACKPOT!!!\nROLLED A 999,999,999"
                )

            else:
                await ctx.followup.send(
                    f"Did not roll epinephrine\nRolled: {random_int:,}"
                )

        except (
            discord.errors.ApplicationCommandInvokeError,
            discord.errors.NotFound,
            pycord_errors.CommandOnCooldown,
        ):
            pass

    @bot_client.slash_command(
        name="unfathomable",
        description="Probably not...",
    )
    async def _bot_scmd_unfathomable(
        ctx: discord.ApplicationContext,
    ):  # /unfathomable scmd
        try:
            await ctx.defer()
            random_int = random.randint(1, 100_000_000)
            if random_int == 1:
                await ctx.followup.send(content="I quite sorry.\nRolled a 1.")

            elif random_int == 100_000_000:
                await ctx.followup.send("Money money!!\nEASY!!!\nROLLED A 100,000,000")

            else:
                await ctx.followup.send(
                    f"Did not roll unfathomable\nRolled: {random_int:,}"
                )

        except (
            discord.errors.ApplicationCommandInvokeError,
            discord.errors.NotFound,
            pycord_errors.CommandOnCooldown,
        ):
            pass

    @bot_client.slash_command(
        name="enigmatic",
        description="Maybe...",
    )
    async def _bot_scmd_enigmatic(
        ctx: discord.ApplicationContext,
    ):  # /enigmatic scmd
        try:
            await ctx.defer()
            random_int = random.randint(1, 50_000_000)
            if random_int == 1:
                await ctx.followup.send(content="I a bit sorry...\nRolled a 1.")

            elif random_int == 50_000_000:
                await ctx.followup.send(
                    "Money money kaching!\nJACKPOT!!!\nROLLED A 50,000,000"
                )

            else:
                await ctx.followup.send(
                    f"Did not roll enigmatic\nRolled: {random_int:,}"
                )

        except (
            discord.errors.ApplicationCommandInvokeError,
            discord.errors.NotFound,
            pycord_errors.CommandOnCooldown,
        ):
            pass

    @bot_client.slash_command(
        name="transcendent",
        description="Maybe...",
    )
    async def _bot_scmd_transcendent(
        ctx: discord.ApplicationContext,
    ):  # /transcendent scmd
        try:
            await ctx.defer()
            random_int = random.randint(1, 15_000_001)
            if random_int == 1:
                await ctx.followup.send(content="I not that sorry...\nRolled a 1.")

            elif random_int == 15_000_001:
                await ctx.followup.send("Money!\nJACKPOT!!!\nROLLED A 15,000,001")

            else:
                await ctx.followup.send(
                    f"Did not roll transcendent\nRolled: {random_int:,}"
                )

        except (
            discord.errors.ApplicationCommandInvokeError,
            discord.errors.NotFound,
            pycord_errors.CommandOnCooldown,
        ):
            pass

    @bot_client.slash_command(
        name="exquisite",
        description="Maybe...",
    )
    async def _bot_scmd_exquisite(
        ctx: discord.ApplicationContext,
    ):  # /exquisite scmd
        try:
            await ctx.defer()
            random_int = random.randint(1, 7_500_000)
            if random_int == 1:
                await ctx.followup.send(content="R.I.P. I guess...\nRolled a 1.")

            elif random_int == 7_500_000:
                await ctx.followup.send(
                    "asdfghjkl\nInstantly cool with this one trick!\nROLLED A 7,500,000"
                )

            else:
                await ctx.followup.send(
                    f"Did not roll exquisite\nRolled: {random_int:,}"
                )

        except (
            discord.errors.ApplicationCommandInvokeError,
            discord.errors.NotFound,
            pycord_errors.CommandOnCooldown,
        ):
            pass

    @bot_client.slash_command(
        name="exotic",
        description="Maybe...",
    )
    async def _bot_scmd_exotic(
        ctx: discord.ApplicationContext,
    ):  # /exotic scmd
        try:
            await ctx.defer()
            random_int = random.randint(1, 1_000_000)
            if random_int == 1:
                await ctx.followup.send(content="Not cool dude...\nRolled a 1.")

            elif random_int == 1_000_000:
                await ctx.followup.send("Cool\nDing ding ding!\nROLLED A 1,000,000")

            else:
                await ctx.followup.send(f"Did not roll exotic\nRolled: {random_int:,}")

        except (
            discord.errors.ApplicationCommandInvokeError,
            discord.errors.NotFound,
            pycord_errors.CommandOnCooldown,
        ):
            pass

    @bot_client.slash_command(
        name="infinite_roll",
        description="IDK...",
    )
    async def _bot_scmd_infinite_roll(
        ctx: discord.ApplicationContext,
    ):  # /infinite_roll scmd
        try:
            await ctx.defer()
            integer = 1

            while True:
                if random.randint(1, 2) == 2:
                    integer *= 2
                else:
                    break

            await ctx.followup.send(f"Rolled: {integer:,}")

        except (
            discord.errors.ApplicationCommandInvokeError,
            discord.errors.NotFound,
            pycord_errors.CommandOnCooldown,
        ):
            pass

    @commands.cooldown(5, 60, commands.BucketType.member)
    @bot_client.slash_command(
        name="change_tracker_channel",
        description="Set to 0 to ignore",
    )
    async def _bot_scmd_change_tracker_channel(
        ctx: discord.ApplicationContext, channel_id: str
    ):  # /change_tracker_channel scmd
        try:
            if ctx.author.guild_permissions.administrator is True:
                await ctx.defer()
                try:
                    if (len(channel_id) <= 20) and (len(channel_id) >= 10):
                        if int(channel_id) in [int(x.id) for x in ctx.guild.channels]:
                            db_cursor.execute(
                                """
                                DELETE FROM "ChannelsPerGuild"
                                WHERE guild_id = ?
                                """,
                                (ctx.guild_id,),
                            )
                            db_cursor.execute(
                                """
                                INSERT INTO "ChannelsPerGuild"
                                (
                                    guild_id,
                                    channel_id
                                )
                                VALUES
                                (
                                    ?,
                                    ?
                                )
                                """,
                                (
                                    ctx.guild_id,
                                    int(channel_id),
                                ),
                            )

                            db_conn.commit()

                            try:
                                await ctx.followup.send(
                                    content="Changed tracker channel in DB"
                                )
                            except Exception as e:
                                print(
                                    f"Failed sending finalizer for add_to_tracker: {e}"
                                )

                        else:
                            try:
                                await ctx.followup.send(
                                    content="That channel isn't in your server."
                                )
                            except Exception as e:
                                print(
                                    f"Failed sending finalizer for add_to_tracker: {e}"
                                )

                    else:
                        try:
                            await ctx.followup.send(
                                "Channel is not of appropriate length, removing."
                            )
                        except Exception as e:
                            print(
                                "Failed to sent finalizing message for change_tracker_channel:",
                                e,
                            )

                            db_cursor.execute(
                                """
                                DELETE FROM "ChannelsPerGuild"
                                WHERE guild_id = ?
                                """,
                                (ctx.guild_id,),
                            )
                            db_cursor.execute(
                                """
                                INSERT INTO "ChannelsPerGuild"
                                (
                                    guild_id,
                                    channel_id
                                )
                                VALUES
                                (
                                    ?,
                                    ?
                                )
                                """,
                                (
                                    ctx.guild_id,
                                    int(channel_id),
                                ),
                            )

                        db_conn.commit()

                except Exception as e:
                    logger.log(
                        logging.ERROR, f"[TBOTv1] Failed adding to database: {e}"
                    )
                    print("Failed adding to database:", e)
                    await ctx.followup.send(content="Failed adding player to DB")

        except (
            discord.errors.ApplicationCommandInvokeError,
            discord.errors.NotFound,
            pycord_errors.CommandOnCooldown,
        ):
            pass

    @commands.cooldown(10, 60, commands.BucketType.guild)
    @bot_client.slash_command(
        name="add_to_tracker",
        description="Adds a username to the tracker.",
    )
    async def _bot_scmd_add_to_tracker(
        ctx: discord.ApplicationContext, username: str
    ):  # /add_to_tracker scmd
        try:
            if ctx.author.guild_permissions.administrator is True:
                await ctx.defer()
                try:
                    db_cursor.execute(
                        """
                        SELECT * FROM "PlayersPerGuild"
                        WHERE guild_id = ?
                        """,
                        (ctx.guild_id,),
                    )

                    selection = db_cursor.fetchall()

                    max_players_added = 5 + (ctx.guild.member_count * 1.1)
                    if len(selection) < max_players_added:
                        if (len(username) <= 20) and (len(username) >= 3):
                            if [ctx.guild_id, username] not in [
                                [x[0], x[1]] for x in selection
                            ]:
                                db_cursor.execute(
                                    """
                                    INSERT INTO "PlayersPerGuild"
                                    (
                                        guild_id,
                                        username
                                    )
                                    VALUES
                                    (
                                        ?,
                                        ?
                                    )
                                    """,
                                    (ctx.guild_id, username),
                                )
                                db_conn.commit()

                                try:
                                    await ctx.followup.send(
                                        content="Added player to DB"
                                    )
                                except Exception as e:
                                    print(
                                        f"Failed sending finalizer for add_to_tracker: {e}"
                                    )

                            else:
                                await ctx.followup.send(
                                    content="Player already added to DB"
                                )

                        else:
                            await ctx.followup.send(
                                "Username is not of appropriate length."
                            )

                    else:
                        await ctx.followup.send(
                            f"Maximum amount of usernames for trackers. Maximum: {max_players_added}"
                        )

                except Exception as e:
                    logger.log(
                        logging.ERROR, f"[TBOTv1] Failed adding to database: {e}"
                    )
                    print("Failed adding to database:", e)
                    await ctx.followup.send(content="Failed adding player to DB")

        except (
            discord.errors.ApplicationCommandInvokeError,
            discord.errors.NotFound,
            pycord_errors.CommandOnCooldown,
        ):
            pass

    @commands.cooldown(10, 60, commands.BucketType.guild)
    @bot_client.slash_command(
        name="remove_from_tracker",
        description="Adds a username to the tracker.",
    )
    async def _bot_scmd_remove_from_tracker(
        ctx: discord.ApplicationContext, username: str
    ):  # /remove_from_tracker scmd
        try:
            if ctx.author.guild_permissions.administrator is True:
                await ctx.defer()
                try:
                    if (len(username) <= 20) and (len(username) >= 3):
                        db_cursor.execute(
                            """
                            DELETE FROM "PlayersPerGuild"
                            WHERE guild_id = ? AND username = ?
                            """,
                            (ctx.guild_id, username),
                        )
                        db_conn.commit()

                        try:
                            await ctx.followup.send(content="Removed player from DB")
                        except Exception as e:
                            print(
                                f"Failed sending finalizer for remove_from_tracker: {e}"
                            )

                    else:
                        await ctx.followup.send(
                            "Username is not of appropriate length."
                        )

                except Exception as e:
                    logger.log(
                        logging.ERROR, f"[TBOTv1] Failed removing from database: {e}"
                    )
                    print("Failed removing from database:", e)
                    await ctx.followup.send(content="Failed removing player from DB")

        except (
            discord.errors.ApplicationCommandInvokeError,
            discord.errors.NotFound,
            pycord_errors.CommandOnCooldown,
        ):
            pass

    @commands.cooldown(10, 60, commands.BucketType.guild)
    @bot_client.slash_command(
        name="check_tracked_usernames",
        description="Adds a username to the tracker.",
    )
    async def _bot_scmd_check_tracked_usernames(
        ctx: discord.ApplicationContext,
    ):  # /check_tracked_usernames scmd
        try:
            if ctx.author.guild_permissions.administrator is True:
                await ctx.defer()
                try:
                    db_cursor.execute(
                        """
                        SELECT * FROM "PlayersPerGuild"
                        WHERE guild_id = ?
                        """,
                        (ctx.guild_id,),
                    )

                    selection = db_cursor.fetchall()

                    await ctx.followup.send(
                        "\n".join(sorted([x[1] for x in selection]))
                    )

                except Exception as e:
                    logger.log(
                        logging.ERROR,
                        f"Failed to either fetch or respond to discord: {e}",
                    )
                    print(e)
                    await ctx.respond(
                        content="Failed to either fetch or respond to discord."
                    )

        except (
            discord.errors.ApplicationCommandInvokeError,
            discord.errors.NotFound,
            pycord_errors.CommandOnCooldown,
        ):
            pass

    @commands.cooldown(10, 60, commands.BucketType.member)
    @bot_client.slash_command(
        name="change_ping",
        description="Changes what username you get pinged with in the tracker.",
    )
    async def _bot_scmd_change_ping(
        ctx: discord.ApplicationContext, username: str
    ):  # /change_ping scmd
        try:
            await ctx.defer()
            try:
                db_cursor.execute(
                    """
                    DELETE FROM "PlayerPingPerMember"
                    WHERE member_id = ? AND guild_id = ?
                    """,
                    (ctx.author.id, ctx.guild_id),
                )
                db_cursor.execute(
                    """
                    INSERT INTO "PlayerPingPerMember"
                    (            
                        username,
                        member_id,
                        guild_id
                    )
                    VALUES
                    (
                        ?,
                        ?,
                        ?
                    )
                    """,
                    (username, ctx.author.id, ctx.guild_id),
                )

                db_conn.commit()

                await ctx.followup.send("Successfully edited the DB")

            except Exception as e:
                logger.log(
                    logging.ERROR,
                    f"Failed to edit DB or had API issues: {e}",
                )
                print(e)
                await ctx.followup.send(content="Failed to edit DB or had API issues.")

        except (
            discord.errors.ApplicationCommandInvokeError,
            discord.errors.NotFound,
            pycord_errors.CommandOnCooldown,
        ):
            pass

    @commands.cooldown(4, 60, commands.BucketType.member)
    @bot_client.slash_command(
        name="remove_ping",
        description="Removes username for user_id in the pings in the tracker.",
    )
    async def _bot_scmd_remove_ping(
        ctx: discord.ApplicationContext, member_id: str
    ):  # /check_tracked_usernames scmd
        try:
            await ctx.defer()
            if (ctx.author.guild_permissions.administrator is True) or (
                ctx.author.id == member_id
            ):
                try:
                    db_cursor.execute(
                        """
                        DELETE FROM "PlayerPingPerMember"
                        WHERE member_id = ? AND guild_id = ?
                        """,
                        (int(member_id), ctx.guild_id),
                    )

                    db_conn.commit()

                    await ctx.followup.send("Successfully edited the DB")

                except Exception as e:
                    logger.log(
                        logging.ERROR,
                        f"Failed to edit DB or had API issues: {e}",
                    )
                    print(e)
                    await ctx.respond(content="Failed to edit DB or had API issues.")

        except (
            discord.errors.ApplicationCommandInvokeError,
            discord.errors.NotFound,
            pycord_errors.CommandOnCooldown,
        ):
            pass

    @commands.cooldown(10, 60, commands.BucketType.guild)
    @bot_client.slash_command(
        name="change_global_message",
        description="Changes global message for the server.",
    )
    async def _bot_scmd_change_global_message(
        ctx: discord.ApplicationContext, global_message: str
    ):  # /change_global_message scmd
        try:
            await ctx.defer()
            if ctx.author.guild_permissions.administrator is True:
                try:
                    if len(global_message) < 100:
                        db_cursor.execute(
                            """
                            DELETE FROM "GlobalMessagePerGuild"
                            WHERE guild_id = ?
                            """,
                            (ctx.guild_id,),
                        )
                        db_cursor.execute(
                            """
                            INSERT INTO "GlobalMessagePerGuild"
                            (
                                guild_id,
                                global_message
                            )
                            VALUES
                            (
                                ?,
                                ?
                            )
                            """,
                            (ctx.guild_id, global_message),
                        )

                        db_conn.commit()

                        await ctx.followup.send("Updated")

                    else:
                        await ctx.followup.send(
                            "Global must be below 100 length in characters"
                        )

                except Exception as e:
                    logger.log(
                        logging.ERROR,
                        f"Failed to either fetch or respond to discord: {e}",
                    )
                    print("Failed to either fetch or respond to discord:", e)
                    await ctx.followup.send(
                        content="Failed to either update or respond to discord."
                    )

        except (
            discord.errors.ApplicationCommandInvokeError,
            discord.errors.NotFound,
            pycord_errors.CommandOnCooldown,
        ):
            pass

    @bot_client.slash_command(
        name="manual_track",
        description="Manually tracks an ore. (DEVELOPER ONLY)",
    )
    async def _bot_scmd_manual_track(
        ctx: discord.ApplicationContext,
        ore_name: str,
        base_rarity: int,
        blocks_mined: int,
        username: str,
        tier: discord.Option(
            str,
            "Enter a tier",
            choices=[
                "Rare",
                "Master",
                "Surreal",
                "Mythic",
                "Exotic",
                "Exquisite",
                "Transcendent",
                "Enigmatic",
                "Unfathomable",
                "Otherworldly",
                "Zenith",
            ],
        ),
        ore_type: discord.Option(
            str,
            "Enter a type",
            choices=[
                "NORMAL",
                "IONIZED",
                "SPECTRAL",
            ],
        ),
        world: str,
        event: str,
        pickaxe: str,
        cave_type: str | None = None,
    ):  # /manual_track scmd
        try:
            await ctx.defer()
            # print(str(ctx.author.id))
            if str(ctx.author.id) == "666960905224978463":
                await ctx.followup.send("Sending")
                await parse_sender(
                    ore_name=ore_name,
                    base_rarity=base_rarity,
                    blocks_mined=blocks_mined,
                    username=username,
                    tier=tier,
                    ore_type=ore_type,
                    world=world,
                    event=event,
                    pickaxe=pickaxe,
                    cave_type=cave_type,
                )

        except (
            discord.errors.ApplicationCommandInvokeError,
            discord.errors.NotFound,
            pycord_errors.CommandOnCooldown,
        ):
            pass

    # Setup client
    ds_setup = discord_socket.DiscordSocketSetup(token=TOKEN, parser=parser)
    ds = discord_socket.DiscordSocket(ds_setup=ds_setup, logger=logger)

    # Connect client
    ds.start()

    # Connect bot
    asyncio.get_event_loop().run_until_complete(bot_client.start(BOT_TOKEN))


if __name__ == "__main__":
    main()
