import asyncio
import datetime
from collections import Counter
from praw.models import Submission, Comment
from praw.reddit import Reddit
from pyhocon.config_tree import ConfigTree

from models import UserStat


async def fetch_comments(submission: Submission) -> list[Comment]:
    submission.comments.replace_more(limit=None)
    return submission.comments.list()


async def process_post(submission: Submission, cutoff_timestamp: int,
                       post_authors: Counter, comment_authors: Counter) -> None:
    if submission.created_utc >= cutoff_timestamp:
        if submission.author:
            post_authors[submission.author.name] += 1

        comments = await fetch_comments(submission)
        for comment in comments:
            if comment.author:
                comment_authors[comment.author.name] += 1


async def get_subreddit_posts(subreddit_name: str,
                              reddit_instance: Reddit,
                              days: int) -> tuple[list[UserStat], list[UserStat]]:

    subreddit = reddit_instance.subreddit(subreddit_name)
    cutoff_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    cutoff_timestamp = int(cutoff_time.timestamp())

    post_authors = Counter()
    comment_authors = Counter()

    submissions = subreddit.new(limit=1000)

    tasks = []
    for submission in submissions:
        tasks.append(process_post(submission, cutoff_timestamp,
                                  post_authors, comment_authors))

    await asyncio.gather(*tasks)

    top_posters = [UserStat(username=user, count=count) for user, count in post_authors.most_common(10)]
    top_commenters = [UserStat(username=user, count=count) for user, count in comment_authors.most_common(10)]

    return top_posters, top_commenters


def get_reddit_instance(config: ConfigTree) -> Reddit:
    return Reddit(
        client_id=config.get('reddit.client_id'),
        client_secret=config.get('reddit.client_secret'),
        user_agent=config.get('reddit.user_agent')
    )


async def run(config: ConfigTree, reddit: Reddit) -> None:
    subreddit_name: str = input(f"Enter subreddit name (default: {config.get('subreddit.default_name')}): ")

    try:
        top_posters, top_commenters = await get_subreddit_posts(subreddit_name,
                                                                reddit,
                                                                days=config.get('subreddit.days'))

        print("\nTop users by number of posts:")
        for rank, user_stat in enumerate(top_posters, start=1):
            print(f"{rank}. {user_stat.username}: {user_stat.count} posts")

        print("\nTop users by number of comments:")
        for rank, user_stat in enumerate(top_commenters, start=1):
            print(f"{rank}. {user_stat.username}: {user_stat.count} comments")

    except Exception as e:
        print(f"Error: {e}")
