"""
牧瞳·猪场多模态传感器数据模拟生成器
生成7天×24小时的分钟级数据，包含正常状态和预设异常场景
输出：simulated_pig_farm_data.csv
"""

import csv
import random
import math
import os

# ============================================================
# 配置参数
# ============================================================
DAYS = 7  # 模拟天数
SAMPLES_PER_HOUR = 60  # 每小时采样点数（分钟级）
TOTAL_HOURS = DAYS * 24
TOTAL_SAMPLES = TOTAL_HOURS * SAMPLES_PER_HOUR

# 猪舍基础参数（基于《农业工程学报》猪舍环境日变化规律）
# 正常值范围
TEMP_BASE = 22.0  # 基础温度(℃)
TEMP_DAY_AMPLITUDE = 3.0  # 日间温度振幅
HUMIDITY_BASE = 65.0  # 基础湿度(%)
HUMIDITY_DAY_AMPLITUDE = 8.0  # 日间湿度振幅
NH3_BASE = 8.0  # 基础氨气浓度(ppm)
NH3_MAX_NORMAL = 15.0  # 正常上限
CO2_BASE = 600.0  # 基础CO2浓度(ppm)
CO2_MAX_NORMAL = 1500.0  # 正常上限

# 猪群活动量基础参数（0-100归一化值）
ACTIVITY_DAY_BASE = 65.0  # 日间基础活动量
ACTIVITY_NIGHT_BASE = 15.0  # 夜间基础活动量
ACTIVITY_MEAL_BOOST = 25.0  # 采食时段活动量增量

# ============================================================
# 预设异常场景
# ============================================================
# 场景一：第3天凌晨2:00-5:00 低温应激
#   - 温度骤降至14-15℃
#   - 活动量下降40-50%
#   - 氨气浓度轻度上升
ANOMALY_COLD_START_HOUR = 2 * 24 + 2  # 第3天 02:00
ANOMALY_COLD_END_HOUR = 2 * 24 + 5  # 第3天 05:00

# 场景二：第4天夜间22:00-第5天凌晨2:00 通风不足氨气蓄积
ANOMALY_NH3_START_HOUR = 3 * 24 + 22  # 第4天 22:00
ANOMALY_NH3_END_HOUR = 4 * 24 + 2  # 第5天 02:00

# 场景三：第6天全天 猪群活动量异常下降（模拟疫病前兆）
ANOMALY_SICK_START_HOUR = 5 * 24 + 0  # 第6天 00:00
ANOMALY_SICK_END_HOUR = 5 * 24 + 23  # 第6天 23:00


def get_hour_of_day(total_hour):
    """获取一天中的小时(0-23)"""
    return total_hour % 24


def get_day(total_hour):
    """获取第几天(1-7)"""
    return total_hour // 24 + 1


def is_in_range(total_hour, start_hour, end_hour):
    """判断当前小时是否在指定时间范围内"""
    return start_hour <= total_hour <= end_hour


def generate_temperature(total_hour):
    """生成温度数据(℃)"""
    hour = get_hour_of_day(total_hour)

    # 正常日变化：凌晨低，午后高
    # 使用正弦函数模拟，最低在凌晨4点，最高在下午14点
    temp = TEMP_BASE + TEMP_DAY_AMPLITUDE * math.sin((hour - 4) / 24 * 2 * math.pi)

    # 场景一：低温应激
    if is_in_range(total_hour, ANOMALY_COLD_START_HOUR, ANOMALY_COLD_END_HOUR):
        temp = 14.0 + random.uniform(-0.5, 0.5)  # 骤降至14℃左右

    # 添加随机噪声
    temp += random.gauss(0, 0.3)
    return round(temp, 1)


def generate_humidity(total_hour, temperature):
    """生成湿度数据(%)，湿度与温度呈负相关"""
    hour = get_hour_of_day(total_hour)
    base_humidity = HUMIDITY_BASE - HUMIDITY_DAY_AMPLITUDE * math.sin((hour - 4) / 24 * 2 * math.pi)

    # 场景一：低温应激伴随湿度升高
    if is_in_range(total_hour, ANOMALY_COLD_START_HOUR, ANOMALY_COLD_END_HOUR):
        base_humidity = 78.0 + random.uniform(-2, 2)

    base_humidity += random.gauss(0, 1.0)
    return round(base_humidity, 1)


