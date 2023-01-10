import sqlite3
import requests
import schedule 
import time
from arxiv1 import get_papers

#function to scrape papers and store it in a db
def store_papers(papers):

    #connect to a db
    conn = sqlite3.connect('papers.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS papers (id text,category text,link text,title text,updated text, published text, authors text, abstract text)''')

    for paper in papers:
        ## make sure papers with same id arent added to the db
        ## c.execute('''SELECT * FROM papers WHERE id=?''', (paper['id']))
        ## result = c.fetchone()
        ##if not result:
        c.execute('''INSERT INTO papers VALUES (?,?,?,?,?,?,?,?)''', ((paper['id'], paper['category'], paper['link'],paper['title'],paper['updated'], 
        paper['published'],','.join(paper['authors']), paper['abstract'])))
    
    conn.commit()
    conn.close()

#check if the papers scrapped were already present
def check_for_new_papers():
    conn = sqlite3.connect('papers.db')
    c = conn.cursor()
    c.execute('''SELECT published FROM papers ORDER BY published DESC''')
    result = c.fetchone()
    if not result:
        last_scraped_timestamp = '2023-01-05T00:00:00Z'
    else:
        last_scraped_timestamp = result[0] 
    
    # c.execute('''SELECT COUNT(*) FROM papers;''')
    # temp = int(c.fetchone()[0])
    # if (temp) == 0:
    #     last_scraped_timestamp = '2023-01-05T00:00:00Z'

    if last_scraped_timestamp:
        start=0
        max_results = 1000
        
        search_query = "cat:cs.CV+OR+cat:cs.LG+OR+cat:cs.CL+OR+cat:cs.AI+OR+cat:cs.NE+OR+cat:cs.RO+OR+cat:cs.CR"
        sort_by = "submittedDate"   
        sort_order = "descending"

        batch = get_papers(search_query,sort_by,sort_order,start,max_results)
        
        batch = [paper for paper in batch if paper['published'] > last_scraped_timestamp]

        # If the filtered batch is empty, break out of the loop
        if not batch:
            return None

        # Add the papers to the list of papers
        ## papers += batch

        # Set the start parameter for the next API call
        ## start += max_results
    else:
        start=0
        search_query = "cat:cs.CV+OR+cat:cs.LG+OR+cat:cs.CL+OR+cat:cs.AI+OR+cat:cs.NE+OR+cat:cs.RO+OR+cat:cs.CR"
        sort_by = "submittedDate"   
        sort_order = "descending"
        # If no papers have been scraped yet, get all papers
        batch = get_papers(search_query, sort_by, sort_order,0,1000)

    conn.close()
    return batch
    

#to collect papers
def job():
    new_papers = check_for_new_papers()
    if new_papers == None:
        print("No new papers published")
    else:
        store_papers(new_papers)
        print("Successfully added")

conn = sqlite3.connect('papers.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS papers (id text,category text,link text,title text,updated text, published text, authors text, abstract text)''')
conn.close

job()


