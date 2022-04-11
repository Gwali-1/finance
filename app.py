
from crypt import methods
from curses.ascii import isdigit
import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, request_tearing_down, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd,round_this,chacher,isfloat

# Configure application

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd
app.jinja_env.filters["round"] = round_this

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response





#index

@app.route("/")
@login_required
def index():
    userid = session["user_id"]
    current_prices = {}
    total_stock_value = 0
   
    owned = db.execute("SELECT symbol FROM user_stocks WHERE user_id = ?",userid)

    for own in owned:
        stock = lookup(own["symbol"])
        if not stock:
            return apology("something went wrong with API call")
        current_prices[own["symbol"]] = stock["price"]

    stock_info = db.execute("SELECT * FROM user_stocks WHERE user_id = ?",userid)

    for info in stock_info:
        if info["shares"] == 0:
            db.execute("DELETE FROM user_stocks WHERE symbol = ? AND user_id = ?",info.get("symbol"),userid)

    stock_info = db.execute("SELECT * FROM user_stocks WHERE user_id = ?",userid)

    user_info = db.execute("SELECT cash FROM users WHERE id = ?",userid)
    for share_number in stock_info:
        total_stock_value+= share_number["shares"] * current_prices[share_number["symbol"]]
    
    return render_template("index.html",stockprice = current_prices, user_info=user_info[0], stock_info=stock_info,total_stock_value=total_stock_value)

    # """Show portfolio of stocks"""
    # return apology("TODO")







#buy

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        share = request.form.get("shares")
        user_id = session["user_id"]
        print(type(share))

        if not share.isnumeric():
            return apology("enter valid inptuts")


        if not symbol or not share or int(share) < 0  :
            return apology("Missing inputs")
        share = float(share)
        stock_quote = lookup(symbol)
        if not stock_quote:
            return apology("ERROR")

        
        rows = db.execute("SELECT * FROM users WHERE id = ?",user_id)
        
        if rows:
            if rows[0]["cash"] < stock_quote["price"] * share:
                return apology("Dont have enough funds")
        
        balance = rows[0]["cash"] - stock_quote["price"] * share

        check = db.execute("SELECT * FROM user_stocks WHERE user_id = ? AND symbol = ?",user_id,symbol)

        #getting date and time
        datetimeobj = datetime.now()
        datestr = datetimeobj.strftime("%d-%b-%Y")
        timeobj = datetimeobj.time()
        timestr=  timeobj.strftime("%H:%M:%S.%f")


        # print(check[0]["symbol"])
        if len(check) == 1:
            if check[0].get("symbol") == symbol:
                db.execute("UPDATE user_stocks SET shares =? WHERE user_id = ? AND symbol = ?",(check[0]["shares"] + share), user_id , symbol)
                db.execute("UPDATE users SET cash = ? WHERE id = ?",balance,user_id)
                db.execute("INSERT INTO history(id,symbol,stockname,shares,date,time,action) VALUES(?,?,?,?,?,?,?)", user_id, symbol,stock_quote.get("name"), share, datestr, timestr,"BUY")
                flash("purchase Succesful")
                return redirect("/")


        db.execute("UPDATE users SET cash = ? WHERE id = ?",balance,user_id)

        db.execute("INSERT INTO  user_stocks(stockname,symbol,shares,user_id) VALUES(?,?,?,?)",stock_quote.get("name"),stock_quote["symbol"],share,user_id)
        
        db.execute("INSERT INTO history(id,symbol,stockname,shares,date,time,action) VALUES(?,?,?,?,?,?,?)", user_id, symbol,stock_quote.get("name"), share, datestr, timestr,"BUY")
        flash("Purchase Succesful!")
        return redirect("/")
       
     
    return render_template("buy.html")






#history

@app.route("/history")
@login_required
def history():
    userid = session["user_id"]
    History = db.execute("SELECT * FROM history WHERE id = ?", userid)
    """Show history of transactions"""
    return render_template("history.html",History=History)