def generate_nh3(total_hour):
    """生成氨气浓度(ppm)"""
    hour = get_hour_of_day(total_hour)
    base_nh3 = NH3_BASE + 3.0 * math.sin((hour - 8) / 24 * 2 * math.pi)

    # 场景二：氨气蓄积
    if is_in_range(total_hour, ANOMALY_NH3_START_HOUR, ANOMALY_NH3_END_HOUR):
        # 线性上升，最高到28ppm
        progress = (total_hour - ANOMALY_NH3_START_HOUR) / (ANOMALY_NH3_END_HOUR - ANOMALY_NH3_START_HOUR)
        base_nh3 = NH3_MAX_NORMAL + progress * 13.0
        if base_nh3 > 28.0:
            base_nh3 = 28.0

    base_nh3 += random.gauss(0, 1.5)
    return round(max(0, base_nh3), 1)


def generate_co2(total_hour):
    """生成CO2浓度(ppm)"""
    hour = get_hour_of_day(total_hour)
    base_co2 = CO2_BASE + 400 * math.sin((hour - 6) / 24 * 2 * math.pi)

    # 场景二：通风不足
    if is_in_range(total_hour, ANOMALY_NH3_START_HOUR, ANOMALY_NH3_END_HOUR):
        base_co2 = CO2_MAX_NORMAL + 500

    base_co2 += random.gauss(0, 50)
    return round(base_co2, 0)


def generate_activity(total_hour):
    """生成猪群活动量(0-100)"""
    hour = get_hour_of_day(total_hour)

    # 正常活动节律：白天活动多，夜间休息
    if 6 <= hour <= 18:
        base_activity = ACTIVITY_DAY_BASE
        # 采食时段（早7点、中午12点、下午5点）活动量增强
        if hour in [7, 8, 12, 13, 17, 18]:
            base_activity += ACTIVITY_MEAL_BOOST
    else:
        base_activity = ACTIVITY_NIGHT_BASE

    # 场景一：低温应激导致活动量骤降
    if is_in_range(total_hour, ANOMALY_COLD_START_HOUR, ANOMALY_COLD_END_HOUR):
        base_activity = ACTIVITY_NIGHT_BASE * 0.5  # 夜间活动量减半

    # 场景三：疫病前兆活动量异常下降
    if is_in_range(total_hour, ANOMALY_SICK_START_HOUR, ANOMALY_SICK_END_HOUR):
        base_activity *= 0.55  # 全天活动量下降45%

    base_activity += random.gauss(0, 5)
    return round(max(0, min(100, base_activity)), 1)


def generate_ear_tag_temp(total_hour, temperature):
    """生成智能耳标体温数据(℃)，正常猪体温38-39.5℃"""
    # 场景三：疫病前兆伴随体温升高
    if is_in_range(total_hour, ANOMALY_SICK_START_HOUR, ANOMALY_SICK_END_HOUR):
        # 约30%的猪只发热
        if random.random() < 0.3:
            return round(40.0 + random.uniform(0.3, 1.5), 1)

    # 正常体温 + 环境温度影响
    base_temp = 38.5 + 0.02 * (temperature - TEMP_BASE)
    base_temp += random.gauss(0, 0.3)
    return round(base_temp, 1)


def generate_feeding_amount(total_hour, is_anomaly_sick):
    """生成采食量(g)，正常约2000-2500g/次"""
    hour = get_hour_of_day(total_hour)

    # 只在采食时段有数据（早7、午12、晚17）
    if hour not in [7, 12, 17]:
        return 0

    base_amount = 2200

    # 场景一：低温采食下降
    if is_in_range(total_hour, ANOMALY_COLD_START_HOUR, ANOMALY_COLD_END_HOUR):
        base_amount *= 0.80

    # 场景三：采食下降20-30%
    if is_anomaly_sick and hour in [7, 12, 17]:
        base_amount *= 0.72

    base_amount += random.gauss(0, 100)
    return round(max(0, base_amount), 0)


def generate_anomaly_label(total_hour):
    """生成异常标签"""
    if is_in_range(total_hour, ANOMALY_COLD_START_HOUR, ANOMALY_COLD_END_HOUR):
        return "低温应激"
    elif is_in_range(total_hour, ANOMALY_NH3_START_HOUR, ANOMALY_NH3_END_HOUR):
        return "氨气蓄积"
    elif is_in_range(total_hour, ANOMALY_SICK_START_HOUR, ANOMALY_SICK_END_HOUR):
        return "疫病前兆"
    else:
        return "正常"


