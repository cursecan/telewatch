import schedule
import time

def job(n=5):
    for i in range(n):
        print(i)
        time.sleep(1)

schedule.every(4).seconds.do(job)

while True:
    schedule.run_pending()
    time.sleep(10)