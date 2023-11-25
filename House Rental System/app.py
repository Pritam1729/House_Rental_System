from flask import Flask, render_template,redirect,url_for, request
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import mysql.connector
from datetime import date
from payment import reset

app = Flask(__name__)

db=mysql.connector.connect(
   host="127.0.0.1",
   port="3306",
   user="root",
   passwd="Pritam@95272",
   database="house_rental_system"
)

cur = db.cursor()

reset(cur,db)

user_id = 0


@app.route('/')
def index():
    return render_template('home.html') 

# owner side backend  

@app.route('/owner_login',methods = ['POST','GET'])
def owner_login():
    msg = ''
    if request.method == 'POST' and 'ownername' in  request.form and 'password' in request.form:
        ownername = request.form['ownername']
        password = request.form['password']
        cur.execute("SELECT * FROM land_lord WHERE username = %s and password = %s",(ownername,password))
        accounts = cur.fetchone()
        if accounts:
            msg = "Land_Lord Logged In"
            return redirect(url_for('owner',msg = accounts[1]))
        else:
            msg = "Enter Correct Username or Password"
    return render_template('owner_login.html',msg = msg)

@app.route('/owner_register',methods = ['GET','POST'])
def owner_register():
    msg = ""
    if request.method == 'POST':
        ownername = request.form['ownername']
        password = request.form['password']
        name = request.form['name']
        contact = request.form['contact']
        # if len(contact) != 10 or contact[0] not in ['9','8','7']:
        #     msg = "Enter Correct Mobile Number"
        cur.execute(f"SELECT * FROM land_lord WHERE username = '{ownername}'")
        account = cur.fetchone()
        if account:
            msg = "The Account Already Exists"
        elif len(contact) != 10 or contact[0] not in ['9','8','7']:
            msg = "Enter a Valid Mobile Number"
        else:
            cur.execute("insert into land_lord (username,password,name,contact_info) values (%s,%s,%s,%s)",(ownername,password,name,contact))
            db.commit()
            msg = "Land_Lord Register"
            return redirect(url_for('owner', msg=ownername))
    return render_template('owner_register.html',msg = msg)

house_owner_register= ""        
    
@app.route('/house_register',methods = ['GET','POST'])
def house_register():
    global user_id
    global house_owner_register
    msg = ''  
    ok = request.args.get('id')
    msg = ""
    if ok !=None:
        user_id = ok
        cur.execute(f"SELECT * from land_lord where land_lord_id = '{user_id}'")
        house_owner_register = cur.fetchone()[1]

    if request.method == "POST":
        size = request.form['size']
        bhk = request.form['bhk']
        rent = request.form['rent']
        house_no = request.form['house_no']
        street_name = request.form['streetname']
        city = request.form['City']
        state = request.form['state']
        pincode = request.form['pincode']
        cur.execute(f"SELECT * FROM house WHERE house_no = '{house_no}' and city = '{city}' and state = '{state}' and pincode = '{pincode}'")
        account = cur.fetchone()
        if account:
            msg = "House Already Exist"
        else:
            print(user_id)
            print(type(user_id))
            cur.execute(f"insert into house (size,bhk,rent_amount,house_no,street_name,city,pincode,state,availibility_status,land_lord_id) values ({size},{bhk},{rent},'{house_no}','{street_name}','{city}','{pincode}','{state}',{1},{int(user_id)})")
            db.commit()
            msg = "House Registered"
    # message = {"msg" : msg,"username" : house_owner_register}
    return render_template('house.html',msg = msg,username = house_owner_register)


