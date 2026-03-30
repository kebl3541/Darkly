# 🚩 8 : Exposed htpasswd / Admin Access

## 📝 Overview

We started looking for `robots.txt`, which is a public file that tells search engine bots which pages not to index. It is not a security mechanism: anyone can read it. In this case, it revealed two hidden directories, one of which contained a password file that was never meant to be accessible from the web. That file gave us a username and a hashed password. We cracked the hash, found a protected admin page, logged in, and got the flag.

## 🔍 What is robots.txt?

Now, `robots.txt` is a plain text file that websites place at their root to give instructions to search engine bots like Google and Bing about which pages they should or should not index. It follows a simple format in general. We added 'robots.txt' and got:

```
User-agent: *
Disallow: /whatever
Disallow: /.hidden
```

`User-agent: *` means these rules apply to all bots. `Disallow` tells them which paths to skip.

When Google crawls a website it reads `robots.txt` first and respects these rules. A developer might add a sensitive path here thinking "if I tell the bot not to index this, nobody will find it." This reasoning is completely wrong for two reasons.

First, `robots.txt` is a public file. It sits at the root of every website and anyone can read it by simply visiting `http://192.168.64.2/robots.txt`. There is no authentication, no restriction, nothing. Every person, bot, and attacker on the internet can read it.

Second, bots respect `robots.txt` out of convention, not because they are forced to. A malicious crawler or an attacker using curl ignores it entirely.

The result is the opposite of what the developer intended. Instead of hiding sensitive paths, `robots.txt` documents them in a public file that anyone can read. In this case it handed us a direct map to two hidden directories: `/whatever` and `/.hidden`. Each of those is a separate breach. This README covers `/whatever`.

## 🛠 The Exploit

Visiting `http://192.168.64.2/robots.txt` returned:

```
User-agent: *
Disallow: /whatever
Disallow: /.hidden

```

Two paths are being hidden from search engines. We checked both.

### Step 2: Browse /whatever

Visiting `http://192.168.64.2/whatever/` showed a directory listing. Instead of returning a 403 Forbidden error, the server displayed its folder contents like a file browser:

```bash
curl -s http://192.168.64.2/whatever/
```

Which returned:

```html
<html>
<head><title>Index of /whatever/</title></head>
<body bgcolor="white">
<h1>Index of /whatever/</h1><hr><pre><a href="../">../</a>
<a href="htpasswd">htpasswd</a>                       29-Jun-2021 18:09          38
</pre><hr></body>
</html>
```

One file inside: `htpasswd`. This should never be publicly accessible.

## What is directory listing?

By default, if a web server has no index file in a folder and directory listing is enabled, it shows the full contents of that folder to anyone who visits. This is a misconfiguration. A properly configured server returns 403 Forbidden instead. Here the server essentially handed us a map of everything inside `/whatever/`.

## What is htpasswd?

The file `htpasswd` is a file used by Apache web servers to implement HTTP Basic Authentication, which is the browser dialog box that asks for a username and password before letting you into a protected area. The file stores credentials in this format:

```
username:hashed_password

```

It is meant to live outside the web root, completely inaccessible from a browser. Finding one exposed at a public URL is a serious misconfiguration.

## Step 3: Read the htpasswd file

```bash
curl -s http://192.168.64.2/whatever/htpasswd
```

This returned:

```
root:437394baff5aa33daa618be47b75cb49

```

Username `root`, password hashed as `437394baff5aa33daa618be47b75cb49`. That 32-character string is an MD5 hash.

## What is MD5 and why is it weak?

MD5 is a hashing algorithm. It takes any input and produces a fixed 32-character string. The same input always produces the same output:

```
qwerty123@  →  437394baff5aa33daa618be47b75cb49

```

Hashing is one-way: you cannot mathematically reverse it. But MD5 was designed in 1991 for data integrity checks, not password storage. It is extremely fast to compute, which means an attacker can hash millions of guesses per second and compare them against a stolen hash until one matches. This is called a brute force attack.

