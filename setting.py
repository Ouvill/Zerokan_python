#-*- coding: utf-8 -*-
import tweepy
import webbrowser

OUTPUT_FILE="setting.ini"

def twitterOnOff():
    global TwitterFunction
    yesno = raw_input("Do you want to enable Twitter ? (yes/no)")
    if yesno == "yes":
        TwitterFunction = True
    elif yesno == "no":
        TwitterFunction = False

        f = open(OUTPUT_FILE,'w')
        f.write("[DEFAULT]\n")
        f.write("NAME="+NAME+"\n")
        f.write("DATA=data.csv"+"\n")
        f.write("TwitterFunction="+str(TwitterFunction)+"\n" )
        f.close()
        print("complete setting !")

        exit(0)
    else:
        print("error:input yes or no")
        twitterOnOff()


NAME = raw_input("Input your name:")

twitterOnOff()
TwitterName = NAME

consumer_key = "3gs1JRC9ikUCkppthko3QI32T"
consumer_secret = "QPOz40YMGLPFoBxwwNKh6nGOwiPUPi7Jq14jshE4OuLpqMOptN"
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
print ("Access:")
url =  auth.get_authorization_url()
webbrowser.open(url)
verifier = raw_input('input PIN code:')
auth.get_access_token(verifier)

AT = auth.access_token
AS = auth.access_token_secret

f = open(OUTPUT_FILE,'w')
f.write("[DEFAULT]\n")
f.write("NAME="+NAME+"\n")
f.write("DATA=data.csv\n")
f.write("TwitterFunction="+str(TwitterFunction) + "\n" )
f.write("TwitterName="+TwitterName + "\n")
f.write("AT="+AT + "\n")
f.write("AS="+AS + "\n")
f.close()

print("complete setting !")
exit(0)
