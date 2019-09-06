#python3
#coding:utf8

import serial
import msvcrt
import subprocess

debugging = True
def moi_nomer():
	modem.write('ATDt067410\r')
	
def debug( *args ):
    if debugging:
        print( args )
        
def write(toModem,fromModem="", timeout=10):
    modem.write(toModem)
    resp = modem.readline()
    
def read_all():
    while True:
        resp = modem.readline()
        debug(resp)
        if  not len(resp):
            break
        
""" Read from port until you meet result """            
def read_port(result=b'OK'):
    while True:
        rline = modem.readline()
        #print(rline)
        if (rline == b''):
            break
        if (rline.find(result) == 0):
            #print( rline)
            return rline
    return b"NO CONN"
        
""" scan all ports and test it for AT command """
def find_port():
    import serial.tools.list_ports
    ports = serial.tools.list_ports.comports(include_links=False)
    print("Find modem ...")
    for port in ports :
        #print(port.device)
        global modem
        try:
            modem = serial.Serial(port.device, 115200, timeout = 1 )
            modem.flushOutput()
            modem.flushInput()
            cmd = bytes("ATZ\r","utf8")    
            modem.write(cmd)
            resp = read_port(b'OK')
            print(port.device, resp)
            if b'OK' in resp:
                break
        except serial.SerialException:
            print("No connection")
            exit(1)
    modem.flushOutput()
    modem.flushInput()
    cmd = bytes("ATI\r","utf8")    
    modem.write(cmd)
    print('.')
    resp = modem.readline()
    # Вариант вывода 3
    while len(resp) > 0:
        print('[{0:d}]\t= '.format(len(resp)), end = '')
        print(resp)
        resp = modem.readline()

def Nosend_sms(to,what):
    modem.write(b'AT+CMGF=1\r')
    print(read_port())
    msg = b'AT+CMGS=\"'
    msg += to
    msg += b'\"\r'
    msg += what
    msg += b'\x1A'
    debug( msg )
    modem.write( msg )
    read_all()

def send_sms(to,what):
    # инициализируем служебную информацию
    print('send_sms:', to, what)
    SMS_SUBMIT_PDU = "11"
    CSMS_reference_number = ""
    emessage = TextToSMS( what )
    modem.write(b'AT+CMGF=0\r')
    print(read_port())
    # готовим строку для отправки в порт
    sms =                             \
        "00" +                        \
        SMS_SUBMIT_PDU +              \
        "00" +                        \
        PhoneNumberToSMS( to ) +      \
        "00" +                        \
        "08" +                        \
        "AA" +                        \
        "%0.2X" % int(len(emessage)/2) + \
        emessage
    
    # подготавливаем модем - передаем ему длину отправляемой строки
    msg = bytes('AT+CMGS=' + str(int(len(sms)/2-1)) + '\r' ,'utf8')
    modem.write( msg )
    # отправляем строку
    msg = bytes(sms + '\x1A','utf8')
    modem.write( msg )
    read_all()
    
"""
"""
def read_sms(smsno):
    modem.write(b'AT+CMGF=1\r')
    msg  = b'AT+CMGR='
    msg += smsno
    msg += b'\r'
    debug( 'DBG:', msg )
    modem.write( msg )
    #read_all()
    
    who = read_port(b'+CMGR:')
    what = modem.readline()
    print(who)
    print(what[0:-2])
    whofrom = who.find(b'\"+7')
    read_all()
    print('\r')
    print ('who,AP', who[whofrom+2:whofrom+13], activPhone)
    if (who[whofrom+2:whofrom+13]== activPhone):
        doit( SMSToText(what[0:-2]))
    clear_sms()

def doit(sms):
    print('Doit', sms)
    if not sms.find("Топи баню"):
        cmd = "1.cmd"
        answer= 'Скоро будет!'
    elif not sms.find("Выключи свет"):
        cmd = "2.cmd"
        answer= 'Да как так-то!'
    elif not sms.find("Формат Цэ"):
        cmd = "3.cmd"
        answer= 'Всё ясно =)'
    else :
        cmd = "0.cmd"
        answer= 'Понятно'
    cmd = cmd + ' ' + sms
    subprocess.Popen(cmd, shell = True)
    send_sms(activPhone, answer)
    print ('doit OK')

