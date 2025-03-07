import os
import pickle
import sys

sys.path.append(os.path.dirname(sys.path[0]))
from flask import Flask, send_from_directory, make_response, jsonify
from utils.tools import get_result_file_content, get_ip_address, resource_path, find_by_id
from utils.config import config
import utils.constants as constants
import subprocess

app = Flask(__name__)

with open(
        resource_path(constants.cache_path, persistent=True),
        "rb",
) as f:
    channel_data = pickle.load(f)


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
    url = find_by_id(channel_data, int(channel_id)).get("url", "")
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
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            return jsonify({'Message': 'Stream pushed successfully', 'Output': stdout.decode()}), 200
        else:
            return jsonify({'Error': 'Error pushing stream', 'Details': stderr.decode()}), 500
    except Exception as e:
        return jsonify({'Error': str(e)}), 500


def run_service():
    try:
        if not os.environ.get("GITHUB_ACTIONS"):
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


if __name__ == "__main__":
    run_service()
