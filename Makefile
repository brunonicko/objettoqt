.PHONY: clean environment tests format lint docs

clean:
	rm -rf ./docs/build .mypy_cache .pytest_cache .tox build dist objettoqt.egg-info
	find . -name '*.pyc' -delete
environment:
	python -m pip install --upgrade pip
	pip install -r requirements.txt --upgrade
	pip install -r dev_requirements.txt --upgrade
tests:
	python -m pytest tests
	python -m pytest objettoqt --doctest-modules
	python -m pytest docs --doctest-glob="*.rst"
	python -m pytest README.rst --doctest-glob="*.rst"
format:
	autoflake --remove-all-unused-imports --in-place --recursive .\objettoqt
	autoflake --remove-all-unused-imports --in-place --recursive .\tests
	autoflake --remove-all-unused-imports --in-place --recursive .\tests_gui
	isort objettoqt tests tests_gui ./docs/source/conf.py setup.py -m 3 -l 88 --up --tc --lbt 0 --color
	black objettoqt tests tests_gui ./docs/source/conf.py setup.py
lint:
	# Stop if there are Python syntax errors or undefined names.
	flake8 objettoqt --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 tests --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 tests_gui --count --select=E9,F63,F7,F82 --show-source --statistics
	# Exit-zero treats all errors as warnings.
	flake8 objettoqt --count --exit-zero --ignore=F403,F401,W503,C901,E203,E731 --max-complexity=10 --max-line-length=88 --statistics
	flake8 tests --count --exit-zero --ignore=F403,F401,W503,C901,E203,E731 --max-complexity=10 --max-line-length=88 --statistics
	flake8 tests_gui --count --exit-zero --ignore=F403,F401,W503,C901,E203,E731 --max-complexity=10 --max-line-length=88 --statistics
docs:
	cd docs; make html
