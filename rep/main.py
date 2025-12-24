import telebot
from telebot.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
import os
from datetime import datetime, time
import logging
import mysql.connector
from config import database_config
from config import API_TOKEN, CHANNEL_ID, ADMIN_CID

bot = telebot.TeleBot(API_TOKEN)

user_steps = {}
user_data = {}

commands = {

    'start'                 :   'شروع مجدد ربات',
    'show_employees'       :   'نمایش کل کارمندان',
    'show_bosses'       :   'نمایش کل رئیس‌ ها',
    'show_users'              :   'نمایش کل کارکنان',
    'salary_payment'        :   'صدور فیش حقوقی'
    
}


def database_information(SQL_query_code, params=None, return_last_id=False):
    conn = mysql.connector.connect(
        user=database_config['user'],
        password=database_config['password'],
        host=database_config['host'],
        database=database_config['database']
    )
    cursor_sql = conn.cursor()
    result = None
    try:
        if params:
            cursor_sql.execute(SQL_query_code, params)
        else:
            cursor_sql.execute(SQL_query_code)

        if SQL_query_code.strip().lower().startswith("select"):
            result = cursor_sql.fetchall()
        else:
            conn.commit()
            if return_last_id:
                result = cursor_sql.lastrowid
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        cursor_sql.close()
        conn.close()
    return result



def check_register(cid):
    if cid == ADMIN_CID:
        return 'ADMIN'
    
    result = database_information(
        "SELECT user_cid FROM employee WHERE user_cid = %s ",
        (cid,)
    )
    if result:
        return True 
    else:
        return False  
    

def save_work_time(cid, work_type, start_cycle, end_cycle):

    start_total = start_cycle.hour * 3600 + start_cycle.minute * 60 + start_cycle.second
    end_total = end_cycle.hour * 3600 + end_cycle.minute * 60 + end_cycle.second
    final_time = end_total - start_total

    info = database_information(
        'SELECT employee_id FROM employee WHERE user_cid=%s',
        (cid,)
    )
    if not info:
        return

    employee_id = info[0][0]

    if work_type == 'simple_work':
        column_name = 'work_hours'
    elif work_type == 'night_work':
        column_name = 'night_hours'
    elif work_type == 'overtime_work':
        column_name = 'overtime_hours'
    else:
        return

    result = database_information(
        f'SELECT {column_name} FROM attendance WHERE employee_id=%s',
        (employee_id,)
    )
    previous_time = result[0][0] if result else 0

    final_time += previous_time

    database_information(
        f'UPDATE attendance SET {column_name}=%s WHERE employee_id=%s',
        (final_time, employee_id)
    )



def listener(messages):
    """
    When new messages arrive TeleBot will call this function.
    """
    for m in messages:
        if m.content_type == 'text':
            logging.info(f'{m.chat.first_name} [{str(m.chat.id)}]: {m.text}')
        elif m.content_type == 'photo':
            logging.info(f'{m.chat.first_name} [{str(m.chat.id)}]: sent photo')
        elif m.content_type == 'contact':
            logging.info(f'{m.chat.first_name} [{str(m.chat.id)}]: sent contact')
        else:
            logging.info(f'{m.chat.first_name} [{str(m.chat.id)}]: another content type: {m.content_type}')          

        
        
bot.set_update_listener(listener)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    cid = message.chat.id
    print(cid)
    regester = check_register(cid)

    if regester == 'ADMIN':
        bot.copy_message(cid,CHANNEL_ID,26)

    elif regester == True:

        result = database_information(
            "SELECT is_boss FROM employee WHERE user_cid = %s",
            (cid,)
        )
        if result:
            is_boss = result[0][0]
        else:
            is_boss = None

        if is_boss == 'yes':
            bot.copy_message(cid,CHANNEL_ID,21)
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(
                        KeyboardButton("➕اضافه کردن کارمند"),
                        KeyboardButton("حذف کارمند❌")
                        )
            
            markup.add(
                        KeyboardButton('جست‌و‌جو👀'),
                        KeyboardButton("🖋️ویرایش")
                        )
            
            markup.add(KeyboardButton("💰 پاداش"))
            markup.add(
                        KeyboardButton("✅ ثبت ورود"),
                        KeyboardButton("🛑 ثبت خروج")
            )
            markup.add(
                        KeyboardButton("حساب کاربری من 👤"),
                        KeyboardButton("📝 ساعت های کاری")
            )
            markup.add(KeyboardButton("پشتیبانی📞"))
            bot.send_message(cid, "منوی شما:", reply_markup=markup)
            
        else:
            bot.copy_message(cid,CHANNEL_ID,22)
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(
                        KeyboardButton("✅ ثبت ورود"),
                        KeyboardButton("🛑 ثبت خروج")
                        )      
            markup.add(KeyboardButton("حساب کاربری من 👤")),
            markup.add(KeyboardButton("📝 ساعت های کاری"))
                        
            markup.add(
                        KeyboardButton("پشتیبانی📞")
                        )      
            bot.send_message(cid, "منوی شما:", reply_markup=markup)

    else:
        bot.send_message(cid,'احراز  هویت:')
        bot.send_message(cid,'نام خود را وارد کنید:')
        user_steps[cid] = 'authentication'
            