def read_modem():
        global to,what,rings,activPhone
        resp = modem.readline()
        if  len(resp) > 0:
          if    not resp.find(b'\r\n'):
              return
          else:     print('MODEM:',end = '')
          
          if    not resp.find(b'^RSSI:'):
              print('Rssi')
          elif  not resp.find(b'RING'):
              rings+=1
              print('Ring..',rings)
              
          elif  not resp.find(b'+CMTI:'):
              smsno = resp[12:14]
              print('SmsNo=',smsno)
              print(resp)
              read_sms(smsno)
          elif  not resp.find(b'+CLIP:'):
              to = resp[9:20]
              what = 'Не могу говорить, я на совещании.'
              print('to:', to)
              print('aP:', allowPhone )
              print('bP:', blackPhone )
              if to in blackPhone: rings = 5
              if rings > 3:
                  modem.write(b'ATH0\r')
                  rings = 0
          elif  not resp.find(b'^CEND'):
              if to in allowPhone:
                  send_sms(to,what)
                  activPhone = to
                  print ("AP",activPhone)
              elif to not in blackPhone:
                  blackPhone.append(to)
                  
              to=what=b''
              print('to:', to)
              print('aP:', allowPhone )
              print('bP:', blackPhone )
          elif  not resp.find(b'^SMMEMFULL:'):
              clear_sms()
          else  :
              print('[{0:d}]\t= '.format(len(resp)), end = '')
              print(resp)

def clear_sms():
    modem.write(b'AT+CMGD=4\r')
    
b = b''
def read_console():
    global b
    result = b''
    while msvcrt.kbhit():
        a = msvcrt.getch()
        print( str(a,'utf8') , end='' )
        b += a
        if a == b'\r':
            result = b
            b = b''
    return result

# http://huh-muh.blogspot.com/2012/08/smspython.html
# Восстановление строки символов в из формата SMS
#
# Исходная строка разбивается на четверки символов, которые преобразуются в целые числа
# и формируется строка, состоящая из соответствующих этим числам символов
#
# Возвращаемое значение - раскодированная строка
#
def SMSToText(intext):
    result = u''
    i = 0
    text = str(intext,'ascii')
    #print(text[0], intext[0])
    if  text[0] == '0': 
        while i+3 < len(text):
            result += chr(int(text[i] + text[i+1] + text[i+2] + text[i+3],16))
            i += 4
    else:
        result = text
    return result
# Преобразование строки символов в формат SMS
#
# Каждый двухбайтовый юникодный символ в строке разбивается на пару байт,
# и формируется новая строка, состоящая из шестнадцатеричных представлений этих байтов
#
# Возвращаемое значение - строка, содержащая строку символов в формате SMS
#
def TextToSMS(text):
    b = text
    result = ''
    i = 0
    while i < len(b):
        o = ord(b[i])
        result += ("%0.2X" % int(o/256)) + ("%0.2X" % int(o%256))
        i += 1
    return result

# Преобразование номера телефона в международном формате в формат SMS
#
# Исходная строка, содержащая телефон в международном формате 79130123456,
# дополняется справа символом F                                                            - 79130123456F,
# разбивается на пары символов                                                             - 79 13 01 23 45 6F,
# в каждой паре символы меняются местами                                                   - 97 31 10 32 54 F6,
# слева приписывается идентификатор международного формата (91)                            - 91 97 31 10 32 54 F6,
# слева приписывается количество цифр в телефоне, т.е. 11 в шестнадцатеричном формате (0B) - 0B 91 97 31 10 32 54 F6
#
# Возвращаемое значение - строка, содержащая закодированный номер телефона 0B919731103254F6
#
def PhoneNumberToSMS(innumber):
    number = str(innumber,'ascii')
    number += 'F'
    result = '0B' + '91'
    i = 0
    while i < len(number):
        result += number[i+1] + number[i]
        i += 2
    return result
"""
    main loop read modem and make things
    
"""
# list of numbers
allowPhone = [b'79999999999',b'79000000000',b'79111111111']
activPhone = b''
blackPhone = [b'']
rings = 0

if __name__ == "__main__":
    find_port()
    
    while True:
        read_modem()
        command = read_console()
        if command :
            if command == b'sms\r':
                read_sms(b'0')
            else:
                modem.write( command )
