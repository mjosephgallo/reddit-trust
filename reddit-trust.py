from wordcloud import WordCloud, STOPWORDS
from urllib.parse import urlparse 
from collections import Counter
from configparser import ConfigParser
from datetime import datetime

import psaw
import praw
import string
import pylab
import datetime as dt
import pandas as pd
import matplotlib.pyplot as plt 
import matplotlib.backends.backend_pdf as backend_pdf

cp = ConfigParser()
cp.read('./praw.ini')

def parse_args(argv):
    import argparse
    parser = argparse.ArgumentParser(
        description='Analyze a subreddit\'s most popular authors, submission titles and comments.')
    parser.add_argument('subreddit', type=str, nargs='?', help='Subreddit name')
    parser.add_argument('timeframe', default='day', type=str, nargs='?', choices=['day', 'month', 'year','all'],
        help='The timeframe of top posts that are analyzed. Defaults to the last day')
    args = parser.parse_args(argv)
    return args

# Converts passed timeframe argument into a value for digestion by psaw/pushshift
def psaw_time_converter(timeframe):
    time_d = 1
    if timeframe == 'week':
        time_d = 7
    elif timeframe == 'month':
        time_d = 30
    elif timeframe == 'year':
        time_d = 365
    elif timeframe == 'all':
        time_d = None
    return time_d

def timestamp():
    return datetime.now().strftime("%Y/%m/%d %H:%M:%S")

def plot_img(sub_data,plot_func,pdf):
    plot = plot_func(sub_data)
    plt.tight_layout()
    pdf.savefig(plot)
    plt.close(plot)

def main(argv):
    args = parse_args(argv)
    reddit = praw.Reddit(client_id=cp['bot']['client_id'],
        client_secret=cp['bot']['client_secret'],
        user_agent='Reddit Trust Data Analyzer')
    # psaw_client = psaw.PushshiftAPI(reddit)
    print("{} - Collecting Subreddit Data".format(timestamp()))
    praw_data = top_submissions(reddit, args.subreddit, args.timeframe)
    # psaw_data = top_submissions_psaw(psaw_client, args.subreddit, psaw_time_converter(args.timeframe))
    print("{} - Generating Report".format(timestamp()))
    with backend_pdf.PdfPages("{}.pdf".format(datetime.now().strftime("%Y%m%d_%H%M%S"))) as pdf:
        plt.figure()
        plt.axis('off')
        plt.text(0.5,0.5,"Reddit Trust Report\n/r/{}\nSubmission data: past {}\nTotal submission objects analyzed: {}".format(args.subreddit,args.timeframe,len(praw_data)),ha='center',va='center')
        pdf.savefig()
        plt.close()

        print("{} - Plotting age of author accounts".format(timestamp()))
        age_plot = accts_age_plot(praw_data)
        plt.tight_layout()
        pdf.savefig(age_plot)
        plt.close(age_plot)

        print("{} - Plotting number of posts by author".format(timestamp()))
        count_plot = accts_count_plot(praw_data)
        plt.tight_layout()
        pdf.savefig(count_plot)
        plt.close(count_plot)

        print("{} - Plotting top links".format(timestamp()))
        links = top_links_plot(praw_data)
        plt.tight_layout()
        pdf.savefig(links)
        plt.close(links)

        print("{} - Creating title wordcloud".format(timestamp()))
        titles = titles_wordcloud(praw_data)
        plt.tight_layout()
        pdf.savefig(titles)
        plt.close(titles)

        print("{} - Creating comment wordcloud".format(timestamp()))
        comments = comments_wordcloud(praw_data)
        plt.tight_layout()
        pdf.savefig(comments)
        plt.close(comments)
        
        print("{} - Report Complete".format(timestamp()))

# Returns a list of top submissions from a subreddit in a time frame, sorted by submission score
def top_submissions(praw_client, sub_name, timeframe):
    sub_data = [subm for subm in praw_client.subreddit(str(sub_name)).top(str(timeframe),limit=None)]
    sub_data.sort(key=lambda x: x.score, reverse=True)
    return sub_data

# Returns top perc of posts in given time_d timeframe (days from today) sorted by score
def top_submissions_psaw(psaw_client, sub_name, time_d, perc=100):
    """
    type(sub_name) str
    type(time_d) str - pushshift value
    type(perc) float
    Return list[praw submission objects]
    
    Returns top perc of posts in given time_d timeframe sorted by score
    """
    if time_d == None:
        gen = psaw_client.search_submissions(subreddit=sub_name)
    else:
        gen = psaw_client.search_submissions(subreddit=sub_name,after=time_d)
    sub_data = list(gen)
    sub_data.sort(key=lambda x: x.score, reverse=True)
    return sub_data[:(perc*.01*len(sub_data))]

