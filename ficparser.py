
from discord.ext import commands
from discord import Embed
from ff.fiction import Story, Chapter, User
import re

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

    def get_ql_fic(self, id, chap):
        print("Getting story " + str(id))
        story = Story(id=int(id))
        story.download_data()
        author = User(id=story.author_id)
        author.download_data()
        print("Getting chapter " + str(chap))
        chapter = Chapter(story_id=story.id, chapter=int(chap))
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
        
        print("Checking for QL")
        for i in ["qlfc", "quidditch league"]:
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

        print("Checking for team")
        lowest_pos = len(r_text)
        for i in self.teams:
            pos = r_text.find(i.lower())
            if pos != -1 and pos < lowest_pos:
                lowest_pos = pos
                info["team"] = i

        pos = r_text.find("round ")
        info["round"] = chapter.text[pos:].split("\n")[0]

        # The vast majority of people go
        # Word Count: nnnn
        pos = r_text.find("word count")
        if pos != -1:
            pos += 10
            local = r_text[pos:]
            pos = local.find(":")
            if pos != -1:
                info["wordcount"] = local[pos+1:].split()[0].strip()
        pos = r_text.find("wordcount")
        if pos != -1:
            pos += 9
            local = r_text[pos:]
            pos = local.find(":")
            if pos != -1:
                info["wordcount"] = local[pos+1:].split()[0].strip()
        
        if info["wordcount"] == "Unknown":
            # It wasn't an easy check, let's estimate
            info["wordcount"] = str(story.word_count / story.chapter_count) + " (Likely an overestimate)"

        split_text = chapter.text.split("\n")
        for i in split_text:
            if self.prompt_re.match(i.lower()):
                info["o_prompts"] += [i]
            
        return info

    @commands.command()
    async def ql(self, ctx, id, chapter):
        """
            Takes an input and tries to get what the the season, round, prompts,
            word count, position, team
        """
        info = self.get_ql_fic(id, chapter)
        if info["forql"]:
            # I think this is for Quidditch League
            emb = Embed(title=info["title"], url=info["url"])
            emb.add_field(name="author", value="by " + info["author"].username, inline=False)
            emb.add_field(name="fic-description", value=info["story"].description, inline=True)
            await ctx.send(embed=emb)
