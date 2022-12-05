import psycopg2
import paho.mqtt.client as mqtt
import threading
from threading import Event
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
            format="%(asctime)s - ORCHESTRATOR%(name)s [%(levelname)s] %(message)s",
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

    def store_event(self, msg):
        try:
            cur = self.conn.cursor()
            q = f"""
                INSERT INTO Events (ts, description) 
                    VALUES ('{datetime.now()}', '{msg}')
            """
            cur.execute(q)
            self.conn.commit()
            cur.close()
        except (TypeError, AttributeError) as e:
            LOG.LOG(e)
            exit(1)
        except Exception as e:
            LOG.LOG(e)

    def get_last_data(self):
        try:
            cur = self.conn.cursor()
            q = f"""
                SELECT jdata 
                FROM data
                WHERE host = 'SENS01'
                ORDER BY ts desc
                LIMIT 1
            """
            cur.execute(q)
            self.conn.commit()
            jdata = cur.fetchone()
            cur.close()
            return jdata[0]
        except (TypeError, AttributeError) as e:
            LOG.LOG(e)
            exit(1)
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



class Orchestrator(DB):

    def __init__(self, config):
        super().__init__(config.get("db"))
        mqtt = config.get("mqtt")
        self.sub_topic = mqtt.get("sub_topic")
        self.mqtt_host = mqtt.get("host")
        self.mqtt_port = mqtt.get("port")
        self.mqtt_user = mqtt.get("user")
        self.mqtt_pass = mqtt.get("pass")
        self.max_ret = mqtt.get("max_retries")
        self.orch = config.get("orchestrator")
    
    def start(self):
        LOG.LOG("Starting Orchestrator...")
        self.start_orchestrator()
        self.client.loop_forever()
    
    def stop(self):
        LOG.LOG("Stopping Orchestrator...")
        self.client = None
    
    def start_orchestrator(self):
        LOG.LOG("Starting Orchestrator...")
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
        LOG.LOG("Orchestrator Disconnected...")
        self.stop()
        time.sleep(15)
        self.start()

    def on_unsubscribe(self, userdata, mid):
        LOG.LOG("Orchestrator Unsubscribed...")
        self.stop()
        time.sleep(15)
        self.start()

    def on_message(self, client, userdata, msg):
        try:
            dt = json.loads(msg.payload)
            topic = msg.topic
            if "SENS" in topic:
                self.manage_lux(dt, topic)
            else:
                self.manage(dt, topic)
        except Exception as e:
            LOG.LOG(e)

    def manage_lux(self, data, topic):
        try:
            if len(data.keys()) == 0:
                err_msg = f"Empty message from {topic.split('/')[0]+topic.split('/')[1]}"
                LOG.LOG(err_msg)
                self.store_event(err_msg)
                host_topic =  f"{topic.split('/')[0]}/{topic.split('/')[1]}/SYS/RESTART"
                self.client.publish(topic = host_topic, payload = '')
            else:
                actual_lux = int(data.get('lux'))
                last_rec_lux = int(self.get_last_data().get('lux'))
                lux_bound = int(self.get_config().get("lux_bound"))
                if actual_lux < lux_bound and last_rec_lux > lux_bound:
                    self.store_event("LIGHTS ON")
                    LOG.LOG("Lights turn on")
                    self.client.publish(topic="/ACT/01/RELAY/Z", payload = json.dumps({"action": True}))
                elif actual_lux > lux_bound and last_rec_lux < lux_bound:
                    self.store_event("LIGHTS OFF")
                    LOG.LOG("Lights turn off")
                    self.client.publish(topic="/ACT/01/RELAY/Z", payload = json.dumps({"action": False}))
        except Exception as e:
            LOG.LOG(e)

    def manage(self, data, topic):
        try:
            msg = f"Recieved data from {topic} with data {str(data)}"
            LOG.LOG(msg)
            self.store_event(msg)
        except Exception as e:
            LOG.LOG(e)
            
        
if __name__ == "__main__":
    time.sleep(20)
    LOG.setup()
    LOG.LOG("Starting...")
    with open("config.json", 'r') as f:
        config = json.load(f)
    Orchestrator(config).start()
