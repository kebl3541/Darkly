# 🌑 Darkly

42 Advanced Curriculum Project 

> **A hands‑on training environment for discovering and exploiting common web vulnerabilities across 14 distinct breaches.**

---

Darkly is a 42 School cybersecurity project that provides a deliberately vulnerable web application running in a VirtualBox VM (Darkly_i386.iso). The objective is to identify and exploit 14 unique security breaches, each revealing a specific flag. This repository documents all breaches with detailed exploitation steps, proofs of concept, and remediation strategies.



---

## 📝 The Project

**Darkly** is designed to teach web‑security fundamentals through practical exploitation. 

The goals are to:

- Discover **14 separate security breaches**.
- For each breach, **trigger the hidden flag** via a well‑defined attack.
- Understand how the vulnerability works and **how to remediate it** in a real‑world application.

The project is typically run inside a virtual machine (e.g., VirtualBox, UTM...). Each breach corresponds to a specific page or interaction in the app:

- Weak password‑change logic
- Broken session management & cookie‑based attacks
- Hidden parameter‑tampering
- Directory traversal
- SQL injection
- XSS (stored & via `data:` URI)
- File upload flaws
- Misconfigured redirects
- and more

This repository specifically contains:

- The vulnerable app and environment setup.
- One folder per breach (e.g., `01-weak_password_change_functionality`, `13-XSS_data_uri`, `14-Stored_XSS_feedback`).
- A `flag` file in each breach folder, released by the app only after the exploit is successfully executed.
- `README.md` files inside each breach folder documenting:
  - The vulnerability,
  - How to exploit it, and
  - How to fix it.

---

## 🧩 Learning Objectives

By working through Darkly, one learns how to:

- **Find attack surfaces** by inspecting HTML, URLs, and directory structure.
- **Discover and exploit**:
  - Authentication flaws (weak credentials, broken password‑change logic).
  - Session‑management issues (predictable sessions, cookie exposure).
  - Access‑control bugs (broken‑ACL, privilege escalation).
  - Input‑validation problems (SQL injection, XSS, path traversal, parameter‑tampering).
  - File‑handling bugs (unrestricted file upload, sensitive‑file exposure).
- **Craft and test payloads** with:
  - `curl`
  - Burp Suite
  - Bash scripts
  - Browser developer tools
- **Write clear, actionable remediation notes** in the same style used here.

This mirrors real‑world penetration‑testing workflows and helps you internalize the OWASP‑style mindset while staying project‑oriented.

---

## 🛠 Setup Instructions

### Prerequisites

- A **Linux Kali** or similar offensive‑sec machine (recommended for tooling).
- **VirtualBox** (or another VM runner).
- The **Darkly ISO** or OVA.
- Basic familiarity with:
  - Browsers and `curl`
  - HTML/HTTP concepts
  - Simple Bash scripting

### Steps

1. **Download the Darkly VM image**  
   - Get the ISO or OVA from your school or similar.

2. **Import the VM and start it**  
   - Open VirtualBox → `Import Appliance` or create a new Linux VM and attach the ISO.
   - Boot the VM and wait for the Darkly login / web‑server prompt.

3. **Determine the VM’s IP**  
   In the VM console (or your attacker machine), run:

   ```bash
   ip a
   ```

   Note the internal IP, e.g., `192.168.0.160`.

4. **Open the app in the browser**  
   On your attacker machine:

   ```text
   http://192.168.0.160
   ```

   You should see the Darkly home page and several navigation links.

5. **Sync this repo to your local machine**

   ```bash
   git clone https://github.com/kebl3541/Darkly.git
   cd Darkly
   ```

   As you solve each breach, update the corresponding breach folder’s `README.md` and `flag`‑related files locally so you have a complete, self‑documented record.

---

## 🧭 How to Approach the Breaches

Each breach is designed to be:

- **Self‑contained** (one folder per vulnerability).
- **Rooted in a real‑world class of bug** (not a toy example).
- **Documented in the same style** you’ve been using, so your write‑ups are consistent.

### Typical flow per breach

1. **Recon**  
   - Inspect the page source.
   - Check for hidden parameters, weak URLs, and exposed data (comments, `flag` files, etc.).

2. **Identify the flaw**  
   - Is it SQL injection?
   - XSS?
   - Parameter tampering?
   - File upload?
   - Path traversal?

