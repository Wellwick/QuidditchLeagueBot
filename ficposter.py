from discord.ext import commands
import json
import difflib
import ficmail
import ficparser
import asyncio

class FicPoster(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Need to load in which channels we are posting to
        with open("post_data.json", "r") as post_datafile:
            self.posting = json.load(post_datafile)

        if "teams" not in self.posting:
            self.posting["teams"] = [
                "Appleby Arrows",
                "Ballycastle Bats",
                "Caerphilly Catapults",
                "Chudley Cannons",
                "Falmouth Falcons",
                "Holyhead Harpies",
                "Kenmare Kestrels",
                "Montrose Magpies",
                "Pride of Portree",
                "Puddlemere United",
                "Tutshill Tornados",
                "Wigtown Wanderers",
                "Wimbourne Wasps",
                "Unknown"
            ]
        if "post_channels" not in self.posting:
            self.posting["post_channels"] = []
        
        # This is a dict going from team names to channels that want to be
        # notified when someone on their team posts
        self.channel_posts = {}
        for i in self.posting["teams"]:
            self.channel_posts[i] = []
        
        self.ready = False
        self.mail = ficmail.FicMail()
        self.parser = ficparser.FicParser()
        self.bot.add_cog(self.parser)
        self.bot.loop.create_task(self.mail.refresh_watch_loop())

    async def setup_post_channels(self):
        if self.ready:
            return
        for i in self.posting["post_channels"]:
            chan = await self.bot.fetch_channel(i["channel"])
            for team in i["teams"]:
                self.channel_posts[team] += [ chan ]
        self.ready = True

    def write_file(self):
        """Write out the file so we can pick up later if the bot shutsdown
        """
        # Save info in self.posting to post_data.json
        with open("post_data.json", "w") as post_datafile:
            json.dump(self.posting, post_datafile)

    def clear_subscription(self, guild):
        """Clears subscription for a guild and returns true if successful
        """
        subscription = None
        for i in self.posting["post_channels"]:
            if guild.id == i["guild"]:
                subscription = i
                chan = guild.get_channel(i["channel"])
                for team in i["teams"]:
                    self.channel_posts[team].remove(chan)
        
        if subscription != None:
            self.posting["post_channels"].remove(subscription)
            return True
        else:
            return False

    @commands.command()
    async def posthere(self, ctx, *, teams="All Teams"):
        """
            Request that updates of when people post Quidditch Leagues stories
            is sent to this channel. Only one posting channel per server is
            allowed.
            Use a comma separated list of teams that you want notifications on
            after the command. This will overwrite your previous choice. By 
            default all teams are included in your selection. 'Unknown' is for
            fics where the bot can't work out the team. Use %posthere list for
            a full list of the teams.
            e.g.
            %posthere Caerphilly Catapults, Puddlemere United, Unknown
        """
        # Only permissible in Omnioculars channel
        if ctx.guild.id == 798284145356046346 and ctx.channel.id != 809165162417750106:
            await ctx.send("Bot commands not allowed here! Please do in #omnioculars!")
            return
        await self.setup_post_channels()
        if teams == "All Teams":
            teams = ", ".join(self.posting["teams"])
        if teams.strip().lower() == "list":
            # They only want a list of teams
            await ctx.send("The list of teams to check for are: **" + "**, **".join(self.posting["teams"])) + "**"
            return

        # We could be replacing an existing thing, so wipe for this guild!
        # We don't care if it fails, that just means nothing is being tracked
        # here yet.
        self.clear_subscription(ctx.guild)
        temp_teams = teams.split(",")
        unrecognized = []
        teams = []
        for i in temp_teams:
            # Remove whitespace around it and Capitalize Each Word
            team = i.strip().title()
            closest_match = difflib.get_close_matches(team, self.posting["teams"])
            if len(closest_match) == 0:
                # Couldn't guess
                unrecognized += [ i.strip() ]
            else:
                if closest_match[0] not in teams:
                    teams += [ closest_match[0] ]
        
        data = {
            "guild": ctx.guild.id,
            "channel": ctx.channel.id,
            "teams": teams
        }
        self.posting["post_channels"] += [ data ]
        for team in teams:
            self.channel_posts[team] += [ ctx.channel ]

        self.write_file()
        string = "This channel is now subscribed for alerts for teams: **" + "**, **".join(teams) + "**"
        if len(unrecognized) > 0:
            string += "\n\nUnfortunately, I didn't recognize: **" + "**, **".join(unrecognized) + "**"
        await ctx.send(string)

    @commands.command()
    async def poststop(self, ctx, *args):
        """
            Request that all posting to this server stops.
        """
        # Only permissible in Omnioculars channel
        if ctx.guild.id == 798284145356046346 and ctx.channel.id != 809165162417750106:
            await ctx.send("Bot commands not allowed here! Please do in #omnioculars!")
            return
        await self.setup_post_channels()
        if self.clear_subscription(ctx.guild):
            self.write_file()
            await ctx.send("You will receive no more notifications on this server")
        else:
            await ctx.send("It doesn't seem this server is subscribed for fic notifications.")

    @commands.command(hidden=True)
    async def pingchannels(self, ctx, *args):
        """Pings all the subscribed channels, very annoying
        """
        if ctx.author.id != "227834498019098624":
            return
        await self.setup_post_channels()
        chans = []
        for i in self.channel_posts:
            for j in self.channel_posts[i]:
                if j not in chans:
                    chans += [j]

        for chan in chans:
            await chan.send("This is a test message to make sure you are subscribed, please ignore it!")
        
        if len(chans) == 0:
            await ctx.send("Seems there are no subscribed channels")

    async def send_notifications(self, team, emb):
        for channel in self.channel_posts[team]:
            try:
                await channel.send(embed=emb)
            except:
                print("Failed to send to channel " + channel.name + " on guild " + channel.guild.name)
        print("Notifications sent!")

    async def check_for_fics(self):
        await self.bot.wait_until_ready()
        await self.setup_post_channels()
        failures = 0
        while(True):
            try:
                fics = self.mail.get_latest()
                if len(fics) > 0:
                    print("Outputting " + str(len(fics)) + " fics")
                for fic in fics:
                    info = await self.parser.get_ql_fic(fic["id"], fic["chapter"])
                    print("Info collected!")
                    emb = self.parser.get_embed(info)
                    print(str(info))
                    if emb != None:
                        await self.send_notifications(info["team"], emb)
                failures = 0
                if len(fics) > 0:
                    # Don't acknowledge unless there is 
                    self.mail.messages_published()
            except:
                print("Failed to get emails!")
                failures += 1
                if failures == 120:
                    # 2 hours of failure in a row means bad news, PM Wellwick
                    creator = await self.bot.fetch_user(227834498019098624)
                    await creator.send("I have been failing to get emails for two hours straight. Woo!")

            await asyncio.sleep(60)