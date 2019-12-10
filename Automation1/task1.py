import os
import shutil
import xml.dom.minidom
import xml
import sqlite3
import re
from datetime import datetime

conn = sqlite3.connect('new.db')
try:
    conn.execute('''CREATE TABLE Logging
                (DateTime datetime, Process text )''')
except sqlite3.OperationalError:
    print("Note: table 'Logging' already exists")
    conn.execute("""INSERT INTO Logging 
                VALUES 
                (datetime('now','localtime'),'Error was found: table Logging already exists')""")

try:
    conn.execute("""CREATE TABLE Book_information
                (book_name text, number_of_paragraph int, number_of_words int, number_of_letters int,
                  words_with_capital_letter int, words_in_lowercase int)""")
    conn.execute("""INSERT INTO Logging 
                VALUES 
                (datetime('now','localtime'),'The table Book_information was created')""")
except sqlite3.OperationalError:
    print("Note: table 'Book_information' already exists")
    conn.execute("""INSERT INTO Logging 
                VALUES 
                (datetime('now','localtime'),'Error was found: table book_information already exists')""")
conn.commit()


class FilesMonitor:  # Creating the class for monitoring input folder

    def __init__(self):
        self.directory = '../Automation1/Input'
        self.files = os.listdir(self.directory)
        self.file1 = self.directory + '/'

    def filter(self):
        for file in self.files:
            file1 = self.file1
            if not file.endswith(".fb2"):
                file1 += file
                shutil.move(file1, '../Automation1/Incorrect_input/')
                conn.execute("""INSERT INTO Logging 
                VALUES 
                (datetime('now','localtime'),'Files that don't have format .fb2 were moved to Incorrect_input')""")

    def getting_file(self):
        for file in self.files:
            file1 = self.file1
            if file.endswith(".fb2"):
                file1 += file
                conn.execute("""INSERT INTO Logging 
                            VALUES 
                            (datetime('now','localtime'),'File for parsing was found')""")
            else:
                conn.execute("""INSERT INTO Logging 
                                VALUES 
                                (datetime('now','localtime'),'Error: The folder is empty')""")
            return file1
        pass


Monitoring = FilesMonitor()
file_for_parsing = Monitoring.getting_file()


class FileParser:

    def __init__(self):
        self.doc = xml.dom.minidom.parse(file_for_parsing)
        self.text = self.getting_formatted_text_list()
        self.word_list = self.word_list_get()

    def getting_book_name(self):
        book_name = self.doc.getElementsByTagName('book-name')[0]
        return book_name.childNodes[0].nodeValue

    def getting_formatted_text_list(self):
        sections = self.doc.getElementsByTagName('section')
        text = []
        for m in sections:
            pp = m.getElementsByTagName('p')
            n = 0
            for p in pp:
                if n == 0:
                    n += 1
                    continue
                text.append(p.childNodes[0].nodeValue)
        self.text = [i.replace('\xa0', '') for i in text if hasattr(i, 'replace')]
        return self.text

    def counter_paragraph(self):
        paragraph_amount = len(self.text)
        return paragraph_amount

    def word_list_get(self):
        self.word_list = []
        wordlist = []
        for i in self.text:
            wordlist1 = i.split()
            wordlist = wordlist + wordlist1
        for x in wordlist:
            x = re.sub(r"[-,.!@#%*()_»«—\?:;\"+\'/&^$~<>=]", "", x)
            if x != '':
                self.word_list.append(x)
        return self.word_list

    def counter_words(self):
        words_amount = len(self.word_list)
        return words_amount

    def counter_letters(self):
        symbols = '1234567890'
        letters = []
        for i in self.word_list:
            for m in i:
                if m in symbols:
                    continue
                letters.append(m)
        letters_amount = len(letters)
        return letters_amount

    def counter_words_with_capital_letters(self):
        CountCapLet = 0
        for i in self.word_list:
            if i != i.lower():
                CountCapLet += 1
        return CountCapLet

    def counter_words_with_lower_case(self):
        Countlowcase = 0
        for i in self.word_list:
            if i == i.lower():
                Countlowcase += 1
        return Countlowcase

    def words_in_the_book(self):
        words_set = set()
        words = []
        count_words = []
        upper_cases = []
        for i in self.word_list:
            i_title = i.title()
            i_lower = i.lower()
            i_upper = i.upper()
            if i_title not in words_set:
                upper_case = self.word_list.count(i_title) + self.word_list.count(i_upper)
                count_word = upper_case + self.word_list.count(i_lower)
                words_set.add(i_title)
                words.append(i_title)
                count_words.append(count_word)
                upper_cases.append(upper_case)
        return words, count_words, upper_cases

    pass


if file_for_parsing is not None:

    Parser = FileParser()

    book_name = Parser.getting_book_name()
    paragraph_amount = Parser.counter_paragraph()
    words_amount = Parser.counter_words()
    letters_amount = Parser.counter_letters()
    lettersCL_amount = Parser.counter_words_with_capital_letters()
    letters_low_case_amount = Parser.counter_words_with_lower_case()

    conn.execute("""INSERT INTO Book_information 
                VALUES ('%s', '%d', '%d', '%d', '%d', '%d')"""
                 % (
                     book_name, paragraph_amount, words_amount, letters_amount, lettersCL_amount,
                     letters_low_case_amount))
    conn.commit()
    conn.execute("""INSERT INTO Logging 
                VALUES 
                (datetime('now','localtime'),'The file was parsed and added to the table Book_information')""")
    conn.commit()

    words_in_the_book_list, count_words_in_the_book, words_in_the_book_with_upper_cases = Parser.words_in_the_book()


    def table_creation():
        now = datetime.now()
        table_name = str(book_name) + '_' + str(now)
        conn.execute("""CREATE TABLE '%s'
                     (word text, count int, count_uppercase int)""" % table_name)
        for i in range(len(words_in_the_book_list)):
            conn.execute("""INSERT INTO '%s'  
                        VALUES ('%s', '%d', '%d')"""
                         % (table_name, words_in_the_book_list[i], count_words_in_the_book[i],
                            words_in_the_book_with_upper_cases[i]))
            conn.commit()
        conn.execute("""INSERT INTO Logging 
                    VALUES
                    (datetime('now','localtime') ,'Statistics about words from the file was add to the table')""")
        conn.commit()


    def move_parsed_file():
        shutil.move(file_for_parsing, '../Automation1/Output/')
        conn.execute("INSERT INTO Logging VALUES (datetime('now','localtime'),'File was moved to the Output folder')")


    Data_add = table_creation()
    Move_file = move_parsed_file()
    conn.commit()
