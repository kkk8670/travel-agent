# app/tools/weather_tools.py

"""
天气工具
"""


from app.common import Tool


def get_weather_forecast(city: str, date: str) -> dict:
    mock = {
        "Tokyo": {"condition": "晴转多云", "temp_high_c": 18, "temp_low_c": 11, "rain_prob": 20},
        "Singapore": {"condition": "雷阵雨", "temp_high_c": 32, "temp_low_c": 26, "rain_prob": 70},
        "Seoul": {"condition": "小雪", "temp_high_c": 2, "temp_low_c": -5, "rain_prob": 60},
    }
    return mock.get(city, {"condition": "未知", "temp_high_c": 20, "temp_low_c": 10, "rain_prob": 30})


WEATHER_TOOLS: list[Tool] = [
    {
        "name": "get_weather_forecast",
        "description": "查询某城市某日的天气。返回天气状况、温度范围、降雨概率。",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "date": {"type": "string", "description": "YYYY-MM-DD"},
            },
            "required": ["city", "date"],
        },
        "execute": get_weather_forecast,
    },
]


if __name__ == "__main__":
    # 跑法: uv run python -m app.tools.weather_tools
    fn = WEATHER_TOOLS[0]["execute"]
    result = fn(city="Tokyo", date="2026-06-01")
    print("结果:", result)
    assert "condition" in result
    assert "temp_high_c" in result
    print("✓ weather tool 通过")
