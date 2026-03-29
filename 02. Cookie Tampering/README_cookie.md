# 🚩 2 : Cookie Tampering (I_am_admin)

---

## 📝 Overview

This breach demonstrates how web applications can be compromised when they store trust decisions in client-side cookies without cryptographic protection. 

We identify a "Client-Side Trust" vulnerability, simulate a cookie tampering
attack to gain admin access, and discuss why server-side session management is
the only reliable defense.

The core problem is this: the server asks the browser "are you an admin?" — and then completely believes whatever the browser says, without any way to verify the answer. 


---

## 🔍 The Vulnerability: Trusting Client-Side Cookies

### What are Cookies?

Cookies are small pieces of data that a web server sends to a browser, and the browser then stores and sends back with every subsequent request to that
server. Basically they work like a stamp on one's hand at a Berlin nightclub. Every time one comes back to the door, the bouncer checks the stamp.

Cookies are commonly used for:
- Keeping a client logged in between page visits
- Storing a client's preferences (language, theme, etc.)
- Tracking the client's session on the server

### The Issue

The problem arises when developers store **sensitive decisions** inside cookies. 

In this case, the server stores whether the client is an admin or not directly in a cookie that the browser holds. Since the browser holds the cookie, **the client can read it, modify it, and send back whatever value they want.**

Let's go back to the Berlin nightclub: the bouncer gave us a stamp that says "NOT VIP". Then they trusted us completely when we come back with a stamp that says "VIP" that we drew yourself. So we got in. That's our plan for this breach.

---

## 🛠 The Exploit

### Step 1: Discovery & Reconnaissance

The first step is to inspect what cookies the server sets when we visit the
site. We can do this using curl with the `-I` flag, which fetches only the
HTTP response headers (not the full page):

```bash
curl -s -I http://localhost:8080/
```

This returns the server's response headers, including any `Set-Cookie` headers:

```
HTTP/1.1 200 OK
Server: nginx/1.4.6 (Ubuntu)
Set-Cookie: I_am_admin=68934a3e9455fa72420237eb05902327; expires=...; Max-Age=3600

```

We can see the server sets a cookie called `I_am_admin` with a value of:

```
68934a3e9455fa72420237eb05902327

```

This is a 32-character hexadecimal string, which suggests we have an **MD5 hash**.

### Step 2: Cracking the Hash

MD5 is a hashing algorithm which takes any input and produces a fixed-length
32-character string. For example:

```

"false"  →  68934a3e9455fa72420237eb05902327
"true"   →  b326b5062b2f0e69046810717534cb09
"hello"  →  5d41402abc4b2a76b9719d911017c592

```

Hashing is a **one-way function**, that is a function that one cannot mathematically reverse. However, for common words and phrases, one can use a **rainbow table**, a massive pre-computed database of hashes and their original values.

We used **crackstation.net** (a free online rainbow table) to crack the hash:

```
68934a3e9455fa72420237eb05902327  →  "false"

```

Bingo! The cookie is storing the MD5 hash of the word "false" to indicate that we are NOT an admin. This immediately tells us what to do next: generate the MD5 hash of "true" and send that instead.

### Step 3: Generating the Fake Cookie Value

We need the MD5 hash of the word "true". We can generate this directly in
the Mac terminal:

```bash
echo -n "true" | md5
```

The `-n` flag is important because it tells echo NOT to add a newline character at the end, which would change the hash. The result is:

```
b326b5062b2f0e69046810717534cb09

```

This is the MD5 hash of "true", namely the value we need to send as our cookie
to convince the server we are an admin.

### Step 4: Sending the Forged Cookie

There are several ways to send the forged cookie to the server. Each method
achieves the same result: tricking the server into thinking we are an admin.

---

#### Option A: curl (Command Line)

```bash
curl -s http://localhost:8080/ --cookie "I_am_admin=b326b5062b2f0e69046810717534cb09"
```

Breaking this down:
- `curl`: the tool we use to make the HTTP request
- `http://localhost:8080/`: the homepage of the site
- `--cookie "I_am_admin=b326b5062b2f0e69046810717534cb09"`: we send our
  forged cookie, claiming to be an admin by sending the MD5 hash of "true"

The server receives this request, reads the cookie, finds the value matches
the MD5 of "true", and grants us admin access. This leads it to reveal the flag.

---

#### Option B: Browser Developer Tools (No Commands Needed)

This method requires no terminal commands at all: just point and click.

1. Open the browser and visit `http://localhost:8080/`
2. Press **F12** (or **Cmd+Option+I** on Mac) to open Developer Tools
3. Go to the **Application** tab
4. In the left sidebar, click **Cookies** → click on `localhost:8080`
5. You will see the `I_am_admin` cookie listed with its current value
6. **Double click the value** and replace it with:
   ```
   b326b5062b2f0e69046810717534cb09
   ```
7. Press Enter, then refresh the page

The browser now automatically sends the modified cookie with every request.
This works because the browser has no way of knowing that the original value
came from the server — it just stores whatever is in the cookie jar and sends
it back. We are simply updating the value in the jar.

---

#### Option C: Browser Console (JavaScript)

One can also modify cookies directly using JavaScript in the browser console:

1. Press **F12** → go to the **Console** tab
2. Type the following and press Enter:

```javascript
document.cookie = "I_am_admin=b326b5062b2f0e69046810717534cb09";
```

3. Refresh the page

