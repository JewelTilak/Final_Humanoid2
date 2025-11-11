PYQt5 Error

1. Download PyQt5 using sudo apt install python3-pyqt5

2. now create virtual env and give it system wide access so that it can use the libs installed using sudo. Type the below command 
python3 -m venv venv --system-site-packages

3. activate venv source/bin/activate

4. pip install all the remaining packages

ps: install opencv-python using sudo only. This is much better