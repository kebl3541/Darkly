# 🚩 Open Redirect

---

## 📝 Overview

This breach demonstrates an Open Redirect vulnerability in the site's social
media redirect feature. The server accepts a user-controlled URL parameter
and redirects the browser to it without validating whether the destination
is safe or expected.

The core problem is simple: the server trusts the `site` parameter completely,
redirecting users to whatever URL it contains. An attacker can craft a link
that appears to come from a trusted domain but silently sends the victim
anywhere they choose.

---

## 🔍 The Vulnerability: Open Redirect

### What is an Open Redirect?

An Open Redirect occurs when a web application uses user-supplied input to
determine where to redirect the browser, without validating that the
destination is an approved location.

The danger is not what happens on the vulnerable server itself — it is that
the attacker can abuse the trusted domain's reputation to make a malicious
link look legitimate:

```
https://trusted-site.com/?page=redirect&site=https://evil.com
```

The victim sees `trusted-site.com` in the URL, trusts it, clicks it, and
ends up on `evil.com`. The trusted domain was used as a launchpad.

### Discovery

Reading the HTML source of the homepage reveals the footer social media links:

```html
<a href="index.php?page=redirect&site=facebook">
<a href="index.php?page=redirect&site=twitter">
<a href="index.php?page=redirect&site=instagram">
```

The `site` parameter controls where the user is sent. The server is clearly
designed to redirect to social media platforms — but the parameter accepts
any value, not just the three expected ones.

---

## 🛠 The Exploit

### Step 1 — Confirm expected behavior

Clicking the Facebook link:
```
http://[IP]/index.php?page=redirect&site=facebook
```
Redirects to Facebook as expected. This confirms the redirect mechanism works
and that `site` directly controls the destination.

### Step 2 — Test with an arbitrary URL

```
http://[IP]/index.php?page=redirect&site=https://www.google.com
```

The server redirects to Google — a completely unexpected destination. This
confirms the server performs no validation on the `site` value whatsoever.

### Step 3 — Retrieve the flag

The server detects that the redirect destination is not one of the approved
social media sites and reveals the flag in the response:

```bash
curl -s "http://[IP]/index.php?page=redirect&site=https://www.google.com" | grep -i flag
```

---

## 🏁 Result

```
FLAG: b9e775a0291fed784a2d9680fcfad7edd6b8cdf87648da647aaf4bba288bcab3
```

---

## 🔑 Why This Flag is Identical to XSS Basic

Both breaches exploit the exact same vulnerable parameter:
```
?page=redirect&site=[USER INPUT]
```

The server fails to sanitize this input in two ways simultaneously:
1. It redirects to whatever URL the user provides → **Open Redirect**
2. It reflects the value unsanitized into the HTML response → **XSS**

Both vulnerabilities exist in the same line of code. This is why both
breaches produce the same flag — they are two different attacks on the
same root cause.

---

## 🌍 Real-World Impact

**a) Phishing Attacks**
The most common real-world use of open redirects. An attacker sends a
victim a link like:
```
https://trusted-bank.com/?page=redirect&site=https://fake-bank.com
```
The victim sees the trusted bank domain in the link preview and clicks it,
arriving at a convincing fake login page. Since the URL started with a
domain they trust, they are far more likely to enter their credentials.

**b) Bypassing Security Filters**
Email security scanners and URL reputation services often whitelist known
trusted domains. An open redirect on a trusted site lets attackers bypass
these filters — the scanner sees `trusted-site.com` and allows the link
through, even though it leads somewhere malicious.

**c) OAuth Token Theft**
In OAuth authentication flows, access tokens are sent to a `redirect_uri`
after login. If an attacker can manipulate the redirect URI via an open
redirect on the trusted domain, they can steal authentication tokens and
take over accounts without knowing the user's password.

**d) SSRF Escalation**
In some server configurations, open redirects can be chained with
Server-Side Request Forgery (SSRF) vulnerabilities to make the server
itself fetch internal resources that should not be publicly accessible,
such as cloud metadata endpoints or internal admin panels.

---

## 🛡️ Remediation Strategies

### 1. Use a Whitelist of Allowed Destinations

The simplest and most effective fix — map parameter values to pre-approved
URLs server-side, so the user never controls the actual destination:

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

The user provides a key (`facebook`) not a URL. The actual URL is chosen
by the server from a trusted list — the user has no control over where
they end up.

### 2. Validate Against Allowed Domains

If dynamic redirects are truly necessary, validate the destination against
a strict list of approved domains before redirecting:

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

If the application must redirect to external sites, show a warning page
first so the user can make an informed decision:

```
You are leaving trusted-site.com and being redirected to:
https://external-site.com

[Continue] [Cancel]
```

### 4. Never Trust User Input for Security Decisions

The golden rule: treat every value from the user as untrusted. The `site`
parameter should never have been used directly in a `Location` header
without validation.

---

## 📊 Attack Chain Summary

```
1. Recon       →  found ?page=redirect&site= in footer HTML source
2. Tested      →  site=facebook redirects to Facebook as expected
3. Tested      →  site=https://www.google.com redirects to Google
4. Confirmed   →  server accepts any URL without validation
5. Flag        →  server detects unexpected destination and reveals flag
6. Key insight →  same parameter also vulnerable to XSS → identical flag
```
