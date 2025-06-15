import schedule
import time
from uptodate_shibu import main
def job():
    print("Running AI Post Bot...")
    main()

# Schedule 5 posts per day = every 288 minutes
schedule.every(77).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
