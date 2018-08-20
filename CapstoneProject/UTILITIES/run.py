# Copyright (C) 2011-2016 Vas Vasiliadis
# University of Chicago
##
__author__ = 'Vas Vasiliadis <vas@uchicago.edu>'

import sys
import time
import driver

# A rudimentary timer for coarse-grained profiling
class Timer(object):
	def __init__(self, verbose=False):
		self.verbose = verbose

	def __enter__(self):
		self.start = time.time()
		return self

	def __exit__(self, *args):
		self.end = time.time()
		self.secs = self.end - self.start
		self.msecs = self.secs * 1000  # millisecs
		if self.verbose:
			print "Elapsed time: %f ms" % self.msecs

if __name__ == '__main__':
	# Call the AnnTools pipeline
	if len(sys.argv) > 1:
		input_file_name = sys.argv[1]
		with Timer() as t:
			driver.run(input_file_name, 'vcf')
		print "Total runtime: %s seconds" % t.secs

	else:
		print 'A valid .vcf file must be provided as input to this program.'