second_owner_id = None      
@app.route('/owner', methods = ['GET','POST'])
def owner():
    global second_owner_id
    name = request.args.get('msg')
    account = None
    users = None
    interest_house = None
    payment_pending = None
    maintenance_req_owner= []
    if name:
        second_owner_id = name
        
    # update the accept request
    if request.method == "POST":
        if 'accept' in request.form:
            accept_id = request.form['accept_data'].split(",")
            cur.execute(f"SELECT house_id from tenant where tenant_id = {accept_id[1]}")
            ok_house = cur.fetchone()
            if ok_house[0]:
                cur.execute(f"UPDATE house set availibility_status = 1 where house_id = {ok_house[0]}")
                db.commit()
                
            str = f"update tenant set house_id = {accept_id[0]} where tenant_id = '{accept_id[1]}'"
                
            cur.execute(f"update tenant set house_id = {accept_id[0]} where tenant_id = '{accept_id[1]}'")
            db.commit()
            # cur.execute(f"delete from interested where house_id = {accept_id[0]} and tenant_id = {accept_id[1]} and land_lord_id = {accept_id[2]}")
            cur.execute(f"call delete_interested_with_house_id({accept_id[0]})")
            db.commit()
            
        elif "reject" in request.form:
            reject_id = request.form['reject_data'].split(",")
            cur.execute(f"delete from interested where house_id = '{reject_id[0]}' and tenant_id = '{reject_id[1]}' and land_lord_id = '{reject_id[2]}'")
            db.commit()
        elif "done_data" in request.form:
            done_data = request.form['done_data'].split(",")
            cur.execute(f"delete from maintenance_req where main_req_id = '{done_data[0]}' and house_id = '{done_data[1]}' and tenant_id = '{done_data[2]}'")
            db.commit()
        elif "payment" in request.form:
            payment_id = request.form['payment']
            cur.execute(f"UPDATE payment SET status = 0 where payment_id = '{payment_id}'")
            db.commit()
            
            
    
            
    cur.execute(f"select * from land_lord inner join house on land_lord.land_lord_id = house.land_lord_id where land_lord.username = '{second_owner_id}'")
    account = cur.fetchall()
    if len(account) == 0:
        cur.execute(f"SELECT * from land_lord where username = '{second_owner_id}'")
        account = cur.fetchall()
        interest_house = [["No Request Found"]]
    else :
        cur.execute(f"SELECT * from house inner join interested on house.house_id = interested.house_id inner join tenant on interested.tenant_id = tenant.tenant_id where interested.land_lord_id = '{account[0][0]}'")
        interest_house = cur.fetchall()
    cur.execute(f"select * from house inner join payment on house.house_id = payment.house_id where payment.land_lord_id = {account[0][0]} and payment.status = 1")
    payment_pending = cur.fetchall()
    if not payment_pending:
        payment_pending = ["No pending Payments"]   
    
    cur.execute(f"SELECT * from maintenance_req inner join house on maintenance_req.house_id = house.house_id where maintenance_req.land_lord_id = '{account[0][0]}'")
    maintenance_req_owner = cur.fetchall()
    if not maintenance_req_owner:
        maintenance_req_owner = [["No request Found"]]
        
    total_house = 0
    cur.execute(f"SELECT count(*) as no_of_house from house where land_lord_id = '{account[0][0]}'")
    total_house = cur.fetchone()[0]
    return render_template('owner_page.html', account = account,not_interested = interest_house,maintenance_owner = maintenance_req_owner,payment_pending = payment_pending,total_house = total_house)


# costumer side backend

