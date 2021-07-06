#!/usr/bin/python3
# coding: utf-8

from code import InteractiveConsole

if __name__ == '__main__':
    print("Hello!")
    vars = globals().copy()
    vars.update(locals())
    shell = InteractiveConsole(vars)
    shell.interact()
