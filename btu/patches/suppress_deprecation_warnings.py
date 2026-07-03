import warnings

print("Module 'supress_deprecation_warnings' is loading")


def init():
	warnings.filterwarnings("ignore", category=DeprecationWarning)
	# warnings.filterwarnings("ignore", category=DeprecationWarning, module="offending_package")
