import urllib.request
# This lets us make HTTP requests without
# installing any external libraries. No pip install needed.

import re
# We use this to extract links from the HTML the server returns.

base = 'http://192.168.64.2/.hidden/'
# Store the base URL of the target directory in a variable.


def get_links(url):
# Define a function called get_links that takes a URL as input
# and returns a list of subfolder links found on that page.

    res = urllib.request.urlopen(url).read().decode()
    # Open the URL, read the raw bytes of the response,
    # and decode them into a string of HTML text.

    return re.findall(r'href="([a-z][^"]+/)"', res)
    # Use a regular expression to find all href attributes in the HTML
    # that start with a lowercase letter and end with a slash.
    # This matches folder links like href="amcbevgondgcrloowluziypjdh/"
    # and ignores links like href="../" (parent directory).
    # re.findall returns a list of all matches.

seen = set()
# Create an empty set called seen.
# A set only stores unique values — adding the same value twice has no effect.
# We use this to track which README contents we have already printed,
# so each unique message appears only once in the output instead of
# being printed thousands of times.

for d1 in get_links(base):
# Loop through every level-1 folder in .hidden/.
# d1 will be something like "amcbevgondgcrloowluziypjdh/"

    for d2 in get_links(base+d1):
    # For each level-1 folder, loop through every level-2 folder inside it.
    # base+d1 constructs the full URL of the level-1 folder.
    # d2 will be something like "acbnunauucfplzmaglkvqgswwn/"

        for d3 in get_links(base+d1+d2):
        # For each level-2 folder, loop through every level-3 folder inside it.
        # base+d1+d2 constructs the full URL of the level-2 folder.
        # d3 will be something like "ayuprpftypqspruffmkuucjccv/"

            content = urllib.request.urlopen(base+d1+d2+d3+'README').read().decode().strip()
            # Build the full URL of the README file at the bottom of this
            # level-3 folder by appending 'README' to the path.
            # Fetch it, read the bytes, decode to string, and strip
            # any leading or trailing whitespace and newlines.
            # The result is the raw text content of that README file.

            if content not in seen:
            # Check if we have already seen this content.
            # If the content is already in our set, skip it silently.
            # This means each French decoy message is only printed once
            # even though it appears in thousands of folders.

                seen.add(content)
                # Add this content to the seen set so we do not print it again.

                print(content)
              