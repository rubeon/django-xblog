from html2text import html2text
from textstat import textstat
import logging

logger = logging.getLogger(__name__)

def calculate_readability(post):
    """
    requires an xblog.Post object to work properly (or anything really that 
    implements a "get_full_body" function)
    """
    full_text = post.get_full_body()
    text = html2text(full_text)
    res = {}
    try:
        res['flesch_reading_ease'] = textstat.textstat.flesch_reading_ease(text)
        res['smog'] = textstat.textstat.smog_index(text)
        res['coleman_liau'] = textstat.textstat.coleman_liau_index(text)
        res['flesch_kincaid_grade'] = textstat.textstat.flesch_kincaid_grade(text)

    except Exception as e:
        import traceback, sys
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.warn(e)
        logger.debug(text)
        traceback.print_tb(exc_traceback)
        print(e)
        res = {}
    return res

def main(test_data):
    print(textstat.textstat.flesch_reading_ease(test_data))
    print(textstat.textstat.smog_index(test_data))
    print(textstat.textstat.flesch_kincaid_grade(test_data))
    print(textstat.textstat.coleman_liau_index(test_data))
    print(textstat.textstat.automated_readability_index(test_data))
    print(textstat.textstat.dale_chall_readability_score(test_data))
    print(textstat.textstat.difficult_words(test_data))
    print(textstat.textstat.linsear_write_formula(test_data))
    print(textstat.textstat.gunning_fog(test_data))

if __name__ == '__main__':
    test_data = """Man oh man, these politicians have gotten my blood all angried up. I mean, how
can you socialize health care with a 50.3% majority? Doesn't something like
that at least deserve some _consensus?_

But this is what I'm talking about. This kind of shit keeps me up nights. _And
I've already got socialized medicine!_ So why in the world would it bother me?

And so, to get away from it all, I decided to go into the office today and
knock out some backlog. A rare warm and sunny Sunday, which started out with
the classic Sunday Roast in an English countryside pub, ended as weekdays do:
with me pissed off in the office, wondering how the hell it all got away from
me.

Obviously, Rube needs a hobby. Something to direct all this anger into. So,
here are a few ideas, just off the top of my head:

  * **Bowling**
Bowling is...fun. But I can't say as I've ever really caught the fever, so to
speak. I think it's the fact that most people who hang around in bowling
alleys are scum.

  * **Pool hustling**
You get a better class of ne'er-do-well in pool halls than you do in bowling
alleys. I'll even accept the fact that you can't smoke inside anymore.
Nevertheless, this one's out. I used to think I was good at pool, until I got
my ass handed to me steadily by that no-account shark,
[Eric](http://straightwhiteguy.com/) . The limiter for me here is the lack of
raw talent.

  * **Juggling**
Juggling is one of those things I can do but can't explain why. I'm not a good
juggler, mind you, but I can keep three going for a few rounds. I guess I
could try to become an expert juggler, but probably lack the requisite
dexterity, and I most certainly I lack the dedication. The payoff here is
minimal.

  * **Stupid cigarette tricks (advanced)
I can do the following tricks already: the quick-snap; the single-loop toss-
and-catch; the single smoke-ring. All of these I can hit with about a 60%
success rate. It's a fine hobby, I guess, except for the fact that _it will
fucking KILL me._ So that's out.**

  * **Blogging**
Now we're talking. Maybe I should take up blogging again?"""
    # test_data = "I think there are 50 ways to leave your lover..."
    main(test_data)
    
