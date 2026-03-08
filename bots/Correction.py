import telebot
import os
import time
from pathlib import Path

# التوكن
BOT_TOKEN = 'Token'
bot = telebot.TeleBot(BOT_TOKEN)

# مجلد مؤقت
TEMP_DIR = Path('temp')
TEMP_DIR.mkdir(exist_ok=True)

# -------------------------------------------------------------------
# جميع التصحيحات من السكربت الأصلي (منسوخة كما هي)
# -------------------------------------------------------------------
def apply_original_fixes(code: str) -> str:
    # السلسلة الطويلة من replace
    code = code.replace("'''", "'")
    code = code.replace("""foo = False""","")
    code = code.replace("""if foo:
    pass""","")
    code = code.replace("""    if __name__ == '__main__':""","""if __name__ == '__main__':""")
    code = code.replace("finally","except")
    code = code.replace("""b = random.choice([
        '7.0',
        '8.1.0',
        '9',
        '10',
        '11',
        '12'])""","""b = random.choice(['7.0','8.1.0','9','10','11','12'])""")
    code = code.replace("""d = random.choice([
        'A',
        'B',
        'C',
        'D',
        'E',
        'F',
        'G',
        'H',
        'I',
        'J',
        'K',
        'L',
        'M',
        'N',
        'O',
        'P',
        'Q',
        'R',
        'S',
        'T',
        'U',
        'V',
        'W',
        'X',
        'Y',
        'Z'])""","""d = random.choice(['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'])""")
    code = code.replace("""f = random.choice([
        'A',
        'B',
        'C',
        'D',
        'E',
        'F',
        'G',
        'H',
        'I',
        'J',
        'K',
        'L',
        'M',
        'N',
        'O',
        'P',
        'Q',
        'R',
        'S',
        'T',
        'U',
        'V',
        'W',
        'X',
        'Y',
        'Z'])""","""f = random.choice(['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'])""")
    code = code.replace("""asu = random.choice([
    m,
    O,
    h,
    u,
    b,
    MJ3,
    MJ2,
    MJ,
    AS2,
    AH2,
    B,
    WR,
    AS_F,
    AKH_T,
    AH_T,
    AB_KH,
    AZ_T,
    BN,
    SM,
    AS_T,
    AKH_F,
    AH_F,
    RS,
    AB_A,
    Z,
    p,
    b,
    kk,
    hh,
    x,
    Y,
    P,
    u,
    B,
    J,
    MJ4,
    p])""","""asu = random.choice([m,O,h,u,b,MJ3,MJ2,MJ,AS2,AH2,B,WR,AS_F,AKH_T,AH_T,AB_KH,AZ_T,BN,SM,AS_T,AKH_F,AH_F,RS,AB_A,Z,p,b,kk,hh,x,Y,P,u,B,J,MJ4,p])""")
    code = code.replace("""dic = {
    '12': 'December',
    '11': 'November',
    '10': 'October',
    '9': 'September',
    '8': 'August',
    '7': 'July',
    '6': 'June',
    '5': 'May',
    '4': 'April',
    '3': 'March',
    '2': 'February',
    '1': 'January' }""","""dic = {'12': 'December','11': 'November','10': 'October','9': 'September','8': 'August','7': 'July','6': 'June','5': 'May','4': 'April','3': 'March','2': 'February','1': 'January' }""")
    code = code.replace("""dic2 = {
    '12': 'Devember',
    '11': 'November',
    '10': 'October',
    '09': 'September',
    '08': 'August',
    '07': 'July',
    '06': 'June',
    '05': 'May',
    '04': 'April',
    '03': 'March',
    '02': 'February',
    '01': 'January' }""","""dic2 = {'12': 'Devember','11': 'November','10': 'October','09': 'September','08': 'August','07': 'July','06': 'June','05': 'May','04': 'April','03': 'March','02': 'February','01': 'January' }""")
    code = code.replace("""None(None, None, None)
    if not None:
        pass""","""""")
    code = code.replace("e = None","")
    code = code.replace("del e","")
    code = code.replace("""if not None:
            pass""","")
    code = code.replace("""bo = random.choice([
        m,
        k,
        h,
        b,
        u,
        x])""","""bo = random.choice([m,k,h,b,u,x])""")
    code = code.replace("""amr = rc([
        '😀',
        '😃',
        '😄',
        '😁',
        '😆',
        '😅',
        '🤣',
        '😂',
        '🙂',
        '🙃',
        '😉',
        '😊',
        '😇',
        '🥰',
        '😍',
        '🤩',
        '😘',
        '😗',
        '😚',
        '😙',
        '😋',
        '😛',
        '😜',
        '🤪',
        '😝',
        '🤑',
        '🤗',
        '🤭',
        '🤫',
        '🤔',
        '🤐',
        '🤨',
        '😐',
        '😑',
        '😶',
        '😏',
        '😒',
        '🙄',
        '😬',
        '🤥',
        '😌',
        '😔',
        '😪',
        '🤤',
        '😴',
        '😷',
        '🤒',
        '🤕',
        '🤢',
        '🤮',
        '🤧',
        '🥵',
        '🥶',
        '🥴',
        '😵',
        '🤯',
        '🤠',
        '🥳',
        '😎',
        '🤓',
        '🧐',
        '😕',
        '😟',
        '🙁',
        '☹️',
        '😮',
        '😯',
        '😲',
        '😳',
        '🥺',
        '😦',
        '😧',
        '😨',
        '😰',
        '😥',
        '😢',
        '😭',
        '😱',
        '😖',
        '😣',
        '😞',
        '😓',
        '😩',
        '😫',
        '🥱',
        '😤',
        '😡',
        '😠',
        '🤬',
        '😈',
        '👿',
        '💀',
        '☠️',
        '💩',
        '🤡',
        '👹',
        '👺',
        '👻',
        '👽',
        '👾',
        '🤖',
        '😺',
        '😸',
        '😹',
        '😻',
        '😼',
        '😽',
        '🙀',
        '😿',
        '😾',
        '🧡',
        '💛',
        '💚',
        '💙',
        '💜',
        '🖤',
        '🤍',
        '🤎',
        '❤️',
        '🧡',
        '💛',
        '💚',
        '💙',
        '💜',
        '🖤',
        '🤍',
        '🤎',
        '❣️',
        '💕',
        '💞',
        '💓',
        '💗',
        '💖',
        '💘',
        '💝',
        '💟',
        '❤️‍🔥',
        '❤️‍🩹',
        '❤️',
        '🚀',
        '🛸',
        '🌍',
        '🌎',
        '🌏',
        '💔',
        '✈️',
        '🦦',
        '🔥',
        '👌🏼',
        '👋🏼',
        '🌚',
        '🔞',
        '🙆‍♂️',
        '🤦‍♂️',
        '✨',
        '🗿',
        '👍🏼',
        '🚬'])""","""amr = rc(['😀','😃','😄','😁','😆','😅','🤣','😂','🙂','🙃','😉','😊','😇','🥰','😍','🤩','😘','😗','😚','😙','😋','😛','😜','🤪','😝','🤑','🤗','🤭','🤫','🤔','🤐','🤨','😐','😑','😶','😏','😒','🙄','😬','🤥','😌','😔','😪','🤤','😴','😷','🤒','🤕','🤢','🤮','🤧','🥵','🥶','🥴','😵','🤯','🤠','🥳','😎','🤓','🧐','😕','😟','🙁','☹️','😮','😯','😲','😳','🥺','😦','😧','😨','😰','😥','😢','😭','😱','😖','😣','😞','😓','😩','😫','🥱','😤','😡','😠','🤬','😈','👿','💀','☠️','💩','🤡','👹','👺','👻','👽','👾','🤖','😺','😸','😹','😻','😼','😽','🙀','😿','😾','🧡','💛','💚','💙','💜','🖤','🤍','🤎','❤️','🧡','💛','💚','💙','💜','🖤','🤍','🤎','❣️','💕','💞','💓','💗','💖','💘','💝','💟','❤️‍🔥','❤️‍🩹','❤️','🚀','🛸','🌍','🌎','🌏','💔','✈️','🦦','🔥','👌🏼','👋🏼','🌚','🔞','🙆‍♂️','🤦‍♂️','✨','🗿','👍🏼','🚬'])""")
    code = code.replace("""kuki = ';'.join((lambda .0: [ f'{key}={value}' for key, value in .0 ])(ses.cookies.get_dict().items()))""","""kuki = (";").join([ "%s=%s" % (key, value) for key, value in ses.cookies.get_dict().items() ])""")
    code = code.replace("""game = (lambda .0: [ i.text for i in .0 ])(x.find_all('h3'))""","""game = [i.text for i in x.find_all("h3")]""")
    code = code.replace("""statusok1 = nel(statusok, 'green', **('style',))""","""statusok1 = nel(statusok, style='green')""")
    code = code.replace("""cetak(nel(statusok1, title='OK'))""","""cetak(nel(statusok1, 'OK', **('title',)))""")
    code = code.replace("""statuscp1 = nel(statuscp, 'red', **('style',))""","""statuscp1 = nel(statuscp, style='red')""")
    code = code.replace("""cetak(nel(statuscp1, 'SESI', **('title',)))""","""cetak(nel(statuscp1, title='SESI'))""")
    code = code.replace("""if __name__ == '__main__':
    
    try:
        os.system('git pull')
    except:
        pass
    
    try:
        os.mkdir('OK')
    except:
        pass
    
    try:
        os.mkdir('CP')
    except:
        pass
    
    try:
        os.mkdir('/sdcard/ALVINO-DUMP')
    except:
        pass
    
    try:
        os.system('touch .prox.txt')
    except:
        pass
    
    try:
        os.system('pkg install play-audio')
    except:
        pass
    
    try:
        os.system('clear')
    except:
        pass""","""if __name__=='__main__':
	try:os.system('git pull')
	except:pass
	try:os.mkdir('OK')
	except:pass
	try:os.mkdir('CP')
	except:pass
	try:os.mkdir('/sdcard/ALVINO-DUMP')
	except:pass
	try:os.system('touch .prox.txt')
	except:pass
	try:os.system('pkg install play-audio')
	except:pass
	try:os.system('clear')
	except:pass""")
    code = code.replace("""\n\n\n\n\n\n\n\n""","""""")
    code = code.replace("""def fak_xy(u):
    for e in u + '
':""","""def fak_xy(u):
    for e in u + '':""")
    code = code.replace("""        except:
        login_lagi334()
        requests.exceptions.ConnectionError
        li = '# PROBLEM INTERNET CONNECTION, CHECK AND TRY AGAIN'
        lo = mark(li, 'red', **('style',))
        sol().print(lo, 'cyan', **('style',))
        exit()""","""        except:
            login_lagi334()
    except:
        requests.exceptions.ConnectionError
        li = '# PROBLEM INTERNET CONNECTION, CHECK AND TRY AGAIN'
        lo = mark(li, 'red', **('style',))
        sol().print(lo, 'cyan', **('style',))
        exit()""")
    code = code.replace("""{
                'cookie': cok }, **('cookies',))""","""cookies={'cookie':cok})""")
    code = code.replace("""def fak_xy(u):
    for e in u + '
':""","""def fak_xy(u):
    for e in u + '':""")
    code = code.replace("""        except:
        
        
        try:
            print(e)
        except:""","""except:pass""")
    code = code.replace("""                except:
                
                
                (KeyError, IOError)
                requests.exceptions.ConnectionError
                exit()""","""except:pass""")
    code = code.replace("""                except:
                
                
                try:
                    print(e)
                    exit()
                except:""","""except:pass""")
    code = code.replace("""def setting():""","""    except:pass
def setting():""")
    code = code.replace("""with tred(30, **('max_workers',)) as""","""with tred(max_workers=30) as""")
    code = code.replace("""open('CP/' + cpc, 'a').write(idf + '|' + pw + '
')""","""open('CP/' + cpc, 'a').write(idf + '|' + pw + '')""")
    code = code.replace("""open('OK/' + okc, 'a').write(idf + '|' + pw + '|' + kuki + '
')""","""open('OK/' + okc, 'a').write(idf + '|' + pw + '|' + kuki + '')""")
    code = code.replace("""print('
')""","""print('')""")
    code = code.replace("""print('
    %s[0m cookie invalid' % M)""","""print('%s[0m cookie invalid' % M)""")
    code = code.replace("""w = session.get('https://mbasic.facebook.com/settings/apps/tabbed/?tab=inactive', {
        'cookie': 'noscript=1;' + kuki }, **('cookies',)).text
    sop = bs4.BeautifulSoup(w, 'html.parser')""","""w=session.get("https://mbasic.facebook.com/settings/apps/tabbed/?tab=inactive",cookies={"cookie":"noscript=1;"+kuki}).text""")
    code = code.replace("""x = sop.find('form', 'post', **('method',))""","""x = sop.find("form",method="post")""")
    code = code.replace("""asu = random.choice([
            m,
            k,
            h,
            b,
            u])""","""asu = random.choice([m,k,h,b,u])""")
    code = code.replace("""b = random.choice([
        '5.0',
        '6.0',
        '7.0',
        '8.1.0',
        '9',
        '10',
        '11',
        '12'])""","""b = random.choice(['5.0','6.0','7.0','8.1.0','9','10','11','12'])""")
    code = code.replace("""c = random.choice([
        'RMX3396'])""","""c = random.choice(['RMX3396'])""")
    code = code.replace("""print('
    %s [0mcookie invalid' % M)""","""print('%s [0mcookie invalid' % M)""")
    code = code.replace("""w = session.get('https://mbasic.facebook.com/settings/apps/tabbed/?tab=active', {
        'cookie': 'noscript=1;' + kuki }, **('cookies',)).text""","""w=session.get("https://mbasic.facebook.com/settings/apps/tabbed/?tab=active",cookies={"cookie":"noscript=1;"+kuki}).text""")
    code = code.replace("""def login():
    
    try:""","""def login():
    try:""")
    code = code.replace("""def menu():
    
    try:""","""def menu():
    try:""")
    code = code.replace("""b = random.choice([
        '8.1.0',
        '9',
        '10',
        '11',
        '12',
        '13'])""","""b = random.choice(['8.1.0','9','10','11','12','13'])""")
    code = code.replace("""try:
    print(' ')
except:
    
    ""","""try:
    print(' ')
except:pass""")
    code = code.replace("""def bot():
    
    try:""","""def bot():
    try:""")
    code = code.replace("""lambda .0: for i in .0:
""","")
    code = code.replace(""")(range""",""") for i in (range""")
    code = code.replace("""headers, {
        'cert_reqs': ssl.CERT_NONE }, **('header', 'sslopt'))""","""header=headers, sslopt={"cert_reqs": ssl.CERT_NONE})""")
    code = code.replace("""(500, **('max_workers',))""","""(max_workers=500)""")
    code = code.replace("""concurrent.futures as concurrent""","""concurrent.futures""")
    code = code.replace("""
executor.submit(create)
os.system('clear')""","""
while True:
    executor.submit(create)
    os.system('clear')""")
    code = code.replace("""return None""","")
    code = code.replace("error = None","")
    code = code.replace("continue","")
    code = code.replace("""import lzma
import zlib
import codecs
import base64""","")
    code = code.replace("""# Encoding: utf-8
# Decode by Plya Team - DecodeX
# Copyright: Plya - Team
# Follow Us On Telegram [ @Plya_Team ]""","")
    code = code.replace("""b = random.choice([
        '2',
        '3',
        '4',
        '5',
        '5.2',
        '6',
        '6.0.1',
        '7',
        '8',
        '9',
        '10',
        '11',
        '11',
        '11.0.1',
        '12',
        '13'])""","""b = random.choice(['2','3','4','5','5.2','6','6.0.1','7','8','9','10','11','11','11.0.1','12','13'])""")
    code = code.replace("""e = random.choice([
        'A',
        'B',
        'C',
        'D',
        'E',
        'F',
        'G',
        'H',
        'I',
        'J',
        'K',
        'L',
        'M',
        'N',
        'O',
        'P',
        'Q',
        'R',
        'S',
        'T',
        'U',
        'V',
        'W',
        'X',
        'Y',
        'Z'])""","""e = random.choice(['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'])""")
    code = code.replace("""""","""""")
    code = code.replace("""g = random.choice([
        'A',
        'B',
        'C',
        'D',
        'E',
        'F',
        'G',
        'H',
        'I',
        'J',
        'K',
        'L',
        'M',
        'N',
        'O',
        'P',
        'Q',
        'R',
        'S',
        'T',
        'U',
        'V',
        'W',
        'X',
        'Y',
        'Z'])""","""g = random.choice(['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'])""")
    code = code.replace("""asu = random.choice([
    m,
    k,
    h,
    u,
    b])""","""asu = random.choice([m,k,h,u,b])""")
    code = code.replace("""dic = {
    '1': 'January',
    '2': 'February',
    '3': 'March',
    '4': 'April',
    '5': 'May',
    '6': 'June',
    '7': 'July',
    '8': 'August',
    '9': 'September',
    '10': 'October',
    '11': 'November',
    '12': 'December' }
dic2 = {
    '01': 'January',
    '02': 'February',
    '03': 'March',
    '04': 'April',
    '05': 'May',
    '06': 'June',
    '07': 'July',
    '08': 'August',
    '09': 'September',
    '10': 'October',
    '11': 'November',
    '12': 'Devember' }""","""dic = {'1': 'January','2': 'February','3': 'March','4': 'April','5': 'May','6': 'June','7': 'July','8': 'August','9': 'September','10': 'October','11': 'November','12': 'December' }
dic2 = {'01': 'January','02': 'February','03': 'March','04': 'April','05': 'May','06': 'June','07': 'July','08': 'August','09': 'September','10': 'October','11': 'November','12': 'Devember' }""")
    code = code.replace("""random.choice([
        u,
        k,
        kk,
        b,
        h,
        hh])""","""random.choice([u,k,kk,b,h,hh])""")
    code = code.replace("""error = None""","")
    code = code.replace("""# Source Generated with Decompyle++
# File: Plya_Team.pyc (Python 3.9)""","""""")
    code = code.replace("""None(None, None, None)
            if not None:
                pass""","""""")
    code = code.replace("""except:
        
        ""","""except:pass""")
    code = code.replace("\n\n\n\n","")
    code = code.replace("""{
                'cookie_by_dyno': cok }, **('cookies',))""","""cookie_by_dyno={'cookie':cok})""")
    code = code.replace("""'red', **('style',))""","""style='red')""")
    code = code.replace("""'cyan', **('style',))""","""style='cyan')""")
    code = code.replace("""        IOError
        DYN01778()""","""    except IOError:
        login_lagi334()""")
    code = code.replace("""        requests.exceptions.ConnectionError""","""except requests.exceptions.ConnectionError:""")
    code = code.replace("""try:
            print(e)
        except:""","""try:
            print(e)
        except:pass""")
    code = code.replace("""try:
                    print(e)
                    exit()
                except:""","""try:
                    print(e)
                    exit()
                except:pass""")
    code = code.replace("""kuki = ';'.join((lambda .0: [ '%s=%s' % (key, value) for key, value in .0 ])(ses.cookies.get_dict().items()))""","""kuki = (";").join([ "%s=%s" % (key, value) for key, value in ses.cookies.get_dict().items() ])""")
    code = code.replace("""print('

')""","""print('')""")
    code = code.replace("""    except:
except requests.exceptions.ConnectionError:""","""    except:""")
    code = code.replace("""try:
                pass
            except:
                
                ""","""try:
                pass
            except:pass""")
    code = code.replace("""try:
                print(e)
            except:
                
                ""","""try:
                print(e)
            except:pass""")
    code = code.replace("""                (KeyError, IOError)""","""                    (KeyError, IOError)""")
    code = code.replace("""except:
                print(f'{u}')
                print('[✘] No Internet connection ')
                exit()
                (KeyError, IOError)
                print(f'[✘] Not Public  {u}')
                time.sleep(3)
                back()""","""                except:
                    print(f'{u}')
                    print('[✘] No Internet connection ')
                    exit()
                    (KeyError, IOError)
                    print(f'[✘] Not Public  {u}')
                    time.sleep(3)
                    back()""")
    code = code.replace("""None(None, None, None)""","""""")
    code = code.replace("""koki = ';'.join((lambda .0: [ '%s=%s' % (key, value) for key, value in .0 ])(p.cookies.get_dict().items()))""","""kuki = (";").join([ "%s=%s" % (key, value) for key, value in ses.cookies.get_dict().items() ])""")
    code = code.replace("""        if 'c_user' in ses.cookies.get_dict().keys():
            ok += 1
            coki = po.cookies.get_dict()
            kuki = (";").join([ "%s=%s" % (key, value) for key, value in ses.cookies.get_dict().items() ])""","""            if 'c_user' in ses.cookies.get_dict().keys():
                ok += 1
                kuki = (";").join([ "%s=%s" % (key, value) for key, value in ses.cookies.get_dict().items() ])""")
    code = code.replace("""        def crackfree(idf, pwv):""","""def crackfree(idf, pwv):""")
    code = code.replace("""        if 'c_user' in ses.cookies.get_dict().keys():
            ok += 1
            coki = po.cookies.get_dict()
            kuki = (";").join([ "%s=%s" % (key, value) for key, value in ses.cookies.get_dict().items() ])
            open('OK/' + okc, 'a').write(idf + '|' + pw + '|' + kuki + '')""","""            if 'c_user' in ses.cookies.get_dict().keys():
                ok += 1
                coki = po.cookies.get_dict()
                kuki = (";").join([ "%s=%s" % (key, value) for key, value in ses.cookies.get_dict().items() ])
                open('OK/' + okc, 'a').write(idf + '|' + pw + '|' + kuki + '')""")
    code = code.replace("""except requests.exceptions.ConnectionError:
        time.sleep(3)""","""        except requests.exceptions.ConnectionError:
            time.sleep(3)""")
    code = code.replace("""        def jalan(keliling):""","""def jalan(keliling):""")
    code = code.replace("""+ '
':""","""+ '':""")
    code = code.replace("""s]
""","""s]'""")
    code = code.replace("""print('
%""","""print('%""")
    code = code.replace("""    def opsi():""","""def opsi():""")
    code = code.replace("""exit('
%""","""exit('%""")
    code = code.replace("""input('
%""","""input('%""")
    code = code.replace("""print('
 %s""","""print(' %s""")
    code = code.replace("""replace('
'""","""replace(''""")
    code = code.replace("""%s
'""","""%s'""")
    code = code.replace("""if __name__ == '__main__':
    
    try:
        os.system('git pull')
    except:
        pass
    
    try:
        os.mkdir('OK')
    except:
        pass
    
    try:
        os.mkdir('CP')
    except:
        pass
    
    try:
        os.system('touch .prox.txt')
    except:
        pass""","""if __name__ == '__main__':
    try:os.system('git pull')
    except:pass
    try:os.mkdir('OK')
    except:pass
    try:os.mkdir('CP')
    except:pass
    try:os.system('touch .prox.txt')
    except:pass""")
    code = code.replace("""print(' 
 
 ')""","""print(' ')""")
    code = code.replace("""+ '
')""","""+ '')""")
    code = code.replace("""import lzma
import zlib
import codecs
import base64
def d(_, __):
    ___ = [chr((ord(char) - __) % 65536) for char in _]
    return ''.join(___)
print('')""","""""")
    code = code.replace("""def d(_, __):
    ___ = [chr((ord(char) - __) % 65536) for char in _]
    return ''.join(___)
print('')""","""""")
    code = code.replace("""    def menu(my_name, my_id):""","""def menu(my_name, my_id):""")
    code = code.replace("""headers_kai, datas_kai, **('headers', 'data')).text""","""headers=headers_kai, data=datas_kai).text""")
    code = code.replace("""print('
[""","""print('[""")
    code = code.replace("""
')""","""')""")
    code = code.replace("""        except:
        Ra_2005_log()
        IOError
        Ra_2005_log()""","""        except:
            Ra_2005_log()
    except IOError:
        Ra_2005_log()""")
    code = code.replace("""('
""","""('""")
    code = code.replace("""except:
                
                
                print('[>>] Total Id : ' + str(len(id)))""","""                except:
                
                
                    print('[>>] Total Id : ' + str(len(id)))
                    setting()""")
    code = code.replace("""                    (KeyError, IOError)""","""        except(KeyError, IOError):""")
    code = code.replace("""    def dump_massal():""","""def dump_massal():""")
    code = code.replace("""def dump_massal():
    try:
        token = open('.token.txt', 'r').read()
        cok = open('.cok.txt', 'r').read()
    except:
        exit()
    
    try:
        ""","""def dump_massal():
        try:
                token = open('.token.txt','r').read()
                cok = open('.cok.txt','r').read()
        except IOError:
                exit()
        try:
                """)
    code = code.replace("""    except:
        pass
        exit()
    if kumpulkan < 1 or kumpulkan > 100:
        exit()""","""        except ValueError:
                print('>> Masukkan Angka Anjing, Malah Huruff ')
                exit()
        if jum<1 or jum>100:
                print('>> Gagal Dump Idz ')
                exit()""")
    code = code.replace("""    ses = requests.Session()""","""        ses=requests.Session()""")
    code = code.replace("""        ses=requests.Session()
    ""","""        ses=requests.Session()
        """)
    code = code.replace("""0
    for""","""0
        for""")
    code = code.replace("""range(kumpulkan):
        ""","""range(kumpulkan):
            """)
    code = code.replace("""+= 1
        ""","""+= 1
            """)
    code = code.replace(""": ')
        uid.append""",""": ')
            uid.append""")
    code = code.replace("""    for user in uid:""","""        for user in uid:""")
    code = code.replace("""        for user in uid:
        
        try:
            head =""","""        for user in uid:
            try:
               head =""")
    code = code.replace("""        for user in uid:
        try:
            head =""","""        for user in uid:
            try:
               head =""")
    code = code.replace("""head ={
                'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36','Mozilla/5.0 (Windows NT 5.1; Trident/7.0; rv:11.0) like Gecko', 'Mozilla/5.0 (X11; Linux i686; rv:45.0) Gecko/20100101 Firefox/45.0', 'Mozilla/5.0 (Windows NT 6.2; rv:45.0) Gecko/20100101 Firefox/45.0', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:46.0) Gecko/20100101 Firefox/46.0', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36', 'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.120 Safari/537.36' }""","""head = (
               {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36','Mozilla/5.0 (Mobile; rv:48.0; A405DL) Gecko/48.0 Firefox/48.0 KAIOS/2.5','Mozilla/5.0 (Linux; Android 9; SH-03J) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36','Mozilla/5.0 (Linux; Android 13; SM-A515F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36','Mozilla/5.0 (Linux; Android 12; M2007J20CG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
               })""")
    code = code.replace("""            if len(id) == 0:
                params = {
                    'fields': 'friends',
                    'access_token': token }""","""               if len(id) == 0:
                   params = (
                   {
                   'access_token': token,
                   'fields': "friends"
                   }
               )""")
    code = code.replace("""            else:
                params = {
                    'fields': 'friends',
                    'access_token': token }
            url = requests.get('https://graph.facebook.com/{}'.format(user), params, head, {
                'cookies': cok }, **('params', 'headers', 'cookies')).json()
            for xr in url['friends']['data']:""","""               else:
                   params = (
                   {
                   'access_token': token,
                   'fields': "friends"
                   }
               )
               url = requests.get('https://graph.facebook.com/{}'.format(user),params=params,headers=head,cookies={'cookies':cok}).json()
               for xr in url['friends']['data']:""")
    code = code.replace("""               for xr in url['friends']['data']:
                
                try:
                    woy = xr['id'] + '|' + xr['name']
                    if woy in id:
                        pass
                    else:
                        id.append(woy)
                except:""","""               for xr in url['friends']['data']:
                   try:
                       woy = (xr['id']+'|'+xr['name'])
                       if woy in id:pass
                       else:id.append(woy)
                   except:continue""")
    code = code.replace("""                    (KeyError, IOError)""","""            except(KeyError, IOError):pass""")
    code = code.replace("""        except requests.exceptions.ConnectionError:
                exit()""","""            except requests.exceptions.ConnectionError:
                exit()""")
    code = code.replace("""except:
                print(f'')""","""except:
                    print(f'')""")
    code = code.replace("""        if 'c_user' in ses.cookies.get_dict().keys():""","""            if 'c_user' in ses.cookies.get_dict().keys():""")
    code = code.replace("""            headapp = {
                'user-agent': 'NokiaX2-01/5.0 (08.35) Profile/MIDP-2.1 Configuration/CLDC-1.1 Mozilla/5.0 AppleWebKit/420+ (KHTML, like Gecko) Safari/420+' }""","""                headapp = {
                'user-agent': 'NokiaX2-01/5.0 (08.35) Profile/MIDP-2.1 Configuration/CLDC-1.1 Mozilla/5.0 AppleWebKit/420+ (KHTML, like Gecko) Safari/420+' }""")
    code = code.replace("""        if 'ya' in taplikasi:
            ok += 1
            coki = po.cookies.get_dict()
            kuki = (";").join([ "%s=%s" % (key, value) for key, value in ses.cookies.get_dict().items() ])
            open('OK/' + okc, 'a').write(idf + '|' + pw + '|' + kuki + '')""","""            if 'ya' in taplikasi:
                ok += 1
                coki = po.cookies.get_dict()
                kuki = (";").join([ "%s=%s" % (key, value) for key, value in ses.cookies.get_dict().items() ])
                open('OK/' + okc, 'a').write(idf + '|' + pw + '|' + kuki + '')""")
    code = code.replace("""            except:
                pass""","""            except:pass""")
    code = code.replace("""    except requests.exceptions.ConnectionError:
            time.sleep(31)""","""        except requests.exceptions.ConnectionError:
            time.sleep(31)""")
    code = code.replace("""    if __name__=='__main__':""","""if __name__=='__main__':""")
    code = code.replace("""{
                    'cookie': cookie }, **('cookies',))""","""cookies={'cookie':cookie})""")
    code = code.replace("""    def create_file_login():""","""def create_file_login():""")
    code = code.replace("""(None, None, None)
            if not None:
                pass""","""""")
    code = code.replace("""        for met in range(jum):
        ""","""        for met in range(jum):
            """)
    code = code.replace("""Erorr = None""","""""")
    code = code.replace("""del Erorr""","""""")
    code = code.replace("""head1, **('headers',))""","""headers=head1)""")
    code = code.replace("""if not None:
                pass""","""""")
    code = code.replace("""        def checklist():""","""def checklist():""")
    code = code.replace("""data, **('headers', 'data'))""","""headers=headers, data=data)""")
    code = code.replace("""    def home():""","""def home():""")
    code = code.replace("""random.choice([
        'A',
        'B',
        'C',
        'D',
        'E',
        'F',
        'G',
        'H',
        'I',
        'J',
        'K',
        'L',
        'M',
        'N',
        'O',
        'P',
        'Q',
        'R',
        'S',
        'T',
        'U',
        'V',
        'W',
        'X',
        'Y',
        'Z'])""","""random.choice(['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'])""")
    code = code.replace("""Qredes = 0x38D7EA4C67FFsource""","""""")
    code = code.replace("""sr, **('target',)""","""target=sr""")
    code = code.replace("""h, **('headers',))""","""headers=h)""")
    code = code.replace("""header, **('headers',))""","""headers=header""")
    code = code.replace("""ser, (), **('target', 'args'))""","""target=ser, args=())""")
    code = code.replace("""ser, **('target',)""","""target=ser""")
    code = code.replace("""if not None:
                    pass""","""""")
    code = code.replace("""head, data, **('headers', 'data'))""","""headers=head, data=data)""")
    code = code.replace("""h, d, 0.4, **('headers', 'data', 'timeout'))""","""headers=h, data=d, timeout=0.4)""")
    code = code.replace("""+= 1
            os.system""","""+= 1
        os.system""")
    code = code.replace("""+= 1
            us""","""+= 1
        us""")
    code = code.replace("""he, **('headers',))""","""headers=he)""")
    code = code.replace("""if not None:
                    pass""","""""")
    code = code.replace("""he, data, **('headers', 'data'))""","""headers=he, data=data)""")
    code = code.replace("""he, da, **('headers', 'data'))""","""headers=he, data=da)""")
    code = code.replace("""except:passIndexError""","""except IndexError:""")
    code = code.replace("""lambda .0: for x in .0:
""","")
    code = code.replace("""hea, **('headers',))""","""headers=hea)""")
    code = code.replace("""+= 1
                        requests.get('https://api.telegram.org/bot' + str(token) + '/sendMessage?chat_id=' + str(ID) + '&text=' + str(statuscp))""","""+= 1
                    requests.get('https://api.telegram.org/bot' + str(token) + '/sendMessage?chat_id=' + str(ID) + '&text=' + str(statuscp))""")
    code = code.replace("""ok += 1
                    coki = po.cookies.get_dict()""","""ok += 1
                coki = po.cookies.get_dict()""")
    code = code.replace("""        if 'ya' in taplikasi:""","""            if 'ya' in taplikasi:""")
    code = code.replace("""+= 1
                            infoakun""","""+= 1
                        infoakun""")
    code = code.replace("""in cek2:
                    infoakun +=""","""in cek2:
                        infoakun +=""")
    code = code.replace("""else:
                    (hit1, hit2) = (0, 0)""","""else:
                        (hit1, hit2) = (0, 0)""")
    code = code.replace("""if __name__=='__main__':
	try:os.system('git pull')
	except:pass
	try:os.mkdir('OK')
	except:pass
	try:os.mkdir('CP')
	except:pass
	try:os.mkdir('/sdcard/ALVINO-DUMP')
	except:pass
	try:os.system('touch .prox.txt')
	except:pass
	try:os.system('pkg install play-audio')
	except:pass
	try:os.system('clear')
	except:pass
    login()""","""if __name__=='__main__':
	try:os.system('git pull')
	except:pass
	try:os.mkdir('OK')
	except:pass
	try:os.mkdir('CP')
	except:pass
	try:os.mkdir('/sdcard/ALVINO-DUMP')
	except:pass
	try:os.system('touch .prox.txt')
	except:pass
	try:os.system('pkg install play-audio')
	except:pass
	try:os.system('clear')
	except:pass
	login()""")
    code = code.replace("""data, **('data',))""","""data=data)""")
    code = code.replace("""dat, cos, **('data', 'cookies'))""","""data=dat, cookies=cos)""")
    code = code.replace("""""","""""")
    code = code.replace("""cos, **('cookies',))""","""cookies=cos)""")
    code = code.replace("""**('style',)))""","""style='bold'))""")
    code = code.replace("""        ses=requests.Session()
        for pw in pwv:""","""    ses=requests.Session()
    for pw in pwv:""")
    code = code.replace("""copyright = '@psh_team'""","""""")
    code = code.replace("""random.choice([
        '6',
        '7',
        '8',
        '9',
        '10',
        '11',
        '12',
        '13'])""","""random.choice(['6','7','8','9','10','11','12','13'])""")
    code = code.replace("""random.choice([
        '6',
        '7',
        '8',
        '9',
        '10',
        '11',
        '12'])""","""random.choice(['6','7','8','9','10','11','12'])""")
    code = code.replace("""{
            'cookie': cookies }, **('headers', 'cookies'))""","""{
    'cookie': cookies
}, headers=headers, cookies=cookies)""")
    code = code.replace("""    def""","""def""")
    code = code.replace("""1, **('limit',))""","""limit=1)""")
    code = code.replace("""'تحقق', **('text',))""","""text='تحقق')""")
    code = code.replace("""kilwa = ''""","""kilwa = '""")
    code = code.replace("""kilwa = 'print('𓏳'*50)'""","""kilwa = ('𓏳'*50)""")
    code = code.replace("""passwrd, **('target',))""","""target=passwrd)""")
    code = code.replace("""+= 1
            tlg""","""+= 1
        tlg""")
    code = code.replace("""n't""","""nt""")
    code = code.replace("""d, h, **('data', 'headers'))""","""data=d, headers=h)""")
    code = code.replace("""{
                'cookie': cookies=cok)""","""cookies=cok)""")
    code = code.replace("""try:
                    print(e)
                except:
                    ""","""try:
                    print(e)
                except:pass""")
    code = code.replace("""ok += 1
                coki""","""ok += 1
            coki""")
    code = code.replace("""    loop = 0
    lim = 0
    oks = []
    cps = []
    twf = []
    pcp = []
    tp = 0
    id = []
    tokenku = []""","""loop = 0
lim = 0
oks = []
cps = []
twf = []
pcp = []
tp = 0
id = []
tokenku = []""")
    code = code.replace("""if None.exceptions""","""except requests.exceptions""")
    code = code.replace("""if None:""","""except:""")
    code = code.replace("""

_ = lambda __ : __import__('marshal').loads(__import__('zlib').decompress(__import__('base64').b64decode(__[::-1])));


""","""""")
    
    return code

