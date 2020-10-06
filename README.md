This is the civility bot!

To run locally:

    - Obtain env var values from Geoff
        - from terminal
            - export mongo='mongo-from-geoff'
    - Obtain mongo access from Geoff and whitelist your IP
    - Create a python 3.7 venv in directory named venv
        - cd to root diretory of project
        - python3 -m venv venv
    - Activate venv: source venv/bin/activate
        - confirm you are on the correct python version
                - python3
                - import sys
                - sys.version_info[:]
                - expect output:
                    - (3, 7, 3, 'final', 0)
                - exit()
    - Install requirements: pip3 install -r requirements.txt
    - Run the application: python3 app.py
    - decative venv when done from terminal
        - deactivate
