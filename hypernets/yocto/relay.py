# TODO :  log output + --verbose mode

from argparse import ArgumentParser
from yoctopuce.yocto_relay import YRelay
from yoctopuce.yocto_api import YModule, YAPI
from urllib.request import urlopen
from time import sleep

from hypernets.yocto.init import init, get_url_base_prefixed
from logging import info, warning, debug


# -----------------------------------------------------------------------------

def get_state_relay(*args, verbose=False):
    config = init()
    if config["yoctopuce"]["yoctopuce_ip"] == "usb":
        return _get_state_relay_usb(*args, verbose)
    else:
        return _get_state_relay_ip(*args, verbose)


def set_state_relay(*args):
    config = init()
    if config["yoctopuce"]["yoctopuce_ip"] == "usb":
        return _set_state_relay_usb(*args)
    else:
        return _set_state_relay_ip(*args)


def set_at_power_on(*args, force=False):
    config = init()
    if config["yoctopuce"]["yoctopuce_ip"] == "usb":
        return _set_at_power_on_usb(*args, force)
    else:
        return _set_at_power_on_ip(*args, force)


# -----------------------------------------------------------------------------


def _get_state_relay_usb(id_relay, verbose=False):

    url_base = get_url_base_prefixed()

    # TODO : Parse Y_STATE_INVALID

    if id_relay == -1:
        id_relay = list(range(1, 7, 1))

    relay_states = list()
    for i in id_relay:
        url = "/".join([url_base, "api", "relay" + str(i), "state"])
        state = urlopen(url)
        state = {b"B": True, b"A": False}[state.read()]
        relay_states.append(state)
        debug(f"Relay #{i} is {state}.")

    return relay_states


def _set_state_relay_usb(id_relay, state, force=False):

    # Display a warning and ask to use "--force" if relay 1 is turned off
    if 1 in id_relay and state in ["off", "reset"] and not force:
        warning("""If your rugged pc is connected throught this
          relay, this action could switch it off. (use --force [-f]
          to enable this functionality)""")
        return

    url_base = get_url_base_prefixed()

    state = {"on": YRelay.STATE_B, "off": YRelay.STATE_A}[state]

    for i in id_relay:
        get = "api?ctx=relay" + str(i) + "&state=" + str(state)
        url = "/".join([url_base, get])
        urlopen(url)
    return


def _set_at_power_on_usb(id_relay, state, force):

    state = {"on": YRelay.STATEATPOWERON_B,
             "off": YRelay.STATEATPOWERON_A,
             "unchanged": YRelay.STATEATPOWERON_UNCHANGED}[state]

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


# -----------------------------------------------------------------------------


def _get_state_relay_ip(id_relay):
    # TODO : Parse Y_STATE_INVALID
    config = init()
    yocto_prefix = config["yoctopuce"]["yocto_prefix1"]

    relay_states = list()

    if id_relay == -1:
        id_relay = list(range(1, 7, 1))

    for i in id_relay:
        state = YRelay.FindRelay(yocto_prefix + '.relay' + str(i))
        relay_states.append(state.get_state())

    for id_relay, state in enumerate(relay_states):
        debug(f"Relay #{id_relay+1} is {state}")

    YAPI.FreeAPI()
    return relay_states


def _set_state_relay_ip(id_relay, state, force=False):
    info(id_relay)
    config = init()
    yocto_prefix = config["yoctopuce"]["yocto_prefix1"]

    if 1 in id_relay and state in ["off", "reset"] and not force:
        warning("""If your rugged pc is connected throught this
          relay, this action could switch it off. (use --force [-f]
          to enable this functionality)""")
        return

    if state == "on":
        for i in id_relay:
            relay = YRelay.FindRelay(yocto_prefix + '.relay' + str(i))
            relay.set_state(YRelay.STATE_B)

    elif state == "off":
        for i in id_relay:
            relay = YRelay.FindRelay(yocto_prefix + '.relay' + str(i))
            relay.set_state(YRelay.STATE_A)

    elif state == "reset":
        for i in id_relay:
            relay = YRelay.FindRelay(yocto_prefix + '.relay' + str(i))
            relay.set_state(YRelay.STATE_A)
            sleep(1)
            relay.set_state(YRelay.STATE_B)

    YAPI.FreeAPI()


def _set_at_power_on_ip(id_relay, state, force):
    config = init()
    yocto_prefix = config["yoctopuce"]["yocto_prefix1"]

    id_relay = id_relay[0]
    relay = YRelay.FindRelay(yocto_prefix + '.relay' + str(id_relay))

    if state == "on":
        relay.set_stateAtPowerOn(YRelay.STATEATPOWERON_B)

    elif state == "off":
        relay.set_stateAtPowerOn(YRelay.STATEATPOWERON_A)

    elif state == "unchanged":
        relay.set_stateAtPowerOn(YRelay.STATEATPOWERON_UNCHANGED)

    if not force:
        warning("""You need to use --force [-f] to write on flash
              memory, else modifications will be lost""")
    else:
        module = YModule.FindModule(yocto_prefix)
        info("Module Save : ")
        info(module.saveToFlash())

    YAPI.FreeAPI()


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

    args = parser.parse_args()

    if args.get:
        get_state_relay(args.id_relay, verbose=True)

    elif args.set:
        set_state_relay(args.id_relay, args.set, args.force)

    elif args.reset:
        set_state_relay(args.id_relay, "reset")

    elif args.set_at_power_on:
        set_at_power_on(args.id_relay, args.set_at_power_on, force=args.force)
