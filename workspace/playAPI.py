from flask import Flask, request, jsonify, send_file
import os
import json
import subprocess

app = Flask(__name__)

@app.route('/', methods=['POST'])
def index():
    print("GOT A REQUEST!!!!")
    # params: bandwidth limit and frame_id? how to send this json over http?
    # solution: using post method
    video_name = request.args.get('video_name')
    bandwidth_dict = json.loads(request.data)

    with open('./profile-%s/profile-separated/bandwidthLimit.yml' %(video_name), 'w') as outfile:
        yaml.dump(bandwidth_dict, outfile, default_flow_style=False)
    
    # Updating the configuration file
    os.system("yq -i '.default.video_name = %s' configuration.yml" %(video_name))

    # Executing the program
    subprocess.run(["python", "entrance.py"])

    return "success"
    

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')