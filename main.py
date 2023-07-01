import flet as ft
import requests
from bs4 import BeautifulSoup
import sqlite3
import webbrowser
import pyperclip

def get_titles():
  # DB接続
  dbname = 'main.db'
  conn = sqlite3.connect(dbname)
  cur = conn.cursor()
  cur.execute(
    'CREATE TABLE IF NOT EXISTS articles(id INTEGER PRIMARY KEY AUTOINCREMENT, title STRING, detail STRING, pw STRING, url STRING, marked BIT DEFAULT 0)'
  )

  # 読み込み
  cur.execute('SELECT * FROM articles')
  ans = list(cur)
  
  # 接続終了
  conn.close()

  return ans

def write_data(message):
  # DB接続
  dbname = 'main.db'
  conn = sqlite3.connect(dbname)
  cur = conn.cursor()
  cur.execute(
    'CREATE TABLE IF NOT EXISTS articles(id INTEGER PRIMARY KEY AUTOINCREMENT, title STRING, detail STRING, pw STRING, url STRING, marked BIT DEFAULT 0)'
  )

  # メッセージを加工
  message = message.splitlines()
  pw = message[0][9:]
  pw = pw[:-3]
  url = message[1]

  # タイトル、詳細を取り出し
  response = requests.get(url)
  bs = BeautifulSoup(response.text, 'html.parser')
  bs_h1 = bs.find('h1').text
  bs_p = bs.find('p').text

  # DBに登録
  cur.execute('INSERT INTO articles(title, detail, pw, url) values(:title, :detail, :pw, :url)', {"title":bs_h1, "detail":bs_p, "pw":pw, "url":url})
  conn.commit()

  # 接続終了
  conn.close()

def mark_article(id):
  # DB接続
  dbname = 'main.db'
  conn = sqlite3.connect(dbname)
  cur = conn.cursor()
  cur.execute(
    'CREATE TABLE IF NOT EXISTS articles(id INTEGER PRIMARY KEY AUTOINCREMENT, title STRING, detail STRING, pw STRING, url STRING, marked BIT DEFAULT 0)'
  )

  # 読み込み
  cur.execute(
    '''
    UPDATE articles
    SET marked =
      CASE 
        WHEN 1 = marked THEN 0
        ELSE 1
      END
    WHERE id=?
    ''', (id,)
  )
  conn.commit()
  
  # 接続終了
  conn.close()

def delete_data(id):
  # DB接続
  dbname = 'main.db'
  conn = sqlite3.connect(dbname)
  cur = conn.cursor()
  cur.execute(
    'CREATE TABLE IF NOT EXISTS articles(id INTEGER PRIMARY KEY AUTOINCREMENT, title STRING, detail STRING, pw STRING, url STRING, marked BIT DEFAULT 0)'
  )

  # 削除
  cur.execute('DELETE FROM articles WHERE id=?', (id,))
  conn.commit()
  
  # 接続終了
  conn.close()

class Article(ft.UserControl):
  def __init__(self, data, delete_article):
    super().__init__()
    self.id, self.title, self.detail, self.pw, self.url, self.marked = data
    self.marked = True if self.marked == 1 else False
    self.delete_article = delete_article

  def build(self):
    self.favorite_btn = ft.IconButton(
      icon=ft.icons.STAR_BORDER_ROUNDED,
      selected_icon=ft.icons.STAR_ROUNDED,
      on_click=self.handle_favorite,
      selected=self.marked,
    )

    return ft.Container(
      content=ft.Row(
        [
          ft.PopupMenuButton(
            items=[
              ft.PopupMenuItem(
                content=ft.Row(
                  [
                    ft.Column(
                      [
                        ft.Text(
                          value=self.title,
                        ),
                        ft.Text(
                          self.detail,
                          weight=ft.FontWeight.NORMAL,
                        ),
                      ],
                    ),
                  ],
                  vertical_alignment=ft.CrossAxisAlignment.START,
                  wrap=True
                )
              ),
              ft.PopupMenuItem(
                text="パスワードをコピー&ページを開く",
                on_click=self.handle_click
              ),
            ],
            content=(ft.Text(self.title)),
          ),
          self.favorite_btn,
          ft.IconButton(
            icon=ft.icons.DELETE,
            on_click=self.handle_delete
          ),
        ],
        wrap=True,
      ),
    )

  def handle_click(self, e):
    pyperclip.copy(self.pw)
    webbrowser.open(self.url, new=0, autoraise=True)

  def handle_favorite(self, e):
    mark_article(self.id)
    self.marked = False if self.marked == True else True
    self.favorite_btn.selected = not self.favorite_btn.selected
    self.favorite_btn.update()

  def handle_delete(self, e):
    delete_data(self.id)
    self.delete_article(self)

class App(ft.UserControl):
  def __init__(self, page_height):
    super().__init__()
    self.page_height = page_height

  def build(self):
    self.new_article = ft.TextField(
      hint_text="BOTのメッセージをコピペしてください",
      multiline=True,
      max_lines=10,
      expand=True,
    )
    self.articles = ft.ListView(auto_scroll=False, expand=True)
    self.articles_container = ft.Container(
      content=self.articles,
      alignment=ft.alignment.center,
      padding=ft.padding.symmetric(horizontal=5),
      height=self.page_height - 130,
    )
    articles_list = get_titles()
    for e in articles_list:
      article = Article(e, self.delete_article)
      self.articles.controls.append(article)

    return ft.Column(
      controls=[
        ft.Row(
          [
            self.new_article,
            ft.FloatingActionButton(icon=ft.icons.ADD, on_click=self.add_clicked),
          ],
          height=60
        ),
        self.articles_container
      ],
    )

  # 記事一覧のリロード
  def reload(self):
    self.articles.controls.clear()
    articles_list = get_titles()
    for e in articles_list:
      article = Article(e, self.delete_article)
      self.articles.controls.append(article)
    self.update()

  # 記事の削除
  def delete_article(self, article):
    self.articles.controls.remove(article)
    self.update()

  # ＋ボタンの動作
  def add_clicked(self, e):
    write_data(self.new_article.value)
    self.new_article.value = ""
    self.reload()

def main(page: ft.Page):

  page.title = "Home"
  page.window_width = 800
  page.window_height = 500

  app = App(page.window_height)

  def page_resize(e):
    page.controls.clear()
    app = App(page.window_height)
    page.add(app)
    app.update()
  page.on_resize = page_resize

  page.add(app)

ft.app(target = main)