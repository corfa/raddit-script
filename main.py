import asyncio
from praw.reddit import Reddit
from pyhocon.config_tree import ConfigTree
from pyhocon import ConfigFactory


from utils import run, get_reddit_instance


async def main():
    config: ConfigTree = ConfigFactory.parse_file('config.conf')
    reddit: Reddit = get_reddit_instance(config)
    await run(config, reddit)


if __name__ == "__main__":
    asyncio.run(main())
