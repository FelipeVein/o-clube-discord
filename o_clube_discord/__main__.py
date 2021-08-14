import os

from .bot import create_bot

def main():
    bot = create_bot()

    bot.run(os.environ["DISCORD_TOKEN"])


if __name__ == "__main__":
    main()
