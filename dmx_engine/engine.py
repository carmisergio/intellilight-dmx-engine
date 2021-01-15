import mqtt
import time

def main():
    print("Main function")
    MqttClient = mqtt.Mqtt("192.168.1.61", Username="sergio", Password="sergio06")
    while True:
        time.sleep(0.1)

if __name__ == "__main__":
    main()