@bot.message_handler(commands=['show_employees'])
def show_all_employees(message):
    cid = message.chat.id
    data = database_information('select * from employee where is_boss="no";')
    if not data:
        bot.send_message(cid,'هیچ کارمندی در سیستم نیست!')
        return
    elif data:
        text = "📋 لیست کارمندان:\n" 
        for row in data:
            text += f'''

شناسه:   {row[0]}
نام:   {row[2]}
نام خانوادگی:  {row[3]}
آدرس:  {row[4]}
شماره تماس:  {row[5]}
تاریخ تولد:  {row[6]}
ایمیل:  {row[7]}
موقعیت شغلی:  {row[8]}
پایه حقوق:   {row[9]}
-----------------------------------------------------------------------
'''
        bot.send_message(cid, text)
    else:
        bot.send_message(cid,'خطا در انجام عملیات لطفا بعدا تلاش کنید')




@bot.message_handler(commands=['show_bosses'])
def show_all_bosses(message):
    cid = message.chat.id
    data = database_information('select * from employee where is_boss="yes";')
    if not data:
        bot.send_message(cid,'هیچ رئیسی در سیستم نیست!')
        return
    elif data:
        text = "📋 لیست رئیس ها:\n" 
        for row in data:
            text += f'''

شناسه:   {row[0]}
نام:   {row[2]}
نام خانوادگی:  {row[3]}
آدرس:  {row[4]}
شماره تماس:  {row[5]}
تاریخ تولد:  {row[6]}
ایمیل:  {row[7]}
موقعیت شغلی:  {row[8]}
پایه حقوق:   {row[9]}
-----------------------------------------------------------------------
'''
        bot.send_message(cid, text)
    else:
        bot.send_message(cid,'خطا در انجام عملیات لطفا بعدا تلاش کنید')



@bot.message_handler(commands=['show_users'])
def show_all_users(message):
    cid = message.chat.id
    data = database_information('select * from employee;')
    if not data:
        bot.send_message(cid,'هیچ یک از کارکنان در سیستم نیستند!')
        return
    elif data:
        text = "📋 لیست کارکنان:\n" 
        for row in data:
            text += f'''

شناسه:   {row[0]}
نام:   {row[2]}
نام خانوادگی:  {row[3]}
آدرس:  {row[4]}
شماره تماس:  {row[5]}
تاریخ تولد:  {row[6]}
ایمیل:  {row[7]}
موقعیت شغلی:  {row[8]}
پایه حقوق:   {row[9]}
-----------------------------------------------------------------------
'''
        bot.send_message(cid, text)
    else:
        bot.send_message(cid,'خطا در انجام عملیات لطفا بعدا تلاش کنید')


