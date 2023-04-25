![OMSI](https://raw.githubusercontent.com/ExtraConcentratedJuice/neoOMSI/main/omsi.png)
# neoOMSI | Modern Online Measurement of Student Insight

- neoOMSI is an unofficial modern [OMSI](https://github.com/matloff/omsi) client.

- neoOMSI uses the original OMSI protocol. It is intended to be used as a drop-in replacement (not tested) for the original OMSI client.

- neoOMSI shares the cross-platform compatibility of OMSI.

- neoOMSI shares OMSI's strict adherence to the Python standard library, except for a 1-file include [PySimpleGUI](https://github.com/PySimpleGUI/PySimpleGUI).py which is a tkinter wrapper. That is, it can be run with a bare Python installation.

On top of what OMSI already provides, neoOMSI also has:

- Smooth connection and answer submit. Socket communication is done in a background thread so that the GUI stays responsive.

- A separate "Run" button, so you aren't forced to wait for the client to submit.

- Cleaner design and an easier-to-use, intuitive UI.

- Easy to configure, and configurable while connected as well. No more PATH issues when you can just open settings and pick your executables and PDF!

- Saves your answers in separate directories, so you can go back and look at them even after taking another exam.

- Somewhat better error handling than the original OMSI

## How to use

You must have Python 3.6+ installed to run neoOMSI.

Clone the repo. Then, open a terminal in the cloned directory and run

`python omsi_gui.py`

You should click on the "Settings" button to configure the client.

## Disclaimer

This is NOT an official client! You will most likely get in trouble if you attempt to use this on an actual exam, so don't do that. This project was developed for fun!
