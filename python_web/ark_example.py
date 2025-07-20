import os
from volcenginesdkarkruntime import Ark
from KyLin.KylinTuningSystem.kylinApp.util import dict_to_custom_str, get_info_to_ai

def ai_optimize_infer():
    client = Ark(
        api_key="cf031d9f-ebdb-4bd0-bde2-e57444a86d31",
    )
    data = get_info_to_ai()
    data_str = dict_to_custom_str(data)
    completion = client.bot_chat.completions.create(
        model="bot-20250702164711-8jhhd",
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": data_str},
                ],
            }
        ],
    )
    return completion.choices[0].message.content

# 保留原有脚本功能
if __name__ == "__main__":
    data = get_info_to_ai()
    data_str = dict_to_custom_str(data)
    print("----- standard request -----")
    print(data_str)
    client = Ark(
        api_key="cf031d9f-ebdb-4bd0-bde2-e57444a86d31",
    )
    completion = client.bot_chat.completions.create(
        model="bot-20250702164711-8jhhd",
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": data_str},
                ],
            }
        ],
    )
    print(completion.choices[0].message.content)
    print(completion.references)