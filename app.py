from flask import Flask, request, jsonify
import requests
import sqlite3
import os

app = Flask(__name__)


# Создаем базу данных SQLite
def init_db():
    conn = sqlite3.connect('ips.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS ip_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            country TEXT,
            region TEXT,
            city TEXT,
            postal TEXT,
            latitude REAL,
            longitude REAL,
            isp TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Функция для запроса информации по IP через внешнее API
def get_ip_info(ip):
    url = f"http://ip-api.com/json/{ip}?fields=status,country,region,city,zip,lat,lon,isp"
    response = requests.get(url)
    return response.json()

@app.route('/send-ip')
def send_ip():
    client_ip = request.remote_addr
    ip_info = get_ip_info(client_ip)

    if ip_info['status'] == 'success':
        conn = sqlite3.connect('ips.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO ip_info (ip, country, region, city, postal, latitude, longitude, isp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (client_ip, ip_info['country'], ip_info['region'], ip_info['city'], ip_info['zip'],
              ip_info['lat'], ip_info['lon'], ip_info['isp']))
        conn.commit()
        conn.close()
        return f'IP {client_ip} registered with geo-info: {ip_info}'
    else:
        return f'Failed to retrieve IP info for {client_ip}', 400

@app.route('/get-connected-ips', methods=['GET'])
def get_connected_ips():
    conn = sqlite3.connect('ips.db')
    c = conn.cursor()
    c.execute('SELECT * FROM ip_info')
    data = c.fetchall()
    conn.close()
    
    ips_info = []
    for row in data:
        ips_info.append({
            'ip': row[1],
            'country': row[2],
            'region': row[3],
            'city': row[4],
            'postal': row[5],
            'latitude': row[6],
            'longitude': row[7],
            'isp': row[8]
        })
    
    return jsonify(ips_info)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Render использует переменную PORT
    app.run(host='0.0.0.0', port=port)