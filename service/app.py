import os
import pickle
import sys

sys.path.append(os.path.dirname(sys.path[0]))
from flask import Flask, send_from_directory, make_response, jsonify, redirect
from utils.tools import get_result_file_content, get_ip_address, resource_path
from utils.config import config
import utils.constants as constants
import subprocess
import atexit

app = Flask(__name__)
nginx_dir = resource_path(os.path.join('utils', 'nginx-rtmp-win32'))
nginx_path = resource_path(os.path.join(nginx_dir, 'nginx.exe'))
stop_path = resource_path(os.path.join(nginx_dir, 'stop.bat'))
result_data_path = resource_path(constants.result_data_path)
if os.path.exists(result_data_path):
    with open(result_data_path, "rb") as f:
        result_data = pickle.load(f)
else:
    result_data = []


@app.route("/")
def show_index():
    return get_result_file_content()


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(resource_path('static/images'), 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@app.route("/txt")
def show_txt():
    return get_result_file_content(file_type="txt")


@app.route("/rtmp-txt")
def show_rtmp_txt():
    return get_result_file_content(file_type="txt", rtmp=True)


@app.route("/m3u")
def show_m3u():
    return get_result_file_content(file_type="m3u")


@app.route("/content")
def show_content():
    return get_result_file_content(show_content=True)


@app.route("/log")
def show_log():
    log_path = resource_path(constants.sort_log_path)
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as file:
            content = file.read()
    else:
        content = constants.waiting_tip
    response = make_response(content)
    response.mimetype = "text/plain"
    return response


@app.route('/rtmp/<channel_id>', methods=['GET'])
def run_rtmp(channel_id):
    url = ''
    for item in result_data:
        if item['id'] == int(channel_id):
            url = item.get('url', '')
            break
    if not url:
        return jsonify({'Error': 'Url not found'}), 400
    cmd = [
        'ffmpeg',
        '-i', url.partition('$')[0],
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        '-b:v', '2500k',
        '-maxrate', '2500k',
        '-bufsize', '5000k',
        '-g', '50',
        '-c:a', 'aac',
        '-f', 'flv',
        f'rtmp://localhost:1935/live/{channel_id}'
    ]
    try:
        subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return redirect(f'rtmp://localhost:1935/live/{channel_id}')
    except Exception as e:
        return jsonify({'Error': str(e)}), 500


def stop_rtmp_service():
    if sys.platform == "win32":
        try:
            os.chdir(nginx_dir)
            subprocess.Popen([stop_path], shell=True)
        except Exception as e:
            print(f"❌ Rtmp service stop failed: {e}")


def run_service():
    try:
        if not os.environ.get("GITHUB_ACTIONS"):
            if sys.platform == "win32":
                original_dir = os.getcwd()
                try:
                    os.chdir(nginx_dir)
                    subprocess.Popen([nginx_path], shell=True)
                except Exception as e:
                    print(f"❌ Rtmp service start failed: {e}")
                finally:
                    os.chdir(original_dir)
            ip_address = get_ip_address()
            print(f"📄 Result content: {ip_address}/content")
            print(f"📄 Log content: {ip_address}/log")
            print(f"🚀 M3u api: {ip_address}/m3u")
            print(f"🚀 Txt api: {ip_address}/txt")
            print(f"🚀 Rtmp api: {ip_address}/rtmp-txt")
            print(f"✅ You can use this url to watch IPTV 📺: {ip_address}")
            app.run(host="0.0.0.0", port=config.app_port)
    except Exception as e:
        print(f"❌ Service start failed: {e}")


atexit.register(stop_rtmp_service)

if __name__ == "__main__":
    run_service()
