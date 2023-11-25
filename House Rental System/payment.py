from datetime import datetime

# Get the current date
current_date = datetime.now().day

def reset(cur,db):
    if current_date == 21:
        cur.execute(f"select * from house inner join tenant on tenant.house_id = house.house_id")
        house_details = cur.fetchall()
        for house in house_details:
            house_id = house[0]
            land_lord_id = house[10]
            tenant_id = house[11]
            amount = house[3]
            date = datetime.now().date()
            cur.execute(f'''INSERT INTO payment (amount, status, payment_date, tenant_id, house_id, land_lord_id)
                            SELECT 
                                {amount},1,'{date}',{tenant_id},{house_id},{land_lord_id}
                            FROM DUAL
                            WHERE NOT EXISTS (
                                SELECT 1
                                FROM payment p
                                WHERE 
                                p.house_id = {house_id}
                                AND p.land_lord_id = {land_lord_id}
                                AND p.tenant_id = {tenant_id}
                                AND DATE(p.payment_date) = '{date}'
                            )''')
            db.commit()


    