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
    
    killNumber=0
    lossNumber=0
    crashNumber=0
    destroyNumber=0
    destroyedNumber=0
    wreckNumber=0
       
    def __init__(self,name):
        self.initPlayerRecord()
        
        self.playerName = name
        self.killPattern = self.playerName + ".* shot down"
        self.lossPattern = "shot down .*" + self.playerName
        self.crashPattern = self.playerName + u".* は\t墜落しました"
        self.destroyPattern = self.playerName + ".* destroyed"
        self.destroyedPattern = "destroyed .*" + self.playerName
        self.wreckedPattern = self.playerName + ".* has been wrecked"

        self.reKillPattern = re.compile(killPattern)
        self.reLossPattern = re.compile(lossPattern)
        self.reCrashPattern= re.compile(crashPattern)
        self.reDestroyPattern= re.compile(destroyPattern)
        self.reDestroyedPattern = re.compile(destroyedPattern)
        self.reWreckedPattern = re.compile(wreckedPattern)

    # player のデータを初期化
    def initPlayerRecord(self):
        self.killNumber=0
        self.lossNumber=0
        self.crashNumber=0
        self.destroyNumber=0
        self.destroyedNumber=0
        self.wreckNumber=0

    # WT の hudmsg/damageから プレイヤー名を探して、戦果を記録
    def countResult(self,damages):
        for damage in damages:
            print(damage["id"])
            if reKillPattern.search(damage["msg"]):
                print("kill count")
                killNumber += 1
            if reLossPattern.search(damage["msg"]):
                print("loss count")
                lossNumber += 1
            if reCrashPattern.search(damage["msg"]):
                print("crash count")
                crashNumber += 1
            if reDestroyPattern.search(damage["msg"]):
                print("destroy count")
                destroyNumber += 1
            if reDestroyedPattern.search(damage["msg"]):
                print("destroyed count")
                destroyedNumber += 1
            if reWreckedPattern.search(damage["msg"]):
                print("wrecked count")
                wreckedNumber += 1

    # playerのデータを表示
    def printRecord(self):
        print("Player's kill count",killNumber)
        print("Player's killed count",lossNumber)
        print("Player's crash count",crashNumber)
        print("Player's destroy count",destroyNumber)
        print("Player's destoryed count",destroyedNumber)
        print("Player's wrecked count",wreckedNumber)

    # player のデータを書き込み
    def writeRecord(self,startTime,endTime):
        strStartTime = startTime.strftime('%Y/%m/%d-%H:%M:%S')
        strEndTime = endTime.strftime('%Y/%m/%d-%H:%M:%S')
        listResult = [strStartTime,strEndTime,killNumber,lossNumber,crashNumber,destroyNumber,destroyedNumber,wreckedNumber]
                
        try:
            f = open("data.csv","a")
            csvWriter = csv.writer(f)
            csvWriter.writerow(listResult)
            f.close()
            print("save result")
        except:
            print("save miss")

    
    

class GameInfo:
    lastEvtMsgId = 0
    lastDmgMsgId = 0
    mapObj=None
    OldMapObj=None

    def __init__(self):
        self.firstStep=True
        startTime = datetime.datetime.today()

    
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
        if oldMapObj == "" and mapObj == "":
            return 0
        elif oldMapObj == ""  and mapObj != "":
            return 1
        elif oldMapObj != "" and mapObj != "":
            return 2
        elif oldMapObj != "" and mapObj == "":
            return 3

    # aces が起動した時に行う動作。
    def acesInit(self):
        mapObj = requests.get('http://localhost:8111/map_obj.json')
        oldMapObj = mapObj
        self.firstStep = False
        print("firstStep",self.firstStep)

    # aces 起動中に繰り返し行う動作
    def reloadLocalHost(self):
        state = requests.get('http://localhost:8111/state').json()
        hudmsgParams={'lastEvt':lastEvtMsgId, 'lastDmg':lastDmgMsgId}
        hudmsg = requests.get('http://localhost:8111/hudmsg', params=hudmsgParams).json()
        mapObj = requests.get('http://localhost:8111/map_obj.json')
        damages = hudmsg["damage"]

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
            gameInfo.acesInit()

        # aces.exeが起動中繰り返し行う動作
        else:
            gameInfo.oldMapObj = gameInfo.mapObj
            try:
                gameInfo.reloadLocalHost()
            except:
                print("network error")

            gameState = gameInfo.getGameState(oldMapObj.text,mapObj.text)
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
