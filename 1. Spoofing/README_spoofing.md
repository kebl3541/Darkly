# 🚩 1 : Header Spoofing (Referer & User-Agent)

---

## 📝 Overview

This breach demonstrates how web applications can be compromised when they rely on client-side HTTP headers for access control. We will identify a "Blind Trust" vulnerability, simulate a spoofing attack to bypass restrictions, and discuss why server-side validation is the only reliable defense.

The core problem is simple enough: the server asks the browser "who are you
and where did you come from?" and then completely believes whatever the browser says, without any way to verify the answer. Instead, one should find ways of having proof of ID, so to speak.

---

## 🔍 The Vulnerability: Blind Trust in HTTP Headers

### What are HTTP Headers?

Every time a browser visits a webpage, it sends a request to the server. Along with that request, it automatically attaches small pieces of metadata called
**HTTP headers**. Like sticky notes attached to a letter, they
provide extra context about the sender, the letter's origin, and how it should
be handled.

Two headers are particularly relevant to this breach:

**1. The `Referer` Header**
This header tells the server what URL the user was on before arriving at the
current page. For example, if you click a link on google.com, your browser
sends:
```
Referer: https://www.google.com
```
Some servers use this to restrict access — for example, only serving content
to users who arrived from a trusted source, like their own homepage or a
partner website.

**2. The `User-Agent` Header**
This acts as your browser's "digital fingerprint." It identifies what browser
and operating system you are using. For example, Chrome on a Mac sends:
```
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36
(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36
```
Some servers use this to restrict access to users with specific browsers, or
to serve different content to mobile vs desktop users.

### The Root Flaw

> Both of these headers are entirely client-controlled.
> The server has absolutely no way to verify whether the values are genuine.
> Because the server "blindly trusts" this data without any secondary
> authentication, an attacker can manually craft these headers to mirror
> any identity or origin the server expects.

This is a fundamental design mistake. Using HTTP headers as a security gate is equivalent to locking a door and hiding the key under the doormat. Anyone who knows to look there can walk right in.

---

## 🛠 The Exploit Path

### Step 1: Discovery & Reconnaissance

The first task in any security assessment is **reconnaissance**: gathering
information about the target without yet attempting to exploit it.

We began by locating a hidden page on the application. By reading the HTML
source code of the homepage (using `curl` or browser "View Source"), we
discovered a suspicious link hidden in the page:

```
?page=b7e44c7a40c5f80139f0a50f3650fb2bd8d00b0d24667c4c2ca32c88e13b758f
```

This is a technique called **Security Through Obscurity** — hiding a page
behind an unguessable URL instead of protecting it with real authentication.
It fails because the URL was linked from a public page, making it discoverable
to anyone who reads the source code.

We visited this hidden page (the "albatross" page, reachable by clicking on '@BorntoSec' at the bottom of the website) and carefully read its
full HTML source code. This revealed two critical breadcrumbs hidden inside
HTML comments. 

There were two notes left by the developer that were invisible on screen
but readable in the raw code:

```html

<!-- You must come from : "https://www.nsa.gov/" -->
<!-- Let's use this browser: "ft_bornToSec". It will help you a lot. -->
```

These comments tell us *exactly* what the server is checking:
- It expects the `Referer` header to be `https://www.nsa.gov/`
- It expects the `User-Agent` header to be `ft_bornToSec`

This is a critical reconnaissance finding. The developer accidentally documented their own security mechanism in the source code, which any attacker can read.

### Step 2: Understanding What We Need to Fake

Now that we know what the server expects, we need to send a request that
satisfies **both conditions simultaneously**:

| Header | Expected Value |
|--------|---------------|
| `Referer` | `https://www.nsa.gov/` |
| `User-Agent` | `ft_bornToSec` |

A normal browser would never send these values. The Referer would be
whatever page you actually came from, and the User-Agent would identify
your real browser. So we need to craft a custom request manually.

### Step 3: Execution

We came up with at least two methods to forge these headers:

---

#### Option A: Using `curl`

`curl` is a command-line tool that lets you make HTTP requests with complete
control over every header, method, and parameter. It is the industry standard
for testing and exploiting web vulnerabilities because it is transparent,
scriptable, and precise.

The `-H` flag in curl allows us to inject any header we want into the request:

```bash
curl "http://localhost:8080/?page=b7e44c7a40c5f80139f0a50f3650fb2bd8d00b0d24667c4c2ca32c88e13b758f" \
  -H "Referer: https://www.nsa.gov/" \
  -H "User-Agent: ft_bornToSec" \
  -v
```

Breaking this down piece by piece:
- `curl` — the tool we are using to make the HTTP request
- `"http://localhost:8080/?page=..."` — the hidden albatross page URL
- `-H "Referer: https://www.nsa.gov/"` — we forge the Referer header to
  pretend we just came from the NSA website
