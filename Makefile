.PHONY: clean environment tests mypy format lint docs

clean:
	rm -rf ./docs/build .mypy_cache .pytest_cache dist
	find . -name '*.pyc' -delete
environment:
	python -m pip install --upgrade pip
	pip install -r requirements.txt --upgrade
	pip install -r dev_requirements.txt --upgrade
tests:
	python -m pytest tests
	python -m pytest objettoqt --doctest-modules
mypy:
	mypy objettoqt
format:
	autoflake --remove-all-unused-imports --in-place --recursive .\objettoqt
	autoflake --remove-all-unused-imports --in-place --recursive .\tests
	isort objettoqt tests ./docs/source/conf.py setup.py -m 3 -l 88 --up --tc --lbt 0 --color
	black objettoqt tests ./docs/source/conf.py setup.py
lint:
	# Stop if there are Python syntax errors or undefined names.
	flake8 objettoqt --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 tests --count --select=E9,F63,F7,F82 --show-source --statistics
	# Exit-zero treats all errors as warnings.
	flake8 objettoqt --count --exit-zero --ignore=F403,F401,W503,C901,E203 --max-complexity=10 --max-line-length=88 --statistics
	flake8 tests --count --exit-zero --ignore=F403,F401,W503,C901,E203 --max-complexity=10 --max-line-length=88 --statistics
docs:
	cd docs; make html