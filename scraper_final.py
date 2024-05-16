from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import tkinter as tk
import time
import os
import json


#Scrolls down the webpage to load all elements. Clicks to show comment replies along the way.
crawl_time = 0
def crawl():

    #Compares current URL to confirm the script hasn't been redirected by Google.
    def validate_url():
      if playlist[page] != driver.current_url:
            print('session was interrupted.  Restarting from current URL')
            time.sleep(1)
            driver.get(playlist[page])
            crawl()

    #Clicks comment reply buttons.
    def show_replies():
        #Initial replies
        if len(driver.find_elements(By.ID, 'more-replies')) > 0:
            for i in range(0, len(driver.find_elements(By.ID, 'more-replies'))):
                try:
                    time.sleep(0.1)
                    driver.find_elements(By.ID, 'more-replies')[i].click()
                except:
                    None
        #More replies
        if len(driver.find_elements(By.CLASS_NAME, 'style-scope ytd-continuation-item-renderer')) > 0:
            for i in range(0, len(driver.find_elements(By.CLASS_NAME, 'style-scope ytd-continuation-item-renderer'))):
                try:
                    time.sleep(0.1)
                    driver.find_elements(By.CLASS_NAME, 'style-scope ytd-continuation-item-renderer')[i].click()
                except:
                    None
    
    #Clicks away cookies popup.
    def cookie_cutter():
        try:
            driver.find_element(By.CSS_SELECTOR, '#content > div.body.style-scope.ytd-consent-bump-v2-lightbox > div.eom-buttons.style-scope.ytd-consent-bump-v2-lightbox > div:nth-child(1) > ytd-button-renderer:nth-child(1) > yt-button-shape > button').click()
        except:
            None
    
    at_page_end = False
    last_height_val = driver.execute_script("return document.documentElement.scrollHeight")

    time.sleep(2)
    cookie_cutter()

    crawls = 0
    while (crawls < crawl_time) and not at_page_end:
        validate_url()
        driver.find_element(By.XPATH, '//body').send_keys(Keys.END)
        time.sleep(1.5)
        new_height_val = int((driver.execute_script("return document.documentElement.scrollHeight")))
        crawls = crawls + 1
        show_replies()
        time.sleep(1.5)
        #Compares scrollheights to recognize when at end of page
        if last_height_val != new_height_val:
            last_height_val = new_height_val
        else:
            at_page_end = True
    validate_url()


send_to_json = {}
def export_comments():
    
    #Sends all html from comments section to a bs4 object.
    def extract_comments():
        comments_section = driver.find_element(By.ID, 'comments')
        comments_html = comments_section.get_attribute('innerHTML')
        comment_soup = BeautifulSoup(comments_html, 'html.parser')
        return comment_soup
    
    #Takes the pure comment text, assigning each comment as a dictionary key, with a list of its replies as the value.
    def parse_comments():
    
        parsed_dict = {}
        comments_param = extract_comments().find_all("ytd-comment-thread-renderer")
        for container in comments_param:
            comment_text = container.find("yt-formatted-string", class_="style-scope ytd-comment-renderer").text.strip()
            
            comment_replies = []
            try:
                replies_param = container.find("ytd-comment-replies-renderer", class_="style-scope ytd-comment-thread-renderer")
                reply_text = replies_param.find_all("yt-formatted-string", id="content-text")
                for i in reply_text:
                    comment_replies.append(i.text.strip())
            except:
                None

            parsed_dict[comment_text] = comment_replies
        return parsed_dict

    if page < len(playlist):
        send_to_json.update(parse_comments())

    #Converts dictionary to json and sends to a specified json file in the same folder as python code.
    if page == (len(playlist) - 1):
        scrape_file.write(json.dumps(send_to_json, indent=4))


def UI_windows():
    
    #Prompts user to enter URLs for YouTube. Returns list of URLs and calls crawltime_window().
    def entry_window():
        to_playlist = []
        def add_entry():
            entry_text = entry_box.get()
            if entry_text:
                to_playlist.append(entry_text)
                entry_box.delete(0, tk.END)
                print('Added ' + to_playlist[-1])

        root = tk.Tk()
        root.title("Playlist Setup")

        frame = tk.Frame(root)
        frame.pack(padx=10, pady=10)

        entry_box = tk.Entry(frame, width=30)
        entry_box.grid(row=0, column=0, padx=5, pady=5)

        add_button = tk.Button(frame, text="Add Entry", command=add_entry)
        add_button.grid(row=0, column=1, padx=5, pady=5)

        close_button = tk.Button(frame, text="Confirm", command=lambda:[add_entry(), root.destroy(), crawltime_window()])
        close_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

        root.mainloop()
        
        return to_playlist

    #Prompts user to determine crawl time.
    def crawltime_window():
        
        root = tk.Tk()
        root.title('Crawl Duration')
        
        
        frame = tk.Frame(root, width=400, height=50)
        frame.pack(padx=10, pady=10)
        
        prompt = tk.Label(frame, text="Approximately how many comments do you want to collect per video?")
        prompt.grid(column=0, row=0, sticky='N')
        
        def set_crawl_time(i):
            global crawl_time
            crawl_time = i

        tk.Button(frame, text="100 comments.", command=lambda:[set_crawl_time(1), root.destroy()]).grid(column=0, row=1, sticky='N', ipady=4, pady= 15)
        tk.Button(frame, text="500 comments.", command=lambda:[set_crawl_time(6), root.destroy()]).grid(column=0, row=2, sticky='N', ipady=4, pady= 15)
        tk.Button(frame, text="1000 comments.", command=lambda:[set_crawl_time(12), root.destroy()]).grid(column=0, row=3, sticky='N', ipady=4, pady= 15)
        tk.Button(frame, text="ALL", command=lambda:[set_crawl_time(999999), root.destroy()]).grid(column=0, row=4, sticky='N', ipady=4, pady= 15)
        
        root.mainloop()

    return entry_window()

#Arguments for webdriver.
def start_your_engine():

    options = Options()
    #options.add_argument('--headless=new')
    options.add_argument("--mute-audio")

    return webdriver.Chrome(options=options)


playlist = UI_windows()
driver = start_your_engine()
scrape_file = open(os.path.join(os.path.dirname(__file__), 'scrape_list.json'), 'w', encoding='utf-8')


page = 0
while page < len(playlist):
    try:
        driver.get(playlist[page])
        crawl()
        export_comments()
    except:
        print('Could not load URL. [' + playlist[page] + ']')
        if page == (len(playlist) - 1):
            scrape_file.write(json.dumps(send_to_json, indent=4))
    finally:
        page = page + 1
