# iia-bomberman-88747-88811
Bomberman clone for AI teaching

![Demo](https://github.com/dgomes/iia-ia-bomberman/raw/master/data/DemoBomberman.gif)

## How to install

Make sure you are running Python 3.5 (or later).

Creating Virtual Environment:

`$ python3 -m venv <nome do virtualenv>`
`$ source <nome do virtualenv>/bin/activate`

Install requirements:

`$ pip install -r requirements.txt`


## How to play

open 3 terminals:

`$ python3 server.py`

`$ python3 viewer.py`

`$ python3 client.py`

to play using the sample client make sure the client pygame hidden window has focus

### Keys

Directions: arrows

*A*: 'a' - detonates (only after picking up the detonator powerup)

*B*: 'b' - drops bomb

## Debug Installation

Make sure pygame is properly installed:

python -m pygame.examples.aliens

# Tested on:
- Ubuntu 18.04
- OSX 10.14.6
- Windows 10.0.18362

