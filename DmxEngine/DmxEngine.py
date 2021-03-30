from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import threading
import json
import signal
import time
import paho.mqtt.client as mqtt
import yaml
import argparse

# DEFAULTS IF NOT IN CONFIG #
RenderFPS = 60
RenderChannels = 100
DefaultTransition = 1 #s
BaseTopic = "smartdmxer"
ClientName = "SmartDMXer"
BrokerHost = ""
BrokerPort = 1883
MqttAuth = False
MqttUser = ""
MqttPass = ""
FilePath = "files/lightdata.json"
ConfigPath = "config.yaml"
# DEFAULTS IF NOT IN CONFIG #

#Init statekeeper arrays 
haLightBright = []
halightState = []
curLightBright = []
FadeDelta = []
FadeTarget = []

mqttfailflag = False
#Mqtt connection callbacks

def handleArguments():
    global ConfigPath
    
    # Construct the argument parser
    ap = argparse.ArgumentParser()

    # Add the arguments to the parser
    ap.add_argument("-c", "--config", required=False,
    help="Config file path")
    args = vars(ap.parse_args())
    for key in args:
        if key == "config" and args[key] != None:
            ConfigPath = args[key]

def parseConfig():
    global RenderFPS
    global RenderChannels
    global DefaultTransition
    global BaseTopic
    global ClientName
    global BrokerHost
    global BrokerPort
    global MqttAuth
    global MqttUser
    global MqttPass

    print("INFO: parsing config file...")
    try:
        with open(ConfigPath) as file:
            config = yaml.load(file, Loader=yaml.FullLoader)
    except Exception as error: 
        print('ERROR: unable to parse config file. Exiting.')
        exitprogramnomqtt()
    if config != None:
        for key in config:
            if key == "dmx channels":
                if isinstance(config[key], int) and 0 < config[key] <= 100:
                    RenderChannels = config[key]
                else:
                    print("ERROR: invalid channel number. Exiting.")
                    exitprogramnomqtt()
            elif key == "render fps":
                if  isinstance(config[key], int) and 0 < config[key] <= 9999:
                    RenderFPS = config[key]
                else:
                    print("ERROR: invalid render FPS. Exiting.")
                    exitprogramnomqtt()
            elif key == "default transition":
                if  isinstance(config[key], int) and 0 < config[key] <= 9999:
                    DefaultTransition = config[key]
                else:
                    print("ERROR: invalid default transition. Exiting.")
                    exitprogramnomqtt()
            elif key == "broker host":
                if isinstance(config[key], str):
                    BrokerHost = config[key]
                else:
                    print("ERROR: invalid broker host. Exiting.")
                    exitprogramnomqtt()
            elif key == "broker port":
                if  isinstance(config[key], int) and 0 < config[key] <= 65535:
                    BrokerPort = config[key]
                else:
                    print("ERROR: invalid broker port. Exiting.")
                    exitprogramnomqtt()
            elif key == "client name":
                if isinstance(config[key], str):
                    ClientName = config[key]
                else:
                    print("ERROR: invalid client name. Exiting.")
                    exitprogramnomqtt()
            elif key == "autentication":
                if isinstance(config[key], bool):
                    MqttAuth = config[key]
                else:
                    print("ERROR: invalid autentication selection, must be true of false. Exiting.")
                    exitprogramnomqtt()
            elif key == "user":
                if isinstance(config[key], str):
                    MqttUser = config[key]
                else:
                    print("ERROR: invalid username. Exiting.")
                    exitprogramnomqtt()
            elif key == "password":
                if isinstance(config[key], str):
                    MqttPass = config[key]
                else:
                    print("ERROR: invalid password. Exiting.")
                    exitprogramnomqtt()
            elif key == "base topic":
                if isinstance(config[key], str):
                    BaseTopic = config[key]
                else:
                    print("ERROR: invalid base topic. Exiting.")
                    exitprogramnomqtt()

    if BrokerHost == "":
        print("ERROR: broker host missing. Exiting.")
        exitprogramnomqtt()
        
    if MqttAuth:
        if MqttPass == "" or MqttUser == "":
            print("ERROR: mqtt autentication tured on but user or password missing. Exiting.")
            exitprogramnomqtt()
        #except:
        #    print("ERROR: could not parse config file. Exiting.")
        #    exitprogramnomqtt()

def on_connect(client, userdata, flags, rc):
    print("INFO: MQTT client connected")
    for i in range(0, RenderChannels):
        publishLightState(i)
    client.publish(BaseTopic + "/avail" ,"online",qos=0,retain=True)
    for i in range(0, RenderChannels):
        client.subscribe(BaseTopic + "/" + str(i) + "/set")

def on_disconnect(client, userdata, rc):
   print("WARN: MQTT connection lost!")

