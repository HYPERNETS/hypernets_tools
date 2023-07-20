from hypernets.yocto.init import get_url_base_prefixed
from urllib.request import urlopen
from time import sleep
from datetime import datetime
from threading import Thread, Event
from logging import info, debug


def lightsensor_thread(event, path):
    url_base = get_url_base_prefixed()
    get = "/".join(["api", "lightSensor", "currentValue"])
    url = "/".join([url_base, get])

    with open(path, "w") as monitor_pd:
        try:
            # record to file until event is set
            while 1:
                light = float(urlopen(url).read())
                now_str = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
                monitor_pd.write(f"{now_str}\t{light}\n")
                monitor_pd.flush()
                
                # main thread requested to stop
                if event.is_set():
                    break

                # log once per second
                sleep(1)
        
        except Exception as e:
            monitor_pd.write(e)


def start_lightsensor_thread(path):
    event = Event()
    thread = Thread(target=lightsensor_thread, args=(event, path, ))
    debug("Starting monitor PD logging thread")
    thread.start()
    return thread, event


def terminate_lightsensor_thread(thread, event):
    debug("Terminating monitor PD logging thread")
    event.set()
    thread.join()
    debug("Monitor PD logging thread has finished")


if __name__ == "__main__":
    from logging import basicConfig, DEBUG

    log_fmt = '%(asctime)s: %(message)s'
    dt_fmt = '%Y-%m-%dT%H:%M:%S'
    basicConfig(format=log_fmt, level=DEBUG, datefmt=dt_fmt)

    path = "/tmp/monitor_pd.csv"
    info(f"Logging monitor photodiode data into {path}")
    thread, event = start_lightsensor_thread(path)

    for i in range(10):
        info(f"Sleeping {i}/10")
        sleep(1)

    info("Stopping the logger")
    terminate_lightsensor_thread(thread, event)

    for i in range(5):
        info(f"Sleeping {i}/5")
        sleep(1)

    info("All done")
