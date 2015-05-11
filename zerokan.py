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

firstStep=True
true=True
false=False
lastEvtMsgId = 0
lastDmgMsgId = 0
killNumber = 0
lossNumber = 0
crashNumber = 0
destroyNumber = 0
fileName = "playerName.txt"
startTime = 0
endTime = 0



# WTの起動状態確認-aces.exe が起動していれば 0、launcher が起動していれば 1、 両方起動していなければ 2 を返す
def getWtProcess():
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

# WT の hudmsg/damageから プレイヤー名を探して、戦果を記録
def countKillLossNumber(playerName):
    killPattern = playerName + ".* shot down"
    lossPattern = "shot down .*" + playerName
    crashPattern = playerName + u".* は\t墜落しました"
    destroyPattern = playerName + ".* destroyed"
    
    reKillPattern = re.compile(killPattern)
    reLossPattern = re.compile(lossPattern)
    reCrashPattern= re.compile(crashPattern)
    reDestroyPattern= re.compile(destroyPattern)
    
    global killNumber
    global lossNumber
    global crashNumber
    global destroyNumber

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
        

# ゲームの状況を判定する。試合をしていない状態は0、試合が開始した時は1、試合中なら2、試合が終了した時は3、を返す
def getGameState(oldMapObj,mapObj):
    if oldMapObj == "" and mapObj == "":
        return 0
    elif oldMapObj == ""  and mapObj != "":
        return 1
    elif oldMapObj != "" and mapObj != "":
        return 2
    elif oldMapObj != "" and mapObj == "":
        return 3
    
def getPlayerName(fileName):
    f = open(fileName,"r")
    readline = f.readlines()
    f.close()
    playerName = readline[0]
    playerName = playerName.strip()
    playerName = playerName.strip("\n")
    return playerName

    
    
WtProcess = getWtProcess()
print("start WT Flight Recorder")    
while WtProcess < 2:
    if WtProcess == 0:
        # aces.exeが起動したときに最初にする動作

        if firstStep:
            time.sleep(15)
            try:
                mapObj = requests.get('http://localhost:8111/map_obj.json')
                oldMapObj = mapObj
                startTime = datetime.datetime.today()
                playerName=getPlayerName(fileName)
                print(playerName)
                firstStep = False
            except:
                print("miss initilaizing")

        else:
            # aces.exeが起動中繰り返し行う動作
            oldMapObj = mapObj

            try:
                state = requests.get('http://localhost:8111/state').json()
                hudmsgParams={'lastEvt':lastEvtMsgId, 'lastDmg':lastDmgMsgId}
                hudmsg = requests.get('http://localhost:8111/hudmsg', params=hudmsgParams).json()
                mapObj = requests.get('http://localhost:8111/map_obj.json')
                damages = hudmsg["damage"]
            except:
                print("network error")

            GameState = getGameState(oldMapObj.text,mapObj.text)

            # 試合中じゃない時
            if GameState == 0:
                print("not gaming")
            
            # 試合開始
            elif GameState == 1:
                startTime = datetime.datetime.today()
                killNumber = 0
                lossNumber = 0
                crashNumber= 0
                destroyNumber= 0
                print("game start")
                print(startTime)
            # 試合中
            elif GameState == 2:
                # 読み込んだid を記録
                length = (len(damages))
                if length > 0:
                    lastDmgMsgId = damages[len(damages)-1]["id"]
                    countKillLossNumber(playerName)
                print("gaming")
            
            
           #試合終了
            elif GameState == 3:
                endTime = datetime.datetime.today()
                print("Player's kill count",killNumber)
                print("Player's killed count",lossNumber)
                print("Player's crash count",crashNumber)
                print("Player's destroy count",destroyNumber)
                print("game end")
                print(endTime)

                strStartTime = startTime.strftime('%Y/%m/%d-%H:%M:%S')
                strEndTime = endTime.strftime('%Y/%m/%d-%H:%M:%S')
            
                listResult = [strStartTime,strEndTime,killNumber,lossNumber,crashNumber,destroyNumber]
                
                try:
                    f = open("data.csv","a")
                    csvWriter = csv.writer(f)
                    csvWriter.writerow(listResult)
                    f.close()
                    print("save result")
                except:
                    print("save miss")
                
    time.sleep(5)
    WtProcess = getWtProcess()

if WtProcess == 2:
    print("WarThunder dont running")
        


        


