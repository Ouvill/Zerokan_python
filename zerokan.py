#coding:UTF-8
import subprocess
import sys
import json
import re
import requests
import time
import datetime
import locale
import csv
import ConfigParser
import os
import codecs
from requests_oauthlib import OAuth1Session

true=True
false=False

SETTING_FILE = "setting.ini"

class Player:

    def __init__(self,name):
        self.initPlayerResult()

        self.playerName = name
        self.killPattern = self.playerName + ".* shot down"
        self.lossPattern = "shot down .*" + self.playerName
        self.crashPattern = self.playerName + u".* は\t墜落しました"
        self.destroyPattern = self.playerName + ".* destroyed"
        self.destroyedPattern = "destroyed .*" + self.playerName
        self.wreckedPattern = self.playerName + ".* has been wrecked"

        self.reKillPattern = re.compile(self.killPattern)
        self.reLossPattern = re.compile(self.lossPattern)
        self.reCrashPattern= re.compile(self.crashPattern)
        self.reDestroyPattern= re.compile(self.destroyPattern)
        self.reDestroyedPattern = re.compile(self.destroyedPattern)
        self.reWreckedPattern = re.compile(self.wreckedPattern)

        print("Welcome " + self.playerName)

    # player のデータを初期化
    def initPlayerResult(self):
        self.result = {}
        self.result["killNumber"] = 0 #飛行機の撃墜数
        self.result["lossNumber"] = 0 #飛行機が撃墜された数
        self.result["crashNumber"] = 0 #飛行機が墜落(地面に激突、脱出)した数
        self.result["deathNumber"] = 0 #死んだ数(飛行機+戦車)
        self.result["destroyNumber"] = 0 #地上物破壊数
        self.result["destroyedNumber"] = 0 #戦車で死んだ数
        self.result["wreckedNumber"] = 0 #戦車で自滅(水没、脱出)した時

    def countKill(self):
        self.result["killNumber"] += 1

    def countLoss(self):
        self.result["lossNumber"] += 1
        self.result["deathNumber"] += 1

    def countCrash(self):
        self.result["crashNumber"] += 1
        self.result["deathNumber"] += 1

    def countDestroy(self):
        self.result["destroyNumber"] += 1

    def countDestroyed(self):
        self.result["destroyedNumber"] += 1
        self.result["deathNumber"] += 1

    def countWrecked(self):
        self.result["wreckedNumber"] += 1
        self.result["deathNumber"] += 1

    # WT の hudmsg/damageから プレイヤー名を探して、戦果を記録
    def countResult(self,damages):
        for damage in damages:
            print(damage["id"])

            if self.reKillPattern.search(damage["msg"]):
                print("kill count")
                self.countKill()

            if self.reLossPattern.search(damage["msg"]):
                print("loss count")
                self.countLoss()

            if self.reCrashPattern.search(damage["msg"]):
                print("crash count")
                self.countCrash()

            if self.reDestroyPattern.search(damage["msg"]):
                print("destroy count")
                self.countDestroy()

            if self.reDestroyedPattern.search(damage["msg"]):
                print("destroyed count")
                self.countDestroyed()

            if self.reWreckedPattern.search(damage["msg"]):
                print("wrecked count")
                self.countWrecked()

    # playerのデータを表示
    def printResult(self):
        print("Player's kill count",self.result["killNumber"])
        # print("Player's killed count",self.result["lossNumber"])
        # print("Player's crash count",self.result["crashNumber"])
        print("Player's destroy count",self.result["destroyNumber"])
        # print("Player's destoryed count",self.result["destroyedNumber"])
        # print("Player's wrecked count",self.result["wreckedNumber"])
        print("Player's death count",self.result["deathNumber"])

    # player のデータを書き込み
    def writeResult(self,dataFile,startTime,endTime):
        strStartTime = startTime.strftime('%Y/%m/%d-%H:%M:%S')
        strEndTime = endTime.strftime('%Y/%m/%d-%H:%M:%S')
        listResult = [strStartTime,strEndTime,self.result["killNumber"],self.result["lossNumber"],self.result["crashNumber"],self.result["destroyNumber"],self.result["destroyedNumber"],self.result["wreckedNumber"]]

        try:

            f = open(dataFile,"a")
            csvWriter = csv.writer(f,lineterminator="\n")
            csvWriter.writerow(listResult)
            f.close()
            print("save result")
        except:
            print("save miss")

