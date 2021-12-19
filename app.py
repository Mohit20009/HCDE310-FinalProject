import urllib.parse, urllib.request, urllib.error, json
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from numerize import numerize

apikey ="13a81fce035965cc6511a08dbb48dda169e1eabe"
url_price = "https://api.nomics.com/v1/currencies/ticker"
url_fiat_exchgane_rates = "https://api.nomics.com/v1/exchange-rates"

def create_table_data(data):
    db.session.query(Coin).delete()
    db.session.commit()
    for i in range(len(data)):
        if((not data[i].get('rank') == None)and (not data[i].get('symbol') == None)):
            if (not data[i].get('market_cap') == None):
                market = numerize.numerize(int(data[i].get('market_cap')))
            else:
                market = "Unkown"
            if (not data[i].get('1d') == None):
                str_pct_change = format(float(data[i].get('1d').get('price_change_pct'))*100,".2f") + "%"
                pct_change = float(data[i].get('1d').get('price_change_pct'))
            else:
                str_pct_change = "Unkown"
                pct_change = None
            if (not data[i].get('high') == None):
                all_time_high = data[i].get('high')
            else:
                all_time_high = "Unkown"

            coin = Coin(rank = data[i].get('rank'),
                        logo = data[i].get('logo_url'),
                        name=data[i].get('name'),
                        symbol = data[i].get('symbol'),
                        price = data[i].get('price'),
                        one_day_change = pct_change,
                        str_one_day_change = str_pct_change,
                        all_time_high = all_time_high,
                        market_cap = market
            )
            db.session.add(coin)
    db.session.commit()

def pretty(obj):
    return json.dumps(obj, sort_keys=True, indent=2)

#-- Part 1 --
# This function handles any errors due to HTTP or connection related exceptions
def get_price_data_safe(currency = "USD", crypto = "BTC"):
    try:
        return(get_data(currency, crypto))
    except urllib.error.URLError as e:
        st = "Error trying to retrieve data: "
        if hasattr(e, "code"):
            print(st, e)
        elif hasattr(e, 'reason'):
            print("We failed to reach a server")
            print("Reason: ", e.reason)
        return None

#-- Part 2 --
#The function below returns a dictionary of data about current price, circulating supply, market cap, etc. for a paticular cryptocurrency
# It takes in two parameter
#   -- currency: fiat currency or other cryptocurrency, default is USD (United States Dollar)
#   -- crypto: any crypto currency coin symbol, default is BTC (Bitcoin)
def get_data(currency = "USD", crypto = "BTC"):
    paramstr = urllib.parse.urlencode({'key': apikey, 'convert': currency})
    request = url_price + "?" + paramstr
    data = urllib.request.urlopen(request).read()
    data = json.loads(data.decode('utf-8'))
    return data

fiat_list = []

def fiat_currency():
     paramstr = urllib.parse.urlencode({'key': apikey})
     request = url_fiat_exchgane_rates + "?" + paramstr
     exchange_rate = urllib.request.urlopen(request).read()
     exchange_rate = json.loads(exchange_rate.decode('utf-8'))
     for i in range(len(exchange_rate)):
         fiat_list.append(exchange_rate[i].get("currency"))


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Coin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rank = db.Column(db.Integer, index=True)
    logo = db.Column(db.String(1000), index=True)
    name = db.Column(db.String(50), index=True)
    symbol = db.Column(db.String(10), index=True)
    price = db.Column(db.Float, index=True)
    one_day_change = db.Column(db.Float, index=True)
    str_one_day_change = db.Column(db.String(100), index=True)
    all_time_high = db.Column(db.String(100), index=True)
    market_cap = db.Column(db.String(100), index=True)

db.create_all()

class currency():
    current_currency = "USD"

@app.route('/')
def index():
    coin = Coin.query
    display_text = "Showing results in: %s" % (currency.current_currency)
    return render_template('table.html', title='CryptoExplorer',
                           coins = coin,
                           currency = display_text)

@app.route('/gresponse')
def fiat():
    fiat_name = request.args.get('fiatname')
    if(fiat_name.upper() in fiat_list):
        data = get_price_data_safe(currency = fiat_name.upper())
        create_table_data(data)
        coin = Coin.query
        currency.current_currency = fiat_name.upper()
        display_text = "Showing results in: %s"%(currency.current_currency)
        return render_template('table.html', title='CryptoExplorer',
                                   coins = coin,
                               currency = display_text)
    else:
        coin = Coin.query
        display_text = "Error: No such currency as %s.\n Showing results in: %s" % (fiat_name, currency.current_currency)
        return render_template('table.html',
                               title = "CryptoExplorer",
                               coins = coin,
                               currency = display_text)

if __name__ == '__main__':
    data = get_price_data_safe(currency="USD")
    create_table_data(data)
    fiat_currency()
    app.run()
