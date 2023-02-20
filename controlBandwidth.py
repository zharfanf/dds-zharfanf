from flask import Flask, request, send_file, jsonify
import os

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    print("GOT A REQUEST!!!!")
    bandwidth = request.args.get('bandwidth')

    address = request.args.get('address')

    os.system("sudo ./traffic-control.sh -i --dspeed=%s %s" % (bandwidth, address))

    return "success"
    


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')