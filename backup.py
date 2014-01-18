#!/usr/bin/env python 
#
# Automatically does some magic to copy a zfs pool to another. Will create a 
# snapshot on the source and transfer to the destination incrementall using
# zfs send and zfs recv. 
# 
# Written by Joshua Gordon <code@joshgordon.net> in 2014. 
# Copyright (c) 2014 Joshua Gordon. 
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License. 
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
# 
# USAGE: 
# TODO: USAGE

#Ultimately, this is what we want: 
# zfs send -R josh@offsite-backup_2-2013-12-07-2342 | zfs recv -F josh-offsite-disk-2 

import subprocess
import sys
import ConfigParser
import os 
import time

confName = "backup.conf"

if __name__ == "__main__": 
  if (os.geteuid() != 0): 
    print "Must be run as root!" 
    sys.exit(1) 
  conf = ConfigParser.ConfigParser()
  conf.read(confName)
  pools_available = set(subprocess.check_output("zpool list -H -o name", shell=True).strip().split("\n"))
  
  pools_available = set(map(lambda x:x.lower(), pools_available))
  
  for srcPool in conf.sections(): 
    if srcPool.lower() in pools_available: 
      pools_available -= set(srcPool.lower())
      print "Found source pool", srcPool, "in mounted pools." 
      print "Looking for availble destination pools." 
      for destPool in conf.options(srcPool): 
        if destPool in pools_available: 
          print "Doing backup to %s. " %(destPool)
          
          #do the actual backup
          snapName = backup(srcPool, destPool, conf.get(srcPool, destPool))

          #open the config file. Update it with the new newest snapshot. 
          confFile = open(confName, 'w') 
          conf.set(srcPool, destPool, snapName)
          conf.write(confFile)
          confFile.close() 
          
          
  
  
def backup(src, dest, old_snap): 
  timeNow = time.localtime() 
  snapshotName = "%s-%04d-%02d-%02d" % (dest, timeNow.tm_year, timeNow.tm_mon, timeNow.tm_mday)
  os.system("zfs snapshot -r %s@%s" % (src, snapshotName))
  
  os.system("zfs send -R -I %s@%s %s@%s | zfs recv -F %s" % (src, old_snap, src, snapshotName, dest))
  
  return snapshotName 
