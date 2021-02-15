
from discord.ext import commands
from discord import Embed
from ff.fiction import Story, Chapter, User
import re
import asyncio

class FicParser(commands.Cog):
    def __init__(self):
        # Who even knows what this is going to need
        self.teams = [
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
            "Wimbourne Wasps"
        ]
        self.positions = [
            "Captain",
            "Keeper",
            "Chaser 1",
            "Chaser 2",
            "Chaser 3",
            "Beater 1",
            "Beater 2",
            "Seeker"
        ]
        self.replacements = {
            "one": "1",
            "two": "2",
            "three": "3",
            "four": "4",
            "five": "5",
            "six": "6",
            "seven": "7",
            "eight": "8",
            "nine": "9",
            "ten": "10",
            "eleven": "11",
            "twelve": "12",
            "thirteen": "13",
            "tornadoes": "tornados",
        }
        self.prompt_re = re.compile(".*(\[|\()[a-z]+(\]|\)).*")

    async def get_ql_fic(self, id, chap):
        print("Getting story " + str(id))
        story = Story(id=int(id))
        # Because access to fanfiction.net is kind of garbage, let's make 5 
        # attempts for each download before giving up!
        attempts = 0
        while attempts < 5:
            try:
                story.download_data()
                attempts = 5
            except:
                attempts += 1
                await asyncio.sleep(1)
        author = User(id=story.author_id)
        attempts = 0
        while attempts < 5:
            try:
                author.download_data()
                attempts = 5
            except:
                attempts += 1
                await asyncio.sleep(1)
        print("Getting chapter " + str(chap))
        attempts = 0
        while attempts < 5:
            try:
                chapter = Chapter(story_id=story.id, chapter=int(chap))
                attempts = 5
            except:
                attempts += 1
                await asyncio.sleep(1)
        # Now we have the information, it's time to get processing
        c_text = chapter.text.lower()
        print("Doing replacements")
        for i in self.replacements.keys():
            r_text = c_text.replace(i, self.replacements[i])
        info = {
            "forql": False,
            "story": story,
            "author": author,
            "title": story.title,
            "url": story.url + "/" + str(chap),
            "season": "9",
            "round": "Unknown",
            "position": "Unknown",
            "team": "Unknown",
            "m_prompt": "Unknown",
            "o_prompts": [],
            "wordcount": "Unknown"
        }

        print("Checking for team")
        lowest_pos = len(r_text)
        for i in self.teams:
            pos = r_text.find(i.lower())
            if pos != -1 and pos < lowest_pos:
                lowest_pos = pos
                info["team"] = i
                # If we find the name of a team, it's pretty unlikely it's not
                # for QL
                info["forql"] = True
        
        print("Checking for QL")
        for i in ["qlfc", "quidditch league", "quidditch fanfiction league"]:
            if i in c_text:
                info["forql"] = True
            if i in story.description.lower():
                info["forql"] = True

        if not info["forql"]:
            print("Not a QL fic")
            return info

        print("Checking for position")
        lowest_pos = len(r_text)
        for i in self.positions:
            pos = r_text.find(i.lower())
            if pos != -1 and pos < lowest_pos:
                lowest_pos = pos
                info["position"] = i

        pos = r_text.find("round ")
        info["round"] = chapter.text[pos:].split("\n")[0]
        if info["round"] == "Unknown" or len(info["round"]) > 50:
            pos = r_text.find("prophet challenge")
            if pos != -1:
                info["round"] = chapter.text[pos:].split("\n")[0]
            else:
                info["round"] = "Round Unknown"

        # The vast majority of people go
        # Word Count: nnnn
        pos = r_text.find("word count")
        if pos != -1:
            pos += 10
            local = r_text[pos:]
            pos = local.find(":")
            if pos != -1:
                info["wordcount"] = local[pos+1:].strip().split()[0]
            else:
                info["wordcount"] = local.strip().split()[0]
        else:
            pos = r_text.find("wordcount")
            if pos != -1:
                pos += 9
                local = r_text[pos:]
                pos = local.find(":")
                if pos != -1:
                    info["wordcount"] = local[pos+1:].strip().split()[0]
                else:
                    info["wordcount"] = local.strip().split()[0]
            else:
                pos = r_text.find("words:")
                if pos != -1:
                    pos += 6
                    local = r_text[pos:]
                    if pos != -1:
                        info["wordcount"] = local[pos+1:].strip().split()[0]
                    else:
                        info["wordcount"] = local.strip().split()[0]
        
        if info["wordcount"] == "Unknown":
            # It wasn't an easy check, let's estimate
            info["wordcount"] = str(story.word_count / story.chapter_count) + " (Likely an overestimate)"

        split_text = chapter.text.split("\n")
        for i in split_text:
            # We can assume that there isn't going to be a prompt more than 80
            # characters long, right? They can get quite long...
            if self.prompt_re.match(i.lower()) and len(i) < 80:
                info["o_prompts"] += [i]
            
        return info

    def get_embed(self, info):
        """Returns an embed for a given fic id and chapter, as long as it is for
        Quidditch League
        """
        if info["forql"]:
            # I think this is for Quidditch League
            emb = Embed(
                title=info["title"], 
                url=info["url"], 
                description=info["story"].description
            )
            emb.set_author(name=info["author"].username, url="https://www.fanfiction.net/u/" + str(info["story"].author_id))
            emb.set_footer(text="Season " + info["season"] + ", " + info["round"])
            emb.add_field(name="Wordcount", value=info["wordcount"], inline=True)
            emb.add_field(name="Team", value=info["team"], inline=True)
            emb.add_field(name="Position", value=info["position"], inline=True)
            if len(info["o_prompts"]) > 0:
                emb.add_field(name="Prompts", value=", ".join(info["o_prompts"]), inline=False)
            return emb
        else:
            return None

    @commands.command(hidden=True)
    async def ql(self, ctx, id, chapter):
        """
            Takes an input and tries to get what the the season, round, prompts,
            word count, position, team
        """
        # Only permissible in Omnioculars channel
        if ctx.guild.id == 798284145356046346 and ctx.channel.id != 809165162417750106:
            await ctx.send("Bot commands not allowed here! Please do in #omnioculars!")
            return
        info = await self.get_ql_fic(id, chapter)
        emb = self.get_embed(info)
        if emb != None:
            await ctx.send(embed=emb)
        else:
            await ctx.send("Does not look like a Quidditch League fic")
