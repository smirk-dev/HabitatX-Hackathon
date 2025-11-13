from flask import Flask, jsonify, render_template
from flask_cors import CORS
import numpy as np
from datetime import datetime, timedelta
import threading
import time
from collections import deque
from sklearn.ensemble import IsolationForest
import random

app = Flask(__name__)
CORS(app)

# Global data storage
sensor_data = {
    'temperature': deque(maxlen=100),
    'humidity': deque(maxlen=100),
    'pressure': deque(maxlen=100),
    'timestamps': deque(maxlen=100)
}

alerts = []
health_index = 100

# AI Model for anomaly detection
anomaly_detector = IsolationForest(contamination=0.1, random_state=42)

# Initialize with some baseline data
def initialize_model():
    baseline = []
    for _ in range(50):
        baseline.append([
            np.random.normal(22, 1),  # temperature
            np.random.normal(45, 5),  # humidity
            np.random.normal(101.3, 0.5)  # pressure
        ])
    anomaly_detector.fit(baseline)

initialize_model()

# Sensor simulation with occasional anomalies
def generate_sensor_reading():
    """Generate realistic sensor data with occasional anomalies"""
    base_temp = 22.0
    base_humidity = 45.0
    base_pressure = 101.3
    
    # 5% chance of anomaly
    if random.random() < 0.05:
        anomaly_type = random.choice(['temp', 'humidity', 'pressure'])
        if anomaly_type == 'temp':
            temp = np.random.normal(28, 2)  # High temperature anomaly
        elif anomaly_type == 'humidity':
            humidity = np.random.normal(70, 5)  # High humidity anomaly
        else:
            pressure = np.random.normal(98, 1)  # Low pressure anomaly
    
    temp = np.random.normal(base_temp, 0.8)
    humidity = np.random.normal(base_humidity, 3)
    pressure = np.random.normal(base_pressure, 0.3)
    
    return {
        'temperature': round(temp, 2),
        'humidity': round(humidity, 2),
        'pressure': round(pressure, 2),
        'timestamp': datetime.now().isoformat()
    }

def calculate_health_index(temp, humidity, pressure):
    """Calculate habitat health index based on sensor readings"""
    temp_score = 100 if 20 <= temp <= 24 else max(0, 100 - abs(temp - 22) * 10)
    humidity_score = 100 if 40 <= humidity <= 60 else max(0, 100 - abs(humidity - 50) * 2)
    pressure_score = 100 if 100 <= pressure <= 102 else max(0, 100 - abs(pressure - 101.3) * 20)
    
    return round((temp_score + humidity_score + pressure_score) / 3, 2)

def detect_anomaly(temp, humidity, pressure):
    """Use AI model to detect anomalies"""
    reading = np.array([[temp, humidity, pressure]])
    prediction = anomaly_detector.predict(reading)
    score = anomaly_detector.score_samples(reading)[0]
    
    return prediction[0] == -1, score

def create_alert(alert_type, message, severity):
    """Create system alert"""
    alert = {
        'type': alert_type,
        'message': message,
        'severity': severity,
        'timestamp': datetime.now().isoformat()
    }
    alerts.append(alert)
    if len(alerts) > 50:
        alerts.pop(0)

# Background thread for continuous monitoring
def sensor_monitoring_loop():
    global health_index
    while True:
        reading = generate_sensor_reading()
        
        temp = reading['temperature']
        humidity = reading['humidity']
        pressure = reading['pressure']
        
        # Store data
        sensor_data['temperature'].append(temp)
        sensor_data['humidity'].append(humidity)
        sensor_data['pressure'].append(pressure)
        sensor_data['timestamps'].append(reading['timestamp'])
        
        # Calculate health index
        health_index = calculate_health_index(temp, humidity, pressure)
        
        # AI anomaly detection
        is_anomaly, anomaly_score = detect_anomaly(temp, humidity, pressure)
        
        if is_anomaly:
            if temp > 25 or temp < 18:
                create_alert('TEMPERATURE', f'Temperature anomaly detected: {temp}°C', 'HIGH')
            if humidity > 65 or humidity < 30:
                create_alert('HUMIDITY', f'Humidity anomaly detected: {humidity}%', 'HIGH')
            if pressure < 100 or pressure > 102.5:
                create_alert('PRESSURE', f'Pressure anomaly detected: {pressure} kPa', 'CRITICAL')
        
        # Predictive maintenance checks
        if len(sensor_data['temperature']) >= 20:
            recent_temps = list(sensor_data['temperature'])[-20:]
            temp_trend = np.polyfit(range(20), recent_temps, 1)[0]
            
            if abs(temp_trend) > 0.1:
                create_alert('PREDICTION', f'Temperature trend detected: {temp_trend:.3f}°C/min. System failure predicted in 30 minutes.', 'MEDIUM')
        
        if health_index < 70:
            create_alert('HEALTH', f'Habitat health index critical: {health_index}%', 'CRITICAL')
        
        time.sleep(2)  # Update every 2 seconds

