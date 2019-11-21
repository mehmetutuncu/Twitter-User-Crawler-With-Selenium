import logging
from selenium import webdriver
from time import sleep
from bs4 import BeautifulSoup
from openpyxl import Workbook

logging.basicConfig(level=logging.INFO)


class Main:
    def __init__(self):
        self.start_date = "2019-09-01"
        self.end_date = "2019-09-30"
        self.usernames = self.get_usernames()
        self.browser = self.start_browser()
        self.content = None
        self.tweet_list = None
        self.item_count = 0
        self.response = []
        self.search_to_usernames()

    @staticmethod
    def is_not_tweet(tweet):
        replying_div = tweet.select_one('div.ReplyingToContextBelowAuthor')
        if replying_div is not None:
            return True
        user_profile = tweet.select_one('div.AdaptiveStreamUserGallery-user')
        if user_profile is not None:
            return True
        return False



    @staticmethod
    def get_tweet_like(tweet):
        like_span = tweet.select_one("span.ProfileTweet-action--favorite span.ProfileTweet-actionCount")
        if like_span is not None and like_span.get('data-tweet-stat-count', None):
            return int(like_span.get('data-tweet-stat-count'))



    @staticmethod
    def get_tweet_comment(tweet):
        comment_span = tweet.select_one("span.ProfileTweet-action--reply span.ProfileTweet-actionCount")
        if comment_span and comment_span.get('data-tweet-stat-count', None):
            return int(comment_span.get('data-tweet-stat-count'))

    @staticmethod
    def get_tweet_retweet(tweet):
        retweet_span = tweet.select_one("span.ProfileTweet-action--retweet span.ProfileTweet-actionCount")
        if retweet_span and retweet_span.get('data-tweet-stat-count', None):
            return int(retweet_span.get('data-tweet-stat-count'))

    def tweet_detail_counter(self, username):
        like = 0
        comment = 0
        retweet = 0
        post_count = 0
        for tweet in self.tweet_list:
            if self.is_not_tweet(tweet):
                continue
            post_count += 1
            like += self.get_tweet_like(tweet)
            comment += self.get_tweet_comment(tweet)
            retweet += self.get_tweet_retweet(tweet)
        self.response.append(
            dict(username=username, retweet=retweet, like=like, comment=comment, post_count=post_count))

    def search_to_usernames(self):
        for username in self.usernames:
            logging.info(f"{username} kullanıcı adına twitter üzerinden sorgu atılıyor.")
            self.get_user_profile_page(username)
        self.browser.close()
        self.write_to_excel()

    def write_to_excel(self):
        try:
            wb = Workbook()
            file_path = f'./{self.start_date}-Twitter-{self.end_date}.xlsx'
            sheet = wb.active
            sheet.append(('Username', 'Retweet', 'Like', 'Comment', 'Post Count'))
            for item in self.response:
                sheet.append((item['username'], item['retweet'], item['like'], item['comment'], item['post_count']))
            wb.save(file_path)
        except Exception as e:
            logging.error(str(e))

    def is_page_ended(self, username):

        if self.content is not None and isinstance(self.content, BeautifulSoup):
            stream_items_ol = self.content.select_one('ol.stream-items')
            if stream_items_ol is None:
                self.tweet_list = None
                return True
            self.tweet_list = stream_items_ol.select('li.js-stream-item')
            count = len(self.tweet_list)
            logging.info(f"Toplam {count} adet tweet var.")
            if count > self.item_count:
                logging.info("Scroll devam ediyor.")
                self.item_count = count
                return False
            else:
                logging.info("Sayfanın sonuna ulaşıldı.")
                return True

    def get_user_profile_page(self, username):
        self.item_count = 0


        self.browser.get(
            f"https://twitter.com/search?l=&q=from%3A{username}%20since%3A{self.start_date}%20until%3A{self.end_date}&src=typd")

        while True:
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            self.content = BeautifulSoup(self.browser.page_source, 'lxml')
            if self.is_page_ended(username):
                break
            sleep(3)


        if self.tweet_list is None:
            self.response.append(dict(username=username, retweet=0, like=0, comment=0, post_count=0))
        else:
            self.tweet_detail_counter(username)

    def get_usernames(self):
        try:
            logging.info("Kullanıcı adları txt dosyasından okunuyor.")
            user_list = []
            with open('./src/usernames.txt', 'r') as file:
                lines = file.readlines()

            for line in lines:
                user_list.append(line.replace("\n", ""))
            logging.info("Kullanıcı adları txt dosyasından okundu.")
            return user_list
        except Exception as e:
            logging.error(str(e))
            
    @staticmethod
    def start_browser():
        options = webdriver.ChromeOptions()
        # options.add_argument('headless')
        # options.add_argument('window-size=1920x1080')
        # options.add_argument("disable-gpu")
        return webdriver.Chrome(executable_path='./chromedriver.exe', chrome_options=options)


if __name__ == '__main__':
    Main()
