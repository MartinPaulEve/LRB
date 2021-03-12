import csv
import re

import requests
import lxml
import bs4
from datetime import datetime
from dateutil import parser


def scrape():
    # a function that will build the data index
    author_index = 0

    authors = {}

    just_reviewers = []
    just_reviewed = []

    edges = []
    for y in range(1, 44):
        for x in range(1, 24):
            print ("v{0}n{1}".format(y, x))
            content = requests.get('https://www.lrb.co.uk/the-paper/'
                                   'v{:02d}/n{:02d}'.format(y, x)).text

            soup = bs4.BeautifulSoup(content)

            try:
                header = soup.find_all("h1", {"class": "toc-title"})[0]

                date = header.getText().strip().split('·')[1].strip()
                date = parser.parse(date)

                timeset = date.isoformat()

                ToC = soup.find_all("div", {"class": "toc-grid-items"})[0]

                ToCs = ToC.find_all("a")

                for ToCitem in ToCs:

                    author = ToCitem.find_all("h3")[0]
                    author = author.getText().strip()
                    by = ToCitem.find_all("span", {"class": "by"})
                    if len(by) > 0:

                        for item in by:
                            regex = r"by\s+(.+?)\.<"
                            title_search = re.search(regex, str(item),
                                                     re.IGNORECASE)

                            if title_search:
                                byline = title_search.group(1)

                                # construct the node table
                                if author not in authors:
                                    author_index += 1
                                    authors[author] = author_index
                                    if author not in just_reviewers:
                                        just_reviewers.append(author)

                                byline = byline.strip()

                                if byline not in authors:
                                    author_index += 1
                                    authors[byline] = author_index
                                    if byline not in just_reviewed:
                                        just_reviewed.append(byline)

                                edges.append([authors[author], authors[byline],
                                              y, x, timeset])
            except:
                print('Error getting ToC for v{0}i{1}'.format(y, x))

    with open('/home/martin/LRB_edges.csv', 'w', newline='') as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        wr.writerow(['source', 'target', 'vol', 'no', 'timeset'])
        for row in edges:
            wr.writerow(row)

    with open('/home/martin/LRB_nodes.csv', 'w', newline='') as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        wr.writerow(['id', 'label'])
        for row in authors.keys():
            wr.writerow([authors[row], row])


def find_circular(authors, edges, input_chain, reviewer_to_check, lowest_edge=0,
                  end_search=0):
    # a function that finds circularities of reviews

    if reviewer_to_check in input_chain:
        print("ALERT!")
        print(authors[reviewer_to_check] + " (" + reviewer_to_check +
              ") is in chain " + str(input_chain))
        translate(input_chain + [reviewer_to_check])
        return

    for edge in edges:
        # uncomment the end of this line to search forwards in time only
        # i.e. X reviews Y, who reviews Z (after the first review), who
        # reviews X (after the second review)
        # if you want this to work, add a sequential "id" column to your
        # edges CSV file
        if edge[0] == reviewer_to_check: # and int(edge[4]) > lowest_edge:
            new_input_chain = input_chain
            #find_circular(authors, edges, new_input_chain + [reviewer_to_check],
            #              edge[1], int(edge[4]))
            find_circular(authors, edges, new_input_chain + [reviewer_to_check],
                          edge[1])


def translate(input_list):
    # a function to translate a list into reviews themselves
    edges = []
    authors = {}

    reviewers = []
    reviewed = []

    with open('/home/martin/LRB_edges.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)

        for row in reader:
            edges.append(row)
            if row[0] not in reviewers:
                reviewers.append(row[0])

            if row[1] not in reviewed:
                reviewed.append(row[1])

    with open('/home/martin/LRB_nodes.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)

        for row in reader:
            authors[row[0]] = row[1]

    out = []
    for count, item in enumerate(input_list):
        # lookup vol and num
        if count < len(input_list) - 1:
            for edge in edges:
                if edge[0] == item and edge[1] == input_list[count + 1]:
                    # found an edge
                    reviewer = authors[edge[0]]
                    reviewed = authors[edge[1]]
                    vol = edge[2]
                    num = edge[3]
                    print('{0} reviewed {1} in vol {2} num {3}'.format(reviewer,
                                                                       reviewed,
                                                                       vol,
                                                                       num))
                    break


def top10():
    edges = []
    authors = {}

    reviewers = []
    reviewed = []

    reviewer_count = {}

    with open('/home/martin/LRB_edges.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)

        for row in reader:
            edges.append(row)
            if row[0] not in reviewers:
                reviewers.append(row[0])

            if row[0] not in reviewer_count.keys():
                reviewer_count[row[0]] = 1
            else:
                reviewer_count[row[0]] = reviewer_count[row[0]] + 1

            if row[1] not in reviewed:
                reviewed.append(row[1])

    sorted_reviews = sorted(reviewer_count.items(), key=lambda item: item[1], reverse=True)
    print(sorted_reviews)

    top = []
    x = 0

    for k, v in sorted_reviews:
        if x > 10:
            break

        top.append(k)
        x = x + 1

    with open('/home/martin/LRB_nodes.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)

        for row in reader:
            authors[row[0]] = row[1]

    for item in top:
        print(authors[item])

    return

def detect(reviewer, reviewee):
    edges = []
    authors = {}

    reviewers = []
    reviewed = []

    with open('/home/martin/LRB_edges.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)

        for row in reader:
            edges.append(row)
            if row[0] not in reviewers:
                reviewers.append(row[0])

            if row[1] not in reviewed:
                reviewed.append(row[1])

    reviewer_id = 0
    reviewee_id = 0

    with open('/home/martin/LRB_nodes.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)

        for row in reader:
            authors[row[0]] = row[1]

            if row[1] == reviewer:
                reviewer_id = row[0]

            if row[1] == reviewee:
                reviewee_id = row[0]

    print("Finding")
    find_circular(authors, edges, [], reviewer_id, end_search=reviewee_id)

    return

def scan():

    edges = []
    authors = {}

    reviewers = []
    reviewed = []

    with open('/home/martin/LRB_edges.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)

        for row in reader:
            edges.append(row)
            if row[0] not in reviewers:
                reviewers.append(row[0])

            if row[1] not in reviewed:
                reviewed.append(row[1])

    with open('/home/martin/LRB_nodes.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)

        for row in reader:
            authors[row[0]] = row[1]

    for reviewer in reviewed:
        if reviewer != 'target':
            find_circular(authors, edges, [], reviewer, 0)
    return


if __name__ == '__main__':
    scrape()
    #top10()
    #detect('Bernard Porter', 'Miles Taylor')
    pass