@app.route('/user_login', methods = ['GET','POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cur.execute('SELECT * FROM tenant WHERE username = %s AND password = %s',(username,password))
        account = cur.fetchone()
        if account:
            msg = 'Logged In Successfully'
            return redirect(url_for('user_page',name = username))
        else:
            msg = 'Incorrect username/password'
    return render_template('User_login.html',msg = msg)

@app.route('/user_register',methods = ['GET','POST'])
def register():
    msg = ''
    if request.method == "POST" and 'username' in request.form and 'password' in request.form:
        print(request)
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        number = request.form['number']
        employment_status = 0
        if "employment" in request.form:
            employment_status = request.form['employment']
        marital_status = 0
        if "marital" in request.form:
            marital_status = request.form['marital']
        age = request.form['age']
        str = f"SELECT * FROM tenant WHERE username = '{(username)}'"
        print(len(number))
        print(number[0] not in [9,8,7])
        print(str)
        cur.execute(str)
        account = cur.fetchone()
        print(account)
        if account:
            msg = "Account Already Exists"
        elif len(number) != 10 or number[0] not in ['9','8','7']:
            msg = "Enter a Valid Mobile Number"
        elif int(age) < 19 or int(age) > 100:
            msg = "Enter Correct Age"
        else:
            cur.execute('INSERT INTO tenant (username, password, age, contact_info, employment_info,tanant_name,marital_status) VALUES (%s,%s,%s,%s,%s,%s,%s)',(username,password,int(age),number,employment_status,name,marital_status))
            db.commit()
            msg = "User Registered"
            return redirect(url_for('user_page',name = username))
    return render_template('user_register.html',msg = msg)


user_name = 0
@app.route('/user_page',methods = ['GET','POST'])
def user_page():
    msg = ''
    global user_name
    house_acquired = []
    house_maintain = []
    payment_list = []
    id = request.args.get('name')
    
    if request.method == 'POST':
        payment_id = request.form['payment']
        cur.execute(f"UPDATE payment SET status = 0 where payment_id = '{payment_id}'")
        db.commit()
        
        
    if id:
        user_name = id
    str = f"SELECT * FROM tenant WHERE username = '{user_name}'"
    cur.execute(str)
    account = cur.fetchone()
    
    cur.execute(f"SELECT * FROM house inner join payment on payment.house_id = house.house_id where payment.tenant_id = '{account[0]}' and payment.status = 1")
    payment_list = cur.fetchall()
    if not payment_list:
        payment_list = ["No Payment Request Found"]
        
    cur.execute(f"SELECT * from house  where house_id = '{account[-1]}'")
    house_acquired = cur.fetchone()
    if not house_acquired:
        house_acquired = ["No House found"]
        
    # cur.execute(f"SELECT * from maintenance_req where tenant_id = '{account[0]}' order by request_date DESC'")
    cur.execute(f"SELECT * from maintenance_req where tenant_id = '{account[0]}' order by request_date DESC")
    house_maintain = cur.fetchall()
    if not house_maintain:
        house_maintain = [["No Request Found"]]
        
    cur.execute(f"select interested.house_id from tenant inner join interested on tenant.tenant_id = interested.tenant_id where interested.approved = 0 and tenant.username = '{user_name}'")
    ok = cur.fetchall()
    not_approved = []
    for house in ok:
        cur.execute(f"select * from house where house_id = '{house[0]}'")
        not_approved.append(cur.fetchone())
    
    return render_template("user_page.html",account = account,not_approved = not_approved,house_acquire = house_acquired,house_maintain = house_maintain,payment_list = payment_list)

search_user_id = 0
tenant_name = 0
@app.route('/search',methods = ['GET','POST'])
def search():
    global search_user_id
    global tenant_name
    
    id = request.args.get('id')
    if id:
        search_user_id = id
    print(search_user_id)
    if search_user_id != 0:
        cur.execute(f"select username from tenant where tenant_id = {search_user_id}")
        tenant_name = cur.fetchone()
    account =[[]]
    if request.method == 'POST':
        search_city = request.form.get('search_city')
        price_range = int(request.form['price_range'])
        bhk = int(request.form['bhk'])
        if search_city:
            if price_range != 0 and bhk != 0:
                cur.execute(f"select * from house where city = '{search_city}' and bhk = '{bhk}' and rent_amount >= '{1000}' and rent_amount <= '{price_range}' and availibility_status = 1")
                account = cur.fetchall()
            elif price_range != 0:
                cur.execute(f"select * from house where city = '{search_city}' and rent_amount >= '{1000}' and rent_amount <= '{price_range}' and availibility_status = 1 order by rent_amount")
                account = cur.fetchall()
            elif bhk != 0:
                cur.execute(f"select * from house where city = '{search_city}' and bhk = '{bhk}' and availibility_status = 1 order by rent_amount")
                account = cur.fetchall()
            else:
                cur.execute(f"SELECT * from house where city = '{search_city}' and availibility_status = 1 ORDER BY rent_amount")
                account = cur.fetchall()
            if len(account) == 0:
                account = [[]]
                account[0].append("No House Found")
    return render_template('search.html', account = account,user_search_id = search_user_id,name = tenant_name)

house_details_id = 0
user_details_id = 0
land_details_id = 0
@app.route('/detail',methods = ['POST','GET'])
def detail():
    msg = ''
    global house_details_id
    global user_details_id
    global land_details_id
    id = request.args.get('id')
    id2 = request.args.get('user_search_id')
    if id2:
        user_details_id = id2
    if id:
        house_details_id = id
        
    cur.execute(f"SELECT * from house where house_id = '{house_details_id}'")
    account = cur.fetchone()
    cur.execute(f"SELECT * from land_lord where land_lord_id = '{account[-1]}'")
    landlord = cur.fetchone()
    if landlord:
        land_details_id = landlord[0]
    print("house = ",house_details_id)
    print("land_lord = ",land_details_id)
    print("user_id = ",user_details_id)
    if request.method == 'POST':
        cur.execute(f"SELECT * from interested where land_lord_id = '{land_details_id}' and house_id = '{house_details_id}' and tenant_id = '{user_details_id}'")
        acc = cur.fetchone()
        if acc:
            msg = "Request Already Submitted"
        else:
            cur.execute(f"INSERT INTO interested (tenant_id,land_lord_id,house_id,approved) values ('{user_details_id}','{land_details_id}','{house_details_id}',0)")
            db.commit()
            msg = "Done"
        
    return render_template('house_details.html',house = account,landlord = landlord,msg = msg,id = user_details_id)           

house_main_id = 0
land_main_id =0
tenant_main_id = 0
@app.route('/maintenance',methods = ["POST","GET"])
def maintenance():
    msg = ''
    global house_main_id,land_main_id,tenant_main_id
    ok1 = request.args.get('house_id')
    ok2 = request.args.get('tenant_id')
    ok3 = request.args.get('land_lord_id')
    account= None
    if ok1 and ok2 and ok3:
        house_main_id = ok1
        land_main_id = ok3
        tenant_main_id = ok2
        cur.execute(f"select username from tenant where tenant_id = {tenant_main_id}")
        account = cur.fetchone()
        print(account[0])
    
    if request.method == "POST":
        subject = request.form['subject']
        description = request.form['description']
        request_date = date.today()
        cur.execute(f"INSERT into  maintenance_req (house_id,tenant_id,land_lord_id,request_date,subject,description,status) values ('{house_main_id}','{tenant_main_id}','{land_main_id}','{request_date}','{subject}','{description}',1)")
        db.commit()
        msg = "Done"
    return render_template('maintenance_req.html',msg = msg,account = account)
           
    
    
if __name__ == '__main__':
    app.run(debug = True)   
    
    
    
    
    


    


