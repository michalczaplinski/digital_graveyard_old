import TwitterAPI, re, time, logging, os.path, unicodedata, sqlite3, os
from Queue import Queue

##  Logging
logger = logging.getLogger("__main__")
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler('digital_graveyard.log', delay=True)
format = logging.Formatter('%(levelname)s  %(asctime)s : %(message)s')
fh.setFormatter(format)

ch = logging.StreamHandler()
ch.setFormatter(format)

logger.addHandler(fh)
logger.addHandler(ch)


def get_names_from_files():
    ''' Get the list of first names and last names from the files on disk. '''

    with open('firstnames.txt', 'r') as f:
        first_names = [ x.strip('\n') for x in f.readlines() ]
    with open('lastnames.txt', 'r') as l:
        last_names  = [ x.strip('\n') for x in l.readlines() ]
    with open('honorifics.txt', 'r') as h:
        honorifics  = [ x.strip('\n') for x in h.readlines() ]
    return first_names, last_names, honorifics


def connect_to_streaming_API():
    ''' Connect to twitter streaming API
        Returns an iterator with all the stream data. '''

    api = TwitterAPI.TwitterAPI(
            'f8olfZWtAPvgANdP9qecg',
            'bSEnCXJuWazjT8S8hZ6BLWMo1C7egIKNgjObHM6Ck',
            '1726636778-jEn4qUAj2wV60ckbskNSbLJgTRr0c7hiemVOU7x',
            'UgwEfM3cukoWIxCWjCiIZiJ0gnQVGH9U42WLfJjnEFODw')

    r = api.request('statuses/filter', {'track': '#rip'})

    return r.get_iterator()


def is_retweet(text):
    ''' Checks if the text starts with RT (indicating a retweet)  '''
    if text.startswith('RT'):
        return True
    else:
        return False


def remove_user_mentions(text):
    ''' Removes user mentions from the tweet text '''

    text = re.sub('\s@[a-zA-Z_]*', ' ', text)
    return text


def clean_up_name(name):

    # get rid of newlines
    name = name.rstrip()

    # if it's an initial and not a name, do not clean up
    if re.match('[A-Z]\.(?=\s|$)', name):
        return name

    # get rid of some punctuation
    name = name.strip('()",.! ')

    # catch names ending with 's
    if name.endswith('\'s'):
        name.rstrip('\'s')

    return name


def precheck_text(text):
    ''' Checks the tweet text for a number of patterns
        before checking for a name from the list.
        Currently checking for "my" <something> "passed away", etc. '''

    # looks for the "my" <sth> "died" pattern
    for phrase in ['died', 'passed away', 'is dead', 'gone']:
        regex = '(\s|^)([mM]y.*)' + ' ' + phrase + '[ \.,;:!\?]'
        match = re.search(regex, text)
        if match is not None:
            name = match.group(2)  # group 2 is between the begining and the <phrase>
            if len(name.split()) <= 2:  # check if <name> is less than 2 words
                return name
    else:
        return None


def get_the_rest(name, text):
    ''' Cuts off the part of the string 'text' up until the end of the name '''

    m = re.search(name, text)
    try:
        rest_of_text = text[m.end(0)+1:]
    except StandardError as e:
        logger.error(e)
        print 'name:', name
        print 'text', text
        print 'regex result', m
    return rest_of_text


def look_for_first_name(text, first_names, honorifics):
    ''' Recursively check every word of the tweet text for the name.
        If the text contains a name that is specified in first_names returns the name.
        Otherwise returns None. '''

    #split the string into two parts at the first occurence of whitespace
    split_text = text.split(None, 1)

    # check if we are on the last word
    try:
        remaining_text = split_text[1]
    except IndexError:
        return None

    candidate_name = split_text[0]
    #candidate_name = clean_up_name(candidate_name)

    # if we encounter an honorific, look ahead to the next word, see if it's a name
    if candidate_name in honorifics:

        second_word = remaining_text.split()[0]
        second_word = clean_up_name(second_word)

        # find the first word in remaining_text
        if second_word in first_names:
            name = candidate_name + ' ' + second_word
            return name

        else:
            return None

    elif candidate_name in first_names:
        return candidate_name
    else:
        # Run again for the rest of the tweet, unless it's the end of the tweet.
        return look_for_first_name(remaining_text, first_names, honorifics)


def get_full_name_from_tweet_text(name, text, name_so_far, first_names, last_names):
    '''
    Runs recursively.
    First, we get the first word from the remaining text.
    Second, we check if it's in the list of first or last names.
    If so, append to the name and repeat from step one.
    '''

    the_rest        = get_the_rest(name, text)
    candidate_name  = the_rest.split(' ', 1)[0]
    candidate_name  = clean_up_name(candidate_name)

    if candidate_name in first_names or candidate_name in last_names:
        name_so_far += ' ' + candidate_name
        return get_full_name_from_tweet_text(candidate_name, the_rest, name_so_far, first_names, last_names)
    else:
        return name_so_far


def get_latest_tweets(stream):
    ''' The core function.
        Returns a 4-tuple:
        (time of the tweet, the extracted name, the full text of
            the tweet and the the username of the person tweeting). '''

    first_names, last_names, honorifics = get_names_from_files()

    for s in stream:

        text, time, user = s['text'], s['created_at'], s['user']['screen_name']

        cleaned_up_text = remove_user_mentions(text)

        tweet = {'text': text, 'time': time, 'user': user, 'name': None, 'retweet': 0}

        if is_retweet(cleaned_up_text):
            tweet['retweet'] = 1

        # check for the 'My' <somethingsomething> 'died', etc. pattern
        name = precheck_text(cleaned_up_text)
        if name is not None:
            tweet['name'] = name
            yield tweet

        # find a full name
        name = look_for_first_name(cleaned_up_text, first_names, honorifics)
        if name is not None:
            name_from_tweet = get_full_name_from_tweet_text(name, cleaned_up_text, name, first_names, last_names)
            tweet['name'] = name_from_tweet
            yield tweet


def save_tweet_to_db(tweet, database):
    tweet_values = tweet['text'], tweet['user'], tweet['time'], tweet['name'], tweet['retweet']
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('INSERT INTO tweet (text, user, time, name, retweet_status) VALUES (?,?,?,?,?)', tweet_values)
    conn.commit()
    conn.close()


def print_tweet(tweet):
    # name = unicodedata.normalize('NFKD', name).encode('ascii','ignore')
    print tweet['time'], '\n', tweet['name'], '\n', tweet['text'], '\n', tweet['user'], '\n\n'


def main():

    database = os.path.join(os.getenv('OPENSHIFT_DATA_DIR'), 'tweets.db')
    stream = connect_to_streaming_API()
    tweets = get_latest_tweets(stream)
    for tweet in tweets:
        save_tweet_to_db(tweet, database)
        print_tweet(tweet)


if __name__ == '__main__':
    main()

# big_dict = {}
# for item in items:
#     text = item[0]
#     user = item[1]

#     if not item[2]:
#         big_dict[text] = [user]
#     elif text not in big_dict:
#         big_dict[text] = [user]
#     else:
#         big_dict[text].append(user)


# look for a more common name w pierwszej kolejnosci (so that if there is a word
# in the tweet text that is identical to a name the ACTUAL name would get selected)

# reconnecting wrapper

# retweet get the same name (same grave)




