#coding: UTF-8
import subprocess
import sys
import json
import re
import requests
import time
import datetime
import locale
import csv

true=True
false=False

def getPlayerName(fileName):
    f = open(fileName,"r")
    readline = f.readlines()
    f.close()
    playerName = readline[0]
    playerName = playerName.strip()
    playerName = playerName.strip("\n")
    return playerName

class Setting:
    def __init__(self):
        self.fileName = "playerName.txt"

class Player:
    
    def __init__(self,name):
        self.initPlayerRecord()
        
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

        print(self.playerName)

    # player のデータを初期化
    def initPlayerRecord(self):
        self.killNumber=0
        self.lossNumber=0
        self.crashNumber=0
        self.destroyNumber=0
        self.destroyedNumber=0
        self.wreckedNumber=0

    # WT の hudmsg/damageから プレイヤー名を探して、戦果を記録
    def countResult(self,damages):
        for damage in damages:
            print(damage["id"])
            if self.reKillPattern.search(damage["msg"]):
                print("kill count")
                self.killNumber += 1
            if self.reLossPattern.search(damage["msg"]):
                print("loss count")
                self.lossNumber += 1
            if self.reCrashPattern.search(damage["msg"]):
                print("crash count")
                self.crashNumber += 1
            if self.reDestroyPattern.search(damage["msg"]):
                print("destroy count")
                self.destroyNumber += 1
            if self.reDestroyedPattern.search(damage["msg"]):
                print("destroyed count")
                self.destroyedNumber += 1
            if self.reWreckedPattern.search(damage["msg"]):
                print("wrecked count")
                self.wreckedNumber += 1

    # playerのデータを表示
    def printRecord(self):
        print("Player's kill count",self.killNumber)
        print("Player's killed count",self.lossNumber)
        print("Player's crash count",self.crashNumber)
        print("Player's destroy count",self.destroyNumber)
        print("Player's destoryed count",self.destroyedNumber)
        print("Player's wrecked count",self.wreckedNumber)

    # player のデータを書き込み
    def writeRecord(self,startTime,endTime):
        strStartTime = startTime.strftime('%Y/%m/%d-%H:%M:%S')
        strEndTime = endTime.strftime('%Y/%m/%d-%H:%M:%S')
        listResult = [strStartTime,strEndTime,self.killNumber,self.lossNumber,self.crashNumber,self.destroyNumber,self.destroyedNumber,self.wreckedNumber]
                
        try:
            f = open("data.csv","a")
            csvWriter = csv.writer(f)
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
        print("firstStep",self.firstStep)

    # aces 起動中に繰り返し行う動作
    def reloadLocalHost(self):
        self.state = requests.get('http://localhost:8111/state').json()
        self.hudmsgParams={'lastEvt':self.lastEvtMsgId, 'lastDmg':self.lastDmgMsgId}
        self.hudmsg = requests.get('http://localhost:8111/hudmsg', params=self.hudmsgParams).json()
        self.mapObj = requests.get('http://localhost:8111/map_obj.json')
        self.damages = self.hudmsg["damage"]


class Twitter:
    def __init__(self):
        self.CK ="f2EM0LCvjYKWZOldMYbQxVA31"
        self.CS ="XEgkfIyFapjyH3TFaVcBlingP169sHC52mTOnbj7LMK5KYUjcx"
        self.AT ="154568552-98zdzBgXC3w2GeTlbt6r6uUJqfRKWzGhh2RLYMru"
        self.AS ="5wTkWNyXPpmUZoKPDo4Kl8gPuZ9XViaRPo17gBhS4KdUu"

        self.url = "https://api.twitter.com/1.1/statuses/update.json"

        self.session = OAuth1Session(self.CK,self.CS,self.AT,self.AS)
        
    def tweetResult(self,name,playingTime,result):
        #Ouvillは10分間の激闘の末、10機撃墜し10個地上物を破壊した。また損害は5であった。#WTFlight_Recorder
        message=name,"は",playingTime,"分間の激闘の末",result["killNumber"],"機撃墜し",result["destroyNumber"],"個地上物を破壊した。また被害は",result["lossNumber"],"であった。 #WTFlingRecorder"

        params = {"status":message}
        req = self.session.post(self.url, params=params)

        if req.status_code == 200:
            print("post twitter")
        else:
            print("Error:%d" % req.status_code)
        
setting=Setting()
gameInfo=GameInfo()
player=Player(getPlayerName(setting.fileName))

WtProcess = gameInfo.getWtProcess()
print("start WT Flight Recorder")    
while WtProcess < 2:
    print("WtProcess",WtProcess)
    if WtProcess == 0:
        # aces.exeが起動したときに最初にする動作

        if gameInfo.firstStep:
            print("firstStep",gameInfo.firstStep)
            time.sleep(15)
            gameInfo.acesInit()

        # aces.exeが起動中繰り返し行う動作
        else:
            gameInfo.oldMapObj = gameInfo.mapObj
            try:
                gameInfo.reloadLocalHost()
            except:
                print("network error")

            gameState = gameInfo.getGameState()
            # 試合中じゃない時
            if gameState == 0:
                print("not gaming")
            
            # 試合開始
            elif gameState == 1:
                startTime = datetime.datetime.today()
                player.initPlayerRecord()
                print("game start")
                print(startTime)
                
            # 試合中
            elif gameState == 2:
                # 読み込んだid を記録
                length = (len(gameInfo.damages))
                if length > 0:
                    gameInfo.lastDmgMsgId = gameInfo.damages[len(gameInfo.damages)-1]["id"]
                    player.countResult(gameInfo.damages)
                print("gaming")
            
            
           #試合終了
            elif gameState == 3:
                endTime = datetime.datetime.today()
                print("game end")
                print(endTime)

                player.printRecord()
                player.writeRecord(startTime,endTime)                
            
    time.sleep(5)
    WtProcess = gameInfo.getWtProcess()

if WtProcess == 2:
    print("WarThunder dont running")
