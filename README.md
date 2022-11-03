# Timeloop
Timeloop is a service that can be used to run periodic tasks after a certain interval.

Each job runs on a separate thread and when the service is shut down, it waits till all tasks currently being executed are completed.

Inspired by this blog [`here`](https://www.g-loaded.eu/2016/11/24/how-to-terminate-running-python-threads-using-signals/)

## this fork version fixes:
o option to avoid sheduling time drift by job execution delay

o options for initial_launch, max_run_times, logger selection/delegation

o fix for default logger hanlder creating duplicated multiple handler

o fix sequential join operation 

o auto-terminates on no more alive-jobs

## Installation
```sh
# pip install git+https://github.com/dev1145/timeloop.git
```

## Writing jobs
```python
import time

from timeloop import Timeloop
from datetime import timedelta

tl = Timeloop()

@tl.job(interval=timedelta(seconds=2))
def sample_job_every_2s():
    print "2s job current time : {}".format(time.ctime())

@tl.job(interval=timedelta(seconds=5), allow_drift=False, initial_launch=False, max_run_times=None) # with default option values
def sample_job_every_5s():
    print "5s job current time : {}".format(time.ctime())


@tl.job(interval=timedelta(seconds=10), allow_drift=True, initial_launch=True, max_run_times=2)
def sample_job_every_10s():
    print "10s job current time : {}".format(time.ctime())
```

## Start time loop in separate thread
By default timeloop starts in a separate thread.

Please do not forget to call ```tl.stop``` before exiting the program, Or else the jobs wont shut down gracefully.

```python
tl.start()

while True:
  try:
    time.sleep(1)
  except KeyboardInterrupt:
    tl.stop()
    break
```

## Start time loop in main thread
Doing this will automatically shut down the jobs gracefully when the program is killed, so no need to  call ```tl.stop```
```python
tl.start(block=True)
```

### based on code forked from sankalpjonn/timeloop
