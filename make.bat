@ECHO OFF

pushd %~dp0
cd /d %~dp0

IF "%1" == "" (
    goto clean
) ELSE IF "%1" == "clean" (
    goto clean
) ELSE IF "%1" == "environment" (
    goto environment
) ELSE IF "%1" == "tests" (
    goto tests
) ELSE IF "%1" == "tests_gui" (
    goto tests_gui
) ELSE IF "%1" == "format" (
    goto format
) ELSE IF "%1" == "lint" (
    goto lint
) ELSE IF "%1" == "docs" (
    goto docs
) ELSE (
    echo Invalid Command
    goto end
)

:clean
rmdir /s /q .\docs\build 2>nul
rmdir /s /q .\.pytest_cache 2>nul
rmdir /s /q .\.tox 2>nul
rmdir /s /q .\build 2>nul
rmdir /s /q .\dist 2>nul
rmdir /s /q .\objettoqt.egg-info 2>nul
del /S *.pyc >nul 2>&1
goto end

:environment
python -m pip install --upgrade pip
pip install git+git://github.com/psf/black
pip install -r requirements.txt --upgrade
pip install -r dev_requirements.txt --upgrade
goto end

:tests
python -m pytest tests
goto end

:tests_gui
for /r %%v in (.\tests_gui\test_*.py) do python -m pytest "%%v" -s
goto end

:format
autoflake --remove-all-unused-imports --in-place --recursive .\objettoqt
autoflake --remove-all-unused-imports --in-place --recursive .\tests
autoflake --remove-all-unused-imports --in-place --recursive .\tests_gui
isort objettoqt tests tests_gui .\docs\source\conf.py setup.py -m 3 -l 88 --up --tc --lbt 0 --color
rem # black .\objettoqt .\tests .\tests_gui .\docs\source\conf.py setup.py
forfiles /p .\objettoqt /s /m *.py /c "cmd /c start /b black @path"
forfiles /p .\tests /s /m *.py /c "cmd /c start /b black @path"
forfiles /p .\tests_gui /s /m *.py /c "cmd /c start /b black @path"
black .\docs\source\conf.py
black setup.py
goto end

:lint
rem # Stop if there are Python syntax errors or undefined names.
flake8 .\objettoqt --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 .\tests --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 .\tests_gui --count --select=E9,F63,F7,F82 --show-source --statistics
rem # Exit-zero treats all errors as warnings.
flake8 .\objettoqt --count --exit-zero --ignore=F403,F401,W503,C901,E203,E731 --max-complexity=10 --max-line-length=88 --statistics
flake8 .\tests --count --exit-zero --ignore=F403,F401,W503,C901,E203,E731 --max-complexity=10 --max-line-length=88 --statistics
flake8 .\tests_gui --count --exit-zero --ignore=F403,F401,W503,C901,E203,E731 --max-complexity=10 --max-line-length=88 --statistics
goto end

:docs
%~dp0docs\make html
goto end

:end
popd
