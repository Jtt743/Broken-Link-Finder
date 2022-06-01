import queue
import requests
import time
import threading
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

begin = time.time()

start = "https://tagonline.com" # Ctrl+L
seen = set()
good, bad_host, not_found = set(), set(), set()
adjacent = {}


def dfs(u, p = None):
  if u in adjacent:
    adjacent[u].append(p)
    return

  if u in seen:
    return
  seen.add(u)

  try:
    r = requests.get(u)
  except requests.exceptions.ConnectionError as e:
    # no status code, but bad host
    if "port=80" in str(e): # *
      bad_host.add(u)
      adjacent[u] = [p]
    return
  if r.status_code == 404:
    not_found.add(u)
    adjacent[u] = [p]
    return

  good.add(u)

  parsed_u = urlparse(u)
  if parsed_u.netloc != urlparse(start).netloc:
    return
  if parsed_u.query or parsed_u.fragment:
    return
  if "text/html" not in r.headers["Content-Type"]:
    print(u)
    return

  html = r.text
  soup = BeautifulSoup(html, "html.parser")
  for a in soup('a'):
    v = a.get("href")
    if v is None or "void(0)" in v:
      continue
    parsed_v = urlparse(v)
    if "http" in parsed_v.scheme:
      dfs(v, u)
    elif parsed_v.netloc == "" and not any(i in v for i in {"mailto:", "tel:"}):
      v = urljoin(u, v)
      dfs(v, u)


q = queue.Queue()
q.put([start, None])


def bfs():
  while not q.empty():
    if u in adjacent:
      adjacent[u].append(p)
      continue

    if u in seen:
      continue
    seen.add(u)

    try:
      r = requests.get(u)
    except requests.exceptions.ConnectionError as e:
      # no status code, but bad host
      if "port=80" in str(e): # *
        bad_host.add(u)
        adjacent[u] = [p]
      continue
    if r.status_code == 404:
      not_found.add(u)
      adjacent[u] = [p]
      continue

    good.add(u)

    parsed_u = urlparse(u)
    if parsed_u.netloc != urlparse(start).netloc:
      continue
    if parsed_u.query or parsed_u.fragment:
      continue
    if "text/html" not in r.headers["Content-Type"]:
      print(u)
      continue

    html = r.text
    soup = BeautifulSoup(html, "html.parser")
    for a in soup('a'):
      v = a.get("href")
      if v is None or "void(0)" in v:
        continue
      parsed_v = urlparse(v)
      if "http" in parsed_v.scheme:
        q.put([v, u])
      elif parsed_v.netloc == "" and not any(i in v for i in {"mailto:", "tel:"}):
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
