import subprocess
from ipywidgets import widgets, Layout
from IPython.display import display


def EDM(filename, with_button=False):
	def launch(sender=None):
		subprocess.Popen(["edm", "-x", filename])
	if with_button:
		title = filename
		if isinstance(with_button, str):
			title = with_button
		edm_button = Button(title, launch)
		display(edm_button)
	else:
		launch()

default_button_layout = Layout(width='30%')

class Button(widgets.Button):
	def __init__(self, text, command, layout=default_button_layout):
		super(Button, self).__init__(description=text, layout=layout)
		self.on_click(command)

