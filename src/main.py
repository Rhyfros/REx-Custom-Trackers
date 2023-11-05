"""
Used to run the bot and client.

Made by Rhyfros
"""

import asyncio
import logging
import random
import sqlite3

import discord
import discord_socket
import message_info
from discord.ext import commands
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


# Main
def main():
    """
    Main function
    """
    print("Starting main")

    # Parser
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

                    tier: str = TIERS.get(str(embed_data["color"]), "NOT FOUND?")

                    base_rarity: str = fields[0]["value"].split()[0].replace("1/", "")
                    blocks_mined: str = fields[1]["value"]
                    pickaxe: str = fields[2]["value"]
                    event: str = fields[3]["value"]

                    text = (
                        "--------------------------------------------------"
                        + f"\n**{str(ore_name[0]).upper() + str(ore_name[1:])}** "
                        + f"{('' if cave_type is None else '(' + str(cave_type) + ') ')}"
                        + f"has been found by **{username}** [**{tier}**]"
                        + f"\nWorld: {world}"
                        + f"\nBase Rarity: {base_rarity}"
                        + f"\nBlocks Mined: {blocks_mined}"
                        + f"\nPickaxe: {pickaxe}"
                        + f"\nEvent: {event}"
                        + "\n--------------------------------------------------"
                    )

                    db_cursor.execute(
                        """
                        SELECT * FROM "ChannelsPerGuild"
                        """
                    )
                    cselect = db_cursor.fetchall()

                    for guild_id, channel_id in cselect:
                        db_cursor.execute(
                            """
                            SELECT username FROM "PlayersPerGuild"
                            WHERE guild_id = ?
                            """,
                            (guild_id,),
                        )
                        pselect = db_cursor.fetchall()
                        # print(pselect in [x[0] for x in pselect])
                        # print([x[0] for x in pselect])

                        if username.lower() in [x[0].lower() for x in pselect]:
                            print("Tracking")
                            await bot_client.get_channel(channel_id).send(text)
                            print("Tracked")

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
        CREATE TABLE IF NOT EXISTS "ChannelsPerGuild"
        (
            guild_id INTEGER,
            channel_id INTEGER
        )
        """
    )

    db_conn.commit()

    # Setup logger
    logger = logging.getLogger(name="logger")
    logging.basicConfig(filename="log.log", filemode="a", level=logging.DEBUG)

    # Bot
    bot_client = discord.Bot()

    @commands.cooldown(1, 1, commands.BucketType.member)
    @bot_client.slash_command(
        name="epinephrine",
        description="Nope...",
    )
    async def _bot_scmd_epinephrine(
        ctx: discord.ApplicationContext,
    ):  # /epinephrine scmd
        await ctx.response.defer()
        try:
            random_int = random.randint(1, 999_999_999)
            if random_int == 1:
                await ctx.followup.send(content="I am so sorry...\nRolled a 1.")

            elif random_int == 999_999_999:
                await ctx.followup.send(
                    "Money money kaching!\nJACKPOT!!!\nROLLED A 999,999,999"
                )

            else:
                await ctx.followup.send(
                    f"Did not roll epinephrine\nRolled: {random_int:,}"
                )

        except discord.errors.ApplicationCommandInvokeError:
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
                await ctx.response.defer()
                try:
                    if (len(channel_id) <= 20) and (len(channel_id) >= 10):
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
                            (ctx.guild_id, int(channel_id)),
                        )

                        db_conn.commit()

                        try:
                            await ctx.followup.send(
                                content="Changed tracker channel in DB"
                            )
                        except Exception as e:
                            print(f"Failed sending finalizer for add_to_tracker: {e}")

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
                            DELETE * FROM "ChannelsPerGuild"
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
                            (ctx.guild_id, int(channel_id)),
                        )

                        db_conn.commit()

                except Exception as e:
                    logger.log(
                        logging.ERROR, f"[TBOTv1] Failed adding to database: {e}"
                    )
                    print("Failed adding to database:", e)
                    await ctx.followup.send(content="Failed adding player to DB")

        except discord.errors.ApplicationCommandInvokeError:
            await ctx.followup.send(content="On cooldown")

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
                await ctx.response.defer()
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

        except discord.errors.ApplicationCommandInvokeError:
            await ctx.followup.send(content="On cooldown")

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
                await ctx.response.defer()
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

        except discord.errors.ApplicationCommandInvokeError:
            await ctx.followup.send(content="On cooldown")

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
                await ctx.response.defer()
                try:
                    db_cursor.execute(
                        """
                        SELECT * FROM "PlayersPerGuild"
                        WHERE guild_id = ?
                        """,
                        (ctx.guild_id,),
                    )

                    selection = db_cursor.fetchall()

                    await ctx.followup.send("\n".join([x[1] for x in selection]))

                except Exception as e:
                    logger.log(
                        logging.ERROR,
                        f"Failed to either fetch or respond to discord: {e}",
                    )
                    print(e)
                    await ctx.respond(
                        content="Failed to either fetch or respond to discord."
                    )

        except discord.errors.ApplicationCommandInvokeError:
            await ctx.followup.send(content="On cooldown")

    # Setup client
    ds_setup = discord_socket.DiscordSocketSetup(token=TOKEN, parser=parser)
    ds = discord_socket.DiscordSocket(ds_setup=ds_setup, logger=logger)

    # Connect client
    ds.start()

    # Connect bot
    asyncio.get_event_loop().run_until_complete(bot_client.start(BOT_TOKEN))


if __name__ == "__main__":
    main()