@bot.message_handler(commands=['salary_payment'])
def send_salary_payment(message):
    admin_cid = message.chat.id
    payment_date = datetime.now().date()
    tax_percent = 10  # درصد مالیات

    users = database_information(
        "SELECT employee_id, user_cid, first_name, last_name, base_salary FROM employee WHERE user_cid IS NOT NULL"
    )

    payroll_summary = "" 
    for row in users:
        employee_id, user_cid, first_name, last_name, base_salary = row

        attendance = database_information(
            "SELECT worked_hours, overtime_hours, night_hours FROM attendance WHERE employee_id=%s",
            (employee_id,)
        )

        if not attendance:
            bot.send_message(admin_cid, f"کاربر {first_name} {last_name} هیچ ثبت ورود ندارد.")
            continue

        worked_hours, overtime_hours, night_hours = attendance[0]
        worked_hours = float(worked_hours or 0)
        overtime_hours = float(overtime_hours or 0)
        night_hours = float(night_hours or 0)
        base_salary = float(base_salary or 0)

        bonus_data = database_information(
            "SELECT bonus_amount FROM bonus WHERE employee_id=%s",
            (employee_id,)
        )
        bonus_amount = float(bonus_data[0][0]) if bonus_data else 0

        worked_payment = worked_hours * base_salary
        overtime_payment = overtime_hours * base_salary * 1.35
        night_payment = night_hours * base_salary * 1.45

        gross_salary = worked_payment + overtime_payment + night_payment
        tax_amount = gross_salary * tax_percent / 100
        final_salary = gross_salary - tax_amount + bonus_amount

        database_information(
            '''INSERT INTO payroll(
                employee_id, total_hours, total_overtime, total_night_hours,
                gross_salary, tax_amount, bonus_id, final_salary, payment_date
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
            (employee_id, worked_hours, overtime_hours, night_hours,
             gross_salary, tax_amount, None, final_salary, payment_date)
        )

        try:
            bot.send_message(user_cid, f"""
💳 فیش حقوقی شما

👤 {first_name} {last_name}
⏱ ساعت کاری: {worked_hours}
⏰ اضافه کاری: {overtime_hours}
🌙 شب کاری: {night_hours}
💰 پایه حقوق: {base_salary}
🎁 پاداش: {bonus_amount}
🧾 مجموع درآمد: {gross_salary}
💸 مالیات: {tax_percent}% ({tax_amount})
🏦 حقوق نهایی: {final_salary}

🛑 توجه داشته باشید که فیش حقوقی اصلی از شرکت دریافت شود.
""")
        except Exception as e:
            bot.send_message(admin_cid, f"ارسال پیام به {first_name} {last_name} ناموفق بود: {e}")

        payroll_summary += f"""
👤 {first_name} {last_name}
⏱ ساعت کاری: {worked_hours}
⏰ اضافه کاری: {overtime_hours}
🌙 شب کاری: {night_hours}
💰 پایه حقوق: {base_salary}
🎁 پاداش: {bonus_amount}
🧾 مجموع درآمد: {gross_salary}
💸 مالیات: {tax_percent}% ({tax_amount})
🏦 حقوق نهایی: {final_salary}
-------------------------------
"""

    bot.send_message(admin_cid, f"💳 فیش حقوقی کل کارمندان برای تاریخ {payment_date}:\n{payroll_summary}")



    


@bot.message_handler(commands=['help'])
def send_welcome(message):
    cid = message.chat.id
    if cid == ADMIN_CID:
        text = "منو دسترسی شما:\n"
        for command, desc in commands.items():
            text += f'/{command} : {desc}\n'
        bot.send_message(cid, text)

    else:
        data = database_information('SELECT is_boss FROM employee WHERE user_cid = %s',(cid,))
        is_boss = data[0][0]

        if is_boss == 'yes':
            bot.copy_message(cid,CHANNEL_ID,23)
        else:
            bot.copy_message(cid,CHANNEL_ID,24)


@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'authentication')
def authenticate_user(message):
    cid = message.chat.id
    first_name = message.text
    user_data[cid] = {'first__name':first_name}
    user_steps[cid] = 'authentication_lastname'
    bot.send_message(cid, "لطفاً نام خانوادگی خود را وارد کنید:")

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'authentication_lastname')
def authenticate_user_last_name(message):
    cid = message.chat.id
    first_name = user_data[cid]["first__name"]
    last_name = message.text
    if cid not in user_data:
        bot.send_message(cid, "خطا: لطفاً ابتدا نام خود را وارد کنید.")
        return

    result = database_information(
        'SELECT user_cid FROM employee WHERE first_name=%s AND last_name=%s',
        (first_name, last_name)
    )

    if not result:
        bot.copy_message(cid,CHANNEL_ID,25)
        return

    database_information(
        'UPDATE employee SET user_cid=%s WHERE first_name=%s AND last_name=%s',
        (cid, first_name, last_name)
    )
    user_steps[cid]
    user_data[cid]


    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton('ورود ⬇️', callback_data='start'),
        InlineKeyboardButton('بازگشت 🔙', callback_data='exit')
    )
    bot.send_message(cid, "یکی از گزینه های زیر را انتخاب کنید:", reply_markup=markup)



@bot.message_handler(func=lambda message: message.text == "➕اضافه کردن کارمند")
def register_employee(message):
    cid = message.chat.id
    user_steps[cid] = 'A'
    bot.send_message(cid,' نام را وارد کنید:')

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'A')
def add_first_name(message):
    cid = message.chat.id
    first_name = message.text
    employee_id = database_information(
    "INSERT INTO employee (first_name) VALUES (%s)",
    (first_name,),
    return_last_id=True
    )
    user_data[cid] = {
    "employee_id": employee_id
    }

    user_steps[cid] = 'B'
    bot.send_message(cid,' نام خانوادگی را وارد کنید')

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'B')
def add_last_name(message):
    cid = message.chat.id
    emp_id = user_data[cid]['employee_id']
    last_name = message.text

    database_information(
    "UPDATE employee SET last_name = %s WHERE employee_id = %s",
    (last_name, emp_id))

    user_steps[cid] = 'C'
    bot.send_message(cid,'آدرس را وارد کنید')

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'C')
def get_address(message):
    cid = message.chat.id
    address = message.text
    emp_id = user_data[cid]['employee_id']  
    database_information(
    "UPDATE employee SET address = %s WHERE employee_id = %s",
    (address, emp_id))
    user_steps[cid] = 'D'
    bot.send_message(cid,'شماره موبایل را وارد کنید:')

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'D')
def get_phone_number(message):
    cid = message.chat.id
    phone_number = message.text
    emp_id = user_data[cid]['employee_id']  
    database_information(
    "UPDATE employee SET phone_number = %s WHERE employee_id = %s",
    (phone_number, emp_id))
    user_steps[cid] = 'E'
    bot.send_message(cid,'''
تاریخ تولد را وارد کنید
مانند نمونه 15-01-2002
''')

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'E')
def get_birth_day(message):
    cid = message.chat.id
    birth_day = message.text
    emp_id = user_data[cid]['employee_id']  
    database_information(
    "UPDATE employee SET birth_day = %s WHERE employee_id = %s",
    (birth_day, emp_id))
    user_steps[cid] = 'F'
    bot.send_message(cid,'ایمیل را وارد کنید')

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'F')
def get_email(message):
    cid = message.chat.id
    email_address = message.text
    emp_id = user_data[cid]['employee_id']  
    database_information(
    "UPDATE employee SET email_address = %s WHERE employee_id = %s",
    (email_address, emp_id))
    user_steps[cid] = 'G'
    bot.send_message(cid,'عنوان شغلی را وارد کنید')

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'G')
def get_position(message):
    cid = message.chat.id
    position = message.text
    emp_id = user_data[cid]['employee_id']  
    database_information(
    "UPDATE employee SET position = %s WHERE employee_id = %s",
    (position, emp_id))
    user_steps[cid] = 'H'
    bot.send_message(cid,'پایه حقوق را وارد کنید')

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'H')
def get_base_salary(message):
    cid = message.chat.id
    base_salary = message.text
    emp_id = user_data[cid]['employee_id']  
    database_information(
    "UPDATE employee SET base_salary = %s WHERE employee_id = %s",
    (base_salary, emp_id))
    user_steps[cid] = 'I'

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'I')
def is_boss(message):
    cid = message.chat.id
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton('بله ✅', callback_data='yes'),
        InlineKeyboardButton('خیر ❌', callback_data='no')
        )
    bot.send_message(cid,'''
آیا موقعیت فرد رئیس است؟
توجه داشته باشین رئیس به تمام چیز هایی که شما دسترسی دارین دسترسی دارند
''',reply_markup=markup)



@bot.message_handler(func=lambda message: message.text == "حذف کارمند❌")
def delete_handler(message):
    cid = message.chat.id
    user_steps[cid] = 'J'
    bot.send_message(cid,'لطفا نام شخص مورد نظر را وارد کنید:')

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'J')
def serch_first_name_to_delete(message):
    cid = message.chat.id
    first_name = message.text
    user_data[cid] = {'first_name': first_name}
    user_steps[cid] = 'K'
    bot.send_message(cid,'لطفا نام خانوادگی شخص مورد نظر خود را وارد کنید:')

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'K')
def serch_last_name_to_delete(message):
    cid = message.chat.id
    last_name = message.text
    user_data[cid]['last_name'] = last_name
    first_name = user_data[cid]['first_name']

    info = database_information('''
        SELECT employee_id,first_name,last_name FROM employee
        WHERE first_name=%s AND last_name=%s
    ''',(first_name,last_name))

    if not info:
        bot.send_message(cid,'هیچ کارمندی با این اسم در سیستم نیست!')

        user_steps.pop(cid, None)
        user_data.pop(cid, None)
        return
    else:
        for row in info:
            bot.send_message(cid,f'''
کارمند پیدا شد

شناسه:  {row[0]}
نام:  {row[1]}
نام خانوادگی:  {row[2]}

''')
            
        markup = InlineKeyboardMarkup()
        markup.add(
        InlineKeyboardButton('بازگشت 🔙 ', callback_data='back'),
        InlineKeyboardButton('حذف کارمند ❌ ', callback_data='delete_employee')
        )
        bot.send_message(cid,'یکی از گزینه های زیر را انتخواب کنید ',reply_markup=markup)



@bot.message_handler(func=lambda message: message.text == 'جست‌و‌جو👀')
def serch_employee(message):
    cid = message.chat.id
    user_steps[cid] = 'L'
    bot.send_message(cid,'لطفا نام شخص مورد نظر را وارد کنید:')

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'L')
def serch_get_first_name(message):
    cid = message.chat.id
    first_name = message.text
    user_data[cid] = {'first_name': first_name}
    user_steps[cid] = 'M'
    bot.send_message(cid,'لطفا نام خانوادگی شخص مورد نظر خود را وارد کنید:')

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'M')
def serch_get_last_name(message):
    cid = message.chat.id
    last_name = message.text
    first_name = user_data[cid]['first_name']
    user_data[cid]['last_name'] = last_name

    info = database_information('''
        SELECT * FROM employee
        WHERE first_name = %s
          AND last_name = %s
          AND user_cid IS NOT NULL
    ''', (first_name, last_name))

    if not info:
        bot.send_message(cid, 'هیچ کارمندی با این مشخصات در سیستم نیست!')
        user_steps.pop(cid, None)
        user_data.pop(cid, None)
        return

    for row in info:
        bot.send_message(cid, f'''
✅ کارمند پیدا شد

شناسه: {row[0]}
نام: {row[2]}
نام خانوادگی: {row[3]}
آدرس: {row[4]}
شماره تماس: {row[5]}
تاریخ تولد: {row[6]}
ایمیل: {row[7]}
موقعیت شغلی: {row[8]}
پایه حقوق: {row[9]}
        ''')

    user_steps.pop(cid, None)
    user_data.pop(cid, None)


@bot.message_handler(func=lambda message: message.text == "🖋️ویرایش")
def start_edit(message):
    cid = message.chat.id
    user_steps[cid] = 'N'
    bot.send_message(cid,'لطفا نام شخص مورد نظر را وارد کنید:')

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'N')
def get_first_name_for_edit(message):
    cid = message.chat.id
    first_name = message.text
    user_data[cid] = {
    'first_name': first_name,
    'user_cid': None
}
    user_steps[cid] = 'O'
    bot.send_message(cid,'لطفا نام خانوادگی شخص مورد نظر را وارد کنید:')
    
@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'O')
def get_last_name_for_edit(message):
    cid = message.chat.id
    last_name = message.text
    first_name = user_data[cid]['first_name']

    info = database_information('''
        SELECT * FROM employee
        WHERE first_name=%s AND last_name=%s
    ''',(first_name,last_name))

    if not info:
        bot.send_message(cid,'هیچ کارمندی با این اسم در سیستم نیست!')

        user_steps.pop(cid, None)
        user_data.pop(cid, None)
        return

    elif info:
        for row in info:
            user_data[cid]['user_cid'] = row[1]
            result = (f'''
کارمند پیدا شد

شناسه:  {row[0]}
نام:  {row[2]}
نام خانوادگی:  {row[3]}
 ادرس: {row[4]}
  شماره تماس: {row[5]}
  تاریخ تولد: {row[6]}
  ایمیل: {row[7]}
  موقعیت شغلی: {row[8]}
پایه حقوق:  {row[9]}  

کدامیک از اطلاعات کاربر را میخواهید تغییر دهید؟ 🖊️
''')
        

        markup = InlineKeyboardMarkup()
        markup.add(
        InlineKeyboardButton('نام', callback_data='name'),
        InlineKeyboardButton('نام خانوادگی', callback_data='family_name')
        )
        markup.add(
            InlineKeyboardButton('آدرس', callback_data='address'),
            InlineKeyboardButton('شماره تماس', callback_data='phone_number')
        )
        markup.add(
            InlineKeyboardButton('تاریخ تولد', callback_data='birth_day'),
            InlineKeyboardButton('ایمیل', callback_data='email')
        )
        markup.add(
            InlineKeyboardButton('موقعیت شغلی', callback_data='position')
        )
        markup.add(
            InlineKeyboardButton('پایه حقوق', callback_data='base_salary'),
            InlineKeyboardButton('موقعیت (رئیس ، کارمند)', callback_data='is_boss')
        )
        markup.add(
            InlineKeyboardButton('🔙 بازگشت', callback_data='back_to_menu')
        )
        bot.send_message(cid,result,reply_markup=markup)


    else:
        bot.send_message(cid,'خطا در انجام عملیات . لطفا بعدا تلاش کنید')
        return


@bot.message_handler(func=lambda message: message.text == "💰 پاداش")
def give_bonus(message):
    cid = message.chat.id
    user_steps[cid] = 'bonus_name'
    bot.send_message(cid,'لطفا نام شخص مورد نظر خود برای پاداش را وارد کنید:')



@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'bonus_name')
def give_bonus_2(message):
    cid = message.chat.id
    first_name = message.text
    user_data[cid] = {'first_name': first_name}
    user_steps[cid] = 'bonus_last_name'
    bot.send_message(cid,'لطفا نام خانوادگی شخص مورد نظر خود برای پاداش را وارد کنید:')


@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'bonus_last_name')
def give_bonus_3(message):
    cid = message.chat.id
    last_name = message.text
    first_name = user_data[cid]['first_name']

    result = database_information(
        "SELECT employee_id FROM employee WHERE first_name=%s AND last_name=%s",
        (first_name, last_name)
    )

    if result:
        employee_id = result[0][0]
        user_data[cid]['employee_ID'] = employee_id
        user_steps[cid] = 'bonus_reason'
        bot.send_message(cid,'دلیل پاداش رو وارد کنید (به صورت یک متن کوتاه باشد.)')
    else:
        bot.send_message(cid,'هیچ کارمندی با این اسم و فامیلی در سیستم نیست!')
        user_steps.pop(cid, None)
        return


@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'bonus_reason')
def get_bonus_info_2(message):
    cid = message.chat.id
    bonus_type = message.text
    if len(bonus_type) <= 50:
        user_steps[cid] = 'bonus_payment'
        user_data[cid]['bonus_type'] = bonus_type
        bot.send_message(cid,'مبلغ پادداش را وارد کنید ( بدون حرف اضافه 1,000,000 ❌ و ✅1000000)')
    else:
        bot.send_message(cid,'متن وارد شده طولانی است')
        return

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'bonus_payment')
def get_bonus_info_3(message):
    cid = message.chat.id
    bonus_amount = (message.text)
    if bonus_amount.isdigit():
        bonus_amount = int(bonus_amount)
        if bonus_amount < 1000000 or bonus_amount == 0:
            bonus_type = user_data[cid]['bonus_type']
            employee_ID = user_data[cid]['employee_ID']
            database_information(
                "INSERT INTO bonus (employee_id, bonus_type, bonus_amount) VALUES (%s, %s, %s)",
            (employee_ID, bonus_type, bonus_amount)
            )
            bot.send_message(cid,'پاداش برای این کاربر ثبت شد ✅')
            user_steps.pop(cid)
            user_data.pop(cid)

        else:
            bot.send_message(cid,'شما نمیتوانید بیشتر از مبلغ   1,000,000 یا 0 پاداش بدهید❌')
            return
    else:
        bot.send_message(cid,'❌ مبلغ پاداش باید فقط عدد باشد')
        return


@bot.message_handler(func=lambda message: message.text == "پشتیبانی📞")
def support(messsage):
    cid = messsage.chat.id
    bot.send_message(
    cid,f'''
خوش آمدید ببخشید پشتیبانی 📞
برای استفاده از پشتیبانی روی <a href="tg://user?id={ADMIN_CID}">Support</a> کلیک کنید
در صورت بروز مشکل پیام به ادمین پیام بدهید
    ''',
    parse_mode="HTML"
)


# emmployee panel 
#-----------------------------------------------------------------------------------------------


@bot.message_handler(func=lambda message: message.text == "✅ ثبت ورود")
def input_time(message):
    cid = message.chat.id
   
    start_cycle = time(6, 55, 0)
    end_cycle = time(7, 10, 0)

    now = datetime.now()
    register_time = now.time()


    print("Start:", start_cycle)
    print("End:", end_cycle)
    print("Register:", register_time)

    if cid not in user_data:
        user_data[cid] = {}

    if start_cycle <= register_time <= end_cycle:
        show_time = register_time.strftime('%H:%M:%S')
        user_data[cid]['check_in'] = register_time
        markup = InlineKeyboardMarkup()
        markup.add(
        InlineKeyboardButton('اضافه کاری', callback_data='overtime_work'),
        InlineKeyboardButton('شب کاری', callback_data='night_work')
        )
        markup.add(
        InlineKeyboardButton('ساعت کاری', callback_data='simple_work')
        )
        bot.send_message(cid,
        "⏰ نوع ثبت ساعت کاری را انتخاب کنید:",
        reply_markup=markup  
        )
        bot.send_message(cid, f'ساعت {show_time} شما حضور خود را ثبت کردید. ✅')
            
    else:
        bot.send_message(cid, 'شما فقط می‌توانید بین ساعت 6:55 تا ساعت 7:10 حضور خود را ثبت کنید.')




@bot.message_handler(func=lambda message: message.text == "🛑 ثبت خروج")
def input_time2(message):
    cid = message.chat.id

    start_cycle = time(16, 30, 0)
    end_cycle = time(19, 40, 0)

    now = datetime.now()
    register_time = now.time()


    print("Start:", start_cycle)
    print("End:", end_cycle)
    print("Register:", register_time)

    if start_cycle <= register_time <= end_cycle:
        show_time = register_time.strftime('%H:%M:%S')
        
        if cid not in user_data or 'work_type' not in user_data[cid]:
            bot.send_message(cid, "❌ لطفاً ابتدا نوع کار خود را ثبت کنید (ثبت ورود).")
            return
        
        work_type = user_data[cid]['work_type']
        user_data[cid]['check_out'] = register_time
        save_work_time(cid, work_type, start_cycle, end_cycle)
        bot.send_message(cid, f'ساعت {show_time} شما خروج خود را ثبت کردید. ✅')
        
        
    else:
        bot.send_message(cid, 'شما فقط می‌توانید بین ساعت 16:30 تا ساعت 19:40 خروج خود را ثبت کنید.')



@bot.message_handler(func=lambda message: message.text == "📝 ساعت های کاری")
def work_hours(message):
    cid = message.chat.id

    result = database_information(
        'SELECT employee_id FROM employee WHERE user_cid=%s',
        (cid,)
    )

    if not result:
        bot.send_message(cid, "❌ شما در سیستم ثبت نشده‌اید")
        return

    employee_id = result[0][0]   # ✅ فقط یک‌بار

    user_info = database_information(
        'SELECT * FROM attendance WHERE employee_id=%s',
        (employee_id,)
    )

    if not user_info:
        bot.send_message(cid, "ℹ️ هنوز ساعت کاری برای شما ثبت نشده است")
        return

    for row in user_info:
        bot.send_message(cid, f'''
پروفایل شما :

شناسه : {row[1]}
شیفت : {row[2]}
ساعت های شب کاری : {row[3]}
ساعت های اضافه کاری : {row[4]}
ساعت های کاری : {row[5]}
        ''')

        

@bot.message_handler(func=lambda message: message.text == "حساب کاربری من 👤")
def my_profile(message):
    cid = message.chat.id
    result = database_information(
        'select employee_id from employee where user_cid=%s',
        (cid,)
    )
    print(result)
    result = result[0][0]
    print(result)
    user_info = database_information('select * from employee where employee_id=%s',
    (result,)
    )
    for row in user_info:
        bot.send_message(cid,f'''
                     
شناسه:  {row[0]}
نام:  {row[2]}
نام خانوادگی:  {row[3]}
 ادرس: {row[4]}
  شماره تماس: {row[5]}
  تاریخ تولد: {row[6]}
  ایمیل: {row[7]}
  موقعیت شغلی: {row[8]}
پایه حقوق:  {row[9]}  
                     
    ''')



@bot.callback_query_handler(func=lambda call: call.data in ['delete_employee', 'back'])
def callback_delete(call):
    cid = call.message.chat.id
    data = call.data
    if data == 'back': 
        user_data.pop(cid, None)
        user_steps.pop(cid, None)
        bot.edit_message_reply_markup(
            chat_id=cid,
            message_id=call.message.message_id,
            reply_markup=None
        )
        return

    elif data == 'delete_employee':
        if cid not in user_data:
            bot.send_message(cid, 'اطلاعات پیدا نشد. لطفا دوباره تلاش کنید.')
            user_data.pop(cid, None)
            user_steps.pop(cid, None)
            return
        else:
            first_name = user_data[cid]['first_name']
            last_name = user_data[cid]['last_name']

        result = database_information(
            "SELECT employee_id FROM employee WHERE first_name=%s AND last_name=%s",
            (first_name, last_name)
        )

        if result:
            employee_id = result[0][0]  
            database_information(
                "DELETE FROM employee WHERE employee_id = %s",
                (employee_id,)
            )
            bot.send_message(cid, "کارمند حذف شد!")
            user_data.pop(cid, None)
            user_steps.pop(cid, None)
            return
        else:
            bot.send_message(cid, 'هیچ کارمندی با این اسم در سیستم نیست!')
            user_data.pop(cid, None)
            user_steps.pop(cid, None)
            return




@bot.callback_query_handler(func=lambda call: call.data in ['yes', 'no'])
def callback_boss_status(call):
    cid = call.message.chat.id

    if cid not in user_data or 'employee_id' not in user_data[cid]:
        bot.send_message(cid, "❌ خطا: اطلاعات کاربر پیدا نشد. لطفاً دوباره تلاش کنید.")
        return

    emp_id = user_data[cid]['employee_id']
    is_boss_value = call.data  

    database_information(
        "UPDATE employee SET is_boss = %s WHERE employee_id = %s",
        (is_boss_value, emp_id)
    )

    bot.edit_message_reply_markup(
        chat_id=cid,
        message_id=call.message.message_id,
        reply_markup=None
    )

    bot.send_message(cid, 'کارمند با موفقیت در سیستم ثبت شد ✅')
    user_steps.pop(cid, None)
    user_data.pop(cid, None)




@bot.callback_query_handler(func=lambda call: call.data in ['start', 'exit'])
def callback_start_exit(call):
    cid = call.message.chat.id
    data = call.data
    if data == 'start':
        send_welcome(call.message)
        bot.edit_message_reply_markup(
            chat_id=cid,
            message_id=call.message.message_id,
            reply_markup=None
        )
        return
    if data == 'exit':
        bot.edit_message_reply_markup(
            chat_id=cid,
            message_id=call.message.message_id,
            reply_markup=None
        )


@bot.callback_query_handler(func=lambda call: True)
def callback_query_delete(call):
    cid = call.message.chat.id
    data = call.data
    
    if data == 'name':
        user_steps[cid] = 'P'
        bot.send_message(cid,'لطفا نام جدید را را وارد کنید:')

    elif data == 'family_name':
        user_steps[cid] = 'Q'
        bot.send_message(cid,'لطفا نام خانوادگی جدید را را وارد کنید:')

    elif data == 'address':
        user_steps[cid] = 'R'
        bot.send_message(cid,'لطفا ادرس جدید را را وارد کنید:')

    elif data == 'phone_number':
        user_steps[cid] = 'S'
        bot.send_message(cid,'لطفا شماره تلفن جدید را را وارد کنید:')
    
    elif data == 'birth_day':
        user_steps[cid] = 'T'
        bot.send_message(cid,'لطفا تاریخ تولد جدید را را وارد کنید:')

    elif data == 'email':
        user_steps[cid] = 'U'
        bot.send_message(cid,'لطفا ایمیل جدید را را وارد کنید:')

    elif data == 'position':
        user_steps[cid] = 'V'
        bot.send_message(cid,'لطفا موقعیت شغلی جدید را را وارد کنید:')

    elif data == 'base_salary':
        user_steps[cid] = 'W'
        bot.send_message(cid,'لطفا پایه حقوق جدید را را وارد کنید:')
    
    elif data == 'is_boss':
        user_steps[cid] = 'X'
        bot.send_message(cid,'لطفا موقعیت را وارد کنید')
    elif data == 'back_to_menu':
            bot.edit_message_reply_markup(
            chat_id=cid,
            message_id=call.message.message_id,
            reply_markup=None
        )


@bot.callback_query_handler(func=lambda call: call.data in ['simple_work', 'night_work', 'overtime_work'])
def callback_type_of_work_hours(call):
    cid = call.message.chat.id
    data = call.data


    if cid not in user_data:
        user_data[cid] = {}
    user_data[cid]['work_type'] = data

    bot.answer_callback_query(call.id, f"نوع ساعت کاری ثبت شد: {data}")

    if 'check_out' in user_data[cid]:
        pass
    else:
        bot.send_message(cid, 'لطفاً ابتدا خروج خود را ثبت کنید.')



@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'P')
def get_first_name_edit(message):
    cid = message.chat.id
    first_name = message.text

    user_cid = user_data[cid]['user_cid']

    if not user_cid:
        bot.send_message(cid, '❌ کاربر یافت نشد')
        user_steps.pop(cid, None)
        user_data.pop(cid, None)
        return
    database_information(
        "UPDATE employee SET first_name = %s WHERE user_cid = %s",
        (first_name, user_cid)
    )
    user_steps.pop(cid, None)
    user_data.pop(cid, None)
    bot.send_message(cid, '✅ نام با موفقیت تغییر یافت')
    return

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'Q')
def get_last_name_edit(message):
    cid = message.chat.id
    last_name = message.text

    user_cid = user_data[cid]['user_cid']
    if not user_cid:
        bot.send_message(cid, '❌ کاربر یافت نشد')
        user_steps.pop(cid, None)
        user_data.pop(cid, None)
        return

    database_information(
        "UPDATE employee SET last_name = %s WHERE user_cid = %s",
        (last_name, user_cid)
    )
    user_steps.pop(cid, None)
    user_data.pop(cid, None)

    bot.send_message(cid, '✅ نام خانوادگی با موفقیت تغییر یافت')
    return


@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'R')
def get_address_edit(message):
    cid = message.chat.id
    address = message.text

    user_cid = user_data[cid]['user_cid']
    if not user_cid:
        bot.send_message(cid, '❌ کاربر یافت نشد')
        user_steps.pop(cid, None)
        user_data.pop(cid, None)
        return

    database_information(
        "UPDATE employee SET address = %s WHERE user_cid = %s",
        (address, user_cid)
    )
    user_steps.pop(cid, None)
    user_data.pop(cid, None)

    bot.send_message(cid, '✅ آدرس با موفقیت تغییر یافت')
    return


@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'S')
def get_phone_number_edit(message):
    cid = message.chat.id
    phone_number = message.text

    user_cid = user_data[cid]['user_cid']
    if not user_cid:
        user_steps.pop(cid, None)
        user_data.pop(cid, None)
        bot.send_message(cid, '❌ کاربر یافت نشد')
        return

    database_information(
        "UPDATE employee SET phone_number = %s WHERE user_cid = %s",
        (phone_number, user_cid)
    )
    user_steps.pop(cid, None)
    user_data.pop(cid, None)

    bot.send_message(cid, '✅ شماره تلفن با موفقیت تغییر یافت')
    return

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'T')
def get_birth_day_edit(message):
    cid = message.chat.id
    birth_day = message.text

    user_cid = user_data[cid]['user_cid']
    if not user_cid:
        user_steps.pop(cid, None)
        user_data.pop(cid, None)
        bot.send_message(cid, '❌ کاربر یافت نشد')
        return

    database_information(
        "UPDATE employee SET birth_day = %s WHERE user_cid = %s",
        (birth_day, user_cid)
    )
    user_steps.pop(cid, None)
    user_data.pop(cid, None)

    bot.send_message(cid, '✅ تاریخ تولد با موفقیت تغییر یافت')
    return


@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'U')
def get_email_address_edit(message):
    cid = message.chat.id
    email_address = message.text

    user_cid = user_data[cid]['user_cid']
    if not user_cid:
        user_steps.pop(cid, None)
        user_data.pop(cid, None)
        bot.send_message(cid, '❌ کاربر یافت نشد')
        return

    database_information(
        "UPDATE employee SET email_address = %s WHERE user_cid = %s",
        (email_address, user_cid)
    )
    user_steps.pop(cid, None)
    user_data.pop(cid, None)

    bot.send_message(cid, '✅ ایمیل با موفقیت تغییر یافت')
    return

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'V')
def get_position_edit(message):
    cid = message.chat.id
    position = message.text

    if cid not in user_data or 'user_cid' not in user_data[cid]:
        user_steps.pop(cid, None)
        user_data.pop(cid, None)
        bot.send_message(cid, '❌ کاربر یافت نشد')
        return

    user_cid = user_data[cid]['user_cid']


    database_information(
        "UPDATE employee SET position = %s WHERE user_cid = %s",
        (position, user_cid)
    )
    user_steps.pop(cid, None)
    user_data.pop(cid, None)

    bot.send_message(cid, '✅ موقعیت شغلی با موفقیت تغییر یافت')
    return


@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'W')
def get_base_salary_edit(message):
    cid = message.chat.id
    base_salary = message.text

    user_cid = user_data[cid]['user_cid']
    if not user_cid:
        user_steps.pop(cid, None)
        user_data.pop(cid, None)
        bot.send_message(cid, '❌ کاربر یافت نشد')
        return

    database_information(
        "UPDATE employee SET base_salary = %s WHERE user_cid = %s",
        (base_salary, user_cid)
    )
    user_steps.pop(cid, None)
    user_data.pop(cid, None)

    bot.send_message(cid, '✅ پایه حقوق با موفقیت تغییر یافت')
    return


bot.infinity_polling()





