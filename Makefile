up:
	docker-compose build
	docker rm -f  $(docker ps -a -q)
	docker-compose up -d

down:
	docker-compose down

bulid:
	docker-compose build
