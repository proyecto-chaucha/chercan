.PHONY: install install-pip setup shell api freeze nohup

a api:
	python3 src/api/__init__.py

n nohup:
	nohup python3 src/api/__init__.py &

i install:
	pipenv install

ip install-pip:
	pip3 install -r requirements.txt

sh shell:
	pipenv shell

s setup:
	python3 __main__.py

f freeze:
	pip3 freeze > requirements.txt