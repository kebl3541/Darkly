# 🚩 9: Open Redirect

---

## 📝 Overview

This breach demonstrates how web applications can be compromised when they
use user-supplied input to determine where to redirect the browser, without
validating that the destination is an approved location.

The core problem is simple enough: the server takes whatever value the user
provides in the `site` parameter and redirects the browser there, completely
trusting that the value will be one of the expected social media destinations.
An attacker can substitute any URL they choose, using the trusted domain as
a launchpad to send victims anywhere.

---

## 🔍 The Vulnerability: Unvalidated Redirect

### What is an Open Redirect?

Every time a user clicks a redirect link, the browser sends a request to the
server containing the intended destination. The server then issues a redirect
response pointing the browser to that destination.

The redirect parameter is particularly relevant to this breach:

**The `site` Parameter**
This parameter tells the server where to redirect the user. For example,
clicking the Facebook icon in the footer sends:
```
GET /?page=redirect&site=facebook
```
The server is supposed to use this to redirect to the Facebook website.

### The Root Flaw

> The `site` parameter is entirely user-controlled.
> The server has no validation to ensure the value is one of the approved
> destinations. Because the server blindly trusts this input, an attacker
> can supply any URL and the server will redirect to it without question.

This is a fundamental design mistake. Using user input directly in a redirect
without a whitelist is equivalent to giving someone a key to your building
and trusting them to only open the doors they are supposed to. Anyone who
knows how the parameter works can redirect victims anywhere they choose.

---

## 🛠 The Exploit Path

### Step 1: Discovery & Reconnaissance

The first task in any security assessment is **reconnaissance**: gathering
information about the target without yet attempting to exploit it.

We began by reading the HTML source code of the homepage. This revealed the
footer social media links:

```html
<a href="index.php?page=redirect&site=facebook">
<a href="index.php?page=redirect&site=twitter">
<a href="index.php?page=redirect&site=instagram">
```

The `site` parameter controls where the user is sent. The server is clearly
designed to redirect to social media platforms — but the parameter name and
structure tell us it accepts a value from the client directly. This is
immediately suspicious.

### Step 2: Understanding What We Can Control

Now that we know the `site` parameter controls the redirect destination, we
need to understand whether the server validates this value at all:

| Expected values | What the server should check |
|----------------|------------------------------|
| `facebook` | Is `site` in the approved list? |
| `twitter` | If not → reject the request |
| `instagram` | If yes → redirect to mapped URL |

A secure server would map parameter values to pre-approved destinations
server-side. An insecure server would use the parameter value directly in
the redirect — which is exactly what this server does.

### Step 3: Execution

We identified two methods to exploit this vulnerability:

---

#### Option A: Browser URL Bar

The simplest method — no tools required. Just modify the `site` parameter
directly in the browser URL bar:

```
http://[IP]/index.php?page=redirect&site=https://www.google.com
```

Breaking this down:
- `http://[IP]/index.php` — the site we are targeting
- `?page=redirect` — loads the redirect handler
- `&site=https://www.google.com` — our arbitrary destination instead of
  a social media platform

The server receives this request, reads the `site` value, and redirects
the browser to Google — a destination it was never designed to redirect to.

---

#### Option B: curl (Command Line)

`curl` is a command-line tool that lets us make HTTP requests with complete
control over every parameter. The `-v` flag shows us the redirect response:

```bash
curl -v "http://[IP]/index.php?page=redirect&site=https://www.google.com"
```

The server's response will include a `Location` header pointing to Google,
confirming the redirect is unvalidated.

To retrieve the flag directly:

```bash
curl -s "http://[IP]/index.php?page=redirect&site=https://www.google.com" | grep -i flag
```

### Step 4: The Result

The server detects that the redirect destination is not one of the approved
social media sites and reveals the flag in the response:

```
FLAG: b9e775a0291fed784a2d9680fcfad7edd6b8cdf87648da647aaf4bba288bcab3
```

---

## 🌍 Real-World Impact

This type of vulnerability has real-world consequences:

**Phishing Attacks**
The most dangerous use of open redirects. An attacker crafts a link like:
```
https://trusted-bank.com/?page=redirect&site=https://fake-bank.com
```
The victim sees `trusted-bank.com` in the URL preview and trusts it. They
click it and arrive at a convincing fake login page, making them far more
likely to enter their credentials.

**Bypassing Security Filters**
Email security scanners and URL reputation services whitelist known trusted
domains. An open redirect on a trusted site lets attackers bypass these
filters — the scanner sees `trusted-site.com` and approves the link, even
though it leads somewhere malicious.

**OAuth Token Theft**
In OAuth authentication flows, access tokens are sent to a `redirect_uri`
after login. If an attacker can manipulate the redirect URI via an open
redirect on the trusted domain, they can steal authentication tokens and
take over accounts without knowing any passwords.

**Reputation Damage**
When a trusted site is used to redirect users to malicious content, the
organization's reputation suffers even though they were the victim, not
the attacker.

---

## 🛡️ Remediation Strategies

The golden rule of secure development is simple:

> **Never use user input directly in a redirect. Ever.**

The `site` parameter should never have been used as a URL without validation.
Here is how a developer should properly protect redirect functionality:

### 1. Use a Whitelist of Allowed Destinations

Map parameter values to pre-approved URLs server-side so the user never
controls the actual destination:

```php
// VULNERABLE
header('Location: ' . $_GET['site']);

// SECURE
$allowed = [
    'facebook'  => 'https://www.facebook.com',
    'twitter'   => 'https://www.twitter.com',
    'instagram' => 'https://www.instagram.com'
];
$site = $_GET['site'];
if (array_key_exists($site, $allowed)) {
    header('Location: ' . $allowed[$site]);
} else {
    die("Invalid redirect destination.");
}
```

The user provides a key (`facebook`), not a URL. The server chooses the
actual destination from a trusted list — the user has no control over
where the redirect goes.

### 2. Validate Against Allowed Domains

If dynamic redirect URLs are truly necessary, validate the destination
against a strict list of approved domains before redirecting:

```php
$url = $_GET['site'];
$parsed = parse_url($url);
$allowed_hosts = ['facebook.com', 'twitter.com', 'instagram.com'];

if (isset($parsed['host']) && in_array($parsed['host'], $allowed_hosts)) {
    header('Location: ' . $url);
} else {
    die("Redirect blocked: untrusted destination.");
}
```

### 3. Show an Intermediate Warning Page

If the application must allow redirects to external sites, show the user
a warning page before redirecting so they can make an informed decision:

```
You are leaving trusted-site.com and being redirected to:
https://external-site.com

[Continue] [Cancel]
```

### 4. Apply the Principle of Least Privilege

Redirect functionality should only ever be able to send users to a
pre-approved list of destinations. Any input that cannot be mapped to an
approved destination should be rejected outright, not used as-is.

### 5. Server-Side Validation for Everything

Assume every byte coming from the user is a potential lie. Validate all
redirect targets against a secure backend whitelist, not against the raw
value provided by the client.

---

## 📊 Quick Reference: Common Open Redirect Patterns

| Pattern | Risk | Mitigation |
|---------|------|------------|
| `?redirect=https://evil.com` | Full URL in parameter | Whitelist only |
| `?site=evil.com` | Domain in parameter | Validate against approved domains |
| `?next=/dashboard` | Relative path | Ensure path stays on same origin |
| `?to=//evil.com` | Protocol-relative URL | Full URL parsing and validation |

None of these patterns should ever be used directly in a `Location` header
without server-side validation against a whitelist of approved destinations.
