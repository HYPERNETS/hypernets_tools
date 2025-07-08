from argparse import ArgumentParser
from yoctopuce.yocto_relay import YRelay
from urllib.request import urlopen
from urllib.error import HTTPError
from time import sleep
from hypernets.yocto.init import get_url_base_prefixed, get_yocto_lower_board_serial
from logging import info, warning, debug, error


def get_state_relay(id_relay):
    try:
        url_base = get_url_base_prefixed()
    
        if id_relay == -1:
            id_relay = list(range(1, 7, 1))
    
        relay_states = list()
        for i in id_relay:
            url = "/".join([url_base, "api", "relay" + str(i), "state"])
            state = urlopen(url)
            state = {b"B": True, b"A": False}[state.read()]
            relay_states.append(state)
            debug(f"Relay #{i} is {state}.")

    except HTTPError as e:
        if e.code == 404:
            error(f"Yocto module '{get_yocto_lower_board_serial()}' is not online")
        else:
            error(f"HTTP Error: {e.code}")
        return None

    except Exception as e:
        error(f"{e}")
        return None

    return relay_states


def set_state_relay(id_relay, state, force=False):

    # Display a warning and ask to use "--force" if relay 1 is turned off
    if 1 in id_relay and state in ["off", "reset"] and not force:
        warning("""If your rugged pc is connected throught this
          relay, this action could switch it off. (use --force [-f]
          to enable this functionality)""")
        return

    try:
        url_base = get_url_base_prefixed()
    
        if state == "reset":
            for i in id_relay:
                # switch off
                get = "api?ctx=relay" + str(i) + "&state=" + str(YRelay.STATE_A)
                url = "/".join([url_base, get])
                urlopen(url)
    
                sleep(1)
    
                # switch on
                get = "api?ctx=relay" + str(i) + "&state=" + str(YRelay.STATE_B)
                url = "/".join([url_base, get])
                urlopen(url)
            return
        
        state = {"on": YRelay.STATE_B, "off": YRelay.STATE_A}[state]
    
        for i in id_relay:
            get = "api?ctx=relay" + str(i) + "&state=" + str(state)
            url = "/".join([url_base, get])
            urlopen(url)

    except HTTPError as e:
        if e.code == 404:
            error(f"Yocto module '{get_yocto_lower_board_serial()}' is not online")
        else:
            error(f"HTTP Error: {e.code}")

    except Exception as e:
        error(f"{e}")


def set_at_power_on(id_relay, state, force=False):

    state = {"on": YRelay.STATEATPOWERON_B,
             "off": YRelay.STATEATPOWERON_A,
             "unchanged": YRelay.STATEATPOWERON_UNCHANGED}[state]

    try:
        id_relay = id_relay[0]
        url_base = get_url_base_prefixed()
        get = "api?ctx=relay" + str(id_relay) + "&stateAtPowerOn=" + str(state)
        url = "/".join([url_base, get])
        urlopen(url)
    
        if not force:
            warning("""You need to use --force [-f] to write on flash
                  memory, else modifications will be lost""")
        else:
            get = "api?ctx=module&persistentSettings=1"
            url = "/".join([url_base, get])
            urlopen(url)

    except HTTPError as e:
        if e.code == 404:
            error(f"Yocto module '{get_yocto_lower_board_serial()}' is not online")
        else:
            error(f"HTTP Error: {e.code}")

    except Exception as e:
        error(f"{e}")




if __name__ == '__main__':

    parser = ArgumentParser()

    mode = parser.add_mutually_exclusive_group(required=True)

    mode.add_argument("-g", "--get", action="store_true",
                      help="display relay's states")

    mode.add_argument("-s", "--set", type=str,
                      help="set the state of the relay",
                      metavar="{on, off}",
                      choices=["on", "off"])

    # XXX : Add N second argument (default=1)
    mode.add_argument("-r", "--reset", action="store_true",
                      help="reset relay (1 sec off, then on)")

    mode.add_argument("-p", "--set-at-power-on", type=str,
                      help="schedule the state of the relay for next wakeup "
                           "(use --force [-f] to write in flash memory)",
                      metavar="{on, off, unchanged}",
                      choices=["on", "off", "unchanged"])

    parser.add_argument("-n", "--id-relay", type=int, action='append',
                        help="ID number of the relay",
                        required=True,
                        metavar="{1..6}",
                        choices=list(range(1, 7, 1)))

    parser.add_argument("-f", "--force", action="store_true",
                        help="forces relay #1 to switch off, and allows to"
                        " write in memory for the state at power-on option")

    from logging import basicConfig, DEBUG
    basicConfig(level=DEBUG)

    args = parser.parse_args()

    if args.get:
        get_state_relay(args.id_relay)

    elif args.set:
        set_state_relay(args.id_relay, args.set, args.force)

    elif args.reset:
        set_state_relay(args.id_relay, "reset")

    elif args.set_at_power_on:
        set_at_power_on(args.id_relay, args.set_at_power_on, force=args.force)

