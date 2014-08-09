import praw
import time
import sqlite3
import rottentomatoes
import urllib2
import datetime
import traceback

'''USER CONFIGURATION'''

USERNAME = ""
# This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD = ""
#This is the bot's Password.
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = []
#This is the word you want to put in reply
MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 30
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.

try:
    import bot

    USERNAME = bot.getUsername()
    PASSWORD = bot.getPassword()
    USERAGENT = bot.getUseragent()
    SUBREDDIT = bot.getSubreddit()
except ImportError:
    pass

sql = sqlite3.connect('sql.db')
print "Loaded SQL DB"
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
print "SQL table Loaded"
sql.commit()



def main():
    WAITS = str(WAIT)

    r = praw.Reddit(USERAGENT)
    r.login(USERNAME, PASSWORD)

    running = True
    while running:
        try:
            botloop(r)
        except Exception as e:
            print "An error has occured: %s" % e
        except KeyboardInterrupt:
            running = False
        print('Running again in ' + WAITS + ' seconds \n')
        sql.commit()
        time.sleep(WAIT)


#end of main()

def isBotSummoned(text):
    botname = '/u/' + USERNAME
    if botname in text.lower():
        return True
    return False


def botloop(r):

    #Setup subreddits
    if str(SUBREDDIT[0]) != 'all':
        combined_subs = ('%s') % '+'.join(SUBREDDIT)
        print('Looking at the following subreddits: "' + combined_subs + '".')
    else:
        comments = praw.helpers.comment_stream(r, 'all', limit=None)
        print('Looking at r/all.')

    # Comments are read here
    if str(SUBREDDIT[0]) != 'all':
        subr = r.get_subreddit(combined_subs)
        comments = subr.get_comments(limit=MAXPOSTS)

    for comm in comments:
        pid = comm.id
        try:
            pauthor = comm.author.name
        except AttributeError:
            pauthor = '[DELETED]'
        cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
        if not cur.fetchone():

            cbody = comm.body.lower()

            if isBotSummoned(cbody):
                bodysplit = cbody.split('\n\n')
                text = ''
                for line in bodysplit:
                    if isBotSummoned(line):
                        movie_title = parse_movie(line)
                        text += build_reply(movie_title)

                text = add_signature(text)
                print text
                replyto(comm,text)
                cur.execute('INSERT INTO oldposts VALUES(?)', [pid])

def parse_movie(comment):
    text = comment.lower()
    begin = text.find('/u/' + USERNAME) + len('/u/' + USERNAME)
    text = text[begin:]

    if '"' in text:
        splitText = text.split('"')
        quotes = find_quoted_titles(text)
        #Extract the quoted titles and split the others by ','
        res = []
        for item in splitText:

            #needs to be split
            if item != ' ' and item != '' and not (item in quotes):
                tmp = item.split(',')
                for title in tmp:
                    if title != ' ' and title != '':
                        res.append(title)
            #quoted title
            elif item != ' ' and item != '':
                res.append(item)
    else:
        res = text.split(',')

    #Remove leading and trailing spaces
    for i in range(0, len(res), 1):
        title = res[i]
        if title[0] == ' ':
            res[i] = title[1:]
            title = res[i]
        if title[len(title) - 1] == ' ':
            res[i] = title[0:len(title) - 1]

    return res


#returns a list of movie titles that were in quotes in the text string
def find_quoted_titles(text):
    start = -1
    end = -1
    quotes = []
    for i in range(0, len(text), 1):
        if text[i] == '"' and start == -1:
            start = i + 1
        elif text[i] == '"' and start != -1:
            end = i
        if start != -1 and end != -1:
            quotes.append(text[start:end])
            start = -1
            end = -1
    return quotes

def build_reply(minput):
    text = ''
    Flag=True
    rt=rottentomatoes.RT()

    print('Movie Found: "' + minput[0] + '".')

    try:
        mov=rt.search(minput[0], page_limit=1)

        if len(mov)!=0:
            if mov[0]['ratings']['critics_score']==-1:
                text += ('* ' + mov[0]['title'] + ' - Rotten Tomatoes Score: ' + str(0) + '%\n')
            text += ('* ' + mov[0]['title'] + ' - Rotten Tomatoes Score: ' + str(mov[0]['ratings']['critics_score']) + '%\n')
        else:
            text += ('* ' + minput[0] + 'not found\n')

    except urllib2.HTTPError, err:
        # 400 error code generally means invalid query structure
        if err.code == 400:
            print 'Something went wrong with the query:'
            print minput
        text += '* ' + minput[0] + ' not found or Rotten Tomatoes is down\n'

    text += '\n\n' + ('_' * 25) + '\n'

    return text

def add_signature(text):
    text += 'NOTE: BOT IS IN BETA!! Availability not guaranteed\n\n'
    text += 'How to use botrt. (/u/botrt <Movie Name> eg: /u/botrt The Matrix)\n\n'
    text += '*Note: Titles or names must match exactly, but capitalization does not matter.*\n\n'
    text += "PM for Feedback /u/kingk89 | [Source](https://github.com/harvinb/botrt) | This bot uses the [Rotten Tomatoes API](http://developer.rottentomatoes.com/)"
    return text

#replies to given comment
def replyto(c, text):
    now = datetime.datetime.now()
    c.reply(text)
    print 'ID:', c.id, 'Author:', c.author.name, 'r/' + str(c.subreddit.display_name), 'Title:', c.submission.title
    print now.strftime("%m-%d-%Y %H:%M"), '\n'

    #print text

#call main function
main()




