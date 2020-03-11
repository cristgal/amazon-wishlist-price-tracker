#!/usr/bin/env python3
"""
Description:
Check wheter items in an Amazon wishlist dropped in price since last time we ran this script.
Data is stored in a SQLite3 db file.

Arguments:
 - 1: wish list ID from Amazon.com

Output:
 Output can be easilly piped to email
 - for new added items to the DB:
    "Add item id: xxxx"
 - for price changes:
    Item Title
    Current: Price
    Stored : Price
    URL: http://smile.amazon.com/dp/xxx
    Wishlist: http://amazon.com/gp/registry/wishlist/xxx

Used modules:
  pip3 install --upgrade "git+https://github.com/Jaymon/wishlist#egg=wishlist"
  pip3 install --upgrade "git+https://github.com/Jaymon/brow#egg=brow"

"""

from wishlist.core import Wishlist
from math import ceil
from os.path import dirname
from inspect import currentframe
import sqlite3
import sys

def lineno():
    """Returns the current line number in our program."""
    return currentframe().f_back.f_lineno

def getArgs():
    if len(sys.argv) != 2:
        print("Error: Argument needed.\n%s <AMAZON_WISHLIST_ID>" % sys.argv[0])
        sys.exit(lineno())
    return sys.argv[1]

class CheckWishlist:
    wishlistid = ''
    conn = ''
    c = ''
    
    def dbConnect(self):
        base = dirname(sys.argv[0])
        dbfile = base + '/' + self.wishlistid
        self.conn = sqlite3.connect(dbfile)
        self.c = self.conn.cursor()
        with self.conn:
            try:
                self.c.execute("CREATE TABLE IF NOT EXISTS items(id VARCHAR(64) PRIMARY KEY, title VARCHAR(1024), url VARCHAR(128), price INT)")
                self.c.execute("CREATE TABLE IF NOT EXISTS history(id VARCHAR(64), price INT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            except sqlite3.Error as e:
                print("An error occurred [execute CREATE]: ", e.args[0])
                sys.exit(lineno())

    def dbCommit(self):
        try:
            self.conn.commit()
        except sqlite3.Error as e:
            print("An error occurred [commit]: ", e.args[0])
            sys.exit(lineno())
        self.c.close()
        self.conn.close()

    def checkWishlistPrices(self):
        w = Wishlist(self.wishlistid)
        for item in w:
            id = item.jsonable()['url'].split('/')[4]
            title = item.jsonable()['title']
            url = 'https://smile.amazon.com/dp/' + id + '/'
            currentPrice = ceil(float(item.jsonable()['price']))
            #print(id, " |>>>", currentPrice, "<<<")

            self.c.execute("SELECT price FROM items WHERE id='%s'" % id)
            try:
                dbPrice=self.c.fetchone()[0]
                #print(currentPrice, "|||", dbPrice)
                if currentPrice < dbPrice:
                    print()
                    print(title)
                    print("Current: ", currentPrice)
                    print("Stored : ", dbPrice)
                    self.c.execute("SELECT price,time FROM history WHERE id='%s' ORDER BY time" % id)
                    prices = self.c.fetchall()
                    for p in prices:
                        print(p)
                    print("URL: %s" % url)
                    print("Wishlist: https://www.amazon.com/gp/registry/wishlist/%s" % self.wishlistid)
                    self.c.execute("UPDATE items SET price='%s' WHERE id='%s'" % (currentPrice, id))
            except TypeError:
                print("Add item id: %s" % id)
                self.c.execute("INSERT INTO items(id,title,url,price) VALUES(?,?,?,?)", (id,title,url,currentPrice))
                self.c.execute("INSERT INTO history(id,price) VALUES(?,?)", (id,currentPrice))

            self.c.execute("SELECT price FROM history WHERE id='%s' AND time=(SELECT MAX(time) FROM history WHERE id='%s')" % (id, id))
            try:
                dbHPrice=self.c.fetchone()[0]
                if currentPrice != dbHPrice:
                    #print(currentPrice, "|", dbHPrice)
                    self.c.execute("INSERT INTO history(id,price) VALUES(?,?)", (id,currentPrice))
            except TypeError:
                self.c.execute("INSERT INTO history(id,price) VALUES(?,?)", (id,currentPrice))

    def __init__(self, wl):
        self.wishlistid = wl
        self.dbConnect()
        self.checkWishlistPrices()

    def __del__(self):
        self.dbCommit()

if __name__ == "__main__":
    wl = getArgs()
    wlc = CheckWishlist(wl)

