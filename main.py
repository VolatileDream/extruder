#!/usr/bin/env python3

import statemachine as fsm


class Mold(fsm.Machine):
	states = [ 'Empty', 'Var', 'Exit' ]
	initial_state = 'Empty'

	def __init__(self, in_io, out, lookup_func, escape_in=b'{{', escape_out=b'}}', log_func=lambda x: x):
		self.lookup = lookup_func
		self.escape_in = escape_in
		self.escape_out = escape_out
		self.in_io = in_io
		self.out = out
		self.content = b''
		self.perror = log_func


	@fsm.event
	def advance(self):

		escape = b''
		escape_index = 0

		self.perror( "State : " + self.state )
		self.perror( "EscIn : " + str(self.escape_in) )
		self.perror( "EscOut: " + str(self.escape_out) )

		while True:
			input = self.in_io.read(1)

			if len(input) == 0:
				if self.state == 'Var':
					# actually an error...do what?
					pass

				self.output()
				yield self.state, 'Exit'
				return

			self.perror( "input (" + str(input) + ") == self.escape_in[0]): " + str(input[0] == self.escape_in[0]) )
				
			if self.state == 'Empty' and input[0] == self.escape_in[escape_index]:
				escape += input
				escape_index += 1

				self.perror("Partial EscIn: " + str(escape) )

				if escape_index == len(self.escape_in):
					escape = b''
					escape_index = 0
					yield 'Empty', 'Var'

			elif self.state == 'Var' and input[0] == self.escape_out[escape_index]:
				escape += input
				escape_index += 1

				self.perror("Partial EscOut: " + str(escape) )

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
		self.perror("Transition: " + self.state )


	@fsm.transition_from('Var')
	def output_var(self):
		# in case they write to self.out
		self.out.flush()

		search = str(self.content, "UTF-8")
		found = self.lookup( search, self.out )

		if found:
			self.content = bytes(found, "UTF-8")
			self.output()

		self.content = b''


	@fsm.transition_from('Empty')
	@fsm.transition_to('Exit')
	def output(self):
		self.out.write(self.content)
		self.content = b''


import os
import subprocess
import sys

def env_lookup(search, _io_out):
	# So that "clean" code can get written
	search = search.lstrip().rstrip()
	return os.environ.get( search, b'' )


def system_lookup(search, io_out ):
	retval = subprocess.call( search, stdout=io_out, shell=True )

	if retval != 0:
		raise Exception("Error building template, sub-process failure: '" + search + "'" )

	return None


import argparse

def arg_parser():
	parser = argparse.ArgumentParser()

	parser.add_argument('-s', '--system', dest='use_system', action='store_true')

	return parser


if __name__ == "__main__":

	parser = arg_parser()

	args = parser.parse_args()

	lookup_func = env_lookup
	if args.use_system:
		lookup_func = system_lookup

	sys.stdin = sys.stdin.detach()
	sys.stdout = sys.stdout.detach()

	m = Mold(sys.stdin, sys.stdout, lookup_func)

	while m.state != 'Exit':
		m.advance()

