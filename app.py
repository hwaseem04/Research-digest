from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

## Global variable to store entire per user relevant tuples retireved from main db
DATA = None

app = Flask(__name__)
app.secret_key = "text123"

# Create table for available users signed in along with their passwords
def create_userListTable():
    conn = sqlite3.connect('userdatabase.db')
    cursor = conn.cursor()
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS userlist(
            userId text PRIMARY KEY,
            username text,
            password text,
            abstract text
        );
    ''')
    cursor.close()
    conn.close()

# Create table per user for storing summaries
def create_perUserTable(username, password):
    conn = sqlite3.connect('userdatabase.db')
    cursor = conn.cursor()
    
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {username}(
            id text PRIMARY KEY,
            title text,
            summary text
        );
    ''')

    cursor.execute('SELECT COUNT(userId) FROM userlist;')
    count = int(cursor.fetchall()[0][0])
    print("COUNT: ", count)

    cursor.execute(f'''
        INSERT INTO userlist (userId, username, password) VALUES ({count+1}, '{username}', '{password}');
    ''')
    session['new'] = 'true'

    conn.commit()
    cursor.close()
    conn.close()

def find_user(username, password):
    
    conn = sqlite3.connect('userdatabase.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM userlist;')
    data = cursor.fetchall()

    if len(data) == 0:
        # Create first user
        print("No User account available in")
        create_perUserTable(username, password)
        session['new'] = 'true'
    else:
        for row in data:
            if row[1].lower() == username.lower():
                if row[2] == password:
                    session['new'] = 'false'
                    print("Valid Password. Logging IN")
                    return username
                else:
                    print("Invalid password")
                    return 1
        
        # Create new user
        create_perUserTable(username, password)
        session['new'] = 'true'

    conn.close()
    return username

# Find and display relevant papers from DB of current user's interest
def find_relevant(username):
    conn = sqlite3.connect('userdatabase.db')
    cursor = conn.cursor()
    cursor.execute(f'''
        SELECT interest FROM userlist
        WHERE username='{username}';
    ''')
    interests = cursor.fetchall()[0][0]
    interests = tuple(interests.split(','))
    conn.close()

    conn = sqlite3.connect('dblite/papers.db')
    cursor = conn.cursor()

    if len(interests) == 1:
        cursor.execute(f'''
            SELECT * FROM papers
            WHERE category='{interests[0]}';
        ''')
    else:
        cursor.execute(f'''
            SELECT * FROM papers
            WHERE category IN {interests};
        ''')

    rows = cursor.fetchall()
    #print(rows)
    conn.close()
    return rows

def store_in_user_db(rows):
    conn = sqlite3.connect('userdatabase.db')
    cursor = conn.cursor()
    
    for i, row in enumerate(rows):
        query = f'''INSERT INTO {session['user']} VALUES ({i+1}, '{row[3]}.strip()', '{row[7].strip()}');'''
        #print(query)
        #cursor.execute(query)
    conn.commit()
    conn.close()

def addInterest(username, interest):
    conn = sqlite3.connect('userdatabase.db')
    cursor = conn.cursor()
    
    interest = ','.join(interest)
    cursor.execute(f'''
        UPDATE userlist SET interest='{interest}' 
        WHERE username='{username}';
    ''')

    conn.commit()
    conn.close()
def get_summary(text: str) -> str:
    import torch
    from transformers  import T5Tokenizer, T5ForConditionalGeneration, T5Config

    model = T5ForConditionalGeneration.from_pretrained(r'model/')
    tokenizer = T5Tokenizer.from_pretrained(r'tokenizer/')
    preprocessed_text = text.strip()
    input_text = "summarize: " + preprocessed_text
    tokenized_text = tokenizer.encode(input_text, return_tensors='pt')
    summary_ids = model.generate(tokenized_text, min_length=100, max_length=180)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    # print(summary)

    return summary


@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == "" or password == "":
            return redirect(url_for('login'))

        user = find_user(username, password)

        if (user == 1):
            return redirect(url_for('login'))

        session["user"] = username
        return redirect(url_for('profile'))
    else:
        if "user" in session:
            user = session["user"]
            return redirect(url_for('profile'))
        return render_template('login.html')

@app.route("/")
def index():
    create_userListTable()
    return redirect(url_for('login'))

@app.route("/profile",  methods=['POST', 'GET'])
def profile():
    global DATA
    if request.method == "POST":
        choices = dict(request.form)
        interest = []
        for value in choices.values():
            interest.append(value)
        if len(interest) == 0:
            return redirect(url_for('new_user'))
        print(f"Interest: {interest}")
        addInterest(session['user'], interest)
        session["set"] = "true"
        return redirect(url_for('profile'))
    else:
        if "user" in session:
            if session['new'] == 'true':
                session['new'] = 'false'
                return redirect(url_for('new_user'))
            user = session["user"]
            # if "stored" in session:
                #     ...
            # else:
            rows = find_relevant(user)
            store_in_user_db(rows)
            DATA = rows

            session["stored"] = "true"
            DATA = rows
            return render_template('profile.html', user=user, rows=rows)
        else:
            return redirect(url_for('login'))
@app.route("/paper-page", methods=['POST', 'GET'])
def paperpage():
    if request.method == 'POST':
        try :
            input = request.form['hugface']
            summary = get_summary(input)
            print("SUmmary: ", summary)
            return render_template('paperpage.html', rows=list(DATA[session['row_index']]) + [summary])
        except Exception as e:
            print(e)
        try:
            data = int((dict(request.form))['Index'])
            session['sum'] = 'true'
            session['row_index'] = data - 1
            return render_template('paperpage.html', rows=list(DATA[data-1]) + [""])
        except Exception as e:
            return render_template('paperpage.html', rows=list(DATA[session['row_index']]) + [""])
    else:
        print()
        return redirect(url_for('login'))
@app.route("/new")
def new_user():
    if "user" in session:
        return render_template('newuser.html', user=session['user'])
    else:
        return redirect(url_for('login'))

@app.route("/logout")
def logout():
    if "user" in session:
        session.pop("user", None)
    return redirect(url_for('login'))
    
@app.route("/about")
def fail():
    return render_template('about.html')

