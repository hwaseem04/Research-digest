import requests
from lxml import etree

def get_papers(search_query,sort_by,sort_order,start,max_results):
    base_url = "http://export.arxiv.org/api/query?"
    # &start={start}
    response = f"{base_url}search_query={search_query}&sortBy={sort_by}&sortOrder={sort_order}&max_results={max_results}"
    response = requests.get(response)
    root = etree.fromstring(response.content)
    entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    papers = []
    for entry in entries:
        paper = dict()
        paper['title'] = entry.find("{http://www.w3.org/2005/Atom}title").text
        paper['link'] = entry.find("{http://www.w3.org/2005/Atom}link").get("href")
        paper['updated'] = entry.find("{http://www.w3.org/2005/Atom}updated").text
        paper['published'] = entry.find("{http://www.w3.org/2005/Atom}published").text
        paper['id'] = entry.find("{http://www.w3.org/2005/Atom}id").text
        paper['category'] = entry.find("{http://www.w3.org/2005/Atom}category").get("term")
        authors = entry.findall("{http://www.w3.org/2005/Atom}author")
        author_names = []
        for author in authors:
            author_name = author.find("{http://www.w3.org/2005/Atom}name").text
            author_names.append(author_name)
        paper['authors'] = author_names

        paper['abstract'] = entry.find("{http://www.w3.org/2005/Atom}summary").text
        papers.append(paper)
    #print(papers)
    return papers

