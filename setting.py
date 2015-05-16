#-*- coding: utf-8 -*-
import webbrowser
import requests
import webbrowser
from requests_oauthlib import OAuth1Session

OUTPUT_FILE="setting.ini"

client_key="3gs1JRC9ikUCkppthko3QI32T"
client_secret="QPOz40YMGLPFoBxwwNKh6nGOwiPUPi7Jq14jshE4OuLpqMOptN"

request_token_url = 'https://api.twitter.com/oauth/request_token'
authorization_url = 'https://api.twitter.com/oauth/authorize'
access_token_url = 'https://api.twitter.com/oauth/access_token'


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
        print("complete setting")

        exit(0)
    else:
        print("error:input yes or no")
        twitterOnOff()

def getTwitterToken():
    client_key="3gs1JRC9ikUCkppthko3QI32T"
    client_secret="QPOz40YMGLPFoBxwwNKh6nGOwiPUPi7Jq14jshE4OuLpqMOptN"


    request_token_url = 'https://api.twitter.com/oauth/request_token'
    authorization_url = 'https://api.twitter.com/oauth/authorize'
    access_token_url = 'https://api.twitter.com/oauth/access_token'

    oauth_session = OAuth1Session(client_key,client_secret=client_secret)

    # First step, fetch the request token.
    oauth_session.fetch_request_token(request_token_url)
    # Second step. Follow this link and authorize
    redirect_url = oauth_session.authorization_url(authorization_url)
    print(redirect_url)

    # Third step. Fetch the access token
    webbrowser.open(redirect_url)
    redirect_response=raw_input('Paste the full redirect URL here.')
    oauth_session.parse_authorization_response(redirect_response)

    access_token=oauth_session.fetch_access_token(access_token_url)

    return access_token




NAME = raw_input("Input your name:")

twitterOnOff()

print("get twitter authority")
access_token = getTwitterToken()

twitterName=access_token["screen_name"]
AT = access_token["oauth_token"]
AS = access_token["oauth_token_secret"]

f = open(OUTPUT_FILE,'w')
f.write("[DEFAULT]\n")
f.write("NAME="+NAME+"\n")
f.write("DATA=data.csv\n")
f.write("TwitterFunction="+str(TwitterFunction) + "\n" )
f.write("TwitterName="+twitterName + "\n")
f.write("AT="+AT + "\n")
f.write("AS="+AS + "\n")
f.close()

print("complete setting")
exit(0)
