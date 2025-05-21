from backend_app import Agent
import time
import random
import json
from datetime import datetime, timedelta
from llm import get_llm_response

class GameSimulation:
    def __init__(self):
        self.agents = []
        self.current_time = datetime.strptime("06:00", "%H:%M")
        self.end_time = datetime.strptime("23:00", "%H:%M")
        self.time_increment = timedelta(minutes=15)  # 每次增加15分鐘
        self.current_date_str = "2025年5月13日"
        self.events = []  # 存儲隨機事件
        
    def initialize_agents(self):
        """初始化模擬中的所有代理"""
        # 創建四個不同的角色
        self.agents.append(Agent(
            agent_id="li_bai",
            name="李白",
            persona_summary="""男，25歲，崇尚自由，自信驕傲，風流倜儻，是一個才子，興趣是喝酒，嗜酒如命，無規律作息、隨時可以睡覺
                                過去經歷：被流放了，有時可以去書院找東西吃，順便聽課""",
            initial_location="河邊"
    ))
        
        self.agents.append(Agent(
            agent_id="zhao_zhanggui",
            name="李清照",
            persona_summary="""女，19歲，個性是多愁善感、戀愛腦，興趣是寫詞，作息規律，家境富有，是一個名副其實的大家閨秀,在書院念書
                                關係：李昇暾和莊子的學生""",
            initial_location="李清照家"
    ))
        
        self.agents.append(Agent(
            agent_id="li_shengdun",
            name="李昇暾",
            persona_summary="""男，51歲，個性是出口成章、對新科技非常了解，興趣是吟詩，作息規律、早睡早起、起床後會運動,是書院的老師
                                關係：莊子的同事，李清照的老師""",
            initial_location="書院"
    ))
        
        self.agents.append(Agent(
            agent_id="zhuang_zi",
            name="莊子",
            persona_summary="""男，55歲，個性是語言犀利、豁達灑脫、爽朗，人生閲歷豐富，對於人生乃至整個世界有獨屬自己的觀點，興趣是開玩笑，容易失眠,
                                關係：李昇暾的同事，李清照的老師""",
            initial_location="莊子家"
    ))
        
        print(f"已初始化 {len(self.agents)} 個代理")
    
    def generate_all_daily_plans(self):
        """為所有代理生成每日計劃"""
        for agent in self.agents:
            print(f"為 {agent.name} 生成日程...")
            agent.generate_daily_plan(self.current_date_str)
            time.sleep(1)  # 避免API請求過快
    
    def generate_random_events(self, num_events=3):
        """生成一些隨機事件，這些事件會在一天中的隨機時間發生"""
        for _ in range(num_events):
            # 使用Agent類中的靜態方法獲取隨機事件
            event_description = Agent.get_normal_event()
            # 解析事件描述以獲取時間、地點等信息
            event_lines = event_description.strip().split('\n')
            event_info = {}
            for line in event_lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    event_info[key.strip()] = value.strip()
            
            # 將事件添加到事件列表
            if '時間' in event_info and '地點' in event_info and '事件' in event_info:
                time_str = event_info['時間']
                if len(time_str) == 3:  # 對於形如 "90" 的時間，轉換為 "09:00"
                    hour, minute = time_str[0], time_str[1:3]
                    time_str = f"{hour.zfill(2)}:{minute}"
                elif len(time_str) == 4:  # 對於形如 "1030" 的時間，轉換為 "10:30"
                    hour, minute = time_str[:2], time_str[2:]
                    time_str = f"{hour}:{minute}"
                
                self.events.append({
                    'time': time_str,
                    'location': event_info['地點'],
                    'participants': event_info.get('人物', '').split(','),
                    'description': event_info['事件']
                })
        
        # 按時間排序事件
        self.events.sort(key=lambda x: datetime.strptime(x['time'], "%H:%M"))
        print(f"已生成 {len(self.events)} 個隨機事件")
    
    def format_time(self, dt):
        """將datetime對象格式化為HH:MM格式"""
        return dt.strftime("%H:%M")
    
    def process_events(self, current_time_str):
        """處理當前時間可能發生的事件"""
        for event in self.events:
            if event['time'] == current_time_str:
                print(f"\n===== 隨機事件發生 @ {current_time_str} =====")
                print(f"地點: {event['location']}")
                print(f"涉及人物: {', '.join(event['participants'])}")
                print(f"事件描述: {event['description']}")
                
                # 更新相關代理的記憶
                for agent in self.agents:
                    if agent.name in event['participants'] or agent.current_location == event['location']:
                        agent.add_memory(current_time_str, f"見證/參與事件: {event['description']}")
                
                print("=============================\n")
    
    def run_simulation(self):
        """運行完整的一天模擬"""
        self.initialize_agents()
        self.generate_all_daily_plans()
        self.generate_random_events()
        
        print(f"\n===== 開始模擬 {self.current_date_str} =====")
        
        # 模擬時間流逝
        while self.current_time <= self.end_time:
            current_time_str = self.format_time(self.current_time)
            print(f"\n----- 當前時間: {current_time_str} -----")
            
            # 處理可能的隨機事件
            self.process_events(current_time_str)
            
            # 更新所有代理的狀態
            for agent in self.agents:
                agent.update_action_for_time(current_time_str)
            
            # 顯示所有代理的當前狀態
            self.display_agents_status()
            
            # 增加時間
            self.current_time += self.time_increment
            
            # 為了模擬效果，可以在這裡添加短暫暫停
            time.sleep(0.5)  # 暫停0.5秒
        
        print(f"\n===== 結束模擬 {self.current_date_str} =====")
        
        # 生成各代理一天的總結
        self.generate_daily_summary()

    def check_special_events(event,name):

        # 使用與 backend_app.py 中相同的邏輯，但正確設置 event 變量
        prompt = f"""請爲我判斷以下事件是否符合特殊事件的條件
        判斷事件：{name}:{event}
        特殊事件條件：1）李白：《晚上李白準備睡覺時
                    2）莊子：莊子到河邊時
                    3）李清照：李清照在自家庭院中思考時
                    4）李昇暾：李昇暾作詩時
        以上條件任只要滿足其中一條即判斷其為特殊事件
        若是特殊事件，回應"True"，否則則回應"False"，你的回復不可以添油加醋，必須嚴格遵照規則
        """
        
        # 調用 LLM API 獲取結果
        GEMINI_MODEL_NAME = "gemini-1.5-flash-latest"
        result = get_llm_response(prompt, provider='gemini', model_name=GEMINI_MODEL_NAME)
        
        # 處理結果字符串，確保返回真正的布爾值
        is_special = result.strip().lower() == "true"
        return is_special
    
    def display_agents_status(self):
        """顯示所有代理的當前狀態"""
        for agent in self.agents:
            location_info = f"📍{agent.current_location}"
            print(f"{agent.name}: {location_info} | 行動: {agent.current_action}")
            print(f"  思考: {agent.current_thought}")
            if agent.current_dialogue:
                print(f"  對話: \"{agent.current_dialogue}\"")
    
    def generate_daily_summary(self):
        """為每個代理生成一天的總結"""
        print("\n===== 一天總結 =====")
        for agent in self.agents:
            print(f"\n{agent.name} 的一天回顧:")
            
            # 構建提示以生成一天的總結
            memory_text = "\n".join([f"{mem['time']}: {mem['description']}" for mem in agent.memory_stream[-10:]])
            prompt = f"""
            角色: {agent.name}
            角色人設: {agent.persona_summary}
            今日日期: {self.current_date_str}
            
            以下是今天的重要記憶和活動:
            {memory_text}
            
            請以第一人稱的角度，寫一個簡短的日記式總結，表達{agent.name}對今天經歷的感受、收穫和反思。
            回應應包含對重要事件的感想，以及對明天的期望或計劃。請使用繁體中文，語調應符合角色人設。
            """
            
            # 在實際應用中，這裡會調用LLM API
            # 為了模擬，這裡直接輸出一個簡短總結
            print(f"【{agent.name}的日記】")
            print(f"今日在{agent.persona_summary}的引領下度過了充實的一天。")
            print(f"經歷了{len(agent.memory_stream)}件事，心中有許多感悟...")
            print("明日將繼續前行，希望能有新的體驗與收穫。")
            
            # 添加到代理的記憶中
            agent.add_memory(self.current_date_str, f"一天總結與反思: 今日經歷了{len(agent.memory_stream)}件事，有所收穫與感悟。")


# 主函數
def main():
    simulation = GameSimulation()
    simulation.run_simulation()


if __name__ == "__main__":
    main()