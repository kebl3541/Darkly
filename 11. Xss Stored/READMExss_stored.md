# 🚩 11 : Stored XSS via Input Field (Client-Side Validation Bypass)

------------------------------------------------------------------------

## 📝 Overview

This breach demonstrates how a web application can be compromised when
it **fails to properly sanitize user input before rendering it in
HTML**. By exploiting a **Stored Cross-Site Scripting (XSS)**
vulnerability, we inject malicious JavaScript into the application,
which is then executed in the browser.

The core issue is straightforward:

> The application trusts user input and directly embeds it into the page
> without sanitization.

Even worse, it relies on **client-side restrictions** (like `maxlength`)
as if they were security controls --- which they are not.

------------------------------------------------------------------------

## 🔍 The Vulnerability: Unsanitized User Input

### What is XSS?

**Cross-Site Scripting (XSS)** is a vulnerability that allows an
attacker to inject **JavaScript code** into a web page viewed by other
users.

When the browser renders the page, it executes the injected script as if
it were part of the application.

------------------------------------------------------------------------

### Where is the flaw?

The application provides a feedback form:

    <input name="txtName" type="text" size="30" maxlength="10">
    <textarea name="txtMessage"></textarea>

User input is later displayed on the page as:

    <div>Name: USER_INPUT</div>

------------------------------------------------------------------------

### The Root Flaw

> The application inserts user input directly into HTML without escaping
> special characters like `<`, `>`, or `"`.

This allows an attacker to inject HTML/JavaScript such as:

    <script>alert(1)</script>

------------------------------------------------------------------------

### Misleading Protection: `maxlength`

The developer attempted to limit input with:

    maxlength="10"

However:

> This is purely a **client-side restriction**, enforced only by the
> browser UI.

It can be bypassed easily by: - Pasting longer input - Sending requests
manually - Using developer tools

------------------------------------------------------------------------

## 🛠 The Exploit Path

### Step 1: Discovery & Reconnaissance

We begin by interacting with the feedback form and observing how input
is handled.

A simple test payload is entered into the **Name field**:

    <script>alert(1)</script>

------------------------------------------------------------------------

### Step 2: Observing Behavior

-   Typing the payload directly is restricted due to `maxlength=10`
-   However, **pasting the payload bypasses this restriction**

This reveals: - The browser UI enforces limits - The server does **not
validate input length**

------------------------------------------------------------------------

### Step 3: Execution

After submitting the payload, the application renders:

    <div>Name: <script>alert(1)</script></div>

The browser interprets this as executable JavaScript and runs it.

------------------------------------------------------------------------

### Step 4: Confirming XSS

The alert box appears, confirming: - JavaScript execution is possible -
The application is vulnerable to **Stored XSS**

------------------------------------------------------------------------

## 🌍 Real-World Impact

Stored XSS vulnerabilities are extremely dangerous because they affect
**every user who views the page**.

### Session Manipulation

Attackers can act within the context of another user.

------------------------------------------------------------------------

### Privilege Escalation

If a privileged user visits the page, their access level can be abused.

------------------------------------------------------------------------

### Data Exposure

Attackers can read: - Page content - User input - Hidden application
data

------------------------------------------------------------------------

### Persistent Attacks

Unlike reflected XSS, stored XSS remains in the system and triggers
repeatedly.

------------------------------------------------------------------------

## 🛡️ Remediation Strategies

The core security principle applies here:

> **Never trust user input. Always sanitize and encode it.**

------------------------------------------------------------------------

### 1. Escape Output Properly

Before rendering user input in HTML:

-   Convert `<` → `&lt;`
-   Convert `>` → `&gt;`
-   Convert `"` → `&quot;`

This ensures input is treated as **text**, not code.

------------------------------------------------------------------------

### 2. Validate Input Server-Side

Do not rely on: - `maxlength` - HTML attributes - JavaScript validation

Instead: - Enforce strict validation on the server - Reject unexpected
input

------------------------------------------------------------------------

### 3. Use Content Security Policy (CSP)

A strong CSP can prevent inline JavaScript execution:

    Content-Security-Policy: default-src 'self'; script-src 'self'

------------------------------------------------------------------------

### 4. Sanitize Input Libraries

Use well-tested libraries for escaping and sanitization instead of
writing custom logic.

------------------------------------------------------------------------

### 5. Treat All Input as Untrusted

Every input source is dangerous: - Form fields - URL parameters -
Headers - Stored data

------------------------------------------------------------------------

## 📊 Quick Reference: XSS Indicators

  Indicator             Meaning
  --------------------- --------------------------------
  `<script>` executes   Direct XSS vulnerability
  HTML tags render      Input not escaped
  Alert box appears     JavaScript execution confirmed
  Input persists        Stored XSS

------------------------------------------------------------------------

## ⚡ Key Takeaway

> The application relied on client-side validation and failed to
> sanitize user input, allowing arbitrary JavaScript execution.

This resulted in a classic **Stored XSS vulnerability**.
