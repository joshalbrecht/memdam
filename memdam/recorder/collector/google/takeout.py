
#TODO: also, intense bullshit from google--their new google hangouts crap breaks imap chat history
#so now I need to synch with takeout or something similarly insane
#done. stupid google.
#which delivers us some crazy json format and should be dealt with in an entirely other collector.

#for parsing:
#https://bitbucket.org/dotcs/hangouts-log-reader

#NOTE: a bunch of features would make this easier:
#want to be able to define a BUNCH of schedules for a single extractor (eg, because this one gets so much different data, and you want to download all chats every day, but not all youtube videos necessarily)
#youtube videos might be once per week, or once per month, or even totally manual
#and having totally manual collectors doesn't seem wholly unreasonable
#will need to have a common log-in / authorization place for all of them though...
#both totally manual collectors, and the log in info above, require a human to actually be present
#figuring out how to work with that is a bit tricky
#maybe there should be a set of tasks that the human has to accomplish, in some queue
#both things like "enter google account info" and "enter 2-factor account information" might be tasks
#hopefuly the one would depend on the other, and multiple requestors would only make a single task
#although I guess in this case, each could use a different mechanism (xoauth, 2-factor app codes, raw logins)