# Start monitoring thread
monitoring_thread = threading.Thread(target=sensor_monitoring_loop, daemon=True)
monitoring_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/current')
def get_current_data():
    """Get current sensor readings"""
    if len(sensor_data['temperature']) == 0:
        return jsonify({'error': 'No data available'}), 404
    
    return jsonify({
        'temperature': sensor_data['temperature'][-1],
        'humidity': sensor_data['humidity'][-1],
        'pressure': sensor_data['pressure'][-1],
        'health_index': health_index,
        'timestamp': sensor_data['timestamps'][-1]
    })

@app.route('/api/history')
def get_history():
    """Get historical sensor data"""
    return jsonify({
        'temperature': list(sensor_data['temperature']),
        'humidity': list(sensor_data['humidity']),
        'pressure': list(sensor_data['pressure']),
        'timestamps': list(sensor_data['timestamps'])
    })

@app.route('/api/alerts')
def get_alerts():
    """Get recent alerts"""
    return jsonify({
        'alerts': alerts[-20:],  # Last 20 alerts
        'count': len(alerts)
    })

@app.route('/api/predictions')
def get_predictions():
    """Get AI predictions for next hour"""
    if len(sensor_data['temperature']) < 30:
        return jsonify({'error': 'Insufficient data for prediction'}), 400
    
    # Simple linear regression for prediction
    recent_temps = list(sensor_data['temperature'])[-30:]
    recent_humidity = list(sensor_data['humidity'])[-30:]
    recent_pressure = list(sensor_data['pressure'])[-30:]
    
    temp_coef = np.polyfit(range(30), recent_temps, 1)
    humidity_coef = np.polyfit(range(30), recent_humidity, 1)
    pressure_coef = np.polyfit(range(30), recent_pressure, 1)
    
    # Predict next 30 readings (1 hour at 2-second intervals)
    predictions = []
    for i in range(31, 61):
        pred_temp = temp_coef[0] * i + temp_coef[1]
        pred_humidity = humidity_coef[0] * i + humidity_coef[1]
        pred_pressure = pressure_coef[0] * i + pressure_coef[1]
        
        predictions.append({
            'temperature': round(pred_temp, 2),
            'humidity': round(pred_humidity, 2),
            'pressure': round(pred_pressure, 2)
        })
    
    # Calculate failure probability
    failure_prob = 0
    for pred in predictions:
        if pred['temperature'] < 18 or pred['temperature'] > 26:
            failure_prob += 3
        if pred['humidity'] < 30 or pred['humidity'] > 70:
            failure_prob += 2
        if pred['pressure'] < 99 or pred['pressure'] > 103:
            failure_prob += 5
    
    failure_prob = min(100, failure_prob)
    
    return jsonify({
        'predictions': predictions[::5],  # Every 5th prediction for visualization
        'failure_probability': failure_prob,
        'estimated_time_to_failure': 'N/A' if failure_prob < 20 else f'{60 - (failure_prob // 2)} minutes'
    })

@app.route('/api/stats')
def get_statistics():
    """Get statistical analysis"""
    if len(sensor_data['temperature']) < 10:
        return jsonify({'error': 'Insufficient data'}), 400
    
    temps = list(sensor_data['temperature'])
    humidities = list(sensor_data['humidity'])
    pressures = list(sensor_data['pressure'])
    
    return jsonify({
        'temperature': {
            'mean': round(np.mean(temps), 2),
            'std': round(np.std(temps), 2),
            'min': round(min(temps), 2),
            'max': round(max(temps), 2)
        },
        'humidity': {
            'mean': round(np.mean(humidities), 2),
            'std': round(np.std(humidities), 2),
            'min': round(min(humidities), 2),
            'max': round(max(humidities), 2)
        },
        'pressure': {
            'mean': round(np.mean(pressures), 2),
            'std': round(np.std(pressures), 2),
            'min': round(min(pressures), 2),
            'max': round(max(pressures), 2)
        }
    })

if __name__ == '__main__':
    print("🚀 AI Habitat Health Monitor Starting...")
    print("📊 Dashboard: http://localhost:5000")
    print("🤖 AI Anomaly Detection: ACTIVE")
    app.run(debug=True, threaded=True)