Rainbow tables take this further. They are precomputed databases of billions of hashes and their original values, built in advance. Cracking a common MD5 hash takes less than a second by lookup.

## Step 4: Crack the hash

We used crackstation.net, a free online rainbow table. Pasting `437394baff5aa33daa618be47b75cb49` returned the result instantly:

```
437394baff5aa33daa618be47b75cb49  →  qwerty123@

```

We now had working credentials: `root` / `qwerty123@`.

## Step 5: Find the admin page

We guessed that `/admin` might exist. In a real engagement, this would be done systematically using a directory brute forcing tool. Let's explore some options to this effect. 

### How professionals find hidden pages

Instead of guessing one path at a time, penetration testers use tools that automatically try thousands of common directory and file names against a target. The most common tools for this are:

**gobuster**
```bash
gobuster dir -u http://192.168.64.2/ -w /usr/share/wordlists/dirb/common.txt
```

**dirb**
```bash
dirb http://192.168.64.2/
```

Both tools work by taking a wordlist (namely a text file containing thousands of common directory names like `admin`, `login`, `backup`, `config`, `uploads`, `private`) and trying each one as a URL. Any path that returns a 200 or 301 response instead of 404 is flagged as existing.

On this server, `/admin` would have appeared in the results immediately since it is one of the most common directory names in every wordlist.

## Step 6: Log into /admin

Visiting `http://192.168.64.2/admin` triggered an HTTP Basic Authentication dialog — a browser-native popup asking for a username and password, labelled "Secured Area."

We entered:
```
Username: root
Password: qwerty123@

```

The server accepted the credentials and displayed the flag.

## 🏁 Result

```
FLAG: d19b4823e0d5600ceed56d5e896ef328d7a2b9e7ac7e80f4fcdb9b10bcb3e7ff
```

## 🌍 Real-World Impact

This breach chains three separate failures together, each of which made the next step possible.

The first failure was using `robots.txt` to hide sensitive paths. This does not hide anything — it publicly documents what the developer wanted to keep secret.

The second failure was directory listing being enabled on `/whatever/`. Any visitor could browse the folder's contents as if they had access to the filesystem.

The third failure was storing the `htpasswd` file inside the web root where it was directly accessible via URL. This file should live outside the web root entirely, unreachable by any browser request.

The fourth failure was using MD5 to hash the password. MD5 has been considered cryptographically broken for decades. The password `qwerty123@` was recovered from the hash in under a second using a free website.

Any one of these failures alone would have been a problem. Together they created a clear path from a public text file to full admin access.

## 🛡️ Remediation Strategies

### Never use robots.txt to hide sensitive content

The file `robots.txt` is a public file. Using it to protect paths is not security. It is the opposite, because it tells attackers exactly where to look. Sensitive areas should be protected by authentication, not by hoping nobody reads the file.

### Disable directory listing

In Apache, directory listing is disabled by adding this to the server configuration or `.htaccess`:

```apache
Options -Indexes
```

With this in place, visiting a directory with no index file returns 403 Forbidden instead of a file browser.

### Store htpasswd outside the web root

The `htpasswd` file must never be inside any directory that the web server can serve. It should live somewhere like `/etc/apache2/.htpasswd` — outside `/var/www/html/` entirely — and be referenced in the server configuration:

```apache
AuthType Basic
AuthName "Secured Area"
AuthUserFile /etc/apache2/.htpasswd
Require valid-user
```

### Use strong password hashing

MD5 must never be used for passwords. Modern password hashing uses algorithms designed to be deliberately slow, making brute force attacks impractical. Apache supports bcrypt via the `$2y$` prefix in htpasswd files:

```bash
htpasswd -B /etc/apache2/.htpasswd root
```

The `-B` flag tells htpasswd to use bcrypt. A bcrypt hash takes hundreds of milliseconds to verify, meaning an attacker trying millions of guesses per second is reduced to a few per second.

### Use strong passwords

`qwerty123@` is a weak password that appears in every common wordlist. Even with a stronger hashing algorithm, a password this predictable can be cracked. Passwords protecting admin areas should be long, random, and unique.