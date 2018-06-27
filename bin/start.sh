#!/bin/bash

# purpose: (re)start dvblast instance(s)
# syntax: $0 [<complete path to dvblast config (has to end in .cfg)> [...]]
# without arguments, every config in /etc/dvb/ will be used

FLAGS="-C -e -W -Y --sap"

[ -e /tmp/dvb ] || mkdir /tmp/dvb

run_dvblast()
{
  cfg="../cfg/$1.cfg"
  pid="/tmp/dvb/$1.pid"
  sock="/tmp/dvb/$1.sock"
  log="/var/log/dvb/$1.log"

  adapter="-a $(head -n 1 $cfg | cut -d ' ' -f 2)"
     freq="-f $(head -n 1 $cfg | cut -d ' ' -f 4)"
   symbol="-s $(head -n 1 $cfg | cut -d ' ' -f 6)"
  voltage="-v $(head -n 1 $cfg | cut -d ' ' -f 8)" # vertical --> 13V, horizontal --> 18V
      mod="-m $(head -n 1 $cfg | cut -d ' ' -f 10)"
  if [ "-m qam_auto" = "$mod" ]; then mod=; fi

  unicable="--unicable --unicable-vers $(head -n 2 $cfg | sed -n 2p | cut -d ' ' -f 2)"
  unicable_freq="--unicable-freq $(head -n 2 $cfg | sed -n 2p | cut -d ' ' -f 4)"
  unicable_id="--unicable-id $(head -n 2 $cfg | sed -n 2p | cut -d ' ' -f 6)"
  satnum="-S $(head -n 2 $cfg | sed -n 2p | cut -d ' ' -f 8)"

  [ -e "$pid" ] && kill $(cat "$pid") 2>&-
  rm -f "$sock"
  sleep .5
  /home/dvb/dvblast/dvblast  $adapter -r "$sock" -c "$cfg" $freq $symbol $voltage $unicable $unicable_freq $unicable_id $satnum $mod $FLAGS >"$log" 2>&1 &
  echo $! >"$pid"

  echo Started: $1
}

configs="${*:-../cfg/$(hostname)*.cfg}"
for cfg in $configs
do
  cfg=$(basename $cfg | cut -d '.' -f 1)
  run_dvblast $cfg &
  #sleep a bit so diseqc does not get mixed up
  sleep 10
done
wait

