"""Repository-root and shipped-data path resolution."""

# Standard Library
import pathlib
import subprocess

# local repo modules
import colorbynumber.constants


#============================================
def get_repo_root() -> pathlib.Path:
	"""Resolve the repository root with the documented Git command.

	Returns:
		The absolute repository-root path.
	"""
	result = subprocess.run(
		["git", "rev-parse", "--show-toplevel"],
		check=True,
		capture_output=True,
		text=True,
	)
	repo_root = pathlib.Path(result.stdout.strip())
	return repo_root


#============================================
def get_default_palette_path() -> pathlib.Path:
	"""Return the absolute path to the shipped Aoartix palette.

	Returns:
		The default marker-palette path.
	"""
	palette_path = get_repo_root() / colorbynumber.constants.DEFAULT_PALETTE_RELATIVE
	return palette_path
