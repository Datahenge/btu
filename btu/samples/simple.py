"""Plain callable sample with no BTU awareness."""


def ordinary_function(number_to_count: int) -> None:
	"""Count with short sleeps; usable as a BTU Task target or Task Component."""
	import time

	for _ in range(0, number_to_count):
		time.sleep(0.5)
	print(f"An ordinary function finished counting to {number_to_count}.")
