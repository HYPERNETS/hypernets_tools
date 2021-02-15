# TODO :  log output + --verbose mode

from argparse import ArgumentParser
from yoctopuce.yocto_relay import YRelay
from yoctopuce.yocto_api import YModule, YAPI
from time import sleep

from hypernets.scripts.yocto_init import init


def get_state_relay(id_relay, verbose=False):
    # TODO : Parse Y_STATE_INVALID
    config = init()
    yocto_prefix = config["yoctopuce"]["yocto_prefix1"]

    def _alias_get_state(id_relay):
        relay = YRelay.FindRelay(yocto_prefix + '.relay' + str(id_relay))
        return tuple((id_relay, relay.get_state()))

    relay_states = list()

    if id_relay == -1:
        for id_relay in range(1, 7, 1):
            relay_states.append(_alias_get_state(id_relay))
    else:
        relay_states.append(_alias_get_state(id_relay))

    if verbose is True:
        str_output = {False: "off", True: "on"}
        for id_relay, state in relay_states:
            print(f"Relay #{id_relay} is {str_output[state]}")

    YAPI.FreeAPI()
    return relay_states


def set_state_relay(id_relay, state, force=False):
    config = init()
    yocto_prefix = config["yoctopuce"]["yocto_prefix1"]

    if id_relay == -1:
        print("Not implemented")
        return

    elif id_relay == 1 and state in ["off", "reset"] and not force:
        print("""Warning : if your rugged pc is connected throught this
          relay, this action could switch it off. (use --force [-f]
          to enable this functionality)""")
        return

    relay = YRelay.FindRelay(yocto_prefix + '.relay' + str(id_relay))

    if state == "on":
        relay.set_state(YRelay.STATE_B)

    elif state == "off":
        relay.set_state(YRelay.STATE_A)

    elif state == "reset":
        relay.set_state(YRelay.STATE_A)
        sleep(1)
        relay.set_state(YRelay.STATE_B)

    YAPI.FreeAPI()


def set_at_power_on(id_relay, state, force=False):
    config = init()
    yocto_prefix = config["yoctopuce"]["yocto_prefix1"]

    if id_relay == -1:
        print("Not implemented")
        return

    relay = YRelay.FindRelay(yocto_prefix + '.relay' + str(id_relay))

    if state == "on":
        relay.set_stateAtPowerOn(YRelay.STATEATPOWERON_B)

    elif state == "off":
        relay.set_stateAtPowerOn(YRelay.STATEATPOWERON_A)

    elif state == "unchanged":
        relay.set_stateAtPowerOn(YRelay.STATEATPOWERON_UNCHANGED)

    if not force:
        print("""Warning : You need to use --force [-f] to write on flash
              memory, else modifications will be lost""")
    else:
        module = YModule.FindModule(yocto_prefix)
        print("Module Save : ")
        print(module.saveToFlash())

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

    mode.add_argument("-r", "--reset", action="store_true",
                      help="reset relay (1 sec off, then on)")

    mode.add_argument("-p", "--set-at-power-on", type=str,
                      help="schedule the state of the relay for next wakeup "
                           "(use --force [-f] to write in flash memory)",
                      metavar="{on, off, unchanged}",
                      choices=["on", "off", "unchanged"])

    parser.add_argument("-n", "--id-relay", type=int,
                        help="ID number of the relay (-1 stands for 'all')",
                        required=True,
                        metavar="{-1,1..6}",
                        choices=[-1] + list(range(1, 7, 1)))

    parser.add_argument("-f", "--force", action="store_true",
                        help="force relay #1 to switch off")

    args = parser.parse_args()

    if args.get:
        get_state_relay(args.id_relay, verbose=True)

    elif args.set:
        set_state_relay(args.id_relay, args.set, args.force)

    elif args.reset:
        set_state_relay(args.id_relay, "reset")

    elif args.set_at_power_on:
        set_at_power_on(args.id_relay, args.set_at_power_on, args.force)
