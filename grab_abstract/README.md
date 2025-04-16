System Requirements:
  (1) Get and install the supported webdriver from https://googlechromelabs.github.io/chrome-for-testing/
  (2) Install anaconda (if already not installed)
  (3) Install Selenium: conda install conda-forge::selenium
  (4) Install Elsapy: pip install elsapy
  (5) Install Pyperclip: conda install conda-forge::pyperclip

Instruction for running the script:
 (1) Run the script: python sel_trial9.py Tag03_04.json 
     The script starts with automated downloads of abstracts using API. Wait for the API download to be over.
 (2) After the API extraction is done, the scipt opens the url one at a time.
     - Accept all cookies statements and solve any available captchs. Then press enter.
     - You will see the following options:
          Press Enter to accept, 'p' to paste from clipboard, 'm' for manual, 'g' for Google Scholar, 'n' for not available, 'r' for non-article
     - Check if the url is actually a research article. If not, reject the article by pressing 'r'
     - If it is a normal research article, and the abstract is present in the page, the script should print it. If it is correct, press enter.
     - If the abstract is not captured properly, copy the abstract text and press p
     - If the capcha is not being solved, (e.g. for jstor) press m. It opens a different browser window. Solve the capcha, and select the abstract text, right click and click on "save selected text". Close the window. Press your if successful.
     - press 'n' if the abstract is not available.
  
  The script keeps on updating the input file.