def on_message(client, userdata, message):
    global curLightBright
    global halightState
    global haLightBright
    global FadeDelta
    global FadeTarget
    lightid = int(message.topic.split("/")[1])
    inPayload = {}
    try:
        inPayload = json.loads(str(message.payload.decode("utf-8")))
    except:
        print("ERROR: unable to parse incoming MQTT message")
    if "state" in inPayload:
        if "transition" in inPayload:
            transition = inPayload["transition"]
        else:
            transition = DefaultTransition
        if transition != 0:
            if inPayload["state"] == "ON":
                #if not halightState[lightid]:
                if "brightness" in inPayload:
                    haLightBright[lightid] = int(inPayload["brightness"])
                FadeTarget[lightid] = int(haLightBright[lightid])
                if FadeTarget[lightid] != curLightBright[lightid]:
                    FadeDelta[lightid] = (FadeTarget[lightid] - curLightBright[lightid]) / (transition * RenderFPS)
                if haLightBright[lightid] == 0:
                    halightState[lightid] = False
                else:
                    halightState[lightid] = True
                print("INFO: start fade on CH" + str(lightid + 1) + " from " + str(int(curLightBright[lightid])) + " to " + str(int(FadeTarget[lightid])) + ", delta " + "{:.2f}".format(FadeDelta[lightid]))
            elif inPayload["state"] == "OFF":
                if curLightBright[lightid] != 0:
                    FadeTarget[lightid] = 0
                    FadeDelta[lightid] = (FadeTarget[lightid] - curLightBright[lightid]) / (transition * RenderFPS)
                halightState[lightid] = False
                print("INFO: start fade on CH" + str(lightid + 1) + " from " + str(int(curLightBright[lightid])) + " to " + str(int(FadeTarget[lightid])) + ", delta " + "{:.2f}".format(FadeDelta[lightid]))
        else:
            if inPayload["state"] == "ON":
                #if not halightState[lightid]:
                if "brightness" in inPayload:
                    haLightBright[lightid] = int(inPayload["brightness"])
                FadeTarget[lightid] = int(haLightBright[lightid])
                if FadeTarget[lightid] != curLightBright[lightid]:
                    curLightBright[lightid] = FadeTarget[lightid]
                if haLightBright[lightid] == 0:
                    halightState[lightid] = False
                else:
                    halightState[lightid] = True
                print("INFO: set CH" + str(lightid + 1) + " to " + str(int(FadeTarget[lightid])))
            elif inPayload["state"] == "OFF":
                if curLightBright[lightid] != 0:
                    FadeTarget[lightid] = 0
                    curLightBright[lightid] = FadeTarget[lightid]
                    halightState[lightid] = False
                print("INFO: set CH" + str(lightid + 1) + " to " + str(int(FadeTarget[lightid])))

        publishLightState(lightid)

def publishLightState(lightid):
    global client
    if halightState[lightid]:
        stateonoff = "ON"
    else:
        stateonoff = "OFF"
    data = {"state": stateonoff, "brightness": haLightBright[lightid]}
    jsonData = json.dumps(data)
    client.publish(BaseTopic + "/" + str(lightid) ,jsonData,qos=0,retain=True)

def exitprogram():
        global client
        client.publish(BaseTopic + "/avail" ,"offline",qos=0,retain=True)
        client.loop_stop()
        outputData = []
        exit()

def exitprogramnomqtt():
        exit()
#Render values from statekeeper arrays to lights
def renderLights():
    outputData = []
    for i, bright in enumerate(curLightBright):
        outputData.append(int(bright))
    data = {"data": outputData}
    with open(FilePath, 'w+') as json_file:
        json.dump(data, json_file)
def main():
    global client
    #  PUT BANNER print("SmartDMXer DMX engine is starting!")
    
    handleArguments()
    
    def signal_handler(sig, frame):
        print('ERRROR: user pressed CTRL+C, exiting...')
        exitprogram()
    FPSCLOCK = pygame.time.Clock()
    signal.signal(signal.SIGINT, signal_handler)

    parseConfig()

    print("INFO: generating statekeeper arrays...")

    for _ in range(0, RenderChannels):
        haLightBright.append(255)
        halightState.append(False)
        curLightBright.append(0)
        FadeDelta.append(0)
        FadeTarget.append(255)

    print("INFO: starting light output")
    lightOutput = True

    #Initialize mqtt client
    print("INFO: Initializing MQTT Client...")
    print("      Host: " + str(BrokerHost))
    print("      Port: " + str(BrokerPort))
    if MqttAuth:
        print("      Using MQTT autentication")
    else:
        print("      MQTT autentication not necessary")
    client = mqtt.Client(ClientName)
    if MqttAuth:
        client.username_pw_set(username=MqttUser,password=MqttPass)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message=on_message #attach function to callback
    client.will_set(BaseTopic + "/avail","offline",qos=1,retain=False)
    try:
        client.connect(BrokerHost, port=BrokerPort)
    except:
        print("WARN: MQTT connection failed")
    client.loop_start()
    while True:
        for lightid in range(0, RenderChannels):
            if FadeDelta[lightid] != 0:
                if FadeDelta[lightid] > 0:
                    if curLightBright[lightid] < FadeTarget[lightid]:
                        curLightBright[lightid] = curLightBright[lightid] + FadeDelta[lightid]
                        if curLightBright[lightid] > 255:
                            curLightBright[lightid] = 255
                    else:
                        FadeDelta[lightid] = 0
                        print("INFO: finished fade on CH" + str(lightid + 1))
                if FadeDelta[lightid] < 0:
                    if curLightBright[lightid] > FadeTarget[lightid]:
                        curLightBright[lightid] = curLightBright[lightid] + FadeDelta[lightid]
                        if curLightBright[lightid] < 0:
                            curLightBright[lightid] = 0
                    else:
                        FadeDelta[lightid] = 0
                        print("INFO: finished fade on CH" + str(lightid + 1))
        if lightOutput:
            lightRenderer = threading.Thread(target=renderLights)
            lightRenderer.start()
        #print(FPSCLOCK.get_fps())
        FPSCLOCK.tick(RenderFPS)
    exitprogram()   

if __name__ == "__main__":
    main()