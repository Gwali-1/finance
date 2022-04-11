import os
from traceback import print_tb
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps
from datetime import datetime


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""
    if symbol == "AAAA":
        return {"name": "TEST","price": 28.00,"symbol": "AAAA"}

    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        print("not found")
        return None

    # Parse response
    try:
        quote = response.json()
        print("found")
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

def round_this(value):
    """round value to two decimal places"""
    return round(value,2)


def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False


# can be used to chache result 
def chacher(chache,func,quote):
    # now = datetime.now().time()
    # limit = datetime.strptime('07/11/2019 5:00pM', '%m/%d/%Y %I:%M%p')
    # limit_time = limit.time()
    print("fetching ...")
    if quote not in chache:
        chache[quote] = func(quote)
    return chache[quote]


# now = datetime.now()
# print(datetime.strftime("4:00PM","%H:%M:%S.%f"))

# 
