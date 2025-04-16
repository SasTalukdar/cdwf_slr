---

# Abstract Scraper

This tool automates the process of downloading abstracts via API and manually extracting them from article pages when needed.

---

## 📦 System Requirements

1. **Chrome WebDriver**  
   Download and install the supported WebDriver:  
   👉 [https://googlechromelabs.github.io/chrome-for-testing/](https://googlechromelabs.github.io/chrome-for-testing/)

2. **Anaconda**  
   Install [Anaconda](https://www.anaconda.com/) if it's not already installed.

3. **Install Required Packages**

   Using conda and pip:

   ```bash
   conda install -c conda-forge selenium
   pip install elsapy
   conda install -c conda-forge pyperclip
   ```

---

## 🚀 How to Run

```bash
python sel_trial9.py Tag03_04.json
```

1. The script starts by downloading abstracts using the API.  
   ⏳ **Wait until the API extraction is complete.**

2. After that, the script opens each article URL one by one.

---

## 🧭 User Interaction Guide

- Accept all cookie banners and solve any CAPTCHA that appears.
- Then press **Enter** in the terminal.

You'll be prompted with the following options:

| Key   | Action                                                                 |
|-------|------------------------------------------------------------------------|
| Enter | Accept the printed abstract                                            |
| `p`   | Paste from clipboard (if abstract wasn’t captured correctly)           |
| `m`   | Manual mode – opens a separate browser window                          |
| `g`   | Use Google Scholar (copy abstract from the pre-opened tab)             |
| `n`   | Abstract not available                                                 |
| `r`   | Reject (not a research article)                                        |

---

### ✅ Decision Guide

- If the URL **is not** a research article → Press `r`
- If the abstract **is correctly** printed → Press `Enter`
- If the abstract is **wrong or missing** → Copy it manually and press `p`
- If the abstract is **not on the page**, copy and search the article title in Google Scholar → Copy abstract and press `g`
- If CAPTCHA can't be solved (e.g., JSTOR):
  - Press `m` to open a manual browser window
  - Solve CAPTCHA → select abstract text → right-click → _Save selected text_
  - Close the window and press `Enter`
- If no abstract is available anywhere → Press `n`

---

📌 **Note:** The script **automatically updates** the input JSON file with the progress.

---
