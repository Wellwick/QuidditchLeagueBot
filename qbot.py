#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
path_here = os.path.dirname(os.path.realpath(__file__))
os.chdir(path_here)
# Lets us not care where smiley runs from
import discord, git
from discord.ext import commands
import asyncio, sys
import sheets
import ficposter
import beta

'''My (Quidditch League Bot's) Main Script
I'm friendly, and I have commands to support the Quidditch League discord server
'''

intents = discord.Intents.default()
intents.members = True
intents.reactions = True

b = commands.Bot(command_prefix=('%'),  case_insensitive=True, intents=intents)

# This will also add the FicParser cog itself!
poster = ficposter.FicPoster(b)
beta_cog = beta.Beta(b)
b.add_cog(poster)
b.loop.create_task(poster.check_for_fics())
b.add_cog()

@b.command()
async def hi(ctx, *args):
    '''The hi command. I'll greet the user.
    '''
    await ctx.send('Hi, <@' + str(ctx.author.id) + '>!')

@b.event()
async def on_raw_reaction_add(payload):
    # We only care about this if it is for a message id that we can find
    # in our list of
    await beta_cog.on_raw_reaction_add(payload)

with open('secret') as s:
    token = s.read()[:-1]
# Read the Discord bot token from a soup or secret file

print("Quidditch League Bot is going live!")
b.run(token)
# Start the bot, finally!