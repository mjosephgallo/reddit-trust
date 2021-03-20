# Reddit Trust
A python script that generates a report on one or more subreddits. Reports are presented in a PDF document.

The report provides the following data visuals:
- Cover Page with summary details
- Account Creation Dates of Authors in the Top Submissions
- Authors With the Most Submissions
- Most Used Sources in Top Submissions
- Submission Titles Wordcloud
- Submission Comments Wordcloud

## Purpose
The goal of reddit-trust is to break down and analyze the activity of a particular subreddit or subreddits.

## Usage
```
reddit-trust.py <subreddit> <timeframe> <--comments>
```
Examples
```
reddit-trust.py bettafish year
reddit-trust.py news+videos month
reddit-trust.py redditdev
reddit-trust.py bettafish year --comments
```