# -------------------------------------------------------------------
# دوال البوت
# -------------------------------------------------------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أرسل لي ملف بايثون (.py) وسأقوم بتصحيحه بنفس طريقة الأداة القديمة.")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    doc = message.document
    file_name = doc.file_name
    if not file_name.endswith('.py'):
        bot.reply_to(message, "الرجاء إرسال ملف بايثون بامتداد .py")
        return

    processing_msg = bot.reply_to(message, "جاري التصحيح...")

    # مسار مؤقت
    input_path = TEMP_DIR / f"{message.from_user.id}_{file_name}"
    output_path = TEMP_DIR / f"fixed_{message.from_user.id}_{file_name}"

    try:
        # تحميل الملف
        file_info = bot.get_file(doc.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(input_path, 'wb') as f:
            f.write(downloaded_file)

        # قراءة المحتوى
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        # تطبيق التصحيحات
        fixed_code = apply_original_fixes(code)

        # حفظ الملف المصحح
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(fixed_code)

        # إرسال الملف المصحح
        with open(output_path, 'rb') as f:
            bot.send_document(message.chat.id, f, caption="تم التصليح")

        # حذف رسالة المعالجة
        bot.delete_message(message.chat.id, processing_msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"حدث خطأ: {e}")
    finally:
        # تنظيف الملفات المؤقتة
        if input_path.exists():
            input_path.unlink()
        if output_path.exists():
            output_path.unlink()

if __name__ == '__main__':
    print("البوت يعمل...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"خطأ: {e}")
            time.sleep(5)