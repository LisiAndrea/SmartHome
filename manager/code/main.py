import psycopg2
import paho.mqtt.client as mqtt
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
            format="%(asctime)s - MANAGER%(name)s [%(levelname)s] %(message)s",
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
        self.set_db_config(db_conf)
        self.db_connect()

    def set_db_config(self, db_conf):
        try:
            self.DSN = f""" host={db_conf.get("host")} 
                            port={db_conf.get("port")}
                            dbname={db_conf.get("dbname")} 
                            user={db_conf.get("user")} 
                            password={db_conf.get("pass")} """
        except Exception as e:
            LOG.LOG(e)


    def db_connect(self):
        try:
            if not self.conn:
                self.conn = psycopg2.connect(self.DSN)
        except Exception as e:
            LOG.LOG(e)


    def get_config(self):
        try:
            cur = self.conn.cursor()
            q = f"""
                SELECT jconf
                    FROM setting 
                    ORDER BY ts DESC
                    LIMIT 1
            """
            cur.execute(q)
            self.conn.commit()
            jconf = cur.fetchone()
            cur.close()
            return jconf[0]
        except (TypeError, AttributeError) as e:
            LOG.LOG(e)
            exit(1)
        except Exception as e:
            LOG.LOG(e)



class Manager(DB):

    def __init__(self, config):
        super().__init__(config.get("db"))
        mqtt = config.get("mqtt")
        self.sub_topic = mqtt.get("sub_topic")
        self.mqtt_host = mqtt.get("host")
        self.mqtt_port = mqtt.get("port")
        self.mqtt_user = mqtt.get("user")
        self.mqtt_pass = mqtt.get("pass")
        self.max_ret = mqtt.get("max_retries")
        manager = config.get("manager")
        self.lux_topic = manager.get('lux_topic')
        self._run()


    def start(self):
        LOG.LOG("Starting Manager...")
        self.start_manager()
    
    def stop(self):
        LOG.LOG("Stopping Manager...")
        self.client.disconnect()
        self.client = None
    
    def start_manager(self):
        LOG.LOG("Starting Manager...")
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.on_unsubscribe = self.on_unsubscribe
        self.client.username_pw_set(self.mqtt_user, self.mqtt_pass)
        self.client.connect(self.mqtt_host, self.mqtt_port, self.max_ret)
        

    def on_connect(self, client, userdata, flags, rc):
        LOG.LOG("Connected with result code "+str(rc))
        for tp in self.sub_topic:
            client.subscribe(tp)

    def on_disconnect(self, userdata, _,rc):
        LOG.LOG("Manager Disconnected...")

    def on_unsubscribe(self, userdata, mid):
        LOG.LOG("Manager Unsubscribed...")

    
    def on_message(self, client, userdata, msg):
        try:
            msg = f"Recieved data {msg}"
            LOG.LOG(msg)
        except Exception as e:
            LOG.LOG(e)

            
    def _run(self):
        while True:
            try:
                self.start()
                LOG.LOG("Sending request")
                self.client.publish(topic=self.lux_topic, payload = '')
                time_interval = int(self.get_config().get('lux_interval_check'))
                self.stop()
                time.sleep(time_interval)
            except Exception as e:
                LOG.LOG(e)
        
if __name__ == "__main__":
    time.sleep(20)
    LOG.setup()
    LOG.LOG("Starting...")
    with open("config.json", 'r') as f:
        config = json.load(f)
    Manager(config)


