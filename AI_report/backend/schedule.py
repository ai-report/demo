import json
from operator import add
from re import split

from poem import get_deepseek_poem
from trigger import check_special_events
from format_content import schedule_text2json_array
from prompt import PROMPT
from llm import get_llm_response
from storage import add_data, retrieve_data


class Agent:
    def __init__(self, name: str, age: str, personality: str, style: str,
                 home: str, relation: str):
        self.name = name
        self.age = age
        self.personality = personality
        self.style = style
        self.home = home
        self.relation = relation
        
    def plan_hour(self):
        text = PROMPT['scheduler']['one_hour'].substitute(
            role_name=self.name,
            old=self.age,
            personality=self.personality,
            style=self.style,
            home=self.home,
            relation=self.relation
        )
        # print(text)
        # print('-' * 20)
        res = get_llm_response(
            prompt_text=text,
            provider='gemini'
        )

        processed_res = schedule_text2json_array(res)
        # print(res)

        pretty = json.dumps(
            processed_res,
            ensure_ascii=False,
            indent=2
        )
        # print(pretty)
        
        add_data(
            f"sch_{self.name}_hour",
            processed_res
        )
        
        return processed_res

    def plan_15_minute(self, hour_schedule: dict[str, dict]):
        
        text = PROMPT['scheduler']['15_minute'].substitute(
            role_name='李白',
            old='25歲',
            personality='崇尚自由、自信驕傲、喜歡喝酒',
            style='隨意、喜歡即興創作與喝酒',
            home='目前被流放，晚上睡在河邊',
            relation='與莊子是好友，與李清照有些許曖昧關係',
            hour_schedule=hour_schedule
        )
        # print(text)
        # print('-' * 20)
        res = get_llm_response(
            prompt_text=text,
            provider='gemini'
        )

        processed_res = schedule_text2json_array(res)
        # print(res)

        pretty = json.dumps(
            processed_res,
            ensure_ascii=False,
            indent=2
        )
        # print(pretty)
        
        add_data(
            f"sch_{self.name}_15_minute",
            processed_res
        )

        return processed_res  # 美化版本，適合輸出

    def check_and_add_trigger(self, event):
        # 這裡可以添加觸發器的邏輯
        # 例如，檢查是否有特殊事件需要觸發
        result = check_special_events(event, self.name)
        if type(result) != bool:
            result = False
            print(f"Error: {result}, set to False")
        if result:
            time_ = event['time']
            if self.name == '李白':
                file_name = f"{self.name}"
                poem_text = """
                床前明月光，疑似地上霜。
                舉頭望明月，低頭思故鄉。
                """
                add_data(
                    f"trigger_{self.name}_{time_}",
                    {time_: result, "poem": str(poem_text), "sound": file_name}
                )
            elif self.name == '李清照':
                file_name = str(self.name)
                poem_text = """
                昨夜雨疏風驟，濃睡不消殘酒。
                試問卷簾人，卻道海棠依舊。
                知否，知否，應是綠肥紅瘦。
                """
                add_data(
                    f"trigger_{self.name}_{time_}",
                    {time_: result, "poem": str(poem_text), "sound": f"{file_name}"}
                )
            elif self.name == '莊子':
                file_name = f"{self.name}"
                poem_text = """
                北冥有魚，其名為鯤。
                鯤之大，不知其幾千里也。
                化而為鳥，其名為鵬。
                鵬之背，不知其幾千里也；
                怒而飛，其翼若垂天之雲。
                """
                add_data(
                    f"trigger_{self.name}_{time_}",
                    {time_: result, "poem": str(poem_text), "sound": f"{file_name}"}
                )
            else: # self.name == '李老師':
                file_name = f"{self.name}_{str(time_)}"
                poem_text = get_deepseek_poem(file_name)
                add_data(
                    f"trigger_{self.name}_{time_}",
                    {time_: result, "poem": str(poem_text), "sound": f"{file_name}"}
                )
            print(f"Trigger added for {self.name} at {time_}: {event} with result {result}, poem: {poem_text}, sound path: {file_name}")
        else:
            time_ = event['time']
            add_data(
                f"trigger_{self.name}_{time_}",
                {time_: result, "poem": "", "sound": ""}
            )
            print(f"Trigger added for {self.name} at {time_}: {event} with result {result}")
            
    def split_plan_to_each_15_minute(self):
        json_text = retrieve_data(f"sch_{self.name}_15_minute")
        for key in json_text:
            add_data(
                f"sch_{self.name}_15_minute_{key}",
                json_text[key]
            )
            self.check_and_add_trigger(json_text[key])


agents = {
    'li': Agent(
        name='李白',
        age='45歲',
        personality='崇尚自由、自信驕傲、喜歡喝酒',
        style='隨意、喜歡即興創作與喝酒',
        home='目前被流放，晚上睡在河邊',
        relation='與莊子是好友，與李清照有些許曖昧關係'
    ),
    "teacher_li":Agent(
        name='李老師',
        age='51歲',
        personality='出口成章、對新科技非常了解',
        style='吟詩，作息規律、早睡早起、起床後會運動',
        home='書院',
        relation='莊子的同事，李清照的老師'
    ),
    "li_qing_zhao":Agent(
        name='李清照',
        age='19歲',
        personality='多愁善感、戀愛腦',
        style='寫詞，作息規律，家境富有，是一個名副其實的大家閨秀,在書院念書',
        home='李清照家',
        relation='李昇暾和莊子的學生',
    ),
    "zhuang_zi":Agent(
        name='莊子',
        age='55歲',
        personality='語言犀利、豁達灑脫、爽朗，人生閲歷豐富，對於人生乃至整個世界有獨屬自己的觀點',
        style='開玩笑，容易失眠',
        home='莊子家',
        relation='李昇暾的同事，李清照的老師'
    )

}

# agents['li'].plan_hour()
# minutes_plan = agents['li'].plan_15_minute(
#     retrieve_data('sch_李白_hour')
# )


# def split_plan_to_each_15_minute(json_text):
#     for key in json_text:
#         add_data(
#             f"sch_{'李白'}_15_minute_{key}",
#             json_text[key]
#         )
        
#         print(f"sch_{'李白'}_15_minute_{key}")  #,
#             # json_text[key])
            
# split_plan_to_each_15_minute(minutes_plan)
