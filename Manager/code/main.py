import psycopg2
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import logging
import os

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

    def __init__(self):
        self.conn = None
        self.set_db_config()
        self.db_connect()

    def set_db_config(self):
        try:
            self.DSN = f""" host={os.environ.get("MANAGER_DB_HOST")} 
                            port={os.environ.get("MANAGER_DB_PORT")}
                            dbname={os.environ.get("MANAGER_DB_NAME")} 
                            user={os.environ.get("MANAGER_DB_USER")} 
                            password={os.environ.get("MANAGER_DB_PASS")} """
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

    def __init__(self):
        super().__init__()
        self.mqtt_host = os.environ.get("MANAGER_MQTT_HOST")
        self.mqtt_port = int(os.environ.get("MANAGER_MQTT_PORT"))
        self.mqtt_user = os.environ.get("MANAGER_MQTT_USER")
        self.mqtt_pass = os.environ.get("MANAGER_MQTT_PASS")
        self.max_ret = int(os.environ.get("MANAGER_MQTT_MAX_RETRIES"))
        self.lux_topic = os.environ.get('MANAGER_MQTT_LUX_TOPIC')
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

    def on_disconnect(self, userdata, _,rc):
        LOG.LOG("Manager Disconnected...")

    def on_unsubscribe(self, userdata, mid):
        LOG.LOG("Manager Unsubscribed...")
    
    def on_message(self, client, userdata, msg):
        try:
            pass
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
    Manager()


