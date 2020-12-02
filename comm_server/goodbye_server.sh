#!/bin/bash

# Oceane :
# ipServer=193.49.112.3
# ipServer=hypernets@193.49.112.3

# Npl :
ipServer="lovr2d2001@hypernetssvr1.npl.co.uk"

set -no
ssh -t $ipServer 'rm ~/system_is_up'
killall ssh
