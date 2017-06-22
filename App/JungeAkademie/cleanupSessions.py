# -*- coding: utf-8 -*-
"""
Created on Thu Apr  6 04:02:50 2017

@author: Andrei
"""

import os
command=r'cd \ & cd Users\Andrei\Documents\Universitate\Jungeakademie\Modulo\Projekt\DjangoTest\JungeAkademie & python ./manage.py clearsessions'
os.system(command)
input("Program finished successfully")

'''
from crontab import CronTab

cron = CronTab(tab="SHELL=C:/Windows/system32/cmd.exe")

job = cron.new(command='dir', comment='list directory items')

print(job)

#job = cron[0]

job_std_out = job.run()

print(job_std_out)
'''