class GameInfo:
    def __init__(self):
        self.firstStep=True
        self.lastEvtMsgId = 0
        self.lastDmgMsgId = 0
        self.mapObj=None
        self.OldMapObj=None
        self.state=None
        self.hudmsg=None
        self.damages=None

        self.gameInit = False

    # WTの起動状態確認-aces.exe が起動していれば 0、launcher が起動していれば 1、 両方起動していなければ 2 を返す
    def getWtProcess(self):
        cmd = "tasklist"
        msg = subprocess.check_output(cmd)
        msg_decode=msg.decode(sys.stdin.encoding)

        if "aces.exe" in msg_decode:
            #print("find aces.exe")
            return 0
        else:
            #print("not find aces.exe")
            if "launcher.exe" in msg_decode:
                #print("find launcher.exe ")
                return 1
            else:
                #print("not find launcher.exe")
                return 2

    # ゲームの状況を判定する。試合をしていない状態は0、試合が開始した時は1、試合中なら2、試合が終了した時は3、を返す
    def getGameState(self):
        oldMapObjTxt = self.oldMapObj.text
        mapObjTxt = self.mapObj.text

        if oldMapObjTxt == "" and  mapObjTxt== "":
            return 0
        elif oldMapObjTxt == ""  and mapObjTxt != "":
            return 1
        elif oldMapObjTxt != "" and mapObjTxt != "":
            return 2
        elif oldMapObjTxt != "" and mapObjTxt == "":
            return 3

    # aces が起動した時に行う動作。
    def acesInit(self):
        self.mapObj = requests.get('http://localhost:8111/map_obj.json')
        self.oldMapObj = self.mapObj
        self.firstStep = False
        print("firstStep complete")

    # aces 起動中に繰り返し行う動作
    def reloadLocalHost(self):
        self.state = requests.get('http://localhost:8111/state').json()
        self.hudmsgParams={'lastEvt':self.lastEvtMsgId, 'lastDmg':self.lastDmgMsgId}
        self.hudmsg = requests.get('http://localhost:8111/hudmsg', params=self.hudmsgParams).json()
        self.mapObj = requests.get('http://localhost:8111/map_obj.json')
        self.damages = self.hudmsg["damage"]


class Twitter:
    def __init__(self,CK,CS,AT,AS):

        self.url = "https://api.twitter.com/1.1/statuses/update.json"
        self.session = OAuth1Session(CK,CS,AT,AS)

    def tweetResult(self,twitterName,playTime,result):
        playTimeMin = playTime.seconds/60

        #Ouvillは10分間の激闘の末、10機撃墜し10個地上物を破壊した。また損害は5であった。#WTFlight_Recorder
        message=twitterName + "は" + str(playTimeMin) + "分間の激闘の末、" + str(result["killNumber"]) + "機撃墜し" + str(result["destroyNumber"]) + "個地上物を破壊した。また被害は" + str(result["deathNumber"])+"であった。 #WTFlightRecorder"

        params = {"status":message}
        req = self.session.post(self.url, params=params)

        if req.status_code == 200:
            print("post twitter")
        else:
            print("Error:%d" % req.status_code)



# メインの処理開始
print("start WT Flight Recorder")

# setting.ini ファイルの読み込み
ini = ConfigParser.SafeConfigParser()
if os.path.exists(SETTING_FILE):
    f = codecs.open(SETTING_FILE,'r','shift_jis')
    ini.readfp(f)
    f.close()
else:
    sys.stderr.write("%s が見つかりません" % SETTING_FILE)
    sys.exit(1)

playerName = ini.get('DEFAULT','NAME').strip()
player=Player(playerName)

gameInfo=GameInfo()
WtProcess = gameInfo.getWtProcess()

while WtProcess < 2:
    print("WtProcess",WtProcess)
    if WtProcess == 0:
        # aces.exeが起動したときに最初にする動作

        if gameInfo.firstStep:
            print("firstStep",gameInfo.firstStep)
            time.sleep(10)
            gameInfo.acesInit()

        # aces.exeが起動中繰り返し行う動作
        else:
            gameInfo.oldMapObj = gameInfo.mapObj
            try:
                gameInfo.reloadLocalHost()
            except:
                print("network error")

            gameState = gameInfo.getGameState()


            # 読み込んだlastDmgMsgId を記録
            length = (len(gameInfo.damages))
            if length > 0:
                    gameInfo.lastDmgMsgId = gameInfo.damages[len(gameInfo.damages)-1]["id"]

            # 試合中じゃない時
            if gameState == 0:
                print("not gaming")

            # 試合開始
            elif gameState == 1:
                startTime = datetime.datetime.today()
                player.initPlayerResult()
                print("game start")
                print(startTime)
                gameInfo.gameInit = True

            # 試合中
            elif gameState == 2:

                if gameInfo.gameInit == False:
                    startTime = datetime.datetime.today()
                    player.initPlayerResult()
                    print("game start")
                    print(startTime)
                    gameInfo.gameInit = True

                player.countResult(gameInfo.damages)
                print("gaming")


           #試合終了
            elif gameState == 3:
                endTime = datetime.datetime.today()
                playTime = endTime - startTime

                gameInfo.gameInit = True

                print("game end")
                print(endTime)
                player.printResult()
                dataFile = ini.get('DEFAULT','DATA')
                player.writeResult(dataFile,startTime,endTime)

                # Twitter の投稿機能
                twitterFunction =bool(ini.get('DEFAULT','TwitterFunction'))
                if twitterFunction == "True":
                    twitterFunction = True
                else:
                    twitterFunction = False
                print ("twitterFunction="+str(twitterFunction))

                if twitterFunction:
                    CK=ini.get('DEFAULT','Consumer_Key')
                    CS=ini.get('DEFAULT','Consumer_Secret')
                    AT=ini.get('DEFAULT','Access_Token')
                    AS=ini.get('DEFAULT','Access_Token_Secret')
                    twitterName=ini.get('DEFAULT','TwitterName')
                    twitter=Twitter(CK, CS, AT, AS)
                    twitter.tweetResult(twitterName, playTime, player.result)

    time.sleep(5)
    WtProcess = gameInfo.getWtProcess()

if WtProcess == 2:
    print("WarThunder dont running")
    sys.exit(0)