- `-H "User-Agent: ft_bornToSec"` — we forge the User-Agent to pretend
  we are using a special custom browser called "ft_bornToSec"
- `-v` — "verbose" mode, which shows us all the headers being sent and
  received, useful for debugging

The server receives this request, checks the headers, finds both values match
what it expects, and rewards us with the flag.

---

#### Option B: Burp Suite (Professional Tool)

Burp Suite is a professional web security testing platform used by penetration
testers worldwide. It works as a **proxy**, sitting between one's browser and
the server, intercepting every request before it is sent, allowing one to
modify any header, parameter, or body content in real time.

With Burp Suite one would:
1. Configure browser to route traffic through Burp
2. Visit the albatross page normally
3. Burp intercepts the request before it reaches the server
4. Manually edit the `Referer` and `User-Agent` headers
5. Forward the modified request to the server
6. The server returns the flag

---

#### Option C: ModHeader extension

Another easy way to modify the header is to add an extension like ModHeader to the browser and then tamper with Referer and User-Agent. It lets you add or override any HTTP header for every request your browser makes.

This is actually the method we used to get the flag.

Steps for this option: 

1. Install ModHeader from the browser
2. Click the extension icon
3. Add a Request Header: Name = Referer, Value = https://www.nsa.gov/
4. Add another: Name = User-Agent, Value = ft_bornToSec
5. Visit the albatross page — the headers are automatically sent

### Step 4: The Result

Upon receiving the forged request with both headers matching the expected
values, the server's access control check passes and it returns the flag:

```
FLAG: f2a29020ef3132e01dd61df97fd33ec8d7fcd1388cc9601e7db691d17d4d6188
```




## 🌍 Real-World Impact

This type of vulnerability has real-world consequences:

**Content Theft / Hotlink Bypassing**
Many image hosting sites use Referer checks to prevent other sites from
directly embedding their images (called "hotlinking"). Referer spoofing
trivially bypasses this.

**Access Control Bypass**
Applications that restrict features to specific browsers (e.g., "this feature
only works in our mobile app") can be bypassed by spoofing the User-Agent to
match the expected app identifier.

**Ad Fraud**
Advertising networks track where traffic comes from using the Referer header.
Fraudsters spoof Referer headers to fake traffic sources and claim ad revenue
they did not earn.

**CSRF Protection Bypass**
Some applications use the Referer header as a weak CSRF (Cross-Site Request
Forgery) protection. If an attacker can spoof the Referer, this protection
is completely defeated.

---

## 🛡️ Remediation Strategies

The golden rule of secure development is simple:

> **Never trust the client. Ever.**

(Sorry, client). HTTP headers should be treated as metadata, not security tokens. 
 So here is how a developer should properly protect sensitive resources:

### 1. Never Use Headers as Authentication
Remove any code that uses `Referer` or `User-Agent` to gate-keep sensitive
content. These values are freely modifiable by any user using curl, browser
extensions, proxy tools like Burp Suite, or simple scripts.

### 2. Implement Proper Session-Based Authentication
Use secure, server-side session management to control access:
- Generate a unique session token when a user logs in
- Store the session server-side (not in a cookie the user can modify)
- Use `HttpOnly` and `Secure` flags on cookies to prevent JavaScript access
  and enforce HTTPS transmission
- Validate the session token on every protected request

### 3. Use Anti-CSRF Tokens (Not Referer Checks)
To prevent Cross-Site Request Forgery attacks, use cryptographically generated
Anti-CSRF tokens that are:
- Generated server-side and unique per session or per request
- Embedded in forms as hidden fields
- Verified server-side on every state-changing request
- Never predictable or reusable

### 4. Apply the Principle of Least Privilege
Sensitive pages and resources should require authentication by default.
Access should be explicitly granted, not implicitly assumed based on
unverifiable metadata.

### 5. Server-Side Validation for Everything
Assume every byte coming from the user is a potential lie. Validate all
access rights against a secure backend database, not against client-provided
headers, cookies, or form fields.

---

## 📊 Quick Reference: Commonly Abused HTTP Headers

| Header | What it Claims | Why it's Dangerous to Trust |
|--------|---------------|----------------------------|
| `Referer` | Where you came from | Freely editable by anyone |
| `User-Agent` | What browser you use | Freely editable by anyone |
| `X-Forwarded-For` | Your real IP behind a proxy | Can be set to any IP address |
| `X-Custom-IP-Authorization` | Your IP for auth purposes | Trivially spoofed |
| `Cookie` | Your session/identity | Can be stolen via XSS or modified |

None of these headers should ever be used as the sole basis for authentication
or authorization decisions.