3. **Build the exploit**  
   - Start with `curl`.
   - Move to Burp or scripts if needed.
   - Test step‑by‑step and observe the response.

4. **Capture the flag**  
   - The app will show the flag somewhere:
     - Directly on the page, or
     - As a newly unlocked `flag` file in the breach folder.
   - Copy it into your local `README.md` or `flag` file.

5. **Write the breach README**  
   Use the structure you’ve already established, e.g.:

   - `Overview`
   - `The Vulnerability`
   - `How We Found It`
   - `The Exploit`
   - `Real‑World Impact`
   - `Remediation Strategies`

---

## 📁 Repository Structure

Our `Darkly/` structure looks more or less like this:

```text
.
├── 01-weak_password_change_functionality
├── 02-absence_of_session_mgmt_and_cookie_predictability
├── 03-broken-access-control-and-weak-password
├── 04-hidden_directory_traversal
├── 05-unvalidated_redirect
├── 06-sql_injection_input
├── 07-useragent_exposure
├── 08-plain-text_password_in_url
├── 09-directory_traversal
├── 10-sql_injection_file_search
├── 11-local_file_upload
├── 12-survey_bad_design
├── 13-XSS_data_uri
├── 14-Stored_XSS_feedback
└── README.md
```

- Each numbered folder corresponds to one of the 14 breaches.
- The `flag` file at the root may contain the first or final flag, depending on how the app is configured.
- The `Ressources/images` folder holds static assets used by the app.

You do not need to modify the app’s code to complete the project; instead, you **document each breach** by filling in and refining the `README.md` inside every folder.

---

## 🧩 Example Breach Layout

Every breach folder should follow a uniform layout, like the ones you’ve already started:

```markdown
# 🚩 13 : XSS via Data URI

## 📝 Overview
...

## 🔍 The Vulnerability
...

## 🧠 How We Found the Attack Vector
...

## 🛠 The Exploit
...

## 🌍 Real‑World Impact
...

## 🛡️ Remediation Strategies
...

## 📊 Attack Chain Summary
...
```

This consistency makes it easy for reviewers to:

- Quickly understand the bug.
- Reproduce the exploit.
- See the recommended fixes.

---

## 🧠 Recommended Tooling

To get the most out of Darkly, use:

- **`curl`** – for quick, scriptable testing of HTTP requests.
- **Burp Suite Community** – for intercepting and modifying requests, exploring referers, cookies, and headers.
- **Browser dev tools (F12)** – for inspecting HTML, modifying hidden fields, and testing DOM‑based flaws.
- **Bash / shell scripts** – for automating brute‑force, loops, or data‑URI constructions.
- **`grep`, `awk`, `sed`** – for parsing responses and extracting flags or patterns.
- **Gobuster**

---

## 🌍 Why This Matters

Darkly is based on **real‑world web‑security flaws** that appear in modern web applications again and again:

- **Broken authentication and session‑management** lead to account takeovers.
- **SQL injection and XSS** let attackers read or exfiltrate data.
- **Path traversal and file‑upload bugs** expose the server’s filesystem.
- **Unvalidated parameters and redirects** open the door to phishing and tampering.

Understanding how these bugs work in a controlled environment makes us far better prepared to:

- Find and fix them in commercial or enterprise apps.
- Write hardening rules and checks that prevent them from reappearing.

---

## 🛡️ General Remediation Philosophy

Across all 14 breaches, the same core principles apply:

- **Never trust the client**:
  - Validate **server‑side**, not inside HTML or JavaScript.
  - Treat `GET`, `POST`, `cookies`, and `headers` as untrusted.
- **Defend in depth**:
  - Use **input validation**, **canonicalization**, and **context‑aware escaping** (OWASP XSS Prevention cheat sheet, SQL‑injection escapes).
  - Apply **rate‑limiting**, **captcha**, and account‑lockout where appropriate.
- **Avoid “security by obscurity”**:
  - Hidden fields, hidden directories, or unusual parameter names are **not** security.
  - Assume any exposed endpoint can be found and tested.
- **Log and monitor**:
  - Record suspicious events (failed attempts, parameter‑tampering signs) so you can detect attacks before they finish.

By documenting each breach with both **attack** and **fix**, we turned Darkly into a personal “cheat sheet” for web‑security that we can reuse far beyond this project.

---

