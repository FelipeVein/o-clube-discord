import arrow
import asyncio
import os
import requests
import re

from discord import File
from discord.ext.commands import Cog, command
from models import session, Messages



images_folder = 'data/saved-images'

url_regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

reactions_dict = {
    u'\U0001F448': -1,
    u'\U0001F449': 1
}


def setup(bot):
    """COG Setup."""
    bot.add_cog(SaveMessage(bot))


class SaveMessage(Cog):
    def __init__(self, bot):
        self.bot = bot
        if(not os.path.isdir(images_folder)):
            os.mkdir(images_folder)
        self.id_image_list = None
        self.messages = None
        self.reactions = [u'\U0001F448', u'\U0001F449']
        self.current_id = 0
        self.ctx = None




    @command(name="salva-ai")
    async def save_message(self, ctx):
        if ctx.message.reference:
            
            user_id = ctx.message.author.id
            user_name = ctx.message.author.name

            original = await ctx.fetch_message(id=ctx.message.reference.message_id)
            
            # Data for database
            text = original.content
            created_at = original.created_at
            sender_id = original.author.id
            sender_name = original.author.name
            image_path = ""
            has_image = False
            has_url = False
            
            if(re.findall(url_regex, text)):
                has_url = True
            
            if(text):
                print(f"{text}")

            # get image url, download and save 
            attachments = original.attachments
            
            if(attachments):
                for att in attachments:
                    url = att.url
                    id = att.id
                    has_image = True
                    # file extension
                    ext = url.split('.')[-1]

                    image_path = "{}/{}-{}.{}".format(images_folder, user_name, id, ext)
                    #            "{}/{}-{}-{}.{}".format(images_folder, user_name, id, created_at, ext)
                    
                    response = requests.get(url)
                    #with open(, "wb") as f:
                    with open(image_path, "wb") as f:
                        f.write(response.content)

                        
            message = Messages(
                user_id = user_id,
                user_name = user_name,
                sender_id = sender_id,
                sender_name = sender_name,
                text = text,
                image_path = image_path,
                created_at = created_at,
                has_image = has_image,
                has_url = has_url
                )
            session.add(message)
            session.commit()

            if(has_image):
                await ctx.reply(f"Imagem salva!")
            else:
                await ctx.reply(f"Mensagem salva!")



    async def send_list_messages(self):
        if(self.messages[self.current_id].image_path):
            self.id_image_list = await self.ctx.reply("**{}:** *{}* \n\n{}\n\n\u2800".format(self.messages[self.current_id].sender_name, self.messages[self.current_id].created_at.to('America/Sao_Paulo'), self.messages[self.current_id].text),
                file=File(self.messages[self.current_id].image_path))
        else:
            self.id_image_list = await self.ctx.reply("**{}:** *{}* \n\n{}\n\n\u2800".format(self.messages[self.current_id].sender_name, self.messages[self.current_id].created_at.to('America/Sao_Paulo'), self.messages[self.current_id].text),
                file=None)

        for react in self.reactions:
            await self.id_image_list.add_reaction(react)
    
    def change_current_id(self, reaction):
        self.current_id += reactions_dict[reaction.emoji]
        if(self.current_id >= len(self.messages)):
            self.current_id = 0
        if(self.current_id < 0):
            self.current_id = len(self.messages)-1

    @command(name="listar-mensagens")
    async def list_messages(self, ctx):
        self.messages = session.query(Messages).all()
        self.id_image_list = None
        if(self.messages):
            self.ctx = ctx
            await self.send_list_messages()

    @Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if(not user.bot):
            self.change_current_id(reaction)
            await self.id_image_list.delete()
            await self.send_list_messages()
