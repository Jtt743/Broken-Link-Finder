import queue
import requests
import time
import threading
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

begin = time.time()

# Original URL, obtained with Ctrl+L
start = "https://www.bromilow.com"
# Already seen set
seen = set()
# Sets of valid URLs, URLs with 404 errors, and URLs with bad host errors
valid, bad_host, not_found = set(), set(), set()
# Adjacency list
adjacent = {}

def dfs(u, p = None):
  # If the current URL is invalid we store its referral link
  if u in adjacent:
    adjacent[u].append(p)
    return
  # Avoids cycles
  if u in seen:
    return
  seen.add(u)
  # Checks for a 404 error or bad host error
  try:
    r = requests.get(u)
  except requests.exceptions.ConnectionError as e:
    # No status code, but bad host
    if "port=80" in str(e): # *
      bad_host.add(u)
      adjacent[u] = [p]
    return
  if r.status_code == 404:
    not_found.add(u)
    adjacent[u] = [p]
    return
  # Stores valid URLs
  valid.add(u)

  parsed_u = urlparse(u)
  # Does not search for links on external URLs
  if parsed_u.netloc != urlparse(start).netloc:
    return
  # Does not search for links on URLs with query parameters or fragment identifiers
  if parsed_u.query or parsed_u.fragment:
    return
  # Only searches for links on URLs with a text/html content type
  if "text/html" not in r.headers["Content-Type"]:
    return

  html = r.text
  soup = BeautifulSoup(html, "html.parser")
  # Finds links on the current URL
  for a in soup('a'):
    v = a.get("href")
    if v is None or "void(0)" in v:
      continue
    parsed_v = urlparse(v)
    if "http" in parsed_v.scheme:
      # Absolute links
      dfs(v, u)
    elif parsed_v.netloc == "" and not any(i in v for i in {"mailto:", "tel:"}):
      # Relative links
      v = urljoin(u, v)
      dfs(v, u)

q = queue.Queue()
q.put([start, None])

def bfs():
  while not q.empty():
    u, p = q.get()
    # If the current URL is invalid we store its referral link
    if u in adjacent:
      adjacent[u].append(p)
      continue
    # Avoids cycles
    if u in seen:
      continue
    seen.add(u)
    # Checks for a 404 error or bad host error
    try:
      r = requests.get(u)
    except requests.exceptions.ConnectionError as e:
      # No status code, but bad host
      if "port=80" in str(e): # *
        bad_host.add(u)
        adjacent[u] = [p]
      continue
    if r.status_code == 404:
      not_found.add(u)
      adjacent[u] = [p]
      continue
    # Stores valid URLs
    valid.add(u)

    parsed_u = urlparse(u)
    # Does not search for links on external URLs
    if parsed_u.netloc != urlparse(start).netloc:
      continue
    # Does not search for links on URLs with query parameters or fragment identifiers
    if parsed_u.query or parsed_u.fragment:
      continue
    # Only searches for links on URLs with a text/html content type
    if "text/html" not in r.headers["Content-Type"]:
      continue

    html = r.text
    soup = BeautifulSoup(html, "html.parser")
    # Finds links on the current URL
    for a in soup('a'):
      v = a.get("href")
      if v is None or "void(0)" in v:
        continue
      parsed_v = urlparse(v)
      if "http" in parsed_v.scheme:
        # Absolute links
        q.put([v, u])
      elif parsed_v.netloc == "" and not any(i in v for i in {"mailto:", "tel:"}):
        # Relative links
        v = urljoin(u, v)
        q.put([v, u])

assert requests.get(start).ok

dfs(start)

# workers = [threading.Thread(target = bfs) for i in range(8)]
# for i in workers:
#   i.start()
# for i in workers:
#   i.join()

# print(f"Runtime: {round(time.time() - begin, 3)} seconds")
# print()
print(len(adjacent))
for i, j in adjacent.items():
  result = "bad host" if i in bad_host else 404
  print(f"Destination: {i}\tNumber of referrals: {len(j)}\tServer response: {result}")
print()
