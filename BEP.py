import requests
from html5_parser import parse
import shelve, dbm
from datetime import datetime
import concurrent.futures

timeout=5
session=requests.session()
BEP_domain='https://businessenglishpod.com'

r = session.post(url='https://businessenglishpod.com/aMember/login',
                 data={'amember_login': 'username',
                        'amember_pass': 'password',
                        'submit': 'Sign+In',
                        'login_attempt_id': '1524297722',
                        '&amember_redirect_url': '/aMember/member'},
                 headers={
                      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
                      'Referer': 'https://businessenglishpod.com/aMember/member',
                      'Connection': 'keep-alive'})

# Init shelve to presist dict
log=shelve.open('download_log.db', writeback=True)
if (len(log)==0):
    log['log']={}

def podcast_list():
    podcast_list=[]
    r_podlist=session.get(url='https://www.businessenglishpod.com/business-english-podcast-lessons/')
    s=r_podlist.content.decode('utf-8')
    tree=parse(s)

    for el in tree.xpath('//*[@id="post-383"]/div/ul/li/a'):
        podcast_list.append(el.get('href'))

    return podcast_list

def download_course(course_url):

    if (course_url in log['log']):
        print("has been downloaded")
        return

    while True: # try to connect the website until success
        try:
            print("Crawling",course_url)
            course_page=session.get(url=course_url)
            break
        except Exception:
            continue

    tree=parse(course_page.content)

    try:
        print(str(datetime.now()))
        pdf_link=''
        mp3_link=tree.xpath("//a[contains(@class,'podpress_downloadlink')]")[0].get('href')

        for a in tree.xpath("//div[@class='post-content']/p/strong/a"):
            if (a.get('href').endswith('pdf')):
                pdf_link=a.get('href')
                if (not pdf_link.startswith('http')):
                    pdf_link=BEP_domain+pdf_link

        if (not mp3_link.startswith('http')):
            mp3_link=BEP_domain+mp3_link

    except IndexError:
        return

    if (pdf_link is '' or mp3_link is ''):
        return

    pdf_filename=pdf_link.split('/')[-1]
    mp3_filename=mp3_link.split('/')[-1]

    with open(pdf_filename, 'wb') as pdf:

        pdf.write(session.get(pdf_link, timeout=timeout).content)
        print('\t'+pdf_filename, "downloaded")

    with open(mp3_filename, 'wb') as mp3:
        mp3.write(session.get(mp3_link, timeout=timeout).content)
        print('\t'+mp3_filename, 'downloaded')

        log['log'][course_url]=True

   
if __name__ == '__main__':

    # Init the thread pool
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
    for course_url in podcast_list():
        executor.submit(download_course, course_url)



