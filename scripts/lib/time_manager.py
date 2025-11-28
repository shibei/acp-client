from datetime import datetime
import time

class TimeManager:
    """时间管理类"""
    def __init__(self, dryrun=False):
        self.dryrun = dryrun
    
    def wait_until(self, target_time, action_name="执行"):
        """等待到指定时间"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {'[DRYRUN] ' if self.dryrun else ''}等待到{action_name}时间...")
        
        if self.dryrun:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] 跳过等待，目标时间: {target_time.strftime('%Y-%m-%d %H:%M:%S')}")
            return
        
        while True:
            now = datetime.now()
            time_diff = (target_time - now).total_seconds()
            
            if time_diff <= 0:
                break
            
            if int(time_diff) % 30 == 0:
                hours = int(time_diff // 3600)
                minutes = int((time_diff % 3600) // 60)
                seconds = int(time_diff % 60)
                print(f"[{now.strftime('%H:%M:%S')}] 距离{action_name}还有: {hours:02d}:{minutes:02d}:{seconds:02d}")
            
            time.sleep(1)
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ⏰ 到达{action_name}时间")
