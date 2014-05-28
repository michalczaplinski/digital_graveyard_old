import twitter, re, time, logging, os.path, unicodedata, arduino_printer


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



def connect_to_API_and_get_statuses():
    ''' Connect to twitter API and pull tweets (statuses) '''

    api = twitter.Api(consumer_key='f8olfZWtAPvgANdP9qecg',
                        consumer_secret='bSEnCXJuWazjT8S8hZ6BLWMo1C7egIKNgjObHM6Ck',
                        access_token_key='1726636778-jEn4qUAj2wV60ckbskNSbLJgTRr0c7hiemVOU7x',
                        access_token_secret='UgwEfM3cukoWIxCWjCiIZiJ0gnQVGH9U42WLfJjnEFODw')
    statuses = api.GetSearch(term='#rip', count=100, result_type='recent')
    return statuses



def is_retweet(text):
    ''' Checks if the text starts with RT (indicating a retweet)  '''

    if text.startswith('RT'):
        return True
    else:
        return False



def clean_up_tweet_text(text):
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

    # catch names ending with  's
    if name.endswith('\'s'):
        name.rstrip('\'s')

    return name



def is_name_in_text(name, text):
    ''' Checks if the string contains the name '''

    if re.search('\s+' + name + '\s', text) is not None:
        return True
    else:
        return False



def precheck_text(text):
    ''' Checks the tweet text for a number of patterns
        before checking for a name from the list
    '''

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
        Otherwise returns None.

    '''

    #split the string into two parts at the first occurence of whitespace
    split_text = text.split(None, 1)

    # check if we are on the last word in the
    try:
        remaining_text = split_text[1]
    except IndexError:
        return None

    candidate_name = split_text[0]
    #candidate_name = clean_up_name(candidate_name)

    # if we encounter an honorific, gotta look ahead to the next word, see if it's a name
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



def get_latest_tweets(include_retweets=True):
    ''' The core function.
        Returns a 3-tuple: (time of the tweet, the extracted name, the full text of the tweet)

    '''
    statuses = connect_to_API_and_get_statuses()
    first_names, last_names, honorifics = get_names_from_files()

    tweets = []

    for s in statuses:

        text = s.text
        time = s.created_at
        user = s.user.screen_name

        cleaned_up_text = clean_up_tweet_text(text)

        if include_retweets is False:
            if is_retweet(cleaned_up_text):
                continue

        # check for the 'My' <somethingsomething> 'died', etc. pattern
        name = precheck_text(text)
        if name is not None:
            tweets.append((time, name, text))

        # checks if there is a first name
        name = look_for_first_name(cleaned_up_text, first_names, honorifics)

        if name is not None:
            name_from_tweet = get_full_name_from_tweet_text(name, cleaned_up_text, name, first_names, last_names)
            tweets.append((time, name_from_tweet, text))

    return tweets



def print_tweets(tweets):

    if len(tweets) == 0:
        time.sleep(100)

    elif len(tweets) > 0:
        sleep_time = 120/len(tweets)
        for tweet in tweets:
            # name is indexed as [1], if you want another attribute  time: [0], tweet text: [2]
            name = tweet[1]
            # normalize and change to ascii
            name = unicodedata.normalize('NFKD', name).encode('ascii','ignore')
            print tweet[0]
            print tweet[1]
            print tweet[2], '\n'
            arduino_printer.show_text(name, sleep_time)

    return



def main(old_tweets = []):
    while True:

        new_tweets = get_latest_tweets()

        # x[1] bucause of the (time, name, tweet) tuple
        tweets = [ x for x in new_tweets if x not in old_tweets ]
        print_tweets(tweets)
        old_tweets.extend(new_tweets)



if __name__ == '__main__':


    while True:
        try:
            main()

        except StandardError as e:
            print 'There was an error, restarting in 3 minutes...'
            logger.exception(e)
            time.sleep(180)



    #main()


# BUGS AND ISSUES:
# - improve the find_the_first_word function (put the honorifics functionality in a separate function.)
# - investigate 'NoneType' object has no attribute 'end'
# - INCLUDE is_name_in_text function


