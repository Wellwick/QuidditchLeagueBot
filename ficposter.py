from discord.ext import commands
import json
import difflib

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

        for i in self.posting["post_channels"]:
            # These have a guild, channel id and list of teams that we must
            # resolve here
            for guild in self.bot.guilds:
                if guild.id == i["guild"]:
                    chan = guild.get_channel(i["channel"])
                    for team in i["teams"]:
                        self.channel_posts[team] += [ chan ]

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
            if guild == i["guild"]:
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
    async def posthere(self, ctx, *, teams=", ".join(self.posting["teams"])):
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
        if teams.strip().lower() == "list":
            # They only want a list of teams
            await ctx.send("The list of teams to check for are: " + ", ".join(self.posting["teams"]))
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
                teams += [ closest_match[0] ]
        
        data = {
            "guild": ctx.guild.id,
            "channel": ctx.channel.id,
            "teams": teams
        }
        self.posting["post_channels"] += [ data ]

        self.write_file()
        string = "This channel is now subscribed for alerts for teams: " + ", ".join(teams)
        if len(unrecognized) > 0:
            string += "\n\nUnfortunately, I didn't recognize: " + ", ".join(unrecognized)
        await ctx.send(string)



    @commands.command()
    async def poststop(self, ctx, *args):
        """
            Request that all posting to this server stops.
        """
        if self.clear_subscription(ctx.guild):
            self.write_file()
        else:
            await ctx.send("It doesn't seem this server is subscribed for fic notifications.")

    @commands.command()
    async def pingchannels(self, ctx, *args):
        """Pings all the subscribed channels, very annoying
        """
        chans = []
        for i in self.channel_posts:
            for j in self.channel_posts[i]:
                if j not in chans:
                    chans += [j]

        for chan in chans:
            await ctx.send("I'm posting here because of a %pingchannels command!")