import paho.mqtt.client as PahoClient

class Mqtt():
    def __init__(self, BrokerHost, BrokerPort=None, Username=None, Password=None, ClientId=None, SubscribeTopics = []):
        self.BrokerHost = BrokerHost
        self.BrokerPort = BrokerPort
        self.Username = Username
        self.Password = Password
        self.ClientId = ClientId

        print("Initializing MQTT client")
        if ClientId:
            self.client = PahoClient.Client(ClientId)
        else:
            self.client = PahoClient.Client()
        
        self.client.on_connect = self.OnConnect
        self.client.on_message = self.Onmessage
        self.client.on_subscibe = self.OnSubscribe
        
        if Username:
            self.client.username_pw_set(Username, password=Password)
        self.client.on_connect = self.OnConnect
        
        try:
            print("Attemtpting MQTT connection")
            self.client.connect(BrokerHost)
        except:
            print("Coult not enstablish MQTT connection. Automatic retries are on.")
        
        self.client.loop_start()
    def OnConnect(self,client,userdata,flags,rc):
        if rc == 0:
            print("MQTT Connection successfully enstablished!")
        else:
            print("Connection not successful. Returned code=",rc)

    def OnSubscribe(self,client, userdata, mid, granted_qos):
        print("Subscription successful")

    def Onmessage(self,client,userdata,msg):
        print('got a message')
        self.received = str(msg.payload.decode())

if __name__ == "__main__":
    print("This is a module for engine.py. It cannot be run directly.")