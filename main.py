from interactions import Client, Intents, listen
from core.extensions_loader import load_extensions

bot = Client(intents=Intents.DEFAULT)


# intents are what events we want to receive from discord, `DEFAULT` is usually fine

@listen()  # this decorator tells snek that it needs to listen for the corresponding event, and run this coroutine
async def on_ready():
    # This event is called when the bot is ready to respond to commands
    print("Ready")
    print(f"This bot is owned by {bot.owner}")

# load all extensions in the ./extensions folder
load_extensions(bot=bot)

with open('config.txt') as f: token = f.readline()

bot.start(token)