#login

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")




#logout

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")





#quote

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("Enter Valid Stock Symbol")
        stock_quote = lookup(symbol)
        if stock_quote:
            return render_template("quoted.html",stock_info = stock_quote)
        else:
            return apology("Enter Valid Symbol")

        """Get stock quote."""
        # return apology("TODO")

    return render_template("quote.html")
    








#register

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
    
        """Register user"""
        name = request.form.get("username")
        password = request.form.get("password")
        confrim_Pass = request.form.get("confirmation") 
        row = db.execute("SELECT * FROM users WHERE  username = ?" , name)    
        if not name:
            return apology("sorry enter valid username")
        if len(row) == 1:
            return apology("user already  exist")
        
        if not password or password != confrim_Pass:
            return apology("invalid Password")

        db.execute("INSERT INTO users(username, hash) VALUES (?,?)",name , generate_password_hash(password))
        flash("Registered")
        return render_template("login.html")


    return render_template("register.html")





#sell

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    userid = session["user_id"]
    stock_info = db.execute("SELECT * FROM user_stocks WHERE user_id = ?",userid)
    print(stock_info)
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        userid = session["user_id"]
        stock_info = db.execute("SELECT * FROM user_stocks WHERE user_id = ? AND symbol = ?",userid,symbol)
        if not symbol or not shares:
            return apology("missing inputs")

        shares = float(shares)
        if (shares) < 0 :
            return apology("invalid input for shares")

        stock_availability = db.execute("SELECT * FROM user_stocks WHERE symbol = ? AND user_id = ?",symbol,userid)
        userbalance = db.execute("SELECT cash FROM users WHERE id = ?",userid)

        if len(stock_availability) != 1:
            return apology("you don't own this stock")
    

        if shares > stock_info[0].get("shares"):
            print(stock_info[0].get("shares"))
            return apology("you dont own that many shares")

        stock_quote = lookup(symbol)
        income = stock_quote.get("price") * shares

        try:
            db.execute("UPDATE users SET cash = ? WHERE id = ?",userbalance[0].get("cash") + income, userid)
            print(shares)
            db.execute("UPDATE user_stocks  SET shares = ? WHERE user_id = ? AND symbol = ?",(stock_info[0].get("shares") - shares) ,userid,symbol)
            datetimeobj = datetime.now()
            datestr = datetimeobj.strftime("%d-%b-%Y")

            timeobj = datetimeobj.time()
            timestr=  timeobj.strftime("%H:%M:%S.%f")
            db.execute("INSERT INTO history(id,symbol,stockname,shares,date,time,action) VALUES(?,?,?,?,?,?,?)",userid, symbol,stock_quote.get("name"), shares, datestr, timestr,"SELL")
            flash("SOLD!")
            return redirect("/")
        except Exception as e:
            flash(e)


    return render_template("sell.html",stocks = stock_info)

    # """Sell shares of stock"""
    # return apology("TODO")



#balance_topup


@app.route("/topup", methods = ["POST","GET"])
def topup():

    if request.method == "POST":
        amount = request.form.get("amount")
        if not amount or not isfloat(amount):
            return apology("Please enter valid amount")
        
        user_id = session.get("user_id")


        user = db.execute("SELECT * FROM users WHERE id = ?",user_id)
        print(user[0].get("cash"))
        if len(user) == 1:
            new_balance = user[0].get("cash") + float(amount)
            try:
                db.execute("UPDATE users SET cash = ? WHERE id = ?" , new_balance,user_id)
                user = db.execute("SELECT * FROM users WHERE id = ?",user_id)
                print(user[0].get("cash"))
                flash("Balance Topped Up!")
            except Exception:
                flash("Couldn't Update Balance")
            return redirect("/")

    return render_template("topup.html")













app.run(host = "172.20.10.2",debug=True)