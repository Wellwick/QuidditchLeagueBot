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
import ficparser
import ficposter

'''My (Quidditch League Bot's) Main Script
I'm friendly, and I have commands to support the Quidditch League discord server
'''

intents = discord.Intents.default()
intents.members = True

b = commands.Bot(command_prefix=('%'),  case_insensitive=True, intents=intents)

@b.command()
async def hi(ctx, *args):
    '''The hi command. I'll greet the user.
    '''
    await ctx.send('Hi, <@' + str(ctx.author.id) + '>!')


b.add_cog(ficparser.FicParser())
b.add_cog(ficposter.FicPoster(b))

with open('secret') as s:
    token = s.read()[:-1]
# Read the Discord bot token from a soup or secret file

print("Quidditch League Bot is going live!")
b.run(token)
# Start the bot, finally!