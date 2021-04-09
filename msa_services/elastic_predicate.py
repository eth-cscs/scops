#import datetime


#def MaxJobWaitTimeDayNight(usage, n, now, values):
    #if 'max_job_wait_time' not in usage:
        #return True
    #current_date = datetime.datetime.fromtimestamp(now)
    #if current_date.hour > 8 and current_date.hour < 16:
        #return usage['max_job_wait_time'] < values[0]
    #else:
        #return usage['max_job_wait_time'] < values[1]

def ConstValue(usage, n, values):
    return values[0]

def ConstValueIfPending(usage, n, values):
    if 'max_pending' not in usage or 'pending' not in usage or 'cap' not in usage:
        return True
    if usage['pending'] > 0:
        return values[0]
    return True

def AvgJobWaitTime(usage, n, values):
    if 'avg_job_wait_time' not in usage:
        return True
    return usage['avg_job_wait_time'] < values[0]

def QuotaAvailableAllowBigJob(usage, n, values):
    if 'max_pending' not in usage or 'pending' not in usage or 'cap' not in usage:
        return True
    quota = values[0]
    # allow big job
    if  usage['max_pending'] > usage['cap']:
        return False
    if usage['cap'] < quota and usage['cap'] < usage['pending']:
        return False
    return True
