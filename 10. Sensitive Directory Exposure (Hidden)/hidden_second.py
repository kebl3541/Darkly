import urllib.request
# Import the urllib.request module from Python's standard library.
# This lets us make HTTP requests without installing any external libraries.

import re
# Import the re module for regular expressions.
# We use this to extract folder links from the HTML the server returns.

base = 'http://192.168.64.2/.hidden/'
# Store the base URL of the target directory.
# Every request we make starts from this address.

def get_links(url):
# Define a function that takes a URL and returns a list of subfolder links.

    res = urllib.request.urlopen(url).read().decode()
    # Fetch the page at the given URL and decode the response into a string.

    return re.findall(r'href="([a-z][^"]+/)"', res)
    # Use a regular expression to find all href attributes that start with
    # a lowercase letter and end with a slash. This matches folder links
    # like href="amcbevgondgcrloowluziypjdh/" and ignores href="../"

seen = set()
# Create an empty set to track unique README contents.
# A set only stores unique values so adding the same string twice has no effect.
# This means each French decoy phrase is printed only once
# instead of thousands of times.

for d1 in get_links(base):
# Loop through every level-1 folder in .hidden/

    for d2 in get_links(base+d1):
    # For each level-1 folder, loop through every level-2 folder inside it.

        for d3 in get_links(base+d1+d2):
        # For each level-2 folder, loop through every level-3 folder inside it.

            content = urllib.request.urlopen(base+d1+d2+d3+'README').read().decode().strip()
            # Build the full URL of the README at the bottom of this level-3 folder,
            # fetch it, and strip any extra whitespace from the result.

            if content not in seen:
            # Only process this content if we have not seen it before.

                seen.add(content)
                # Add to the seen set so we do not print it again.

                print(content)
                # Print the content. Most of the time this is a French decoy phrase.
                # The one time it prints something different, that is the flag.