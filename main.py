from flask import Flask
from turnoverOracle import turnoverOracle

turnover = turnoverOracle('28901061')
print(turnover)
print(type(turnover))

app = Flask(__name__)

@app.route('/')
def hello_world():
    return str(turnover)