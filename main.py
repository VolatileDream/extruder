#!/usr/bin/env python3

import statemachine as fsm
import os
import sys

def perror(val):
	return
	print(val, file=sys.stderr)

class Mold(fsm.Machine):
	states = [ 'Empty', 'Var', 'Exit' ]
	initial_state = 'Empty'

	def __init__(self, in_io, out, escape_in=b'{{', escape_out=b'}}'):
		self.escape_in = escape_in
		self.escape_out = escape_out
		self.in_io = in_io
		self.out = out
		self.content = b''

	@fsm.event
	def advance(self):

		escape = b''
		escape_index = 0

		perror( "State : " + self.state )
		perror( "EscIn : " + str(self.escape_in) )
		perror( "EscOut: " + str(self.escape_out) )

		while True:
			input = self.in_io.read(1)

			if len(input) == 0:
				if self.state == 'Var':
					# actually an error...do what?
					pass

				self.output()
				yield self.state, 'Exit'
				return

			perror( "input (" + str(input) + ") == self.escape_in[0]): " + str(input[0] == self.escape_in[0]) )
				
			if self.state == 'Empty' and input[0] == self.escape_in[escape_index]:
				escape += input
				escape_index += 1

				perror("Partial EscIn: " + str(escape) )

				if escape_index == len(self.escape_in):
					escape = b''
					escape_index = 0
					yield 'Empty', 'Var'

			elif self.state == 'Var' and input[0] == self.escape_out[escape_index]:
				escape += input
				escape_index += 1

				perror("Partial EscOut: " + str(escape) )

				if escape_index == len(self.escape_out):
					escape = b''
					escape_index = 0
					yield 'Var', 'Empty'

			else:
				if escape_index > 0:
					self.content += escape
					escape_index = 0
					escape = b''

				self.content += input

				if self.state == 'Empty' and len(self.content) > 1024:
					self.output()



	@fsm.transition_to('Empty')
	@fsm.transition_to('Var')
	@fsm.transition_to('Exit')
	def log(self):
		perror("Transition: " + self.state )


	@fsm.transition_from('Var')
	def output_var(self):
		search = str(self.content, "UTF-8")
		found = os.environ.get( search, b'' )

		perror("Searching for: " + search )
		perror("Found : " + found )

		self.content = bytes(found, "UTF-8")
		self.output()


	@fsm.transition_from('Empty')
	@fsm.transition_to('Exit')
	def output(self):
		self.out.write(self.content)
		self.content = b''


if __name__ == "__main__":

	sys.stdin = sys.stdin.detach()
	sys.stdout = sys.stdout.detach()

	m = Mold(sys.stdin, sys.stdout)

	while m.state != 'Exit':
		m.advance()