# Accepts list of reddit submission objects
# Returns a list of dictionary objects containing submission author's name and account creation date
def accts_age(sub_data):
    date_plot = []
    for subm in sub_data:
        try:
            if subm.author is not None and hasattr(subm.author,'created_utc'):
                date_plot.append({
                    'Name': subm.author.name,
                    'Date': subm.author.created_utc
                })
        except:
            continue
    return date_plot
    
# Accepts list of reddit submission objects
# Returns a line graph of authors of the top submissions and their account creation date
def accts_age_plot(sub_data):
    date_plot = accts_age(sub_data)
    df = pd.DataFrame([i for n,i in enumerate(date_plot) if i not in date_plot[n + 1:]])
    
    df['Date'] = pd.to_datetime(df['Date'],unit='s')
    x = df['Name'].groupby([df['Date'].dt.year,df['Date'].dt.month]).agg('count')
    gph = x.plot(x=x.index,y=x.values,title='Account Creation Dates of Authors of Top Submissions')
    gph.set_xlabel("Date Created")
    gph.set_ylabel("Number of Accounts")
    ya = gph.get_yaxis()
    ya.set_major_locator(pylab.MaxNLocator(integer=True))
    z = gph.get_figure()
    return z

# Accepts list of reddit submission objects
# Returns a list of account/author names from each submission
def accts_name(sub_data):
    accts = []
    for subm in sub_data:
        try:
            if subm.author is not None:
                accts.append(subm.author.name)
            else:
                accts.append('[deleted]')
        except:
            continue
    return accts
            
# Accepts list of reddit submission objects
# Returns a graph of top ten authors with the most submissions in the passed data structure
def accts_count_plot(sub_data):
    # author_counts = pd.DataFrame([x.author.name for x in sub_data if x.author != None])
    author_counts = pd.DataFrame(accts_name(sub_data))
    x = author_counts[0].groupby(author_counts[0]).agg('count')
    x = x.sort_values(0,ascending=False).head(10)
    gph = x.plot.bar(title='Authors With the Most Submissions')
    gph.set_xlabel("Author")
    gph.set_ylabel("Number of Submissions in subreddit")
    z = gph.get_figure()
    return z

# Accepts list of reddit submission objects
# Returns a wordcloud of most used words in submission titles
def titles_wordcloud(sub_data):
    stopwords = set(STOPWORDS) 
    titles = [str(subm.title).lower() for subm in sub_data]
    all_titles = ' '.join(titles)
    wordcloud = WordCloud(width=1600, height=800,background_color ='white',stopwords=stopwords,collocations=False).generate(all_titles)
    plt.figure()
    plt.suptitle('Submission Titles Wordcloud') 
    plt.imshow(wordcloud,interpolation='bilinear') 
    plt.axis("off") 
    return plt.gcf()

# Accepts list of reddit submission objects
# Returns a list of comment strings for any top-level comments with a score greater than 10
def comments_body(sub_data):
    comments = []
    for subm in sub_data:
        subm.comments.replace_more(limit=0)
        comments.extend([comment.body for comment in subm.comments.list() if comment.score > 10])
    return comments

# Accepts list of reddit submission objects
# Returns a wordcloud of most used words in submission titles
def comments_wordcloud(sub_data):
    stopwords = set(STOPWORDS)
    comments_cache = comments_body(sub_data)
    all_comments = ' '.join(comments_cache)
    wordcloud = WordCloud(width=1600, height=800,background_color ='white',stopwords=stopwords,collocations=False).generate(all_comments)
    plt.figure()
    plt.suptitle('Submission Comments Wordcloud') 
    plt.imshow(wordcloud,interpolation='bilinear') 
    plt.axis("off") 
    return plt.gcf()

# Accepts list of reddit submission objects
# returns a list of urls used in the submissions, based on the url's network locality
def top_links(sub_data):
    urls = []
    for subm in sub_data:
        urls.append(urlparse(subm.url).netloc)
    return urls

# Accepts list of reddit submission objects
# Returns a plot of the top links used in the submissions
def top_links_plot(sub_data):
    x = pd.DataFrame(top_links(sub_data))
    x = x[0].groupby(x[0]).agg('count')
    x = x.sort_values(0,ascending=False).head(10)
    gph = x.plot.bar(title='Most Used Sources in Top Submissions')
    gph.set_xlabel("Source")
    gph.set_ylabel("Number of Submissions")
    ya = gph.get_yaxis()
    ya.set_major_locator(pylab.MaxNLocator(integer=True))
    z = gph.get_figure()
    return z


if __name__ == '__main__':
    from sys import argv
    exit(main(argv[1:]))