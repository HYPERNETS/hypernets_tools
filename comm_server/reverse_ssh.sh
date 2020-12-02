#!/usr/bin/bash

# If issues : 
# use autossh with an independant service : 
# see : https://gist.github.com/thomasfr/9707568

# Oceane :
# ipServer=193.49.112.3

# Npl :
ipServer="139.143.5.63"
ipServer="lovr2d2001@hypernetssvr1.npl.co.uk"

# -f : stdin > /dev/null
#
# -N : do not execute remote command (usefull for just forwarding port)
#
# -R : Specifies that connections to the given TCP port or Unix socket on 
#      the remote (server) host are to be forwarded to the local side. 

ssh -o "ExitOnForwardFailure yes" -f -N -R0:127.0.0.1:22 $ipServer > /tmp/ssh_last 2>&1
ssh $ipServer "cat >> ssh_ports" < /tmp/ssh_last 