The `document.cookie` property in JavaScript gives read and write access
to all cookies for the current page. By assigning a new value, we overwrite
the existing cookie with the forged one.

---

#### Option D: Browser Extensions

Extensions like **EditThisCookie** (available for Chrome) provide a simple
graphical interface to view, edit, add, and delete any cookie on any website
with just a few clicks.

Once installed, a cookie icon appears in the browser toolbar. Click it while
on the target site to see all cookies, then simply edit the `I_am_admin` value
directly in the extension's interface.

---

#### Option E: Burp Suite (Professional Tool)

Burp Suite is a professional web security testing platform used by penetration
testers worldwide. It works as a **proxy** — sitting between the browser and
the server, intercepting every request before it is sent.

With Burp Suite one would:
1. Configure the browser to route traffic through Burp
2. Visit the homepage normally
3. Burp intercepts the request before it reaches the server
4. Modify the `I_am_admin` cookie value directly in the intercepted request
5. Forward the modified request to the server
6. The server returns the flag

Burp Suite is the industry standard tool for this type of work in professional
penetration testing engagements.

---

### Step 5: The Result

Regardless of which method is used, the server receives the forged cookie,
trusts it completely, and returns the flag:

```
FLAG: df2eb4ba34ed059a1e3e89ff4dfc13445f104a1a52295214def1c4fb1693a5c3
```

---

## 🌍 Real-World Impact

Cookie tampering is one of the most common and dangerous web vulnerabilities.
Here are some real-world scenarios where this type of attack causes serious damage:

**a) Privilege Escalation**
An attacker modifies a cookie that stores their user role from `role=user`
to `role=admin`, gaining administrative access to the entire application (user management, database access, and configuration settings...).

**b) Account Takeover**
If session tokens are predictable or stored insecurely, an attacker can
forge a cookie to impersonate any user on the platform without knowing
their password.

**c) Price Manipulation**
E-commerce sites that store prices or discount values in cookies can be
exploited by users who modify the cookie so to change the price of items
in their cart.

**d) Authentication Bypass**
Applications that store `isLoggedIn=true` in a cookie can be bypassed by
simply setting that cookie value and skipping the login process entirely.

---

## 🛡️ Remediation Strategies

### 1. Never Store Trust Decisions in Client-Side Cookies

The fundamental rule: **never store anything in a cookie that the server
will use to make security decisions, unless it is cryptographically signed
and verified.**

The following should NEVER be stored directly in cookies:
- User roles (`admin=true`, `role=admin`)
- Authentication status (`isLoggedIn=true`)
- User IDs used directly for database lookups
- Prices, discounts, or quantities

### 2. Use Server-Side Sessions

Instead of storing the user's role in a cookie, one should store only a **random,
unpredictable session ID** in the cookie. The actual user data (including
their role) is stored on the server, indexed by that session ID.

```
Cookie: session_id=a3f9b2c1d4e5f6a7b8c9d0e1f2a3b4c5

```

When the server receives this cookie, it looks up `a3f9b2c1...` in its
own database and retrieves the user's real role from there. The client
cannot modify their role because the role is stored on the server, not
in the cookie.

### 3. Sign Cookies Cryptographically

If one absolutely must store data in cookies, one should use **cryptographic signing** (HMAC) to ensure the data has not been tampered with:

```
Cookie: I_am_admin=false.HMAC_SIGNATURE

```

Here is how this works. The server generates a signature using a secret key only it knows. When it receives the cookie back, it re-computes the signature and compares. If the user modifies the value, the signature will not match and the server will reject it.

### 4. Secure Cookie Flags

One should always set these flags on sensitive cookies:

- `HttpOnly`: prevents JavaScript from reading the cookie, protecting
  against XSS attacks that try to steal cookies

- `Secure`: ensures the cookie is only sent over HTTPS connections,
  preventing interception on unencrypted networks

- `SameSite`: controls when the browser is allowed to send the cookie
  along with cross-site requests, protecting against CSRF attacks.
  There are two main values:

  **SameSite=Strict**
  The cookie is ONLY sent if the user is already on the same site. If ANY
  other website sends a request to our server, the cookie is NOT included.
  This is the most secure option, but can feel jarring. For example, if
  someone emails you a link to the site, clicking it won't include your
  cookie, so you'll appear logged out even though you were already logged in.

  **SameSite=Lax**
  The cookie IS sent when the user clicks a normal link from another site,
  but NOT for hidden background requests (like form submissions or image
  loads triggered by a malicious site). This is the recommended default: a  good balance between security and usability.


### 5. Never Use Weak Hashing for Security

MD5 is completely broken for security purposes:
- It is trivially crackable using rainbow tables (as demonstrated here)
- It is not designed for password or security token storage
- It produces identical output for identical input (no salting)

For any security-sensitive hashing, one should use **bcrypt**, **Argon2**, or
**scrypt**, namely algorithms specifically designed to be slow and resistant
to brute force attacks.

---

## 📊 Cookie Security Checklist

| Check | Secure Practice |
|-------|----------------|
| Where is user role stored? | Server-side session, never in cookie |
| Is the cookie signed? | Yes, using HMAC with a secret key |
| Is HttpOnly set? | Yes, always |
| Is Secure flag set? | Yes, always (requires HTTPS) |
| Is SameSite set? | Yes, Strict or Lax depending on use case |
| Is the session ID random? | Yes, cryptographically random |
| Does the session expire? | Yes, with a reasonable timeout |