from discord.ext import commands
import json
import discord
from discord import Embed
import random

class Beta(commands.Cog):
    """ This needs to collate information into one thing sometimes
    """
    def __init__(self, bot):
        # Need to load in what betaing still needs doing
        with open("beta-data.json", "r") as beta_datafile:
            self.beta = json.load(beta_datafile)

        needs_write = False

        if "data" not in self.beta:
            self.beta["data"] = {}
            needs_write = True

        if "reacts" not in self.beta:
            self.beta["reacts"] = [
                "👍",
                "🎉",
                "🥳",
                "✍",
                "📖",
                "✨",
                "🎊",
                "🔥"
            ]
            needs_write = True
        
        if needs_write:
            self.write_data()

        self.bot = bot

    def write_data(self):
        with open("beta_data.json", "w") as beta_datafile:
            json.dump(self.beta, beta_datafile)

    def story_id(self, story):
        # A 'hash' method to compare story values
        return story["title"] + story["link"] + story["info"] + story["reaction"]

    def story(self, author, title, link, info, reaction):
        # Normally this would be a class, but I want to insert it into a dict
        # structure and turning it back and forth between a class is going to
        # suck...
        story = {
            "author": author,
            "title": title,
            "link": link,
            "info": info,
            "reaction": reaction,
            "betas": [], # Always start with 0 betas. How sad!
            "messages": [] # Ids for messages that we are checking for reactions on
        }
        return story

    def pick_reaction(self, guild_id):
        reacts = self.beta["reacts"].copy()
        if guild_id not in self.beta["data"]:
            return random.choice(reacts)

        for i in self.beta["data"][guild_id]:
            reacts.remove(i["reaction"])

        return random.choice(reacts)

    def add_story(self, guild_id, story):
        if guild_id not in self.beta["data"]:
            self.beta["data"][guild_id] = []

        self.beta["data"][guild_id] += [story]
        self.write_data()

    async def check_beta_complete(self, story, channel):
        if len(story["betas"]) == 2:
            # We need to message the author and the two betas
            string = story["author"] + ", your story " + story["title"]
            string += " has been beta'd by " + " and ".join(story["betas"])
            await channel.send(string)
            guild_id = channel.guild.id
            self.beta["data"][guild_id].remove(story)

    async def on_raw_reaction_add(self, payload):
        # We only care about this if it is for a message id that we can find
        # in our list of tracked messages
        if payload.event_type != "REACTION_ADD":
            return
        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if message.author.id != self.bot.user.id:
            return

        # Don't care if the bot is reacting...
        if payload.member.id == self.bot.user.id:
            return

        # We only use unicode emojis so...
        if not payload.emoji.is_unicode_emoji():
            return

        guild_id = message.guild.id
        if guild_id not in self.beta["data"]:
            return
        
        # Work our way through, and we only want to check if it's the matching
        # reaction
        reaction = payload.emoji.name
        for i in self.beta["data"][guild_id]:
            if i["reaction"] != reaction:
                continue
            for j in i["messages"]:
                if j == message.id:
                    if payload.member.mention not in i["betas"]:
                        j["betas"] += [payload.member.mention]
                        await self.check_beta_complete(i, channel)
                        return

    @commands.command()
    async def beta(self, ctx, *, args=""):
        """Used for asking for and listing betas
        If you are requesting betas, you can give an optional title, then a link
        to your google sheet. You can add extra details after the link if you
        like
        %beta Your title https://docs.google.com/document/d/id/edit Some extra details you want to provide
        The only bit you must provide is the link, because it helps people find your stuff.
        """
        if args == "" or args.lower() == "list":
            server_stories = self.get_stories(ctx.guild.id)
        else:
            info = args.strip().split("http")
            if len(info) < 2:
                await ctx.send("Expecting a link!")
                return

            title = info[0].strip().title()
            if title == "":
                title = ctx.author.name + "'s Story"
            link = "http" + "http".join(info[1:])
            separated = link.split()
            link = separated[0]
            info = " ".join(separated[1:])
            reaction = self.pick_reaction(ctx.guild.id)
            story = self.story(ctx.author.mention, title, link, info, reaction)
            
            emb = Embed(
                title=story["title"], 
                url=story["link"], 
                description=story["info"] + "\n This story needs two betas for " + story["author"] + "!"
            )
            emb.set_footer(text="React with " + story["reaction"] + " if you have beta'd this story!")
            message = await ctx.send(embed=emb)
            story["messages"] += [ message.id ]
            await message.add_reaction(story["reaction"])

            # Make sure to add it to the info
            self.add_story(ctx.guild.id, story)