def export_anomaly_summary(csv_file):
    """自动提取异常场景的关键数据点，输出汇总表格"""
    import csv

    anomalies = {
        "低温应激": [],
        "氨气蓄积": [],
        "疫病前兆": []
    }

    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = row['anomaly_label']
            if label in anomalies:
                anomalies[label].append({
                    'timestamp': row['timestamp'],
                    'temperature': float(row['temperature']),
                    'activity': float(row['activity']),
                    'nh3': float(row['nh3']),
                    'feeding_amount': float(row['feeding_amount'])
                })

    print("\n" + "=" * 70)
    print("异常场景数据摘要（Agent触发阈值配置参考）")
    print("=" * 70)

    for scene, data in anomalies.items():
        if not data:
            continue

        print(f"\n【{scene}】共 {len(data)} 条数据")

        # 统计关键参数的区间
        temps = [d['temperature'] for d in data]
        acts = [d['activity'] for d in data]
        nh3s = [d['nh3'] for d in data]
        feeds = [d['feeding_amount'] for d in data if d['feeding_amount'] > 0]

        print(f"  温度范围: {min(temps):.1f} ~ {max(temps):.1f}℃")
        print(f"  活动量范围: {min(acts):.1f} ~ {max(acts):.1f}")
        print(f"  氨气范围: {min(nh3s):.1f} ~ {max(nh3s):.1f} ppm")
        if feeds:
            print(f"  采食量范围: {min(feeds):.0f} ~ {max(feeds):.0f} g")

        # 取第一条数据作为典型样本
        first = data[0]
        print(f"  典型样本时间: {first['timestamp']}")
        print(f"  典型参数: 温度{first['temperature']}℃, 活动量{first['activity']}, 氨气{first['nh3']}ppm")

    print("\n" + "=" * 70)
    print("以上数据用于：①Flask看板异常标注 ②Agent推理阈值配置")
    print("=" * 70)


def main():
    print("=" * 50)
    print("牧瞳·猪场多模态传感器数据模拟生成器")
    print("=" * 50)
    print(f"模拟天数: {DAYS}天")
    print(f"总数据量: {TOTAL_SAMPLES}条 (分钟级采样)")
    print(f"预设场景: 3个异常场景")
    print()

    # 创建输出文件
    output_file = "simulated_pig_farm_data.csv"

    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)

        # 写表头
        writer.writerow([
            'timestamp',  # 时间戳
            'day',  # 第几天
            'hour',  # 小时
            'minute',  # 分钟
            'temperature',  # 温度(℃)
            'humidity',  # 湿度(%)
            'nh3',  # 氨气浓度(ppm)
            'co2',  # CO2浓度(ppm)
            'activity',  # 群体活动量(0-100)
            'ear_tag_temp',  # 耳标体温(℃)
            'feeding_amount',  # 采食量(g)
            'anomaly_label'  # 异常标签
        ])

        # 生成数据
        anomaly_count = 0
        for hour in range(TOTAL_HOURS):
            is_anomaly_sick = is_in_range(hour, ANOMALY_SICK_START_HOUR, ANOMALY_SICK_END_HOUR)

            for minute in range(SAMPLES_PER_HOUR):
                day = get_day(hour)
                hour_of_day = get_hour_of_day(hour)

                # 生成各传感器数据
                temp = generate_temperature(hour)
                hum = generate_humidity(hour, temp)
                nh3 = generate_nh3(hour)
                co2 = generate_co2(hour)
                act = generate_activity(hour)
                ear_temp = generate_ear_tag_temp(hour, temp)
                feed = generate_feeding_amount(hour, is_anomaly_sick)
                label = generate_anomaly_label(hour)

                if label != "正常":
                    anomaly_count += 1

                # 生成时间戳字符串
                base_minutes = hour * 60 + minute
                ts_day = base_minutes // (24 * 60) + 1
                ts_hour = (base_minutes % (24 * 60)) // 60
                ts_minute = base_minutes % 60
                timestamp_str = f"Day{ts_day:02d}-{ts_hour:02d}:{ts_minute:02d}"

                writer.writerow([
                    timestamp_str,
                    day,
                    hour_of_day,
                    minute,
                    temp,
                    hum,
                    nh3,
                    co2,
                    act,
                    ear_temp,
                    feed,
                    label
                ])

        # 打印进度
        if hour % 24 == 0:
            print(f"  已完成: 第{hour // 24 + 1}天数据...")

    print()
    print(f"数据生成完毕！")
    print(f"输出文件: {output_file}")
    print(f"总数据量: {TOTAL_SAMPLES} 条")
    print(f"其中异常数据: {anomaly_count} 条")
    print(f"正常数据: {TOTAL_SAMPLES - anomaly_count} 条")
    print()
    print("预设异常场景：")
    print(f"  场景一：第3天凌晨2:00-5:00 低温应激")
    print(f"  场景二：第4天22:00-第5天2:00 氨气蓄积")
    print(f"  场景三：第6天全天 疫病前兆（活动量下降+体温升高）")
    print()
    print("下一步：将此CSV文件用于Flask看板的数据源。")

    # 自动输出异常摘要
    export_anomaly_summary(output_file)
if __name__ == "__main__":
    main()