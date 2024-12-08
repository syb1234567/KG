# modules/time_and_rhythm.py

class TimeAndRhythm:
    # 六经运行规律（简单表示）
    CYCLES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

    @staticmethod
    def get_cycle(hour):
        """
        根据小时返回六经时间规律
        :param hour: 小时
        :return: 对应的六经时间
        """
        index = hour // 2 % len(TimeAndRhythm.CYCLES)
        return TimeAndRhythm.CYCLES[index]
