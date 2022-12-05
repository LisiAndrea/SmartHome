import psycopg2
import paho.mqtt.client as mqtt
import time
import json
import time
from datetime import datetime
import logging

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

    def __init__(self, db_conf):
        self.conn = None
        self.get_config(db_conf)
        self.db_connect()

    def get_config(self, db_conf):
        try:
            self.DSN = f""" host={db_conf.get("host")} 
                            port={db_conf.get("port")}
                            dbname={db_conf.get("dbname")} 
                            user={db_conf.get("user")} 
                            password={db_conf.get("pass")} """
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

    def __init__(self, config):
        super().__init__(config.get("db"))
        mqtt = config.get("mqtt")
        self.sub_topic = mqtt.get("sub_topic")
        self.mqtt_host = mqtt.get("host")
        self.mqtt_port = mqtt.get("port")
        self.mqtt_user = mqtt.get("user")
        self.mqtt_pass = mqtt.get("pass")
        self.max_ret = mqtt.get("max_retries")
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
    with open("config.json", 'r') as f:
        config = json.load(f)
    Consumer(config)


