import mysql.connector
from config import database_config

database_name = database_config['database']

def create_database(database_name):
    conn = mysql.connector.connect(user = database_config['user'], password = database_config['password'],
    host = database_config['host'])
    
    cursor_sql = conn.cursor()
    
    cursor_sql.execute(f'drop database if exists {database_name}')
    cursor_sql.execute(f"create database {database_name}")

    cursor_sql.close()
    conn.close()
    print(f'database {database_name} created successfully')

#----------------------------------------------------------------------------------------------

def create_table_employee():
    conn = mysql.connector.connect(**database_config)
    cursor_sql = conn.cursor()

    cursor_sql.execute('''
                        create table employee (

                        `employee_id`           int unsigned not null auto_increment primary key,
                        `user_cid`              bigint unique,
                        `first_name`            varchar(75),
                        `last_name`             varchar(75),
                        `address`               varchar(255),
                        `phone_number`          varchar(11),
                        `birth_day`             date,
                        `email_address`         varchar(150) unique,
                        `position`              varchar(100),
                        `base_salary`           int unsigned,
                        `is_boss`               enum('yes','no') not null,
                        `register_date`         datetime default current_timestamp,
                        `last_update`           timestamp default current_timestamp on update current_timestamp
                        );
    ''')

    cursor_sql.close()
    conn.close()
    print('employee table created successfully')

#----------------------------------------------------------------------------------------------

def create_table_attendance():
    conn = mysql.connector.connect(**database_config)
    cursor_sql = conn.cursor()

    cursor_sql.execute('''
                        create table attendance (

                        `attendance_id`         int unsigned not null primary key auto_increment,
                        `employee_id`           int unsigned,
                        `shift`                 enum('day','night') default 'day',
                        `night_hours`           FLOAT,
                        `overtime_hours`        FLOAT,
                        `worked_hours`          FLOAT,
                        foreign key (employee_id) references employee(employee_id)

                        );
    ''')

    cursor_sql.close()
    conn.close()
    print('attendance table created successfully')

#---------------------------------------------------------------------------------------------
def create_table_bonus():
    conn = mysql.connector.connect(**database_config)
    cursor_sql = conn.cursor()

    cursor_sql.execute('''
                        create table bonus (

                        `bonus_id`              int unsigned not null primary key auto_increment,
                        `employee_id`           int unsigned,
                        `bonus_type`            varchar(50),
                        `bonus_amount`          int,
                        foreign key (employee_id) references employee(employee_id)

                        );
    ''')

    cursor_sql.close()
    conn.close()
    print('bonus table created successfully')


#----------------------------------------------------------------------------------------------
def create_table_payroll():
    conn = mysql.connector.connect(**database_config)
    cursor_sql = conn.cursor()

    cursor_sql.execute('''
                        create table payroll (

                        `payroll_id`            int unsigned not null primary key auto_increment,
                        `employee_id`           int unsigned,
                        `start_date`            date,
                        `end_date`              date,
                        `total_hours`           FLOAT,
                        `total_overtime`        FLOAT,
                        `total_night_hours`     FLOAT,
                        `gross_salary`          int,
                        `tax_amount`            int,
                        `bonus_id`              int unsigned,
                        `final_salary`          int,
                        `payment_date`          date,
                        foreign key (employee_id) references employee(employee_id),
                        foreign key (bonus_id) references bonus(bonus_id)

                        );
    ''')

    cursor_sql.close()
    conn.close()
    print('payroll table created successfully')


#---------------------------------------------------------------------------
def insert_employees():
    conn = mysql.connector.connect(**database_config)
    cursor = conn.cursor()

    sql = """
    INSERT INTO employee (
        user_cid,
        first_name,
        last_name,
        address,
        phone_number,
        birth_day,
        email_address,
        position,
        base_salary,
        is_boss
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    data = [
        (6716225040, 'بنیامین', 'نادری', 'خانی آباد', '09225014668', '2007-03-07', 'benyamin@gmail.com', 'مدیر',200, 'yes'),
        (6123711795, 'نقی', 'معمولی', 'علی آباد', '09212014668', '1998-03-07', 'naghi@gmail.com', 'سرپرست', 180,'yes'),
        (8396189092, 'نجم الدین', 'شریعتی', 'تهران', '09365014668', '1971-05-07', 'najm@gmail.com', 'مجری',105 ,'no')
    ]

    cursor.executemany(sql, data)
    conn.commit()

    cursor.close()
    conn.close()
    print('Employees inserted successfully')


#----------------------------------------------------------------------------------------------
def insert_attendance():
    conn = mysql.connector.connect(**database_config)
    cursor = conn.cursor()

    sql = """
    INSERT INTO attendance (
        employee_id,
        night_hours,
        overtime_hours,
        worked_hours
    ) VALUES (%s, %s, %s, %s)
    """

    data = [
        (1, 0, 120, 400),
        (2, 50, 70, 250),
        (3, 70, 10, 120)
    ]

    cursor.executemany(sql, data)
    conn.commit()

    cursor.close()
    conn.close()
    print('Attendance records inserted successfully')


#----------------------------------------------------------------------------------------------


if __name__ == '__main__':
    create_database(database_name)
    create_table_employee()
    create_table_attendance()
    create_table_bonus()
    create_table_payroll()
    insert_employees()
    insert_attendance()
    print('Done')
    
