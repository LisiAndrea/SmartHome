import psycopg2
import paho.mqtt.client as mqtt
import json
from datetime import datetime
import logging
import ast
import os 
import time

logger = None

class LOG(object):

    def setup():
        global logger
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - CONSUMER%(name)s [%(levelname)s] %(message)s",
            handlers=[
                logging.StreamHandler()
            ]
        )
        logger  = logging.getLogger(__name__)

    def LOG(msg):
        global logger
        logger.debug(msg)
    
        

class DB(object):

    def __init__(self):
        self.conn = None
        self.get_config()
        self.db_connect()

    def get_config(self):
        try:
            self.DSN = f""" host={os.environ.get("CONSUMER_DB_HOST")} 
                            port={os.environ.get("CONSUMER_DB_PORT")}
                            dbname={os.environ.get("CONSUMER_DB_NAME")} 
                            user={os.environ.get("CONSUMER_DB_USER")} 
                            password={os.environ.get("CONSUMER_DB_PASS")} """
        except Exception as e:
            LOG.LOG(e)


    def db_connect(self):
        LOG.LOG("Connecting to db...")
        try:
            if not self.conn:
                self.conn = psycopg2.connect(self.DSN)
        except Exception as e:
            LOG.LOG(e)

    def format_data(self, dt):
        try:
            res = dict()
            for k,v in dt.items():
                if k.lower() in ["sender", "source", "host"]:
                    continue
                try:
                    if v.isnumeric():
                        res[k] = float(v)
                    else:
                        res[k] = v
                except:
                    res[k] = v
            return res
        except Exception as e:
            LOG.LOG(e)

    def store(self, host, dt):
        try:
            cur = self.conn.cursor()
            q = f"""
                INSERT INTO data (host, jdata, ts) VALUES 
                    ('{host}', '{json.dumps(dt)}', '{datetime.now()}')
            """
            cur.execute(q)
            self.conn.commit()
            cur.close()
        except (TypeError, AttributeError) as e:
            LOG.LOG(e)
            exit(1)
        except Exception as e:
            LOG.LOG(e)



class Consumer(DB):

    def __init__(self):
        super().__init__()
        self.sub_topic = ast.literal_eval(ast.literal_eval(os.environ.get("CONSUMER_MQTT_SUB_TOPIC")))
        self.mqtt_host = os.environ.get("CONSUMER_MQTT_HOST")
        self.mqtt_port = int(os.environ.get("CONSUMER_MQTT_PORT"))
        self.mqtt_user = os.environ.get("CONSUMER_MQTT_USER")
        self.mqtt_pass = os.environ.get("CONSUMER_MQTT_PASS")
        self.max_ret = int(os.environ.get("CONSUMER_MQTT_MAX_RETRIES"))
        self.start_consumer()

    def start_consumer(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.on_unsubscribe = self.on_unsubscribe
        self.client.username_pw_set(self.mqtt_user, self.mqtt_pass)
        self.client.connect(self.mqtt_host, self.mqtt_port, self.max_ret)
        self.client.loop_forever()

    def reset_client(self):
        self.client = None

    def on_connect(self, client, userdata, flags, rc):
        LOG.LOG("Connected with result code "+str(rc))
        for tp in self.sub_topic:
            client.subscribe(tp)

    def on_disconnect(self, userdata, _, rc):
        LOG.LOG("Consumer Disconnected...")
        self.reset_client()
        time.sleep(15)
        self.start_consumer()

    def on_unsubscribe(self,userdata, mid):
        LOG.LOG("Consumer Unsubscribed...")
        self.reset_client()
        time.sleep(10)
        self.start_consumer()
    
    def on_message(self, client, userdata, msg):
        LOG.LOG("Received data")
        dt = json.loads(msg.payload)
        self.store(dt.get("sender"), self.format_data(dt))

        

if __name__ == "__main__":
    time.sleep(20)
    LOG.setup()
    LOG.LOG("Starting...")
    Consumer()