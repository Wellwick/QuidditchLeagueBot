
from discord.ext import commands
from ff.fiction import Story, Chapter, User

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
        self.replacements = [
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
        ]

    def get_ql_fic(self, id, chapter):
        story = Story(id=int(id))
        story.download_data()
        author = User(id=story.author_id)
        author.download_data()
        chapter = Chapter(story_id=story.id, chapter=int(chapter))
        # Now we have the information, it's time to get processing
        c_text = chapter.text.lower()
        for i in self.replacements.keys():
            c_text = c_text.replace(i, self.replacements[i])
        info = {
            "forql": False,
            "title": story.title,
            "url": story.url + "/" + str(chapter),
            "season": "9",
            "round": "Unknown",
            "position": "Unknown",
            "team": "Unknown",
            "m_prompt": "Unknown",
            "o_prompts": [],
            "wordcount": "Unknown"
        }
        lowest_pos = len(c_text)
        
        for i in ["qlfc", "quidditch league"]:
            if i in c_text:
                info["forql"] = True

        if not info["forql"]:
            return info

        for i in self.positions:
            pos = c_text.find(i.lower())
            if pos != -1 and pos < lowest_pos:
                lowest_pos = pos
                info["position"] = i
            
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
            await ctx.send("I think this fic is for Quidditch League\n" + str(info))
