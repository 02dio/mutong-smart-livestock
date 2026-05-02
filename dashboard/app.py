from flask import Flask, render_template, jsonify, request
import pandas as pd
import os

app = Flask(__name__)

# CSV路径（自动定位，不用手动改）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, '..', 'simulated_pig_farm_data.csv')

df = pd.read_csv(CSV_PATH)
days = sorted(df['day'].unique())

@app.route('/')
def index():
    return render_template('index.html', days=days)

@app.route('/api/data')
def get_data():
    day = request.args.get('day', type=int)
    if day is None:
        day = days[0]
    day_data = df[df['day'] == day]
    return jsonify({
        'timestamps': day_data['timestamp'].tolist(),
        'temperature': day_data['temperature'].tolist(),
        'humidity': day_data['humidity'].tolist(),
        'nh3': day_data['nh3'].tolist(),
        'co2': day_data['co2'].tolist(),
        'activity': day_data['activity'].tolist(),
        'ear_tag_temp': day_data['ear_tag_temp'].tolist(),
        'anomaly_label': day_data['anomaly_label'].tolist()
    })

@app.route('/api/summary')
def get_summary():
    day = request.args.get('day', type=int)
    if day is None:
        day = days[0]
    day_data = df[df['day'] == day]
    anomalies = day_data[day_data['anomaly_label'] != '正常']['anomaly_label'].unique().tolist()
    return jsonify({
        'day': day,
        'avg_temp': round(day_data['temperature'].mean(), 1),
        'max_nh3': round(day_data['nh3'].max(), 1),
        'avg_activity': round(day_data['activity'].mean(), 1),
        'anomalies': anomalies,
        'total_samples': len(day_data)
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)